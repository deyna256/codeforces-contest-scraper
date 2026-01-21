"""Value objects for parsed data."""

from dataclasses import dataclass

from .identifiers import ProblemIdentifier


@dataclass
class ProblemData:
    """Data extracted from a problem page."""

    identifier: ProblemIdentifier
    description: str | None = None
    time_limit: str | None = None
    memory_limit: str | None = None


@dataclass
class ContestPageData:
    """Data extracted from a contest page."""

    contest_id: str
    title: str | None = None
    editorial_url: str | None = None
