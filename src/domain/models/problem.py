from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProblemIdentifier:
    contest_id: str
    problem_id: str
    is_gym: bool = False


@dataclass
class ProblemData:
    identifier: ProblemIdentifier
    title: str
    url: str
    contest_name: Optional[str]
    possible_editorial_links: List[str]
