"""Protocol interfaces for parsers."""

from typing import Protocol

from domain.models import ContestPageData, ProblemData, ProblemIdentifier
from domain.models.problem import Problem


class URLParserProtocol(Protocol):
    """Protocol for URL parsing."""

    @classmethod
    def parse(cls, url: str) -> ProblemIdentifier:
        """Parse URL to extract problem identifier."""
        ...

    @classmethod
    def build_problem_url(cls, identifier: ProblemIdentifier) -> str:
        """Build problem URL from identifier."""
        ...


class ProblemPageParserProtocol(Protocol):
    """Protocol for parsing problem pages."""

    async def parse_problem_page(self, identifier: ProblemIdentifier) -> ProblemData:
        """Parse problem page and extract data."""
        ...


class ParsingError(ValueError):
    """Error parsing HTML or PDF content."""

    pass


class APIClientProtocol(Protocol):
    """Protocol for Codeforces API client."""

    async def get_problem(self, identifier: ProblemIdentifier) -> Problem:
        """Get problem data from Codeforces API."""
        ...


class HTTPClientProtocol(Protocol):
    """Protocol for HTTP client."""

    async def get_text(self, url: str) -> str:
        """Get text content from URL."""
        ...


class ContestPageParserProtocol(Protocol):
    """Protocol for parsing contest pages."""

    async def parse_contest_page(self, contest_id: str) -> ContestPageData:
        """Parse contest page and extract data."""
        ...

    async def parse_problem_in_contest(self, contest_id: str, problem_id: str) -> ProblemData:
        """Parse problem page within a contest."""
        ...


class ContestAPIClientProtocol(Protocol):
    """Protocol for Codeforces contest API client."""

    async def fetch_contest_standings(self, contest_id: str) -> dict:
        """Fetch contest standings from Codeforces API."""
        ...

    async def fetch_problemset_problems(self) -> dict:
        """Fetch all problems from Codeforces problemset."""
        ...
