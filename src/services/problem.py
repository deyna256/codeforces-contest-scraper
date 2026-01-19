"""Service for handling problem-related operations."""

from loguru import logger

from domain.models import Problem, ProblemIdentifier
from domain.parsers.problem_page import ProblemPageParser
from domain.parsers.url_parser import URLParser
from infrastructure.codeforces_client import CodeforcesApiClient


class ProblemService:
    """Service for managing Codeforces problems."""

    def __init__(self):
        """Initialize service."""
        # Create HTTP client directly instead of using dependency injection
        # to avoid async cleanup issues with curl_cffi
        from infrastructure.http_client import AsyncHTTPClient

        self.http_client = AsyncHTTPClient()
        self.client = CodeforcesApiClient(self.http_client)
        self.parser = ProblemPageParser(self.http_client)

    async def get_problem(self, identifier: ProblemIdentifier) -> Problem:
        """Get problem details using Codeforces API and page parser."""
        logger.info(f"Getting problem via service: {identifier}")

        # Get basic info from Codeforces API
        problem = await self.client.get_problem(identifier)

        # Get description and limits from problem page
        try:
            problem_data = await self.parser.parse_problem_page(identifier)
            problem.description = problem_data.description
            problem.time_limit = problem_data.time_limit
            problem.memory_limit = problem_data.memory_limit
        except Exception as e:
            logger.warning(f"Failed to parse problem page data: {e}")
            # Continue without description/limits - they're optional

        return problem

    async def get_problem_by_url(self, url: str) -> Problem:
        """Get problem by Codeforces problem URL."""
        logger.info(f"Getting problem by URL: {url}")

        # Parse URL to get identifier
        identifier = URLParser.parse(url)
        return await self.get_problem(identifier)
