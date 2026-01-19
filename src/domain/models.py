"""Data models for codeforces-editorial-finder."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProblemIdentifier:
    """Identifies a specific Codeforces problem."""

    contest_id: str
    problem_id: str
    is_gym: bool = False

    def __str__(self) -> str:
        """String representation."""
        prefix = "gym/" if self.is_gym else ""
        return f"{prefix}{self.contest_id}/{self.problem_id}"


@dataclass
class Problem:
    """Domain model for a Codeforces problem."""

    contest_id: str
    id: str
    statement: str
    description: str | None = None
    time_limit: str | None = None
    memory_limit: str | None = None
    rating: int | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ProblemData:
    """Data extracted from a problem page."""

    identifier: ProblemIdentifier
    description: str | None = None
    time_limit: str | None = None
    memory_limit: str | None = None
