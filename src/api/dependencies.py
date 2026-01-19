from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from loguru import logger

from infrastructure.cache_redis import AsyncRedisCache

if TYPE_CHECKING:
    from litestar.datastructures import State


async def provide_cache_client(
    state: "State",
) -> AsyncGenerator[tuple[AsyncRedisCache | None, bool], None]:
    client = AsyncRedisCache()
    use_cache = False

    try:
        await client.connect()
        logger.debug("Connected to Redis for request")
        use_cache = True
    except Exception as e:
        logger.warning(f"Failed to connect to Redis, caching disabled: {e}")

    try:
        yield (client if use_cache else None, use_cache)
    finally:
        await client.close()
        logger.debug("Redis connection closed")
