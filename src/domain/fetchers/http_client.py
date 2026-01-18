"""HTTP client with retry logic for fetching web content."""

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

# Lazy import for playwright to avoid loading it if not needed
_playwright = None
_browser_context = None


class HTTPClient:
    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        """
        Initialize the client, using configured timeout and user-agent if not provided.
        """
        settings = get_settings()
        self.timeout = timeout or settings.http_timeout
        self.user_agent = user_agent or settings.user_agent
        self.retries = settings.http_retries

        self.client = httpx.Client(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        self.client.close()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def get(self, url: str) -> httpx.Response:
        """
        Fetch a URL with automatic retries and map HTTP errors to domain-specific exceptions.
        404 responses raise ProblemNotFoundError; other failures raise NetworkError.
        """
        logger.debug(f"Fetching URL: {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()
            logger.debug(
                f"Successfully fetched URL: {url} (status: {response.status_code})"
            )
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

    def get_text(self, url: str) -> str:
        response = self.get(url)
        return response.text

    def get_bytes(self, url: str) -> bytes:
        response = self.get(url)
        return response.content

    def get_content_type(self, url: str) -> str:
        response = self.get(url)
        return response.headers.get("content-type", "").lower()

    def get_text_with_js(self, url: str, wait_time: int = 3000) -> str:
        """
        Fetch a page using a headless browser so JavaScript-rendered content can load.
        Use this for sites that populate data dynamically.
        """
        logger.info(f"Fetching URL with JS rendering: {url} (wait: {wait_time}ms)")

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.user_agent)

                # Navigate to page
                page.goto(
                    url, wait_until="domcontentloaded", timeout=self.timeout * 1000
                )

                # Wait for dynamic content to load
                page.wait_for_timeout(wait_time)

                # Get rendered HTML
                content = page.content()

                # Cleanup
                browser.close()

                logger.info(
                    f"Successfully fetched URL with JS: {url} ({len(content)} chars)"
                )
                return content

        except Exception as e:
            logger.error(f"Failed to fetch URL with JS rendering: {url} - {e}")
            raise NetworkError(f"Failed to fetch {url} with JS rendering: {e}") from e


def create_http_client() -> HTTPClient:
    return HTTPClient()
