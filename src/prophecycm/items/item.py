from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from prophecycm.core import Serializable


class EquipmentSlot(str, Enum):
    HEAD = "head"
    CHEST = "chest"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    TWO_HAND = "two_hand"
    ACCESSORY = "accessory"


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
    slot: EquipmentSlot = EquipmentSlot.ACCESSORY
    modifiers: Dict[str, int] = field(default_factory=dict)
    requirements: Dict[str, int] = field(default_factory=dict)
    two_handed: bool = False
    off_hand_only: bool = False
    item_type: str = "equipment"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Equipment":
        slot_value = data.get("slot", EquipmentSlot.ACCESSORY)
        try:
            slot = slot_value if isinstance(slot_value, EquipmentSlot) else EquipmentSlot(str(slot_value))
        except ValueError:
            slot = EquipmentSlot.ACCESSORY

        return cls(
            id=data["id"],
            name=data.get("name", ""),
            rarity=data.get("rarity", "common"),
            value=int(data.get("value", 0)),
            tags=list(data.get("tags", [])),
            slot=slot,
            modifiers=data.get("modifiers", {}),
            requirements=data.get("requirements", {}),
            two_handed=bool(data.get("two_handed", False)),
            off_hand_only=bool(data.get("off_hand_only", False)),
        )

    def to_dict(self) -> Dict[str, object]:
        payload = super().to_dict()
        payload["slot"] = self.slot.value
        return payload


@dataclass
class Consumable(Item):
    effect_id: str = ""
    charges: int = 1
    usable_in_combat: bool = True
    action_cost: int = 1
    item_type: str = "consumable"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Consumable":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            rarity=data.get("rarity", "common"),
            value=int(data.get("value", 0)),
            tags=list(data.get("tags", [])),
            effect_id=data.get("effect_id", data.get("effect", "")),
            charges=int(data.get("charges", 1)),
            usable_in_combat=bool(data.get("usable_in_combat", True)),
            action_cost=int(data.get("action_cost", 1)),
        )
