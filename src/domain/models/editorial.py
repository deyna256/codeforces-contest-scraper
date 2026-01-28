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


@dataclass
class EditorialURL:
    """URL for an editorial blog entry."""

    url: str
    source_type: str  # e.g., "blog_entry", "announcement"


@dataclass
class ContestEditorialURLs:
    """Collection of editorial URLs for a contest."""

    contest_id: str
    urls: List[EditorialURL]
