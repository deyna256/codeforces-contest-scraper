"""Core domain model for Codeforces problems."""

from dataclasses import dataclass, field


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
