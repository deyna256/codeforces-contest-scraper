"""Value objects for problem identification."""

from dataclasses import dataclass


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


@dataclass(frozen=True)
class ContestIdentifier:
    """Identifies a specific Codeforces contest."""

    contest_id: str
    is_gym: bool = False

    def __str__(self) -> str:
        """String representation."""
        prefix = "gym/" if self.is_gym else ""
        return f"{prefix}{self.contest_id}"
