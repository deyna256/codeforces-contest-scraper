"""Parser for extracting contest data from HTML pages."""

from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup
from loguru import logger

from domain.models.parsing import ContestPageData, ProblemData
from domain.models.identifiers import ProblemIdentifier

from .interfaces import ParsingError
from .llm_editorial_finder import LLMEditorialFinder

if TYPE_CHECKING:
    from infrastructure.http_client import AsyncHTTPClient


class ContestPageParser:
    """Parser for extracting data from Codeforces contest HTML pages."""

    def __init__(
        self,
        http_client: Optional["AsyncHTTPClient"] = None,
        llm_editorial_finder: Optional[LLMEditorialFinder] = None,
    ):
        """
        Initialize parser.

        Args:
            http_client: Async HTTP client instance
            llm_editorial_finder: LLM-based editorial finder (optional)
        """
        self.http_client = http_client
        self.llm_editorial_finder = llm_editorial_finder

    async def parse_contest_page(self, contest_id: str) -> ContestPageData:
        """
        Parse contest page and extract data (title, editorial URL).
        """
        from infrastructure.parsers import URLParser
        from domain.models.identifiers import ContestIdentifier

        url = URLParser.build_contest_url(ContestIdentifier(contest_id=contest_id, is_gym=False))
        logger.info(f"Parsing contest page: {url}")

        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            title = self._extract_contest_title(soup)
            editorial_url = await self._extract_editorial_url(soup, contest_id)

            contest_data = ContestPageData(
                contest_id=contest_id,
                title=title,
                editorial_url=editorial_url,
            )

            logger.info(f"Successfully parsed contest: {contest_id}")
            return contest_data

        except Exception as e:
            logger.error(f"Failed to parse contest page: {e}")
            raise ParsingError(f"Failed to parse contest page {url}: {e}") from e

    async def parse_problem_in_contest(self, contest_id: str, problem_id: str) -> ProblemData:
        """
        Parse problem page within a contest and extract data.
        """
        url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"
        logger.info(f"Parsing problem page in contest: {url}")

        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            # Extract data using same methods as ProblemPageParser
            description = self._extract_description(soup)
            time_limit = self._extract_time_limit(soup)
            memory_limit = self._extract_memory_limit(soup)

            identifier = ProblemIdentifier(
                contest_id=contest_id,
                problem_id=problem_id,
                is_gym=False,
            )

            problem_data = ProblemData(
                identifier=identifier,
                description=description,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

            logger.info(f"Successfully parsed problem: {contest_id}/{problem_id}")
            return problem_data

        except Exception as e:
            logger.error(f"Failed to parse problem page: {e}")
            raise ParsingError(f"Failed to parse problem page {url}: {e}") from e

    def _extract_contest_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract contest title from contest page."""
        try:
            # Contest title is typically in the header with specific structure
            # Look for contest name in the breadcrumbs or page title
            title_tag = soup.find("title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # Remove "- Codeforces" suffix if present
                if " - Codeforces" in title_text:
                    title_text = title_text.replace(" - Codeforces", "").strip()
                return title_text

            return None
        except Exception as e:
            logger.warning(f"Failed to extract contest title: {e}")
            return None

    async def _extract_editorial_url(self, soup: BeautifulSoup, contest_id: str) -> Optional[str]:
        """Extract editorial/tutorial URL from contest page using LLM or fallback to regex."""
        try:
            # Try LLM-based detection first
            if self.llm_editorial_finder:
                logger.debug("Attempting LLM-based editorial detection")
                llm_url = await self.llm_editorial_finder.find_editorial_url(soup, contest_id)
                if llm_url:
                    logger.info(f"LLM found editorial URL: {llm_url}")
                    return llm_url
                logger.debug("LLM did not find editorial, falling back to regex")

            # Fallback to regex-based detection
            return self._extract_editorial_url_regex(soup, contest_id)

        except Exception as e:
            logger.warning(f"Failed to extract editorial URL: {e}")
            return None

    def _extract_editorial_url_regex(self, soup: BeautifulSoup, contest_id: str) -> Optional[str]:
        """Extract editorial URL using regex patterns (fallback method)."""
        try:
            # Look for editorial links in sidebar or main content
            # Common patterns:
            # 1. Link with text containing "tutorial" or "editorial"
            # 2. Link in the sidebar to /blog/entry/...

            # Search all links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not isinstance(href, str):
                    continue
                link_text = link.get_text(strip=True).lower()

                # Check if link text mentions tutorial/editorial (including Russian)
                keywords = ["tutorial", "editorial", "разбор"]
                if any(keyword in link_text for keyword in keywords):
                    # Convert relative URL to absolute
                    if href.startswith("/"):
                        return f"https://codeforces.com{href}"
                    return href

            # Alternative: look for blog entry links in specific sections
            sidebar = soup.find("div", id="sidebar")
            if sidebar:
                for link in sidebar.find_all("a", href=True):
                    href = link["href"]
                    if not isinstance(href, str):
                        continue
                    if "/blog/entry/" in href:
                        # This might be the editorial
                        if href.startswith("/"):
                            return f"https://codeforces.com{href}"
                        return href

            logger.debug(f"No editorial URL found for contest {contest_id}")
            return None

        except Exception as e:
            logger.warning(f"Failed to extract editorial URL with regex: {e}")
            return None

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
                text = time_limit.get_text(strip=True)
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
                text = memory_limit.get_text(strip=True)
                if "memory limit per test" in text.lower():
                    text = text.lower().replace("memory limit per test", "").strip()
                return text

            return None
        except Exception as e:
            logger.warning(f"Failed to extract memory limit: {e}")
            return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract problem statement/description."""
        try:
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
                logger.warning("Problem statement block not found")
                return None

            text_parts = []

            # Get main sections
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

            return problem_statement.get_text(separator="\n", strip=True)

        except Exception as e:
            logger.warning(f"Failed to extract description: {e}")
            return None
