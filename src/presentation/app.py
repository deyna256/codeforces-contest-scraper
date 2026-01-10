"""LiteStar application setup."""

from litestar import Litestar
from litestar.config.response_cache import ResponseCacheConfig
from litestar.middleware.rate_limit import RateLimitConfig
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
    OpenAIAPIError,
)
from presentation.exceptions import exception_to_http_response
from presentation.routes import EditorialController


def create_app() -> Litestar:
    """
    Create and configure LiteStar application.

    Returns:
        Configured Litestar app instance
    """
    settings = get_settings()

    # Configure Redis store for rate limiting and caching
    redis_store = RedisStore.with_client(
        url=settings.redis_url,
    )

    # Configure rate limiting
    # Limit: 10 requests per minute per client
    rate_limit_config = RateLimitConfig(
        rate_limit=("minute", 10),
        store="redis",
        exclude=["/schema"],  # Exclude OpenAPI schema endpoint
    )

    # Configure response caching
    # Cache responses for 1 hour (3600 seconds)
    response_cache_config = ResponseCacheConfig(
        default_expiration=3600,
    )

    # Exception handlers mapping
    exception_handlers = {
        CodeforcesEditorialError: exception_to_http_response,
        URLParsingError: exception_to_http_response,
        EditorialNotFoundError: exception_to_http_response,
        ExtractionError: exception_to_http_response,
        ParsingError: exception_to_http_response,
        CacheError: exception_to_http_response,
        OpenAIAPIError: exception_to_http_response,
    }

    # Create LiteStar app
    app = Litestar(
        route_handlers=[EditorialController],
        stores={"redis": redis_store},
        middleware=[rate_limit_config.middleware],
        response_cache_config=response_cache_config,
        exception_handlers=exception_handlers,
        debug=settings.log_level == "DEBUG",
        openapi_config=None,  # Disable OpenAPI docs for minimal API
    )

    logger.info("LiteStar application created")
    logger.info("Rate limit: 10 requests per minute")
    logger.info("Response cache TTL: 3600 seconds")
    logger.info(f"Redis URL: {settings.redis_url}")

    return app


# Create app instance
app = create_app()
