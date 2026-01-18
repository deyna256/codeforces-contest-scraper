from loguru import logger


async def clear_cache(cache_client) -> None:
    if cache_client:
        logger.info("Clearing cache")
        await cache_client.flushdb()
    else:
        logger.warning("Cache is not enabled")
