from dataclasses import dataclass
from typing import List


@dataclass
class Editorial:
    """Editorial analysis for a specific problem."""

    problem_id: str
    analysis_text: str
    contest_id: str | None = None  # Contest ID for disambiguation in multi-contest editorials


@dataclass
class ContestEditorial:
    """Complete editorial with all problem analyses for a contest."""

    contest_id: str
    editorials: List[Editorial]
