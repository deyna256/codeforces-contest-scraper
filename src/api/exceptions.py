from litestar import Request, Response
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from loguru import logger

from infrastructure.errors import (
    CacheError,
    CodeforcesEditorialError,
    ContestNotFoundError,
)
from infrastructure.parsers import ParsingError, URLParsingError
from api.schemas import ErrorResponse


def exception_to_http_response(request: Request, exc: Exception) -> Response[ErrorResponse]:
    logger.error(f"Exception in {request.url}: {exc}")

    if isinstance(exc, URLParsingError):
        status_code = HTTP_400_BAD_REQUEST
        error_type = "URLParsingError"
        detail = str(exc)

    elif isinstance(exc, ContestNotFoundError):
        status_code = HTTP_404_NOT_FOUND
        error_type = "ContestNotFoundError"
        detail = str(exc)

    elif isinstance(exc, ParsingError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "ParsingError"
        detail = str(exc)

    elif isinstance(exc, CacheError):
        logger.warning(f"Cache error (non-fatal): {exc}")
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "CacheError"
        detail = "Internal cache error occurred"

    elif isinstance(exc, CodeforcesEditorialError):
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "CodeforcesEditorialError"
        detail = str(exc)

    else:
        logger.exception(f"Unexpected error: {exc}")
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = type(exc).__name__
        detail = "An unexpected error occurred"

    error_response = ErrorResponse(
        status_code=status_code,
        detail=detail,
        error_type=error_type,
    )

    return Response(
        content=error_response,
        status_code=status_code,
    )
