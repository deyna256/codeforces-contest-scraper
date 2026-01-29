"""Infrastructure-level exceptions."""


class CodeforcesEditorialError(Exception):
    """Base exception for all codeforces-editorial-finder errors."""

    pass


class NetworkError(CodeforcesEditorialError):
    """Network or HTTP request error."""

    pass


class ProblemNotFoundError(CodeforcesEditorialError):
    """Problem page not found (404) or inaccessible."""

    pass


class ContestNotFoundError(CodeforcesEditorialError):
    """Contest not found (404) or inaccessible."""

    pass


class CacheError(CodeforcesEditorialError):
    """Cache operation error."""

    pass
