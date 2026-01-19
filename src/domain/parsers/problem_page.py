"""Parser for Codeforces problem pages."""

from typing import Optional, TYPE_CHECKING

from bs4 import BeautifulSoup
from loguru import logger

from domain.models import ProblemData, ProblemIdentifier
from domain.exceptions import ParsingError
from domain.parsers.url_parser import URLParser

if TYPE_CHECKING:
    from infrastructure.http_client import AsyncHTTPClient


class ProblemPageParser:
    """Parser for extracting data from Codeforces problem pages."""

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
        url = URLParser.build_problem_url(identifier)
        logger.info(f"Parsing problem page: {url}")

        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract minimal metadata
            description = self._extract_description(soup)
            time_limit = self._extract_time_limit(soup)
            memory_limit = self._extract_memory_limit(soup)

            problem_data = ProblemData(
                identifier=identifier,
                description=description,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

            logger.info(f"Successfully parsed problem: {identifier}")
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page: {e}")
            raise ParsingError(f"Failed to parse problem page {url}: {e}") from e

    def _extract_time_limit(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract time limit from problem page."""
        try:
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
                return None

            header = problem_statement.find("div", class_="header")
            if not header:
                return None

            time_limit = header.find("div", class_="time-limit")
            if time_limit:
                # Extract just the value, e.g., "2 seconds" from "time limit per test2 seconds"
                text = time_limit.get_text(strip=True)
                # Remove the label part
                if "time limit per test" in text.lower():
                    text = text.lower().replace("time limit per test", "").strip()
                return text

            return None
        except Exception as e:
            logger.warning(f"Failed to extract time limit: {e}")
            return None

    def _extract_memory_limit(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract memory limit from problem page."""
        try:
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
                return None

            header = problem_statement.find("div", class_="header")
            if not header:
                return None

            memory_limit = header.find("div", class_="memory-limit")
            if memory_limit:
                # Extract just the value, e.g., "256 megabytes" from "memory limit per test256 megabytes"
                text = memory_limit.get_text(strip=True)
                # Remove the label part
                if "memory limit per test" in text.lower():
                    text = text.lower().replace("memory limit per test", "").strip()
                return text

            return None
        except Exception as e:
            logger.warning(f"Failed to extract memory limit: {e}")
            return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract problem statement/description (without time/memory limits)."""
        try:
            # Find the problem statement block
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
                logger.warning("Problem statement block not found")
                return None

            # Extract all text from the problem statement, preserving structure
            # We'll get text from all divs within problem-statement
            text_parts = []

            # Get the header (title only, not limits)
            header = problem_statement.find("div", class_="header")
            if header:
                title_div = header.find("div", class_="title")
                if title_div:
                    text_parts.append(title_div.get_text(strip=True))

            # Get main sections: input, output, etc.
            for section_class in [
                "",
                "input-specification",
                "output-specification",
                "sample-tests",
                "note",
            ]:
                if section_class:
                    section = problem_statement.find("div", class_=section_class)
                else:
                    # First div without class is usually the problem description
                    section = problem_statement.find("div", recursive=False)

                if section and section_class != "header":
                    section_text = section.get_text(separator="\n", strip=True)
                    if section_text:
                        text_parts.append(section_text)

            if text_parts:
                return "\n\n".join(text_parts)

            # Fallback: get all text from problem-statement
            return problem_statement.get_text(separator="\n", strip=True)

        except Exception as e:
            logger.warning(f"Failed to extract description: {e}")
            return None
