"""Parser for extracting problem data from HTML pages."""

from typing import Optional, TYPE_CHECKING

from bs4 import BeautifulSoup
from loguru import logger

from domain.models.identifiers import ProblemIdentifier
from domain.models.parsing import ProblemData

from .interfaces import ParsingError

from .interfaces import ProblemPageParserProtocol
from .html_utils import extract_time_limit, extract_memory_limit, extract_description

if TYPE_CHECKING:
    from infrastructure.http_client import AsyncHTTPClient


class ProblemPageParser(ProblemPageParserProtocol):
    """Parser for extracting data from Codeforces problem HTML pages."""

    def __init__(self, http_client: Optional["AsyncHTTPClient"] = None):
        """
        Initialize parser.

        Args:
            http_client: Async HTTP client instance
        """
        self.http_client = http_client

    async def parse_problem_page(self, identifier: ProblemIdentifier) -> ProblemData:
        """
        Parse problem page and extract data.
        """
        from infrastructure.parsers import URLParser

        url = URLParser.build_problem_url(identifier)
        logger.debug(f"Parsing problem page: {url}")

        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract minimal metadata using shared HTML parsing utilities
            description = extract_description(soup)
            time_limit = extract_time_limit(soup)
            memory_limit = extract_memory_limit(soup)

            problem_data = ProblemData(
                identifier=identifier,
                description=description,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

            logger.debug(f"Successfully parsed problem: {identifier}")
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page for {identifier}", exc_info=True)
            raise ParsingError(f"Failed to parse problem page {url}: {e}") from e
