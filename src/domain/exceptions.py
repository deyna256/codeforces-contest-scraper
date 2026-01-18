"""Custom exceptions for codeforces-editorial-finder."""


class CodeforcesEditorialError(Exception):
    """Base exception for all codeforces-editorial-finder errors."""

    pass


class URLParsingError(CodeforcesEditorialError):
    """Invalid URL format or unable to parse URL."""

    pass


class ProblemNotFoundError(CodeforcesEditorialError):
    """Problem page not found (404) or inaccessible."""

    pass


class EditorialNotFoundError(CodeforcesEditorialError):
    """Editorial/tutorial link not found for the problem."""

    pass


class EditorialLoadError(CodeforcesEditorialError):
    """Failed to load or download editorial content."""

    pass


class ExtractionError(CodeforcesEditorialError):
    """Failed to extract solution from editorial."""

    pass


class NetworkError(CodeforcesEditorialError):
    """Network or HTTP request error."""

    pass


class CacheError(CodeforcesEditorialError):
    """Cache operation error."""

    pass


class ConfigurationError(CodeforcesEditorialError):
    """Configuration or settings error."""

    pass


class ParsingError(CodeforcesEditorialError):
    """Error parsing HTML or PDF content."""

    pass
