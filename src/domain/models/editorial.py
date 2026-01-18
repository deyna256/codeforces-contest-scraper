# src/domain/models/editorial.py
from dataclasses import dataclass


@dataclass(slots=True)
class Editorial:
    problem_id: str
    tutorial_text: str


@dataclass(slots=True)
class TutorialData:
    title: str
    content: str
