from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.combat.status_effects import StatusEffect
from prophecycm.core import Serializable
from prophecycm.items.item import Item


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
    status_effects: List[StatusEffect] = field(default_factory=list)
    level: int = 1
    xp: int = 0
    hit_points: int = 0
    armor_class: int = 10
    saves: Dict[str, int] = field(default_factory=dict)
    initiative: int = 0
    proficiency_bonus: int = 2

    def __post_init__(self) -> None:
        self.recompute_statistics()

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

        for item in self.inventory:
            if hasattr(item, "modifiers"):
                merge(getattr(item, "modifiers"))

        for effect in self.status_effects:
            merge(effect.modifiers)

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
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            level=int(data.get("level", 1)),
            xp=int(data.get("xp", 0)),
            hit_points=int(data.get("hit_points", 0)),
            armor_class=int(data.get("armor_class", 10)),
            saves=data.get("saves", {}),
            initiative=int(data.get("initiative", 0)),
            proficiency_bonus=int(data.get("proficiency_bonus", 2)),
        )
        return instance
