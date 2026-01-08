"""Orchestrator for coordinating all modules."""

from typing import Optional

from loguru import logger

from codeforces_editorial.cache import EditorialCache
from codeforces_editorial.openai.client import OpenAIClient
from codeforces_editorial.extractors.editorial_extractor import EditorialExtractor
from codeforces_editorial.extractors.markdown_formatter import MarkdownFormatter
from codeforces_editorial.fetchers.http_client import HTTPClient
from codeforces_editorial.fetchers.tutorial_finder import TutorialFinder
from codeforces_editorial.models import CachedEditorial, ProblemData, Editorial
from codeforces_editorial.parsers.problem_page import ProblemPageParser
from codeforces_editorial.parsers.tutorial_parser import TutorialParser
from codeforces_editorial.parsers.url_parser import URLParser
from codeforces_editorial.utils.exceptions import CodeforcesEditorialError


class EditorialOrchestrator:
    """Orchestrates the editorial extraction process."""

    def __init__(
        self,
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            use_cache: Whether to use caching
            cache_dir: Cache directory (uses config if None)
        """
        self.use_cache = use_cache
        self.cache = EditorialCache(cache_dir) if use_cache else None

        # Initialize clients
        self.http_client = HTTPClient()
        self.ai_client = OpenAIClient()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.http_client.close()
        if self.cache:
            self.cache.close()

    def get_editorial(self, url: str) -> tuple[Editorial, ProblemData]:
        """
        Get editorial for problem URL.

        Args:
            url: Codeforces problem URL

        Returns:
            Tuple of (Editorial, ProblemData)

        Raises:
            CodeforcesEditorialError: If process fails
        """
        logger.info(f"Getting editorial for URL: {url}")

        try:
            # Step 1: Parse URL
            logger.info("Step 1: Parsing URL")
            identifier = URLParser.parse(url)

            # Step 2: Check cache
            if self.use_cache and self.cache:
                logger.info("Step 2: Checking cache")
                cached = self.cache.get(identifier)
                if cached:
                    logger.info("Using cached editorial")
                    # We need to fetch problem data for formatting
                    problem_parser = ProblemPageParser(self.http_client)
                    problem_data = problem_parser.parse_problem_page(identifier)
                    return cached.editorial, problem_data

            # Step 3: Parse problem page
            logger.info("Step 3: Parsing problem page")
            problem_parser = ProblemPageParser(self.http_client)
            problem_data = problem_parser.parse_problem_page(identifier)

            # Step 4: Find tutorial URL
            logger.info("Step 4: Finding tutorial URL")
            tutorial_finder = TutorialFinder(self.ai_client, self.http_client)
            tutorial_url = tutorial_finder.find_tutorial(identifier)

            # Step 5: Parse tutorial content
            logger.info("Step 5: Parsing tutorial content")
            tutorial_parser = TutorialParser(self.http_client)
            tutorial_data = tutorial_parser.parse(tutorial_url)

            # Step 6: Extract editorial
            logger.info("Step 6: Extracting editorial")
            extractor = EditorialExtractor(self.ai_client)
            editorial = extractor.extract(
                tutorial_data,
                identifier,
                problem_data.title,
            )

            # Step 7: Cache result
            if self.use_cache and self.cache:
                logger.info("Step 7: Caching result")
                cached_editorial = CachedEditorial(
                    problem=identifier,
                    editorial=editorial,
                    tutorial_url=tutorial_url,
                    tutorial_format=tutorial_data.format,
                )
                self.cache.set(cached_editorial)

            logger.info("Editorial extraction completed successfully")
            return editorial, problem_data

        except CodeforcesEditorialError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in orchestrator: {e}")
            raise CodeforcesEditorialError(f"Failed to get editorial: {e}") from e

    def get_editorial_markdown(self, url: str) -> str:
        """
        Get editorial as formatted Markdown.

        Args:
            url: Codeforces problem URL

        Returns:
            Markdown string

        Raises:
            CodeforcesEditorialError: If process fails
        """
        editorial, problem_data = self.get_editorial(url)
        formatter = MarkdownFormatter()
        return formatter.format(editorial, problem_data)

    def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache:
            logger.info("Clearing cache")
            self.cache.clear()
        else:
            logger.warning("Cache is not enabled")


def get_editorial_markdown(
    url: str,
    use_cache: bool = True,
    cache_dir: Optional[str] = None,
) -> str:
    """
    Convenience function to get editorial as Markdown.

    Args:
        url: Codeforces problem URL
        use_cache: Whether to use caching
        cache_dir: Cache directory

    Returns:
        Markdown string

    Raises:
        CodeforcesEditorialError: If process fails
    """
    with EditorialOrchestrator(use_cache, cache_dir) as orchestrator:
        return orchestrator.get_editorial_markdown(url)
