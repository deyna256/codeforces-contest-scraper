import re
from typing import Optional

from bs4 import BeautifulSoup
from loguru import logger

from codeforces_editorial.models import ProblemData, ProblemIdentifier
from codeforces_editorial.utils.exceptions import ParsingError
from codeforces_editorial.fetchers.http_client import HTTPClient
from codeforces_editorial.parsers.url_parser import URLParser


class ProblemPageParser:
    def __init__(self, http_client: Optional[HTTPClient] = None):
        """Initialize parser."""
        self.http_client = http_client or HTTPClient()
        self._should_close_client = http_client is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_client:
            self.http_client.close()

    def parse_problem_page(self, identifier: ProblemIdentifier) -> ProblemData:
        """
        Parse problem page and extract data.

        Args:
            identifier: Problem identifier

        Returns:
            ProblemData with extracted information

        Raises:
            ParsingError: If parsing fails
        """
        url = URLParser.build_problem_url(identifier)
        logger.info(f"Parsing problem page: {url}")

        try:
            html = self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            title = self._extract_title(soup)

            contest_name = self._extract_contest_name(soup)

            time_limit = self._extract_time_limit(soup)
            memory_limit = self._extract_memory_limit(soup)

            description = self._extract_description(soup)

            tags = self._extract_tags(soup)

            problem_data = ProblemData(
                identifier=identifier,
                title=title,
                url=url,
                contest_name=contest_name,
                description=description,
                time_limit=time_limit,
                memory_limit=memory_limit,
                tags=tags,
            )

            logger.info(f"Successfully parsed problem: {title}")
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page: {e}")
            raise ParsingError(f"Failed to parse problem page {url}: {e}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract problem title."""
        try:
            # Strip leading problem identifiers like "A." or "1234A."
            title_div = soup.find("div", class_="title")
            if title_div:
                title_text = title_div.get_text(strip=True)
                title_text = re.sub(r"^[A-Z]\d*\.\s*", "", title_text)
                return title_text

            # Fallback: try header
            header = soup.find("div", class_="header")
            if header:
                title_elem = header.find("div", class_="title")
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    title_text = re.sub(r"^[A-Z]\d*\.\s*", "", title_text)
                    return title_text

            return "Unknown Problem"

        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")
            return "Unknown Problem"

    def _extract_contest_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract contest name."""
        try:
            breadcrumbs = soup.find("div", class_="breadcrumbs")
            if breadcrumbs:
                links = breadcrumbs.find_all("a")
                if len(links) > 0:
                    return links[0].get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Failed to extract contest name: {e}")
            return None

    def _extract_time_limit(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract time limit."""
        try:
            time_limit_div = soup.find("div", class_="time-limit")
            if time_limit_div:
                return time_limit_div.get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Failed to extract time limit: {e}")
            return None

    def _extract_memory_limit(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract memory limit."""
        try:
            memory_limit_div = soup.find("div", class_="memory-limit")
            if memory_limit_div:
                return memory_limit_div.get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Failed to extract memory limit: {e}")
            return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract problem description (first few paragraphs)."""
        try:
            statement = soup.find("div", class_="problem-statement")
            if statement:
                paragraphs = statement.find_all("p", limit=3)
                if paragraphs:
                    return "\n\n".join(p.get_text(strip=True) for p in paragraphs)
            return None
        except Exception as e:
            logger.warning(f"Failed to extract description: {e}")
            return None

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        """Extract problem tags."""
        try:
            tags = []
            tag_elements = soup.find_all("span", class_="tag-box")
            for elem in tag_elements:
                tag_text = elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            return tags
        except Exception as e:
            logger.warning(f"Failed to extract tags: {e}")
            return []


def parse_problem(url: str, http_client: Optional[HTTPClient] = None) -> ProblemData:
    """
    Convenience function to parse problem from URL.

    Args:
        url: Problem URL
        http_client: Optional HTTP client

    Returns:
        ProblemData
    """
    from codeforces_editorial.parsers.url_parser import parse_problem_url

    identifier = parse_problem_url(url)

    with ProblemPageParser(http_client) as parser:
        return parser.parse_problem_page(identifier)
