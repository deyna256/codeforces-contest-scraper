"""API route handlers."""

from litestar import Controller, post, Request
from litestar.di import Provide
from loguru import logger

from application.orchestrator import AsyncEditorialOrchestrator
from presentation.dependencies import provide_orchestrator
from presentation.schemas import (
    EditorialRequest,
    EditorialResponse,
    EditorialSchema,
    ProblemSchema,
)


def build_cache_key(request: Request) -> str:
    """
    Build cache key for response caching.

    Args:
        request: Litestar request object

    Returns:
        Cache key based on request
    """
    # For POST requests, built-in caching is limited if we need the body.
    # Here we use the path as a fallback, but in practice, you might want
    # to use a custom middleware or handle caching in the service layer
    # for POST requests with different bodies.
    return f"response:{request.url.path}"


class EditorialController(Controller):
    """Controller for editorial endpoint."""

    path = "/"
    dependencies = {"orchestrator": Provide(provide_orchestrator)}

    @post(
        "/editorial",
        summary="Get editorial for Codeforces problem",
        description="Fetch and extract editorial/solution for a given Codeforces problem URL",
        status_code=200,
        cache=False,
        cache_key_builder=build_cache_key,
    )
    async def get_editorial(
        self,
        data: EditorialRequest,
        orchestrator: AsyncEditorialOrchestrator,
    ) -> EditorialResponse:
        """
        Get editorial for problem URL.

        Args:
            data: Request with problem URL
            orchestrator: Injected orchestrator instance

        Returns:
            EditorialResponse with problem and editorial data

        Raises:
            Various domain exceptions (handled by exception handlers)
        """
        logger.info(f"Received request for URL: {data.url}")

        # Get editorial using orchestrator
        editorial, problem_data = await orchestrator.get_editorial(data.url)

        # Convert domain models to response schemas
        problem_schema = ProblemSchema(
            contest_id=problem_data.identifier.contest_id,
            problem=problem_data.identifier.problem,
            title=problem_data.title,
            url=problem_data.url,
            contest_name=problem_data.contest_name,
            tags=[],  # removed from domain model
            time_limit=None,  # removed from domain model
            memory_limit=None,  # removed from domain model
        )

        editorial_schema = EditorialSchema(
            problem=editorial.problem,
            solution_text=editorial.solution_text,
            source_url=editorial.source_url,
            extracted_at=editorial.extracted_at,
        )

        response = EditorialResponse(
            problem=problem_schema,
            editorial=editorial_schema,
        )

        logger.info(f"Successfully processed request for {problem_data.identifier}")
        return response
