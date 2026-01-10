"""API route handlers."""

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Body
from loguru import logger

from application.orchestrator import AsyncEditorialOrchestrator
from presentation.dependencies import provide_orchestrator
from presentation.schemas import (
    EditorialRequest,
    EditorialResponse,
    EditorialSchema,
    ProblemSchema,
    CodeSnippetSchema,
)


def build_cache_key(request: EditorialRequest) -> str:
    """
    Build cache key for response caching.

    Args:
        request: Editorial request

    Returns:
        Cache key based on URL
    """
    # Use URL as cache key (normalize it first)
    normalized_url = request.url.lower().strip()
    return f"response:{normalized_url}"


class EditorialController(Controller):
    """Controller for editorial endpoint."""

    path = "/"
    dependencies = {"orchestrator": Provide(provide_orchestrator)}

    @post(
        "/editorial",
        summary="Get editorial for Codeforces problem",
        description="Fetch and extract editorial/solution for a given Codeforces problem URL",
        status_code=200,
        cache=True,  # Enable response caching
        cache_key_builder=build_cache_key,
    )
    async def get_editorial(
        self,
        data: EditorialRequest = Body(...),
        orchestrator: AsyncEditorialOrchestrator = None,
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
            problem_id=problem_data.identifier.problem_id,
            title=problem_data.title,
            url=problem_data.url,
            contest_name=problem_data.contest_name,
            tags=problem_data.tags or [],
            time_limit=problem_data.time_limit,
            memory_limit=problem_data.memory_limit,
        )

        code_snippets_schema = [
            CodeSnippetSchema(
                language=snippet.language,
                code=snippet.code,
                description=snippet.description,
            )
            for snippet in editorial.code_snippets
        ]

        editorial_schema = EditorialSchema(
            problem_id=editorial.problem_id,
            solution_text=editorial.solution_text,
            approach=editorial.approach,
            algorithm=editorial.algorithm,
            time_complexity=editorial.time_complexity,
            space_complexity=editorial.space_complexity,
            code_snippets=code_snippets_schema,
            hints=editorial.hints or [],
            notes=editorial.notes,
            source_url=editorial.source_url,
            extracted_at=editorial.extracted_at,
            ai_model=editorial.ai_model,
        )

        response = EditorialResponse(
            problem=problem_schema,
            editorial=editorial_schema,
        )

        logger.info(f"Successfully processed request for {problem_data.identifier}")
        return response
