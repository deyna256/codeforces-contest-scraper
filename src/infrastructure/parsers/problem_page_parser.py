"""Parser for extracting problem data from HTML pages."""

from typing import Optional, TYPE_CHECKING

from bs4 import BeautifulSoup
from loguru import logger

from domain.models.identifiers import ProblemIdentifier
from domain.models.parsing import ProblemData

from .interfaces import ParsingError

from .interfaces import ProblemPageParserProtocol

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

            logger.debug(f"Successfully parsed problem: {identifier}")
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page for {identifier}", exc_info=True)
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
        except Exception:
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
        except Exception:
            return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract problem statement/description (without time/memory limits)."""
        try:
            # Find the problem statement block
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
                return None

            # Extract all text from the problem statement, preserving structure
            # We'll get text from all divs within problem-statement except header
            text_parts = []

            # Get main sections: input, output, etc. (excluding header)
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
                    # Find the first non-header div (usually the problem description)
                    all_divs = problem_statement.find_all("div", recursive=False)
                    for div in all_divs:
                        if not div.get("class") or div.get("class") == [""]:
                            section = div
                            break
                    else:
                        section = None

                if section:
                    section_text = section.get_text(separator="\n", strip=True)
                    if section_text:
                        text_parts.append(section_text)

            if text_parts:
                return "\n\n".join(text_parts)

            # Fallback: get all text from problem-statement
            return problem_statement.get_text(separator="\n", strip=True)

        except Exception:
            return None
