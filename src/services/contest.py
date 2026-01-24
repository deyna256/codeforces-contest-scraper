"""Service for handling contest-related operations."""

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from domain.models.contest import Contest, ContestProblem
from domain.models.editorial import ContestEditorial
from infrastructure.errors import GymContestError
from infrastructure.parsers import (
    ContestAPIClientProtocol,
    ContestPageParserProtocol,
    URLParser,
)
from infrastructure.parsers.editorial_content_parser import EditorialContentParser

if TYPE_CHECKING:
    pass


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

        # Validate: reject gym contests
        contest_type = contest_data.get("type", "")
        if "GYM" in contest_type.upper():
            logger.error(f"Gym contest not supported: {contest_id}")
            raise GymContestError(f"Gym contests are not supported: {contest_id}")

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
            # Get rating and tags from problemset.problems
            key = (contest_id, problem_id)
            problem_metadata = problem_map.get(key, {})
            rating = problem_metadata.get("rating")
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

        # Parse URL to get identifier
        identifier = self.url_parser.parse_contest_url(url)

        # Validate: reject gym contests
        if identifier.is_gym:
            logger.error(f"Gym contest not supported: {identifier}")
            raise GymContestError(f"Gym contests are not supported: {identifier}")

        return await self.get_contest(identifier.contest_id)

    async def get_editorial_content(
        self,
        contest_id: str,
        editorial_urls: list[str] | None = None
    ) -> ContestEditorial:
        """
        Get editorial content for a contest, segmented by individual problems.

        Args:
            contest_id: Contest identifier
            editorial_urls: Optional editorial URLs (will fetch from contest page if not provided)

        Returns:
            ContestEditorial with individual problem analyses

        Raises:
            GymContestError: If contest is a gym contest
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
