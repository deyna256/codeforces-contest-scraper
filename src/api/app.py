from litestar import Litestar
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.stores.redis import RedisStore
from litestar.stores.memory import MemoryStore
import asyncio
from loguru import logger

from config import get_settings
from domain.exceptions import (
    CodeforcesEditorialError,
    URLParsingError,
    EditorialNotFoundError,
    ExtractionError,
    ParsingError,
    CacheError,
)
from api.exceptions import exception_to_http_response
from api.routes import CacheController, ProblemController


def create_app() -> Litestar:
    settings = get_settings()

    # Try to connect to Redis, fallback to memory store if not available
    stores = {}
    middleware = []
    use_redis = False

    try:
        redis_store = RedisStore.with_client(url=settings.redis_url)
        stores["redis"] = redis_store
        rate_limit_config = RateLimitConfig(
            rate_limit=("minute", 10),
            store="redis",
            exclude=["/schema"],
        )
        middleware.append(rate_limit_config.middleware)
        use_redis = True
        logger.info("Redis connected successfully")

    except Exception as e:
        logger.warning(f"Redis not available, falling back to in-memory storage: {e}")
        stores["memory"] = MemoryStore()
        # No rate limiting in fallback mode
        logger.info("Using in-memory storage without rate limiting")

    exception_handlers = {
        CodeforcesEditorialError: exception_to_http_response,
        URLParsingError: exception_to_http_response,
        EditorialNotFoundError: exception_to_http_response,
        ExtractionError: exception_to_http_response,
        ParsingError: exception_to_http_response,
        CacheError: exception_to_http_response,
    }

    openapi_config = OpenAPIConfig(
        title="Codeforces Editorial Finder API",
        version="1.0.0",
        description="API for finding and extracting editorials for Codeforces problems",
    )

    app = Litestar(
        route_handlers=[CacheController, ProblemController],
        stores=stores,
        middleware=middleware,
        exception_handlers=exception_handlers,
        debug=settings.log_level == "DEBUG",
        openapi_config=openapi_config,
    )

    logger.info("LiteStar application created")
    logger.info(f"Redis available: {use_redis}")

    return app


app = create_app()
