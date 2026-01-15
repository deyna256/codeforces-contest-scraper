from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any
from .problem import ProblemIdentifier

@dataclass
class CodeSnippet:
    language: str
    code: str
    description: str = ""

@dataclass
class TutorialData:
    language: str
    content: str

@dataclass
class Editorial:
    problem: ProblemIdentifier
    solution_text: str
    approach: str
    algorithm: str
    time_complexity: str
    space_complexity: str
    code_snippets: List[CodeSnippet]
    hints: List[str]
    notes: List[str]
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem.full_id,
            "solution_text": self.solution_text,
            "approach": self.approach,
            "algorithm": self.algorithm,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "code_snippets": [s.__dict__ for s in self.code_snippets],
            "hints": self.hints,
            "notes": self.notes,
            "source_url": self.source_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Editorial:
        return cls(
            problem=data["problem"],
            solution_text=data.get("solution_text", ""),
            approach=data.get("approach", ""),
            algorithm=data.get("algorithm", ""),
            time_complexity=data.get("time_complexity", ""),
            space_complexity=data.get("space_complexity", ""),
            code_snippets=[CodeSnippet(**s) for s in data.get("code_snippets", [])],
            hints=data.get("hints", []),
            notes=data.get("notes", []),
            source_url=data.get("source_url", ""),
        )
