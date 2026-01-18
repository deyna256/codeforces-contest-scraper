from litestar import Controller, delete
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from loguru import logger

from api.dependencies import provide_cache_client
from services import clear_cache
from infrastructure.cache_redis import AsyncRedisCache


class CacheController(Controller):
    path = "/cache"
    dependencies = {"cache": Provide(provide_cache_client)}

    @delete("/", status_code=HTTP_200_OK)
    async def clear_cache_endpoint(
        self,
        cache: tuple[AsyncRedisCache | None, bool],
    ) -> dict[str, str]:
        cache_client, use_cache = cache

        if not use_cache or cache_client is None:
            logger.warning("Cache clear requested but cache is not available")
            return {
                "status": "warning",
                "message": "Cache is not enabled or not available",
            }

        await clear_cache(cache_client)
        logger.info("Cache cleared successfully via API")

        return {
            "status": "success",
            "message": "Cache cleared successfully",
        }
