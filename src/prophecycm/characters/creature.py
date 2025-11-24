from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from prophecycm.combat.status_effects import DispelCondition, DurationType, StatusEffect
from prophecycm.core import Serializable
from prophecycm.characters.player import AbilityScore


@dataclass
class CreatureAction(Serializable):
    """Represents a creature combat action/attack profile."""

    name: str
    attack_ability: str = "strength"
    to_hit_bonus: int = 0
    damage_dice: str = "1d6"
    damage_bonus: int = 0
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CreatureAction":
        return cls(
            name=data.get("name", ""),
            attack_ability=data.get("attack_ability", "strength"),
            to_hit_bonus=int(data.get("to_hit_bonus", 0)),
            damage_dice=data.get("damage_dice", "1d6"),
            damage_bonus=int(data.get("damage_bonus", 0)),
            tags=list(data.get("tags", [])),
        )


@dataclass
class Creature(Serializable):
    """Enemy/creature stat block with 5e-inspired derived stats.

    Creatures are authored as static templates. NPC wrappers decide whether and
    how to scale them to the player's level. This class only tracks permanent
    state such as current hit points and death.
    """

    id: str
    name: str
    level: int
    role: str
    hit_die: int
    armor_class: int
    abilities: Dict[str, AbilityScore]
    actions: List[CreatureAction]
    alignment: str = ""
    traits: List[str] = field(default_factory=list)
    save_proficiencies: List[str] = field(default_factory=list)
    speed: int = 30
    hit_points: int = 0
    proficiency_bonus: int = 2
    saves: Dict[str, int] = field(default_factory=dict)
    status_effects: List[StatusEffect] = field(default_factory=list)
    current_hit_points: Optional[int] = None
    is_alive: bool = True
    _base_armor_class: int = field(init=False, repr=False, default=0)

    def __post_init__(self) -> None:
        self._base_armor_class = self.armor_class
        self.recompute_statistics()
        if self.current_hit_points is None:
            self.current_hit_points = self.hit_points
        self.current_hit_points = min(self.current_hit_points, self.hit_points)
        if self.current_hit_points <= 0:
            self.current_hit_points = 0
            self.is_alive = False

    def recompute_statistics(self) -> None:
        aggregated_modifiers = self._collect_modifiers()
        for ability_name, ability_score in self.abilities.items():
            total_score = ability_score.score + aggregated_modifiers.get(ability_name, 0)
            ability_score.modifier = (total_score - 10) // 2

        self.proficiency_bonus = 2 + (self.level - 1) // 4

        con_mod = self.abilities.get("constitution", AbilityScore()).modifier
        dex_mod = self.abilities.get("dexterity", AbilityScore()).modifier
        wis_mod = self.abilities.get("wisdom", AbilityScore()).modifier

        avg_hit_per_level = max(1, (self.hit_die // 2) + 1 + con_mod)
        max_hit_points = avg_hit_per_level * max(1, self.level) + aggregated_modifiers.get("hit_points", 0)
        self.hit_points = max_hit_points

        self.armor_class = self._base_armor_class + aggregated_modifiers.get("armor_class", 0) + dex_mod

        save_proficiencies = set(self.save_proficiencies)
        self.saves = {
            "fortitude": con_mod + (self.proficiency_bonus if "fortitude" in save_proficiencies else 0)
            + aggregated_modifiers.get("fortitude", 0),
            "reflex": dex_mod + (self.proficiency_bonus if "reflex" in save_proficiencies else 0)
            + aggregated_modifiers.get("reflex", 0),
            "will": wis_mod + (self.proficiency_bonus if "will" in save_proficiencies else 0)
            + aggregated_modifiers.get("will", 0),
        }

        if self.current_hit_points is None:
            self.current_hit_points = self.hit_points
        else:
            self.current_hit_points = min(self.current_hit_points, self.hit_points)
        if self.current_hit_points <= 0:
            self.current_hit_points = 0
            self.is_alive = False

    def _collect_modifiers(self) -> Dict[str, int]:
        modifiers: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for key, value in source.items():
                modifiers[key] = modifiers.get(key, 0) + int(value)

        for effect in self.status_effects:
            merge(effect.total_modifiers())
        return modifiers

    def add_status_effect(self, effect: StatusEffect) -> None:
        for existing in self.status_effects:
            if existing.id == effect.id:
                existing.combine(effect)
                break
        else:
            self.status_effects.append(effect)
        self.recompute_statistics()

    def tick_status_effects(self, tick_type: DurationType = DurationType.TURNS) -> None:
        self.status_effects = [effect for effect in self.status_effects if effect.tick(tick_type)]
        self.recompute_statistics()

    def dispel_status_effects(self, dispel_type: DispelCondition = DispelCondition.ANY) -> None:
        self.status_effects = [effect for effect in self.status_effects if not effect.can_be_dispelled(dispel_type)]
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

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Creature":
        abilities_data = data.get("abilities", {})
        abilities: Dict[str, AbilityScore] = {}
        for name, value in abilities_data.items():
            if isinstance(value, dict):
                abilities[name] = AbilityScore.from_dict({"name": name, **value})
            else:
                abilities[name] = AbilityScore(name=name, score=int(value))

        actions = [CreatureAction.from_dict(action) for action in data.get("actions", [])]

        creature = cls(
            id=data["id"],
            name=data.get("name", ""),
            level=int(data.get("level", 1)),
            role=data.get("role", ""),
            hit_die=int(data.get("hit_die", 6)),
            armor_class=int(data.get("armor_class", 10)),
            abilities=abilities,
            actions=actions,
            alignment=data.get("alignment", ""),
            traits=list(data.get("traits", [])),
            save_proficiencies=list(data.get("save_proficiencies", [])),
            speed=int(data.get("speed", 30)),
            hit_points=int(data.get("hit_points", 0)),
            proficiency_bonus=int(data.get("proficiency_bonus", 2)),
            saves=data.get("saves", {}),
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            current_hit_points=data.get("current_hit_points"),
            is_alive=bool(data.get("is_alive", True)),
        )
        return creature
