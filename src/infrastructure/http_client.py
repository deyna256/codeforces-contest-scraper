"""Async HTTP client with retry logic for fetching web content."""

from typing import Optional

from curl_cffi.requests import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from config import get_settings
from infrastructure.errors import NetworkError, ProblemNotFoundError


class AsyncHTTPClient:
    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        """
        Initialize the client, falling back to configured timeout and user-agent when not provided.
        """
        settings = get_settings()
        self.timeout = timeout or 30  # Default timeout: 30 seconds
        self.user_agent = user_agent or settings.user_agent or "codeforces-editorial-finder/1.0"
        self.retries = settings.http_retries

        # HTTP client using curl_cffi with browser impersonation
        self.client = AsyncSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        try:
            await self.client.close()
        except Exception:
            # Ignore cleanup errors to prevent breaking dependency injection
            pass

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
                raise ProblemNotFoundError(f"Resource not found: {url}")

            if response.status_code >= 400:
                raise NetworkError(f"HTTP error {response.status_code}: {url}")

            return response

        except ProblemNotFoundError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(f"Failed to fetch {url}: {e}") from e

    async def get_text(self, url: str) -> str:
        """
        Fetch a URL and return its text body, decoding bytes if needed.
        """
        response = await self.get(url)
        return response.text if hasattr(response, "text") else response.content.decode("utf-8")
