from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable


@dataclass
class Item(Serializable):
    id: str
    name: str
    rarity: str = "common"
    value: int = 0
    tags: List[str] = field(default_factory=list)
    item_type: str = "generic"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Item":
        item_type = data.get("item_type", "generic")
        if item_type == "equipment":
            return Equipment.from_dict(data)
        if item_type == "consumable":
            return Consumable.from_dict(data)
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            rarity=data.get("rarity", "common"),
            value=int(data.get("value", 0)),
            tags=list(data.get("tags", [])),
            item_type=item_type,
        )


@dataclass
class Equipment(Item):
    slot: str = ""
    modifiers: Dict[str, int] = field(default_factory=dict)
    requirements: Dict[str, int] = field(default_factory=dict)
    item_type: str = "equipment"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Equipment":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            rarity=data.get("rarity", "common"),
            value=int(data.get("value", 0)),
            tags=list(data.get("tags", [])),
            slot=data.get("slot", ""),
            modifiers=data.get("modifiers", {}),
            requirements=data.get("requirements", {}),
        )


@dataclass
class Consumable(Item):
    effect: str = ""
    charges: int = 1
    item_type: str = "consumable"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Consumable":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            rarity=data.get("rarity", "common"),
            value=int(data.get("value", 0)),
            tags=list(data.get("tags", [])),
            effect=data.get("effect", ""),
            charges=int(data.get("charges", 1)),
        )
