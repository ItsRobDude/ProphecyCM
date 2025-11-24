from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from prophecycm.core import Serializable


@dataclass
class StatusEffect(Serializable):
    id: str
    name: str
    duration: int
    modifiers: Dict[str, int] = field(default_factory=dict)
    source: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StatusEffect":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            duration=int(data.get("duration", 0)),
            modifiers=data.get("modifiers", {}),
            source=data.get("source", ""),
        )
