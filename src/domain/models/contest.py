"""Core domain model for Codeforces contests."""

from dataclasses import dataclass, field


@dataclass
class ContestProblem:
    """Domain model for a problem within a contest."""

    contest_id: str
    id: str
    title: str
    statement: str | None = None
    rating: int | None = None
    tags: list[str] = field(default_factory=list)
    time_limit: str | None = None
    memory_limit: str | None = None
    explanation: str | None = None


@dataclass
class Contest:
    """Domain model for a Codeforces contest."""

    contest_id: str
    title: str
    problems: list[ContestProblem] = field(default_factory=list)
    editorials: list[str] = field(default_factory=list)
