from services.cache import clear_cache
from services.contest import ContestService
from services.problem import ProblemService


def create_problem_service() -> ProblemService:
    """Factory function to create problem service with all dependencies."""
    from infrastructure.http_client import AsyncHTTPClient
    from infrastructure.codeforces_client import CodeforcesApiClient
    from infrastructure.parsers import ProblemPageParser, URLParser

    # Create infrastructure dependencies
    http_client = AsyncHTTPClient()
    api_client = CodeforcesApiClient(http_client)
    page_parser = ProblemPageParser(http_client)

    return ProblemService(
        api_client=api_client,
        page_parser=page_parser,
        url_parser=URLParser,
    )


def create_contest_service() -> ContestService:
    """Factory function to create contest service with all dependencies."""
    from config import get_settings
    from infrastructure.http_client import AsyncHTTPClient
    from infrastructure.codeforces_client import CodeforcesApiClient
    from infrastructure.llm_client import OpenRouterClient
    from infrastructure.parsers import ContestPageParser, URLParser, EditorialContentParser
    from infrastructure.parsers.llm_editorial_finder import LLMEditorialFinder

    settings = get_settings()

    # Create infrastructure dependencies
    http_client = AsyncHTTPClient()
    api_client = CodeforcesApiClient(http_client)

    # Create LLM editorial finder if enabled and configured
    llm_editorial_finder = None
    if settings.llm_enabled and settings.openrouter_api_key:
        llm_client = OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
        )
        llm_editorial_finder = LLMEditorialFinder(llm_client)

    page_parser = ContestPageParser(http_client, llm_editorial_finder)

    # Create editorial content parser if LLM is enabled
    editorial_parser = None
    if settings.llm_enabled and settings.openrouter_api_key:
        editorial_parser = EditorialContentParser(http_client, llm_client)

    return ContestService(
        api_client=api_client,
        page_parser=page_parser,
        url_parser=URLParser,
        editorial_parser=editorial_parser,
    )


__all__ = [
    "clear_cache",
    "ContestService",
    "create_contest_service",
    "create_problem_service",
    "ProblemService",
]
