# src/domain/models/cached_editorial.py
from dataclasses import dataclass
from domain.models.editorial import Editorial


@dataclass
class CachedEditorial:
    editorial: Editorial

    def to_dict(self) -> dict:
        return {"editorial": self.editorial.tutorial_text}

    @classmethod
    def from_dict(cls, data: dict):
        editorial = Editorial(problem_id="", tutorial_text=data["editorial"])
        return cls(editorial=editorial)
