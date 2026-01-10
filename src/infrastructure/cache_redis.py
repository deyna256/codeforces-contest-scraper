"""Async Redis cache client for editorial data."""

import json
from typing import Optional

import redis.asyncio as redis
from loguru import logger

from config import get_settings
from domain.exceptions import CacheError


class AsyncRedisCache:
    """Async Redis cache client."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize async Redis cache.

        Args:
            redis_url: Redis connection URL (uses config if None)
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = settings.cache_ttl_hours * 3600

        self.client: Optional[redis.Redis] = None
        logger.debug(f"Initialized async Redis cache (URL: {self.redis_url})")

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(f"Failed to connect to Redis: {e}") from e

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.debug("Closed Redis connection")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get(self, key: str) -> Optional[dict]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached dictionary if found, None otherwise
        """
        if not self.client:
            raise CacheError("Redis client not connected")

        try:
            data = await self.client.get(key)

            if data is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            logger.debug(f"Cache hit for key: {key}")
            return json.loads(data)

        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
            return None

    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Dictionary to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if not self.client:
            raise CacheError("Redis client not connected")

        ttl = ttl or self.ttl_seconds

        try:
            data = json.dumps(value)
            await self.client.setex(key, ttl, data)
            logger.debug(f"Cached data for key: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Failed to cache data: {e}")
            raise CacheError(f"Failed to cache data: {e}") from e

    async def delete(self, key: str) -> None:
        """
        Delete key from cache.

        Args:
            key: Cache key
        """
        if not self.client:
            raise CacheError("Redis client not connected")

        try:
            await self.client.delete(key)
            logger.debug(f"Deleted cache entry: {key}")

        except Exception as e:
            logger.warning(f"Error deleting cache entry: {e}")

    async def flushdb(self) -> None:
        """Clear all cache (flushes current database)."""
        if not self.client:
            raise CacheError("Redis client not connected")

        try:
            await self.client.flushdb()
            logger.info("Flushed Redis database")

        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            raise CacheError(f"Failed to flush cache: {e}") from e

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.client:
            raise CacheError("Redis client not connected")

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Error checking key existence: {e}")
            return False
