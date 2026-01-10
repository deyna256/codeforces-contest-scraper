"""Tutorial finder using OpenAI API."""

from typing import Optional
import re

from loguru import logger

from domain.openai.client import OpenAIClient
from domain.fetchers.http_client import HTTPClient
from domain.models import ProblemIdentifier
from domain.parsers.url_parser import URLParser
from domain.exceptions import EditorialNotFoundError


class TutorialFinder:
    """Finds tutorial/editorial links for Codeforces problems."""

    def __init__(
        self,
        ai_client: Optional[OpenAIClient] = None,
        http_client: Optional[HTTPClient] = None,
    ):
        """
        Initialize tutorial finder.

        Args:
            ai_client: OpenAI API client
            http_client: HTTP client
        """
        self.ai_client = ai_client or OpenAIClient()
        self.http = http_client or HTTPClient()
        self._should_close_http = http_client is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._should_close_http:
            self.http.close()

    def find_tutorial(self, identifier: ProblemIdentifier) -> str:
        """
        Find tutorial URL for a problem.

        Args:
            identifier: Problem identifier

        Returns:
            Tutorial URL

        Raises:
            EditorialNotFoundError: If tutorial not found
        """
        logger.info(f"Searching for tutorial for problem {identifier}")

        # Strategy 1: Try contest page
        tutorial_url = self._try_contest_page(identifier)
        if tutorial_url:
            return tutorial_url

        # Strategy 2: Try common blog patterns
        tutorial_url = self._try_blog_patterns(identifier)
        if tutorial_url:
            return tutorial_url

        # If all strategies fail
        raise EditorialNotFoundError(
            f"Could not find tutorial for problem {identifier}. "
            f"The contest might not have an editorial, or it might be in an unexpected location."
        )

    def _try_contest_page(self, identifier: ProblemIdentifier) -> Optional[str]:
        """
        Try to find editorial link on contest main page using OpenAI.

        Args:
            identifier: Problem identifier

        Returns:
            Tutorial URL if found, None otherwise
        """
        logger.debug("Strategy 1: Searching contest page for editorial link")

        try:
            contest_url = URLParser.build_contest_url(identifier)
            html = self.http.get_text(contest_url)

            # Use OpenAI to find editorial link
            editorial_url = self.ai_client.find_editorial_link(html, identifier.problem_id)

            if editorial_url:
                # Normalize URL
                editorial_url = self._normalize_url(editorial_url)
                logger.info(f"Found editorial via contest page: {editorial_url}")
                return editorial_url

        except Exception as e:
            logger.warning(f"Failed to search contest page: {e}")

        return None

    def _try_blog_patterns(self, identifier: ProblemIdentifier) -> Optional[str]:
        """
        Try common blog URL patterns for editorials.

        Args:
            identifier: Problem identifier

        Returns:
            Tutorial URL if found, None otherwise
        """
        logger.debug("Strategy 2: Trying common blog patterns")

        # Common patterns for editorial blogs
        # Format: /blog/entry/{entry_id}
        # We can try searching for these patterns

        # Try to search Codeforces for editorial blog posts
        try:
            search_url = (
                f"https://codeforces.com/search?query=contest+{identifier.contest_id}+tutorial"
            )

            html = self.http.get_text(search_url)

            # Look for blog entry links in search results
            blog_pattern = r'href="(/blog/entry/\d+)"'
            matches = re.findall(blog_pattern, html)

            if matches:
                # Try first few matches
                for match in matches[:3]:
                    blog_url = f"https://codeforces.com{match}"
                    logger.debug(f"Checking potential editorial: {blog_url}")

                    # Fetch and validate
                    try:
                        blog_html = self.http.get_text(blog_url)

                        # Simple validation: check if problem ID appears in blog
                        if identifier.problem_id in blog_html or identifier.full_id in blog_html:
                            logger.info(f"Found editorial via blog search: {blog_url}")
                            return blog_url
                    except Exception as e:
                        logger.debug(f"Failed to validate {blog_url}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Failed to search blogs: {e}")

        return None

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL to full absolute URL.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        # If relative URL, make it absolute
        if url.startswith("/"):
            url = f"https://codeforces.com{url}"

        # Ensure https
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        return url


def find_tutorial_url(
    identifier: ProblemIdentifier,
    ai_client: Optional[OpenAIClient] = None,
    http_client: Optional[HTTPClient] = None,
) -> str:
    """
    Convenience function to find tutorial URL.

    Args:
        identifier: Problem identifier
        ai_client: Optional OpenAI client
        http_client: Optional HTTP client

    Returns:
        Tutorial URL

    Raises:
        EditorialNotFoundError: If tutorial not found
    """
    with TutorialFinder(ai_client, http_client) as finder:
        return finder.find_tutorial(identifier)
