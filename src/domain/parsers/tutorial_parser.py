"""Parser for tutorial content (HTML and PDF)."""

from bs4 import BeautifulSoup
from loguru import logger
import fitz  # PyMuPDF

from config import get_settings
from domain.models import TutorialData, TutorialFormat, Language
from domain.exceptions import ParsingError


class TutorialParser:
    """Parses tutorial content from HTML or PDF."""

    def __init__(self, http_client):
        """
        Initialize parser.

        Args:
            http_client: Async HTTP client
        """
        self.http = http_client

    async def parse(self, url: str) -> TutorialData:
        """
        Parse tutorial from URL.

        Args:
            url: Tutorial URL

        Returns:
            TutorialData

        Raises:
            ParsingError: If parsing fails
        """
        logger.info(f"Parsing tutorial from: {url}")

        try:
            # Detect content type
            content_type = await self.http.get_content_type(url)
            logger.debug(f"Content type: {content_type}")

            if "pdf" in content_type:
                return await self._parse_pdf(url)
            else:
                return await self._parse_html(url)

        except Exception as e:
            logger.error(f"Failed to parse tutorial: {e}")
            raise ParsingError(f"Failed to parse tutorial {url}: {e}") from e

    async def _parse_html(self, url: str) -> TutorialData:
        """Parse HTML tutorial."""
        logger.debug("Parsing as HTML")

        # Use JS rendering for blog pages (editorials are usually posted as blog entries)
        # which may load content dynamically
        if "/blog/" in url or "/contest/" in url:
            settings = get_settings()
            wait_time = settings.http_js_wait
            logger.info(f"Using JS rendering for blog/contest page (wait: {wait_time}ms)")
            html = await self.http.get_text_with_js(url, wait_time=wait_time)
        else:
            html = await self.http.get_text(url)

        soup = BeautifulSoup(html, "lxml")

        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        # Extract main content
        content_div = soup.find("div", class_="ttypography") or soup.find("body")

        if content_div:
            content = content_div.get_text(separator="\n", strip=True)
        else:
            content = soup.get_text(separator="\n", strip=True)

        # Try to extract title
        title = None
        title_elem = soup.find("h1") or soup.find("title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        return TutorialData(
            url=url,
            format=TutorialFormat.HTML,
            content=content,
            language=Language.AUTO,
            title=title,
        )

    async def _parse_pdf(self, url: str) -> TutorialData:
        """Parse PDF tutorial."""
        logger.debug("Parsing as PDF")

        pdf_bytes = await self.http.get_bytes(url)

        # Extract text from PDF
        text_content = []

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text_content.append(page.get_text())

        content = "\n\n".join(text_content)

        return TutorialData(
            url=url,
            format=TutorialFormat.PDF,
            content=content,
            language=Language.AUTO,
            raw_bytes=pdf_bytes,
        )
