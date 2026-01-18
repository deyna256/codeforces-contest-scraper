"""Service for handling problem-related operations."""

from loguru import logger

from domain.models import Problem, ProblemIdentifier
from domain.parsers.url_parser import URLParser
from infrastructure.codeforces_client import CodeforcesApiClient


class ProblemService:
    """Service for managing Codeforces problems."""

    def __init__(self):
        """Initialize service."""
        # Create HTTP client directly instead of using dependency injection
        # to avoid async cleanup issues with curl_cffi
        from infrastructure.http_client import AsyncHTTPClient
        self.client = CodeforcesApiClient(AsyncHTTPClient())

    async def get_problem(self, identifier: ProblemIdentifier) -> Problem:
        """Get problem details using Codeforces API."""
        logger.info(f"Getting problem via service: {identifier}")
        return await self.client.get_problem(identifier)

    async def get_problem_by_url(self, url: str) -> Problem:
        """Get problem by Codeforces problem URL."""
        logger.info(f"Getting problem by URL: {url}")

        # Parse URL to get identifier
        identifier = URLParser.parse(url)
        return await self.get_problem(identifier)