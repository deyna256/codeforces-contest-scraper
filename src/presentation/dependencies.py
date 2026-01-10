"""Dependency injection providers for LiteStar."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from loguru import logger

from application.orchestrator import AsyncEditorialOrchestrator
from infrastructure.http_client import AsyncHTTPClient
from infrastructure.openai_client import AsyncOpenAIClient
from infrastructure.cache_redis import AsyncRedisCache

if TYPE_CHECKING:
    from litestar.datastructures import State


async def provide_orchestrator(state: "State") -> AsyncGenerator[AsyncEditorialOrchestrator, None]:
    """
    Provide AsyncEditorialOrchestrator with all dependencies.

    This is a dependency injection provider that:
    1. Creates all required clients (HTTP, OpenAI, Redis)
    2. Initializes the orchestrator
    3. Yields it to the route handler
    4. Cleans up all resources after the request

    Args:
        state: LiteStar application state

    Yields:
        AsyncEditorialOrchestrator instance
    """

    # Initialize clients
    http_client = AsyncHTTPClient()
    ai_client = AsyncOpenAIClient()
    cache_client = AsyncRedisCache()

    try:
        # Connect to Redis
        await cache_client.connect()
        logger.debug("Connected to Redis for request")

        # Create orchestrator with dependency injection
        orchestrator = AsyncEditorialOrchestrator(
            http_client=http_client,
            ai_client=ai_client,
            cache_client=cache_client,
            use_cache=True,
        )

        logger.debug("Orchestrator created with dependencies")

        # Yield orchestrator to route handler
        yield orchestrator

    finally:
        # Cleanup resources
        logger.debug("Cleaning up request resources")

        await http_client.close()
        logger.debug("Closed HTTP client")

        await ai_client.close()
        logger.debug("Closed OpenAI client")

        await cache_client.close()
        logger.debug("Closed Redis connection")
