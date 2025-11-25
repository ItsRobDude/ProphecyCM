from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.combat.status_effects import DispelCondition, DurationType, StatusEffect
from prophecycm.core import Serializable
from prophecycm.items.item import Equipment, EquipmentSlot, Item


def _safe_slot_conversion(raw_slot: object) -> EquipmentSlot | None:
    try:
        return raw_slot if isinstance(raw_slot, EquipmentSlot) else EquipmentSlot(str(raw_slot))
    except ValueError:
        return None


@dataclass
class AbilityScore(Serializable):
    name: str = ""
    score: int = 10
    modifier: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AbilityScore":
        return cls(
            name=data.get("name", ""),
            score=int(data.get("score", 10)),
            modifier=int(data.get("modifier", 0)),
        )


@dataclass
class Skill(Serializable):
    name: str
    key_ability: str
    proficiency: str = "untrained"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            key_ability=data.get("key_ability", ""),
            proficiency=data.get("proficiency", "untrained"),
        )


@dataclass
class Race(Serializable):
    id: str = ""
    name: str = ""
    ability_bonuses: Dict[str, int] = field(default_factory=dict)
    bonuses: Dict[str, int] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Race":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            ability_bonuses=data.get("ability_bonuses", {}),
            bonuses=data.get("bonuses", {}),
            traits=list(data.get("traits", [])),
        )


@dataclass
class Class(Serializable):
    id: str = ""
    name: str = ""
    hit_die: int = 6
    save_proficiencies: List[str] = field(default_factory=list)
    ability_bonuses: Dict[str, int] = field(default_factory=dict)
    bonuses: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Class":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            hit_die=int(data.get("hit_die", 6)),
            save_proficiencies=list(data.get("save_proficiencies", [])),
            ability_bonuses=data.get("ability_bonuses", {}),
            bonuses=data.get("bonuses", {}),
        )


@dataclass
class Feat(Serializable):
    id: str
    name: str
    description: str = ""
    modifiers: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Feat":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            modifiers=data.get("modifiers", {}),
        )


