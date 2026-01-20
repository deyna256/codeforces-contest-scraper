from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Editorial:
    problem: str
    solution_text: str
    source_url: Optional[str] = None
    extracted_at: Optional[datetime] = None


@dataclass
class TutorialData:
    url: str
    format: str
    content: str
    language: str
    title: str
    raw_bytes: Optional[bytes] = None


# Optional: if you have CachedEditorial or CodeSnippet, define them too
@dataclass
class CachedEditorial:
    editorial: Editorial
    cached_at: datetime


@dataclass
class CodeSnippet:
    language: str
    code: str
