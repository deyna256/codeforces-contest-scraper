"""Service for handling contest-related operations."""

import asyncio

from loguru import logger

from domain.models.contest import Contest, ContestProblem
from domain.models.editorial import ContestEditorial
from infrastructure.parsers import (
    ContestAPIClientProtocol,
    ContestPageParserProtocol,
    URLParser,
)
from infrastructure.parsers.editorial_content_parser import EditorialContentParser


class ContestService:
    """Service for managing Codeforces contests."""

    def __init__(
        self,
        *,
        api_client: ContestAPIClientProtocol,
        page_parser: ContestPageParserProtocol,
        url_parser: type[URLParser] = URLParser,
        editorial_parser: EditorialContentParser | None = None,
    ):
        """Initialize service with dependencies."""
        self.api_client = api_client
        self.page_parser = page_parser
        self.url_parser = url_parser
        self.editorial_parser = editorial_parser

    async def get_contest(self, contest_id: str) -> Contest:
        """Get contest details using Codeforces API and page parser."""
        logger.debug(f"Getting contest via service: {contest_id}")

        # Fetch contest standings from API
        standings_data = await self.api_client.fetch_contest_standings(contest_id)
        result = standings_data.get("result", {})
        contest_data = result.get("contest", {})
        problems_list = result.get("problems", [])

        # Get contest title from API
        contest_title = contest_data.get("name", f"Contest {contest_id}")

        # Fetch problemset.problems for ratings and tags
        logger.debug("Fetching problemset.problems for ratings and tags")
        problemset_data = await self.api_client.fetch_problemset_problems()
        all_problems = problemset_data.get("result", {}).get("problems", [])

        # Create a map for quick lookup: (contestId, index) -> problem data
        problem_map = {}
        for problem in all_problems:
            key = (str(problem.get("contestId")), problem.get("index"))
            problem_map[key] = problem

        # Parse contest page for editorial URL
        contest_page_data = None
        try:
            contest_page_data = await self.page_parser.parse_contest_page(contest_id)
        except Exception:
            logger.warning(f"Failed to parse contest page for {contest_id}", exc_info=True)
            # Continue without editorial URL

        editorials = contest_page_data.editorial_urls if contest_page_data else []

        # Parse each problem page for description and limits (in parallel)
        logger.debug(f"Parsing {len(problems_list)} problems in parallel")
        problem_tasks = []
        for problem_data in problems_list:
            problem_id = problem_data.get("index")
            problem_tasks.append(
                self._fetch_problem_details(contest_id, problem_id, problem_data, problem_map)
            )

        problem_results = await asyncio.gather(*problem_tasks, return_exceptions=True)

        # Filter out failed results and create ContestProblem objects
        contest_problems = []
        failed_count = 0
        for result in problem_results:
            if isinstance(result, Exception):
                failed_count += 1
                continue
            if result is not None:
                contest_problems.append(result)

        if failed_count > 0:
            logger.warning(f"Failed to parse {failed_count} problem(s) for contest {contest_id}")

        # Try to fetch editorial content and populate explanations
        if self.editorial_parser and editorials:
            try:
                # Build expected problems list: [(contest_id, letter), ...]
                expected_problems = [
                    (problem.contest_id, problem.id.upper()) for problem in contest_problems
                ]

                # Parse editorial with context
                editorial_data = await self.editorial_parser.parse_editorial_content(
                    contest_id, editorials, expected_problems=expected_problems
                )

                # Create explanation map with contest-aware filtering
                explanation_map = {}
                other_contest_count = 0
                no_contest_id_count = 0

                for edit in editorial_data.editorials:
                    problem_letter = edit.problem_id.upper()

                    # Prefer exact contest_id match
                    if edit.contest_id == contest_id:
                        explanation_map[problem_letter] = edit.analysis_text

                    # Fallback: if no contest_id, use letter-only matching (with warning)
                    elif edit.contest_id is None and problem_letter not in explanation_map:
                        logger.warning(
                            f"Editorial for problem {problem_letter} has no contest_id, "
                            f"using fallback matching (may be incorrect for multi-contest editorials)"
                        )
                        explanation_map[problem_letter] = edit.analysis_text
                        no_contest_id_count += 1

                    # Explicitly skip editorials from other contests
                    elif edit.contest_id and edit.contest_id != contest_id:
                        logger.debug(
                            f"Skipping editorial {edit.contest_id}/{problem_letter} "
                            f"(requested: {contest_id})"
                        )
                        other_contest_count += 1

                # Update problems with explanations
                for problem in contest_problems:
                    problem.explanation = explanation_map.get(problem.id.upper())

                matched_count = len([p for p in contest_problems if p.explanation])
                logger.info(
                    f"Matched {matched_count}/{len(contest_problems)} problems with editorials "
                    f"(parsed {len(editorial_data.editorials)} total, "
                    f"skipped {other_contest_count} from other contests, "
                    f"{no_contest_id_count} without contest_id)"
                )

            except Exception as e:
                logger.warning(f"Failed to fetch editorial content for contest {contest_id}: {e}")
                # Continue without explanations

        # Create Contest object
        contest = Contest(
            contest_id=contest_id,
            title=contest_title,
            problems=contest_problems,
            editorials=editorials,
        )

        logger.info(
            f"Successfully fetched contest {contest_id} with {len(contest_problems)} problems and {len(editorials)} editorial(s)"
        )
        return contest

    async def _fetch_problem_details(
        self,
        contest_id: str,
        problem_id: str,
        api_problem_data: dict,
        problem_map: dict,
    ) -> ContestProblem | None:
        """Fetch detailed information for a single problem."""
        try:
            # Try to get rating and tags from contest.standings first (api_problem_data)
            # If not available, fall back to problemset.problems
            rating = api_problem_data.get("rating")
            tags = api_problem_data.get("tags", [])

            # Fallback to problemset.problems if not in standings
            if rating is None or not tags:
                key = (contest_id, problem_id)
                problem_metadata = problem_map.get(key, {})
                if rating is None:
                    rating = problem_metadata.get("rating")
                if not tags:
                    tags = problem_metadata.get("tags", [])

            # Get problem name from API data
            problem_title = api_problem_data.get("name", f"Problem {problem_id}")

            # Parse problem page for description and limits
            problem_page_data = None
            try:
                problem_page_data = await self.page_parser.parse_problem_in_contest(
                    contest_id, problem_id
                )
            except Exception:
                logger.warning(
                    f"Failed to parse problem page {contest_id}/{problem_id}", exc_info=True
                )
                # Continue without description/limits

            description = problem_page_data.description if problem_page_data else None
            time_limit = problem_page_data.time_limit if problem_page_data else None
            memory_limit = problem_page_data.memory_limit if problem_page_data else None

            # Create ContestProblem object
            contest_problem = ContestProblem(
                contest_id=contest_id,
                id=problem_id,
                title=problem_title,
                statement=description,
                rating=rating,
                tags=tags,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

            logger.debug(f"Successfully fetched problem {contest_id}/{problem_id}")
            return contest_problem

        except Exception:
            logger.error(
                f"Failed to fetch problem details for {contest_id}/{problem_id}", exc_info=True
            )
            return None

    async def get_contest_by_url(self, url: str) -> Contest:
        """Get contest by Codeforces contest URL."""
        logger.debug(f"Getting contest by URL: {url}")

        # Parse URL to get identifier (gym URLs rejected by parser)
        identifier = self.url_parser.parse_contest_url(url)

        return await self.get_contest(identifier.contest_id)

    async def get_editorial_content(
        self, contest_id: str, editorial_urls: list[str] | None = None
    ) -> ContestEditorial:
        """
        Get editorial content for a contest, segmented by individual problems.

        Args:
            contest_id: Contest identifier
            editorial_urls: Optional editorial URLs (will fetch from contest page if not provided)

        Returns:
            ContestEditorial with individual problem analyses

        Raises:
            EditorialNotFoundError: If no editorial URLs available
        """
        logger.debug(f"Getting editorial content for contest: {contest_id}")

        if not self.editorial_parser:
            from infrastructure.parsers.editorial_content_parser import EditorialNotFoundError

            raise EditorialNotFoundError(contest_id)

        # Get editorial URLs if not provided
        if editorial_urls is None:
            contest = await self.get_contest(contest_id)
            editorial_urls = contest.editorials

        if not editorial_urls:
            from infrastructure.parsers.editorial_content_parser import EditorialNotFoundError

            raise EditorialNotFoundError(contest_id)

        # Parse editorial content
        editorial_data = await self.editorial_parser.parse_editorial_content(
            contest_id, editorial_urls
        )

        logger.info(
            f"Successfully parsed editorial for contest {contest_id} with {len(editorial_data.editorials)} problems"
        )

        return editorial_data
