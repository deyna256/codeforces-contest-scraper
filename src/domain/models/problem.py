from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class ProblemIdentifier:
    contest_id: int
    problem_index: str
    is_gym: bool = False

    def __init__(
        self,
        contest_id: int,
        problem_index: str | None = None,
        *,
        problem: str | None = None,
        problem_id: str | None = None,
        is_gym: bool = False,
    ) -> None:
        object.__setattr__(self, "contest_id", int(contest_id))

        index = problem_index or problem or problem_id
        if index is None:
            raise TypeError("ProblemIdentifier requires a problem index")

        object.__setattr__(self, "problem_index", index)
        object.__setattr__(self, "is_gym", is_gym)

    @property
    def cache_key(self) -> str:
        return f"{self.contest_id}-{self.problem_index}"

    @property
    def problem(self) -> str:
        return self.problem_index

    @property
    def problem_id(self) -> str:
        return self.problem_index


@dataclass
class ProblemData:
    identifier: ProblemIdentifier
    title: str
    url: str
    contest_name: Optional[str]
    possible_editorial_links: List[str]
