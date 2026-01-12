"""Async orchestrator for coordinating the editorial extraction process."""

from typing import Optional

from loguru import logger

from domain.models import Editorial, ProblemData, CachedEditorial
from domain.parsers.url_parser import URLParser
from domain.parsers.problem_page import ProblemPageParser
from domain.parsers.tutorial_parser import TutorialParser
from domain.fetchers.tutorial_finder import TutorialFinder
from domain.extractors.editorial_extractor import EditorialExtractor
from domain.exceptions import CodeforcesEditorialError


class AsyncEditorialOrchestrator:
    """Async orchestrator for editorial extraction process."""

    def __init__(
        self,
        http_client,
        ai_client,
        cache_client=None,
        use_cache: bool = True,
    ):
        """
        Initialize async orchestrator with dependency injection.

        Args:
            http_client: Async HTTP client (AsyncHTTPClient)
            ai_client: Async OpenAI client (AsyncOpenAIClient)
            cache_client: Optional async cache client (Redis)
            use_cache: Whether to use caching
        """
        self.http_client = http_client
        self.ai_client = ai_client
        self.cache_client = cache_client
        self.use_cache = use_cache and cache_client is not None

        # Initialize parsers and extractors
        self.problem_parser = ProblemPageParser(self.http_client)
        self.tutorial_parser = TutorialParser(self.http_client)
        self.tutorial_finder = TutorialFinder(self.ai_client, self.http_client)
        self.editorial_extractor = EditorialExtractor(self.ai_client)

    async def get_editorial(self, url: str) -> tuple[Editorial, ProblemData]:
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
            logger.info("Step 1: Parsing URL")
            identifier = URLParser.parse(url)

            if self.use_cache and self.cache_client:
                logger.info("Step 2: Checking cache")
                cached = await self._get_from_cache(identifier.cache_key)
                if cached:
                    logger.info("Using cached editorial")
                    # Fetch problem data for response
                    problem_data = await self.problem_parser.parse_problem_page(identifier)
                    return cached.editorial, problem_data

            logger.info("Step 3: Parsing problem page")
            problem_data = await self.problem_parser.parse_problem_page(identifier)

            logger.info("Step 4: Finding tutorial URL")
            tutorial_url = await self.tutorial_finder.find_tutorial(identifier)

            logger.info("Step 5: Parsing tutorial content")
            tutorial_data = await self.tutorial_parser.parse(tutorial_url)

            logger.info("Step 6: Extracting editorial")
            editorial = await self.editorial_extractor.extract(
                tutorial_data,
                identifier,
                problem_data.title,
            )

            if self.use_cache and self.cache_client:
                logger.info("Step 7: Caching result")
                cached_editorial = CachedEditorial(
                    editorial=editorial,
                )
                await self._save_to_cache(identifier.cache_key, cached_editorial)

            logger.info("Editorial extraction completed successfully")
            return editorial, problem_data

        except CodeforcesEditorialError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in orchestrator: {e}")
            raise CodeforcesEditorialError(f"Failed to get editorial: {e}") from e

    async def _get_from_cache(self, cache_key: str) -> Optional[CachedEditorial]:
        """
        Get cached editorial from Redis.

        Args:
            cache_key: Cache key

        Returns:
            CachedEditorial if found, None otherwise
        """
        if not self.cache_client:
            return None

        try:
            cached_data = await self.cache_client.get(cache_key)
            if cached_data:
                return CachedEditorial.from_dict(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
            return None

    async def _save_to_cache(self, cache_key: str, cached_editorial: CachedEditorial) -> None:
        """
        Save editorial to Redis cache.

        Args:
            cache_key: Cache key
            cached_editorial: Editorial to cache
        """
        if not self.cache_client:
            return

        try:
            cached_data = cached_editorial.to_dict()
            await self.cache_client.set(cache_key, cached_data)
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    async def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache_client:
            logger.info("Clearing cache")
            await self.cache_client.flushdb()
        else:
            logger.warning("Cache is not enabled")
