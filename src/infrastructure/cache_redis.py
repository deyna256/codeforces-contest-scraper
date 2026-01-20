"""Async Redis client for caching Codeforces editorial data."""

from typing import Optional

import redis.asyncio as redis
from loguru import logger

from config import get_settings
from infrastructure.errors import CacheError


class AsyncRedisCache:
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the cache client, using the configured Redis URL if none is provided.
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = settings.cache_ttl_hours * 3600

        self.client: Optional[redis.Redis] = None
        logger.debug(f"Initialized async Redis cache (URL: {self.redis_url})")

    async def connect(self) -> None:
        """Establish a Redis connection and verify it by issuing a ping."""
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
        if self.client:
            await self.client.close()
            logger.debug("Closed Redis connection")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

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
