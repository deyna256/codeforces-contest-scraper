from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from loguru import logger

from infrastructure.http_client import AsyncHTTPClient
from infrastructure.codeforces_client import CodeforcesApiClient
from infrastructure.cache_redis import AsyncRedisCache
from services.problem import ProblemService

if TYPE_CHECKING:
    from litestar.datastructures import State


async def provide_http_client(state: "State") -> AsyncGenerator[AsyncHTTPClient, None]:
    client = AsyncHTTPClient()
    logger.debug("HTTP client created")
    try:
        yield client
    finally:
        await client.close()
        logger.debug("HTTP client closed")


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


async def provide_clients(state: "State") -> AsyncGenerator[dict, None]:
    http_client = AsyncHTTPClient()
    cache_client = AsyncRedisCache()

    use_cache = False
    try:
        await cache_client.connect()
        logger.debug("Connected to Redis for request")
        use_cache = True
    except Exception as e:
        logger.warning(f"Failed to connect to Redis, caching disabled: {e}")

    try:
        yield {
            "http_client": http_client,
            "cache_client": cache_client if use_cache else None,
            "use_cache": use_cache,
        }
    finally:
        logger.debug("Cleaning up request resources")
        await http_client.close()
        await cache_client.close()
        logger.debug("All clients closed")


async def provide_problem_service(state: "State") -> AsyncGenerator[ProblemService, None]:
    service = ProblemService()

    logger.debug("ProblemService created")

    try:
        yield service
    finally:
        logger.debug("ProblemService cleaned up")
