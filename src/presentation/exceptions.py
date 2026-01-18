"""HTTP exception handlers for domain exceptions."""

from typing import TYPE_CHECKING

from litestar import Request, Response
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from loguru import logger

from domain.exceptions import (
    CodeforcesEditorialError,
    URLParsingError,
    EditorialNotFoundError,
    ExtractionError,
    ParsingError,
    CacheError,
    OpenAIAPIError,
)
from presentation.schemas import ErrorResponse

if TYPE_CHECKING:
    pass


def exception_to_http_response(
    request: Request, exc: Exception
) -> Response[ErrorResponse]:
    """
    Convert domain exceptions to HTTP responses.

    Args:
        request: HTTP request
        exc: Exception to convert

    Returns:
        HTTP response with error details
    """
    logger.error(f"Exception in {request.url}: {exc}")

    # Map domain exceptions to HTTP status codes
    if isinstance(exc, URLParsingError):
        status_code = HTTP_400_BAD_REQUEST
        error_type = "URLParsingError"
        detail = str(exc)

    elif isinstance(exc, EditorialNotFoundError):
        status_code = HTTP_404_NOT_FOUND
        error_type = "EditorialNotFoundError"
        detail = str(exc)

    elif isinstance(exc, ExtractionError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "ExtractionError"
        detail = str(exc)

    elif isinstance(exc, ParsingError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        error_type = "ParsingError"
        detail = str(exc)

    elif isinstance(exc, OpenAIAPIError):
        status_code = HTTP_503_SERVICE_UNAVAILABLE
        error_type = "OpenAIAPIError"
        detail = "OpenAI API is currently unavailable. Please try again later."

    elif isinstance(exc, CacheError):
        # Cache errors shouldn't fail the request
        logger.warning(f"Cache error (non-fatal): {exc}")
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "CacheError"
        detail = "Internal cache error occurred"

    elif isinstance(exc, CodeforcesEditorialError):
        # Generic domain error
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "CodeforcesEditorialError"
        detail = str(exc)

    else:
        # Unexpected error
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