@dataclass
class PlayerCharacter(Serializable):
    id: str
    name: str
    background: str
    abilities: Dict[str, AbilityScore]
    skills: Dict[str, Skill]
    race: Race
    character_class: Class
    feats: List[Feat] = field(default_factory=list)
    inventory: List[Item] = field(default_factory=list)
    equipment: Dict[EquipmentSlot, Equipment] = field(default_factory=dict)
    status_effects: List[StatusEffect] = field(default_factory=list)
    level: int = 1
    xp: int = 0
    hit_points: int = 0
    current_hit_points: int | None = None
    is_alive: bool = True
    armor_class: int = 10
    saves: Dict[str, int] = field(default_factory=dict)
    initiative: int = 0
    proficiency_bonus: int = 2

    def __post_init__(self) -> None:
        self.recompute_statistics()
        if self.current_hit_points is None:
            self.current_hit_points = self.hit_points
        self.current_hit_points = min(self.current_hit_points, self.hit_points)
        if self.current_hit_points <= 0:
            self.current_hit_points = 0
            self.is_alive = False

    def recompute_statistics(self) -> None:
        ability_bonuses = self._collect_ability_bonuses()
        aggregated_modifiers = self._collect_modifiers()

        for ability_name, ability_score in self.abilities.items():
            bonus = ability_bonuses.get(ability_name, 0) + aggregated_modifiers.get(ability_name, 0)
            total_score = ability_score.score + bonus
            ability_score.modifier = (total_score - 10) // 2

        self.proficiency_bonus = 2 + (self.level - 1) // 4

        con_mod = self.abilities.get("constitution", AbilityScore()).modifier
        dex_mod = self.abilities.get("dexterity", AbilityScore()).modifier
        wis_mod = self.abilities.get("wisdom", AbilityScore()).modifier

        base_hp = max(1, self.character_class.hit_die + con_mod)
        self.hit_points = self.level * base_hp + aggregated_modifiers.get("hit_points", 0)

        self.armor_class = 10 + dex_mod + aggregated_modifiers.get("armor_class", 0)

        save_proficiencies = set(self.character_class.save_proficiencies)
        self.saves = {
            "fortitude": con_mod + (self.proficiency_bonus if "fortitude" in save_proficiencies else 0)
            + aggregated_modifiers.get("fortitude", 0),
            "reflex": dex_mod + (self.proficiency_bonus if "reflex" in save_proficiencies else 0)
            + aggregated_modifiers.get("reflex", 0),
            "will": wis_mod + (self.proficiency_bonus if "will" in save_proficiencies else 0)
            + aggregated_modifiers.get("will", 0),
        }

        self.initiative = dex_mod + self.proficiency_bonus + aggregated_modifiers.get("initiative", 0)

        if self.current_hit_points is not None:
            self.current_hit_points = min(self.current_hit_points, self.hit_points)
            if self.current_hit_points <= 0:
                self.is_alive = False

    def _collect_ability_bonuses(self) -> Dict[str, int]:
        bonuses: Dict[str, int] = {}
        for source in (self.race.ability_bonuses, self.character_class.ability_bonuses):
            for key, value in source.items():
                bonuses[key] = bonuses.get(key, 0) + int(value)
        return bonuses

    def _collect_modifiers(self) -> Dict[str, int]:
        modifiers: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for key, value in source.items():
                modifiers[key] = modifiers.get(key, 0) + int(value)

        for bonus_source in (self.race.bonuses, self.character_class.bonuses):
            merge(bonus_source)

        for feat in self.feats:
            merge(feat.modifiers)

        for item in self.equipment.values():
            merge(getattr(item, "modifiers", {}))

        for effect in self.status_effects:
            merge(effect.total_modifiers())

        return modifiers

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PlayerCharacter":
        abilities_data = data.get("abilities", {})
        abilities: Dict[str, AbilityScore] = {}
        for name, value in abilities_data.items():
            if isinstance(value, dict):
                abilities[name] = AbilityScore.from_dict({"name": name, **value})
            else:
                abilities[name] = AbilityScore(name=name, score=int(value))

        skills_data = data.get("skills", {})
        skills: Dict[str, Skill] = {}
        for name, value in skills_data.items():
            if isinstance(value, dict):
                skills[name] = Skill.from_dict({"name": name, **value})
            else:
                skills[name] = Skill(name=name, key_ability="", proficiency=str(value))

        feats = [Feat.from_dict(feat) for feat in data.get("feats", [])]
        equipment_data = data.get("equipment", {})

        instance = cls(
            id=data["id"],
            name=data.get("name", ""),
            background=data.get("background", ""),
            abilities=abilities,
            skills=skills,
            race=Race.from_dict(data.get("race", {})),
            character_class=Class.from_dict(data.get("character_class", {})),
            feats=feats,
            inventory=[Item.from_dict(item) for item in data.get("inventory", [])],
            equipment={
                slot_value: Equipment.from_dict(equipment)
                for slot, equipment in equipment_data.items()
                if (slot_value := _safe_slot_conversion(slot)) is not None
            },
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            level=int(data.get("level", 1)),
            xp=int(data.get("xp", 0)),
            hit_points=int(data.get("hit_points", 0)),
            current_hit_points=data.get("current_hit_points"),
            is_alive=bool(data.get("is_alive", True)),
            armor_class=int(data.get("armor_class", 10)),
            saves=data.get("saves", {}),
            initiative=int(data.get("initiative", 0)),
            proficiency_bonus=int(data.get("proficiency_bonus", 2)),
        )
        return instance

    def to_dict(self) -> Dict[str, object]:
        payload = super().to_dict()
        payload["equipment"] = {slot.value: item.to_dict() for slot, item in self.equipment.items()}
        return payload

    def add_status_effect(self, effect: StatusEffect) -> None:
        for existing in self.status_effects:
            if existing.id == effect.id:
                existing.combine(effect)
                break
        else:
            self.status_effects.append(effect)
        self.recompute_statistics()

    def apply_damage(self, amount: int) -> None:
        if not self.is_alive:
            return
        self.current_hit_points = max(0, (self.current_hit_points or 0) - max(0, amount))
        if self.current_hit_points == 0:
            self.is_alive = False

    def heal(self, amount: int) -> None:
        if not self.is_alive:
            return
        self.current_hit_points = min(self.hit_points, (self.current_hit_points or 0) + max(0, amount))

    def gain_xp(self, amount: int) -> List[int]:
        self.xp += max(0, amount)
        leveled_up: List[int] = []
        while True:
            next_level = self.level + 1
            threshold = XP_THRESHOLDS.get(next_level)
            if threshold is None or self.xp < threshold:
                break
            self.level = next_level
            self.recompute_statistics()
            if self.current_hit_points is None:
                self.current_hit_points = self.hit_points
            leveled_up.append(self.level)
        return leveled_up

    def tick_status_effects(self, tick_type: DurationType = DurationType.TURNS) -> None:
        self.status_effects = [effect for effect in self.status_effects if effect.tick(tick_type)]
        self.recompute_statistics()

    def dispel_status_effects(self, dispel_type: DispelCondition = DispelCondition.ANY) -> None:
        self.status_effects = [effect for effect in self.status_effects if not effect.can_be_dispelled(dispel_type)]
        self.recompute_statistics()

    def equip_item(self, item: Equipment) -> None:
        if not isinstance(item, Equipment):
            raise TypeError("Only equipment can be equipped")

        if item.slot == EquipmentSlot.TWO_HAND:
            if EquipmentSlot.MAIN_HAND in self.equipment or EquipmentSlot.OFF_HAND in self.equipment:
                raise ValueError("Cannot equip a two-handed item while hands are occupied")
            self.equipment[EquipmentSlot.TWO_HAND] = item
        elif item.slot == EquipmentSlot.MAIN_HAND:
            if EquipmentSlot.TWO_HAND in self.equipment:
                raise ValueError("Cannot equip main-hand item while using two-handed weapon")
            self.equipment[EquipmentSlot.MAIN_HAND] = item
        elif item.slot == EquipmentSlot.OFF_HAND:
            if EquipmentSlot.TWO_HAND in self.equipment:
                raise ValueError("Cannot equip off-hand item while using two-handed weapon")
            if item.two_handed:
                raise ValueError("Off-hand items cannot be two-handed")
            self.equipment[EquipmentSlot.OFF_HAND] = item
        else:
            self.equipment[item.slot] = item

        if item not in self.inventory:
            self.inventory.append(item)

        self.recompute_statistics()

    def unequip(self, slot: EquipmentSlot) -> Equipment | None:
        removed = self.equipment.pop(slot, None)
        self.recompute_statistics()
        return removed
XP_THRESHOLDS: Dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
}

