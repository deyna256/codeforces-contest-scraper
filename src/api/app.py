from litestar import Litestar
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.stores.redis import RedisStore
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
from api.routes import CacheController


def create_app() -> Litestar:
    settings = get_settings()

    redis_store = RedisStore.with_client(url=settings.redis_url)

    rate_limit_config = RateLimitConfig(
        rate_limit=("minute", 10),
        store="redis",
        exclude=["/schema"],
    )

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
        route_handlers=[CacheController],
        stores={"redis": redis_store},
        middleware=[rate_limit_config.middleware],
        exception_handlers=exception_handlers,
        debug=settings.log_level == "DEBUG",
        openapi_config=openapi_config,
    )

    logger.info("LiteStar application created")
    logger.info(f"Redis URL: {settings.redis_url}")

    return app


app = create_app()
