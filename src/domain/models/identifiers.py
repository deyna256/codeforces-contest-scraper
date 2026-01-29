"""Value objects for problem identification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemIdentifier:
    """Identifies a specific Codeforces problem."""

    contest_id: str
    problem_id: str

    def __str__(self) -> str:
        """String representation."""
        return f"{self.contest_id}/{self.problem_id}"


@dataclass(frozen=True)
class ContestIdentifier:
    """Identifies a specific Codeforces contest."""

    contest_id: str

    def __str__(self) -> str:
        """String representation."""
        return f"{self.contest_id}"
