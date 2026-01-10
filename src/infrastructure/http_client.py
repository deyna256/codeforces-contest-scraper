"""Async HTTP client with retry logic for fetching web content."""

from typing import Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import get_settings
from domain.exceptions import NetworkError, ProblemNotFoundError


class AsyncHTTPClient:
    """Async HTTP client with retry logic and error handling."""

    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        """
        Initialize async HTTP client.

        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        settings = get_settings()
        self.timeout = timeout or settings.http_timeout
        self.user_agent = user_agent or settings.user_agent
        self.retries = settings.http_retries

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get(self, url: str) -> httpx.Response:
        """
        Perform GET request with retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTTP response

        Raises:
            ProblemNotFoundError: If resource not found (404)
            NetworkError: For other network/HTTP errors
        """
        logger.debug(f"Fetching URL: {url}")

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            logger.debug(f"Successfully fetched URL: {url} (status: {response.status_code})")
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error(f"Resource not found: {url}")
                raise ProblemNotFoundError(f"Resource not found: {url}") from e
            logger.error(f"HTTP error for {url}: {e}")
            raise NetworkError(f"HTTP error {e.response.status_code}: {url}") from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Network error for {url}: {e}")
            raise  # Let tenacity retry

        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise NetworkError(f"Failed to fetch {url}: {e}") from e

    async def get_text(self, url: str) -> str:
        """
        Fetch URL and return text content.

        Args:
            url: URL to fetch

        Returns:
            Response text content
        """
        response = await self.get(url)
        return response.text

    async def get_bytes(self, url: str) -> bytes:
        """
        Fetch URL and return binary content.

        Args:
            url: URL to fetch

        Returns:
            Response binary content
        """
        response = await self.get(url)
        return response.content

    async def get_content_type(self, url: str) -> str:
        """
        Get content type of URL.

        Args:
            url: URL to check

        Returns:
            Content-Type header value
        """
        response = await self.get(url)
        return response.headers.get("content-type", "").lower()

    async def get_text_with_js(self, url: str, wait_time: int = 3000) -> str:
        """
        Fetch URL with JavaScript rendering (for dynamic content).

        This method uses a headless browser to load the page and wait for
        dynamic content to load. Use this for pages that load content via JavaScript.

        Args:
            url: URL to fetch
            wait_time: Time to wait for content to load (milliseconds), default 3000ms

        Returns:
            Rendered page HTML content

        Raises:
            NetworkError: If fetching fails
        """
        logger.info(f"Fetching URL with JS rendering: {url} (wait: {wait_time}ms)")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.user_agent)

                # Navigate to page
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

                # Wait for dynamic content to load
                await page.wait_for_timeout(wait_time)

                # Get rendered HTML
                content = await page.content()

                # Cleanup
                await browser.close()

                logger.info(f"Successfully fetched URL with JS: {url} ({len(content)} chars)")
                return content

        except Exception as e:
            logger.error(f"Failed to fetch URL with JS rendering: {url} - {e}")
            raise NetworkError(f"Failed to fetch {url} with JS rendering: {e}") from e
