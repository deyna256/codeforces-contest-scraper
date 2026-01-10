"""Cache system for editorial data."""

import json
from typing import Optional

from diskcache import Cache
from loguru import logger

from codeforces_editorial.config import get_settings
from codeforces_editorial.models import CachedEditorial, ProblemIdentifier
from codeforces_editorial.utils.exceptions import CacheError


class EditorialCache:
    """Cache for editorial data."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory (uses config if None)
        """
        settings = get_settings()
        self.cache_dir = cache_dir or str(settings.get_cache_path())
        self.ttl_seconds = settings.cache_ttl_hours * 3600

        try:
            self.cache = Cache(self.cache_dir)
            logger.debug(f"Initialized cache at {self.cache_dir}")
        except Exception as e:
            raise CacheError(f"Failed to initialize cache: {e}") from e

    def _get_key(self, identifier: ProblemIdentifier) -> str:
        """Generate cache key for problem."""
        return f"editorial_{identifier.contest_id}_{identifier.problem_id}"

    def get(self, identifier: ProblemIdentifier) -> Optional[CachedEditorial]:
        """
        Get cached editorial.

        Args:
            identifier: Problem identifier

        Returns:
            CachedEditorial if found and not expired, None otherwise
        """
        key = self._get_key(identifier)
        logger.debug(f"Checking cache for key: {key}")

        try:
            data = self.cache.get(key)

            if data is None:
                logger.debug("Cache miss")
                return None

            # Deserialize
            cached = CachedEditorial.from_dict(json.loads(data))

            # Check if expired
            if cached.is_expired:
                logger.debug("Cache entry expired")
                self.delete(identifier)
                return None

            logger.info(f"Cache hit for {identifier}")
            return cached

        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
            return None

    def set(self, cached_editorial: CachedEditorial) -> None:
        """
        Store editorial in cache.

        Args:
            cached_editorial: Editorial to cache
        """
        key = self._get_key(cached_editorial.problem)
        logger.debug(f"Caching editorial with key: {key}")

        try:
            # Serialize
            data = json.dumps(cached_editorial.to_dict())

            # Store with TTL
            self.cache.set(key, data, expire=self.ttl_seconds)

            logger.info(f"Cached editorial for {cached_editorial.problem}")

        except Exception as e:
            logger.error(f"Failed to cache editorial: {e}")
            raise CacheError(f"Failed to cache editorial: {e}") from e

    def delete(self, identifier: ProblemIdentifier) -> None:
        """
        Delete cached editorial.

        Args:
            identifier: Problem identifier
        """
        key = self._get_key(identifier)
        logger.debug(f"Deleting cache entry: {key}")

        try:
            self.cache.delete(key)
        except Exception as e:
            logger.warning(f"Error deleting cache entry: {e}")

    def clear(self) -> None:
        """Clear all cache."""
        logger.info("Clearing cache")

        try:
            self.cache.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise CacheError(f"Failed to clear cache: {e}") from e

    def close(self) -> None:
        """Close cache."""
        try:
            self.cache.close()
        except Exception as e:
            logger.warning(f"Error closing cache: {e}")


def get_cache() -> EditorialCache:
    """Get cache instance."""
    return EditorialCache()
