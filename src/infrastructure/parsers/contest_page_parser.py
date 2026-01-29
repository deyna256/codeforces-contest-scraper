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

        url = URLParser.build_contest_url(ContestIdentifier(contest_id=contest_id))

        if not self.http_client:
            raise ParsingError(f"HTTP client not initialized for {url}")

        try:
            html = await self.http_client.get_text(url)
            soup = BeautifulSoup(html, "lxml")

            title = self._extract_contest_title(soup)
            editorial_urls = await self._extract_editorial_url(soup, contest_id)

            contest_data = ContestPageData(
                contest_id=contest_id,
                title=title,
                editorial_urls=editorial_urls,
            )

            return contest_data

        except Exception as e:
            raise ParsingError(f"Failed to parse contest page {url}: {e}") from e

    async def parse_problem_in_contest(self, contest_id: str, problem_id: str) -> ProblemData:
        """
        Parse problem page within a contest and extract data.
        """
        url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"

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
            )

            problem_data = ProblemData(
                identifier=identifier,
                description=description,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

            return problem_data

        except Exception as e:
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
        except Exception:
            return None

    async def _extract_editorial_url(self, soup: BeautifulSoup, contest_id: str) -> list[str]:
        """Extract editorial/tutorial URLs from contest page using LLM or fallback to regex."""
        try:
            # Try LLM-based detection first
            if self.llm_editorial_finder:
                llm_urls = await self.llm_editorial_finder.find_editorial_url(soup, contest_id)
                if llm_urls:
                    return llm_urls
                logger.debug(f"LLM did not find editorials for contest {contest_id}, using regex")

            # Fallback to regex-based detection
            regex_urls = self._extract_editorial_url_regex(soup, contest_id)
            if regex_urls:
                logger.info(
                    f"Found {len(regex_urls)} editorial URL(s) for contest {contest_id} using regex"
                )
            return regex_urls

        except Exception:
            logger.exception(f"Error extracting editorial URLs for contest {contest_id}")
            return []

    def _extract_editorial_url_regex(self, soup: BeautifulSoup, contest_id: str) -> list[str]:
        """Extract editorial URL using regex patterns (fallback method)."""
        try:
            # Look for editorial links in sidebar or main content
            # Common patterns:
            # 1. Link with text containing "tutorial" or "editorial"
            # 2. Link in the sidebar to /blog/entry/...

            editorial_urls = []

            # Search all links on the page
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not isinstance(href, str):
                    continue
                link_text = link.get_text(strip=True).lower()

                # Check if link text mentions tutorial/editorial (including Russian)
                keywords = ["tutorial", "editorial", "разбор", "analysis", "solution"]
                if any(keyword in link_text for keyword in keywords):
                    # Convert relative URL to absolute
                    url = f"https://codeforces.com{href}" if href.startswith("/") else href
                    if url not in editorial_urls:  # Avoid duplicates
                        editorial_urls.append(url)

            return editorial_urls

        except Exception:
            logger.exception(f"Error in regex editorial URL extraction for contest {contest_id}")
            return []

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
                text = memory_limit.get_text(strip=True)
                if "memory limit per test" in text.lower():
                    text = text.lower().replace("memory limit per test", "").strip()
                return text

            return None
        except Exception:
            return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract problem statement/description."""
        try:
            problem_statement = soup.find("div", class_="problem-statement")
            if not problem_statement:
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

        except Exception:
            return None
