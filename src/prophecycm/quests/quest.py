from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable


@dataclass
class Quest(Serializable):
    id: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    stage: int = 0
    status: str = "active"
    rewards: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Quest":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            objectives=list(data.get("objectives", [])),
            stage=int(data.get("stage", 0)),
            status=data.get("status", "active"),
            rewards=data.get("rewards", {}),
        )
