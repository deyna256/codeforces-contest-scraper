"""Async HTTP client with retry logic for fetching web content."""

from typing import Optional

from curl_cffi.requests import AsyncSession
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from config import get_settings
from domain.exceptions import NetworkError, ProblemNotFoundError


class AsyncHTTPClient:
    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        """
        Initialize the client, falling back to configured timeout and user-agent when not provided.
        """
        settings = get_settings()
        self.timeout = timeout or settings.http_timeout
        self.user_agent = user_agent or settings.user_agent
        self.retries = settings.http_retries

        # HTTP client using curl_cffi with browser impersonation
        self.client = AsyncSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        await self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get(self, url: str):
        """
        Fetch a URL using curl_cffi with automatic retries and domain-specific error mapping.

        404 responses raise ProblemNotFoundError; other HTTP failures raise NetworkError.
        """
        logger.debug(f"Fetching URL: {url}")

        try:
            # Use curl_cffi with Chrome 120 impersonation to bypass TLS fingerprinting
            response = await self.client.get(
                url,
                timeout=self.timeout,
                impersonate="chrome120",
                allow_redirects=True,
            )

            # Check status code
            if response.status_code == 404:
                logger.error(f"Resource not found: {url}")
                raise ProblemNotFoundError(f"Resource not found: {url}")

            if response.status_code >= 400:
                logger.error(f"HTTP error {response.status_code} for {url}")
                raise NetworkError(f"HTTP error {response.status_code}: {url}")

            logger.debug(
                f"Successfully fetched URL: {url} (status: {response.status_code})"
            )
            return response

        except ProblemNotFoundError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise NetworkError(f"Failed to fetch {url}: {e}") from e

    async def get_text(self, url: str) -> str:
        """
        Fetch a URL and return its text body, decoding bytes if needed.
        """
        response = await self.get(url)
        return (
            response.text
            if hasattr(response, "text")
            else response.content.decode("utf-8")
        )

    async def get_bytes(self, url: str) -> bytes:
        response = await self.get(url)
        return response.content

    async def get_content_type(self, url: str) -> str:
        response = await self.get(url)
        return response.headers.get("content-type", "").lower()

    async def get_text_with_js(self, url: str, wait_time: int = 3000) -> str:
        """
        Fetch a page using a headless browser to allow JavaScript-rendered content to load.
        Use this for sites that populate data dynamically via JS.
        """
        logger.info(f"Fetching URL with JS rendering: {url} (wait: {wait_time}ms)")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.user_agent)

                # Navigate to page
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=self.timeout * 1000
                )

                # Wait for dynamic content to load
                await page.wait_for_timeout(wait_time)

                # Get rendered HTML
                content = await page.content()

                # Cleanup
                await browser.close()

                logger.info(
                    f"Successfully fetched URL with JS: {url} ({len(content)} chars)"
                )
                return content

        except Exception as e:
            logger.error(f"Failed to fetch URL with JS rendering: {url} - {e}")
            raise NetworkError(f"Failed to fetch {url} with JS rendering: {e}") from e
