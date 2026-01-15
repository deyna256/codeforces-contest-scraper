"""Parser for Codeforces problem pages."""

import re
from typing import Optional, TYPE_CHECKING

from bs4 import BeautifulSoup, Tag
from loguru import logger

from domain.models import ProblemData, ProblemIdentifier
from domain.exceptions import ParsingError
from domain.parsers.url_parser import URLParser

if TYPE_CHECKING:
    from infrastructure.http_client import AsyncHTTPClient


class ProblemPageParser:
    """Parser for extracting data from Codeforces problem pages."""

    # Constants
    MATERIALS_CAPTION_KEYWORD = "materials"
    RELEVANT_URL_SEGMENTS = ("/blog/", "/contest/")
    CODEFORCES_BASE_URL = "https://codeforces.com"

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
        logger.debug(
            f"Parsing problem page for problem_id={identifier.cache_key}"
        )


        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract minimal metadata
            title = self._extract_title(soup)
            contest_name = self._extract_contest_name(soup)

            # Extract only the links from 'Contest materials'
            editorial_links = self._extract_editorial_links(soup)

            problem_data = ProblemData(
                identifier=identifier,
                title=title,
                url=url,
                contest_name=contest_name,
                possible_editorial_links=editorial_links,
            )

            logger.debug(
                f"Successfully parsed problem page for problem_id={identifier.cache_key}"
            )
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page: {e}")
            raise ParsingError(f"Failed to parse problem page {url}: {e}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract problem title."""
        try:
            # Try to find problem title in div.title
            title_div = soup.find("div", class_="title")
            if title_div:
                # Remove problem ID (e.g., "A. " or "1234A. ")
                title_text = title_div.get_text(strip=True)
                # Remove leading problem identifier
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
            # Look for contest name in breadcrumbs or header
            breadcrumbs = soup.find("div", class_="breadcrumbs")
            if breadcrumbs:
                links = breadcrumbs.find_all("a")
                if len(links) > 0:
                    # grab the last link
                    return links[-1].get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Failed to extract contest name: {e}")
            return None

    def _extract_editorial_links(self, soup: BeautifulSoup) -> list[str]:
        """Extract links from the Contest materials section."""

        links = []
        # find all sidebar boxes
        sideboxes = soup.find_all("div", class_="sidebox")

        for box in sideboxes:
            if self._is_materials_box(box):
                box_links = self._extract_links_from_box(box)
                links.extend(box_links)

        return links

    def _is_materials_box(self, box: Tag) -> bool:
        """Check if sidebar box contains contest materials"""

        caption = box.find("div", class_="caption")
        if not caption:
            return False

        return self.MATERIALS_CAPTION_KEYWORD in caption.get_text(strip=True).lower()

    def _extract_links_from_box(self, box: Tag) -> list[str]:
        """Extract links from sidebar box"""

        links = []
        for link in box.find_all("a", href=True):
            href = str(link["href"])

            # Check if link contains any relevant path segment
            if any(segment in href for segment in self.RELEVANT_URL_SEGMENTS):
                full_link = self._normalize_url(href=href)
                links.append(full_link)
        return links

    def _normalize_url(self, href: str) -> str:
        """Ensure URL is absolute"""
        if href.startswith("/"):
            return f"{self.CODEFORCES_BASE_URL}{href}"
        return href


async def parse_problem(url: str, http_client: Optional["AsyncHTTPClient"] = None) -> ProblemData:
    """
    Convenience function to parse problem from URL.

    Args:
        url: Problem URL
        http_client: Optional HTTP client

    Returns:
        ProblemData
    """
    from domain.parsers.url_parser import parse_problem_url

    identifier = parse_problem_url(url)

    parser = ProblemPageParser(http_client)
    return await parser.parse_problem_page(identifier)
