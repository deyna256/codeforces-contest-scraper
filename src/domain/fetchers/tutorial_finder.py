"""Finds Codeforces tutorial and editorial links using OpenAI and web scraping."""

from typing import Optional
import re

from loguru import logger

from domain.models import ProblemIdentifier
from domain.parsers.url_parser import URLParser
from domain.exceptions import EditorialNotFoundError
from infrastructure.openai_client import AsyncOpenAIClient
from infrastructure.http_client import AsyncHTTPClient


class TutorialFinder:
    """Finds tutorial/editorial links for Codeforces problems."""

    def __init__(self, ai_client, http_client):
        self.ai_client = ai_client
        self.http = http_client

    async def find_tutorial(self, identifier: ProblemIdentifier) -> str:
        """
        Find a tutorial URL by trying multiple strategies, starting with the contest page
        and falling back to blog searches if needed.
        """
        logger.info(f"Searching for tutorial for problem {identifier}")

        # Strategy 1: Try contest page
        tutorial_url = await self._try_contest_page(identifier)
        if tutorial_url:
            return tutorial_url

        # Strategy 2: Try common blog patterns
        tutorial_url = await self._try_blog_patterns(identifier)
        if tutorial_url:
            return tutorial_url

        # If all strategies fail
        raise EditorialNotFoundError(
            f"Could not find tutorial for problem {identifier}. "
            f"The contest might not have an editorial, or it might be in an unexpected location."
        )

    async def _try_contest_page(self, identifier: ProblemIdentifier) -> Optional[str]:
        """
        Attempt to extract the editorial link from the contest page using OpenAI.
        """
        logger.debug("Strategy 1: Searching contest page for editorial link")

        try:
            contest_url = URLParser.build_contest_url(identifier)
            html = await self.http.get_text(contest_url)

            # Use OpenAI to find editorial link
            editorial_url = await self.ai_client.find_editorial_link(html, identifier.problem)

            if editorial_url:
                # Normalize URL
                editorial_url = self._normalize_url(editorial_url)
                logger.info(f"Found editorial via contest page: {editorial_url}")
                return editorial_url

        except Exception as e:
            logger.warning(f"Failed to search contest page: {e}")

        return None

    async def _try_blog_patterns(self, identifier: ProblemIdentifier) -> Optional[str]:
        """
        Search Codeforces blog pages for likely editorial links using common URL patterns.
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

            html = await self.http.get_text(search_url)

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
                        blog_html = await self.http.get_text(blog_url)

                        # Simple validation: check if problem ID appears in blog
                        if identifier.problem in blog_html or identifier.full_id in blog_html:
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
        Convert relative or http URLs into absolute https Codeforces URLs.
        """
        # If relative URL, make it absolute
        if url.startswith("/"):
            url = f"https://codeforces.com{url}"

        # Ensure https
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        return url


async def find_tutorial_url(
    identifier: ProblemIdentifier,
    ai_client: Optional[AsyncOpenAIClient] = None,
    http_client: Optional[AsyncHTTPClient] = None,
) -> str:
    finder = TutorialFinder(ai_client, http_client)
    return await finder.find_tutorial(identifier)
