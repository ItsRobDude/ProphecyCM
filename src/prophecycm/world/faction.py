from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from prophecycm.core import Serializable
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, ensure_typed_id


@dataclass
class Faction(Serializable):
    id: str
    name: str
    ideology: str = ""
    relationships: Dict[str, int] = field(default_factory=dict)
    base_rep: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Faction":
        faction_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data["id"], expected_prefix="faction", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="faction",
        )
        return cls(
            id=faction_id,
            name=data.get("name", ""),
            ideology=data.get("ideology", ""),
            relationships=data.get("relationships", {}),
            base_rep=int(data.get("base_rep", 0)),
        )
