"""Service for handling problem-related operations."""

from loguru import logger

from domain.models.problem import Problem
from domain.models.identifiers import ProblemIdentifier
from infrastructure.parsers import URLParser, APIClientProtocol, ProblemPageParserProtocol


class ProblemService:
    """Service for managing Codeforces problems."""

    def __init__(
        self,
        *,
        api_client: APIClientProtocol,
        page_parser: ProblemPageParserProtocol,
        url_parser: type[URLParser] = URLParser,
    ):
        """Initialize service with dependencies."""
        self.api_client = api_client
        self.page_parser = page_parser
        self.url_parser = url_parser

    async def get_problem(self, identifier: ProblemIdentifier) -> Problem:
        """Get problem details using Codeforces API and page parser."""
        logger.debug(f"Getting problem via service: {identifier}")

        # Get basic info from Codeforces API
        problem = await self.api_client.get_problem(identifier)

        # Get description and limits from problem page
        try:
            problem_data = await self.page_parser.parse_problem_page(identifier)
            problem.description = problem_data.description
            problem.time_limit = problem_data.time_limit
            problem.memory_limit = problem_data.memory_limit
        except Exception as e:
            logger.debug(f"Failed to parse problem page data: {e}")
            # Continue without description/limits - they're optional

        return problem

    async def get_problem_by_url(self, url: str) -> Problem:
        """Get problem by Codeforces problem URL."""
        logger.debug(f"Getting problem by URL: {url}")

        # Parse URL to get identifier
        identifier = self.url_parser.parse(url)
        return await self.get_problem(identifier)
