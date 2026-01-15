from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .editorial import Editorial


@dataclass
class CachedEditorial:
    editorial: Editorial

    def to_dict(self) -> dict[str, Any]:
        """Serialize CachedEditorial to dict."""
        return {"editorial": self.editorial.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CachedEditorial:
        """Deserialize CachedEditorial from dict."""
        editorial_data = data.get("editorial", {})
        return cls(editorial=Editorial.from_dict(editorial_data))
