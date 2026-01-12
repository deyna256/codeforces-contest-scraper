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
    approach: Optional[str] = None
    algorithm: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    code_snippets: list[CodeSnippet] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    source_url: Optional[str] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    ai_model: Optional[str] = None


@dataclass
class CachedEditorial:
    """Cached editorial with metadata."""
    editorial: Editorial
    cached_at: datetime = field(default_factory=datetime.now)
    ttl_hours: int = 168  # 7 days default
    problem: Optional[ProblemIdentifier] = None
    tutorial_url: Optional[str] = None
    tutorial_format: TutorialFormat = TutorialFormat.UNKNOWN


    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age_hours = (datetime.now() - self.cached_at).total_seconds() / 3600
        return age_hours > self.ttl_hours

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "problem": {
    "contest_id": self.problem.contest_id if self.problem else None,
    "problem_id": self.problem.problem_id if self.problem else None,
    "is_gym": self.problem.is_gym if self.problem else False,
},

            "editorial": {
                "problem_id": self.editorial.problem_id,
                "solution_text": self.editorial.solution_text,
                "approach": self.editorial.approach,
                "algorithm": self.editorial.algorithm,
                "time_complexity": self.editorial.time_complexity,
                "space_complexity": self.editorial.space_complexity,
                "code_snippets": [
                    {
                        "language": snippet.language,
                        "code": snippet.code,
                        "description": snippet.description,
                    }
                    for snippet in self.editorial.code_snippets
                ],
                "hints": self.editorial.hints,
                "notes": self.editorial.notes,
                "source_url": self.editorial.source_url,
                "extracted_at": self.editorial.extracted_at.isoformat(),
                "ai_model": self.editorial.ai_model,
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

        code_snippets = [
            CodeSnippet(
                language=snippet["language"],
                code=snippet["code"],
                description=snippet.get("description"),
            )
            for snippet in data["editorial"].get("code_snippets", [])
        ]

        editorial = Editorial(
            problem_id=data["editorial"]["problem_id"],
            solution_text=data["editorial"]["solution_text"],
            approach=data["editorial"].get("approach"),
            algorithm=data["editorial"].get("algorithm"),
            time_complexity=data["editorial"].get("time_complexity"),
            space_complexity=data["editorial"].get("space_complexity"),
            code_snippets=code_snippets,
            hints=data["editorial"].get("hints", []),
            notes=data["editorial"].get("notes"),
            source_url=data["editorial"].get("source_url"),
            extracted_at=datetime.fromisoformat(data["editorial"]["extracted_at"]),
            ai_model=data["editorial"].get("ai_model"),
        )

        return cls(
            problem=problem,
            editorial=editorial,
            tutorial_url=data["tutorial_url"],
            tutorial_format=TutorialFormat(data["tutorial_format"]),
            cached_at=datetime.fromisoformat(data["cached_at"]),
            ttl_hours=data["ttl_hours"],
        )
