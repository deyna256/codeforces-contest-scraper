from services.cache import clear_cache
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


__all__ = ["clear_cache", "ProblemService", "create_problem_service"]
