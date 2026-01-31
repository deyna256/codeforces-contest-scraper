from litestar import Litestar
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.stores.redis import RedisStore
from litestar.stores.memory import MemoryStore
from loguru import logger

from config import get_settings
from infrastructure.errors import (
    CacheError,
    CodeforcesEditorialError,
    ContestNotFoundError,
)
from infrastructure.parsers import ParsingError, URLParsingError
from infrastructure.parsers.errors import (
    EditorialContentFetchError,
    EditorialContentParseError,
    EditorialNotFoundError,
    LLMSegmentationError,
)
from api.exceptions import exception_to_http_response
from api.routes import CacheController, ContestController, ProblemController


def create_app() -> Litestar:
    settings = get_settings()

    # Try to connect to Redis, fallback to memory store if not available
    stores = {}
    middleware = []

    try:
        redis_store = RedisStore.with_client(url=settings.redis_url)
        stores["redis"] = redis_store
        rate_limit_config = RateLimitConfig(
            rate_limit=("minute", 10),
            store="redis",
            exclude=["/schema"],
        )
        middleware.append(rate_limit_config.middleware)

    except Exception as e:
        logger.debug(f"Redis not available, falling back to in-memory storage: {e}")
        stores["memory"] = MemoryStore()

    exception_handlers = {
        CacheError: exception_to_http_response,
        CodeforcesEditorialError: exception_to_http_response,
        ContestNotFoundError: exception_to_http_response,
        EditorialContentFetchError: exception_to_http_response,
        EditorialContentParseError: exception_to_http_response,
        EditorialNotFoundError: exception_to_http_response,
        LLMSegmentationError: exception_to_http_response,
        ParsingError: exception_to_http_response,
        URLParsingError: exception_to_http_response,
    }

    openapi_config = OpenAPIConfig(
        title="Codeforces Editorial Finder API",
        version="1.0.0",
        description="API for finding and extracting editorials for Codeforces problems",
    )

    app = Litestar(
        route_handlers=[CacheController, ContestController, ProblemController],
        stores=stores,
        middleware=middleware,
        exception_handlers=exception_handlers,
        debug=settings.log_level == "DEBUG",
        openapi_config=openapi_config,
    )

    return app


app = create_app()
