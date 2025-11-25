from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from prophecycm.core import Serializable


@dataclass
class Faction(Serializable):
    id: str
    name: str
    ideology: str = ""
    relationships: Dict[str, int] = field(default_factory=dict)
    base_rep: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Faction":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            ideology=data.get("ideology", ""),
            relationships=data.get("relationships", {}),
            base_rep=int(data.get("base_rep", 0)),
        )
