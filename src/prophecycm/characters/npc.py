from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.combat.status_effects import StatusEffect
from prophecycm.core import Serializable
from prophecycm.items.item import Item


@dataclass
class NPC(Serializable):
    id: str
    archetype: str
    faction_id: str
    disposition: str
    inventory: List[Item] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)
    quest_hooks: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "NPC":
        return cls(
            id=data["id"],
            archetype=data.get("archetype", ""),
            faction_id=data.get("faction_id", ""),
            disposition=data.get("disposition", "neutral"),
            inventory=[Item.from_dict(item) for item in data.get("inventory", [])],
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            quest_hooks=list(data.get("quest_hooks", [])),
        )
