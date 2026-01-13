"""Data models for codeforces-editorial-finder."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TutorialFormat(str, Enum):
    """Tutorial content format."""

    HTML = "html"
    PDF = "pdf"
    UNKNOWN = "unknown"


class Language(str, Enum):
    """Tutorial language."""

    ENGLISH = "en"
    RUSSIAN = "ru"
    AUTO = "auto"


@dataclass(frozen=True)
class ProblemIdentifier:
    """Identifies a specific Codeforces problem."""

    contest_id: str
    problem_id: str
    is_gym: bool = False

    @property
    def full_id(self) -> str:
        """Get full problem identifier (e.g., '1234A')."""
        return f"{self.contest_id}{self.problem_id}"

    @property
    def cache_key(self) -> str:
        """Get cache key for this problem."""
        prefix = "gym_" if self.is_gym else ""
        return f"editorial_{prefix}{self.contest_id}_{self.problem_id}"

    def __str__(self) -> str:
        """String representation."""
        prefix = "gym/" if self.is_gym else ""
        return f"{prefix}{self.contest_id}/{self.problem_id}"


@dataclass
class ProblemData:
    """Data extracted from a problem page."""

    identifier: ProblemIdentifier
    title: str
    url: str
    contest_name: Optional[str] = None
    description: Optional[str] = None
    time_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    announcement_text: Optional[str] = None
    possible_editorial_links: list[str] = field(default_factory=list)


@dataclass
class TutorialData:
    """Tutorial/editorial content and metadata."""

    url: str
    format: TutorialFormat
    content: str  # Raw HTML or extracted text
    language: Language = Language.AUTO
    title: Optional[str] = None
    author: Optional[str] = None
    raw_bytes: Optional[bytes] = None  # For PDF content


@dataclass
class CodeSnippet:
    """Code snippet from editorial."""

    language: str
    code: str
    description: Optional[str] = None


@dataclass
class Editorial:
    """Extracted editorial/solution for a problem."""

    problem_id: str
    solution_text: str
    source_url: Optional[str] = None
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class CachedEditorial:
    """Cached editorial with metadata."""

    problem: ProblemIdentifier
    editorial: Editorial
    tutorial_url: str
    tutorial_format: TutorialFormat
    cached_at: datetime = field(default_factory=datetime.now)
    ttl_hours: int = 168  # 7 days default

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age_hours = (datetime.now() - self.cached_at).total_seconds() / 3600
        return age_hours > self.ttl_hours

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "problem": {
                "contest_id": self.problem.contest_id,
                "problem_id": self.problem.problem_id,
                "is_gym": self.problem.is_gym,
            },
            "editorial": {
                "problem_id": self.editorial.problem_id,
                "solution_text": self.editorial.solution_text,
                "source_url": self.editorial.source_url,
                "extracted_at": self.editorial.extracted_at.isoformat(),
            },
            "tutorial_url": self.tutorial_url,
            "tutorial_format": self.tutorial_format.value,
            "cached_at": self.cached_at.isoformat(),
            "ttl_hours": self.ttl_hours,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedEditorial":
        """Create from dictionary."""
        problem = ProblemIdentifier(
            contest_id=data["problem"]["contest_id"],
            problem_id=data["problem"]["problem_id"],
            is_gym=data["problem"]["is_gym"],
        )

        editorial = Editorial(
            problem_id=data["editorial"]["problem_id"],
            solution_text=data["editorial"]["solution_text"],
            source_url=data["editorial"].get("source_url"),
            extracted_at=datetime.fromisoformat(data["editorial"]["extracted_at"]),
        )

        return cls(
            problem=problem,
            editorial=editorial,
            tutorial_url=data["tutorial_url"],
            tutorial_format=TutorialFormat(data["tutorial_format"]),
            cached_at=datetime.fromisoformat(data["cached_at"]),
            ttl_hours=data["ttl_hours"],
        )
