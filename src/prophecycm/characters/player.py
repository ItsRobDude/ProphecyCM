from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.combat.status_effects import StatusEffect
from prophecycm.core import Serializable
from prophecycm.items.item import Item


@dataclass
class PlayerCharacter(Serializable):
    id: str
    name: str
    background: str
    attributes: Dict[str, int]
    skills: List[str]
    inventory: List[Item] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)
    level: int = 1
    xp: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PlayerCharacter":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            background=data.get("background", ""),
            attributes=data.get("attributes", {}),
            skills=list(data.get("skills", [])),
            inventory=[Item.from_dict(item) for item in data.get("inventory", [])],
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            level=int(data.get("level", 1)),
            xp=int(data.get("xp", 0)),
        )
