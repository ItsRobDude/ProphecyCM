from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from prophecycm.combat.status_effects import StatusEffect
from prophecycm.core import Serializable
from prophecycm.items.item import Item

if TYPE_CHECKING:
    from prophecycm.characters.creature import Creature
else:
    from prophecycm.characters.creature import Creature


@dataclass
class NPCScalingProfile(Serializable):
    """Controls how an NPC's attached stat block scales to player level."""

    base_level: int = 1
    min_level: int = 1
    max_level: int = 20
    attack_progression: int = 0
    damage_progression: int = 0
    difficulty_multipliers: Dict[str, float] = field(
        default_factory=lambda: {"easy": 0.75, "standard": 1.0, "hard": 1.25, "deadly": 1.5}
    )

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "NPCScalingProfile":
        return cls(
            base_level=int(data.get("base_level", 1)),
            min_level=int(data.get("min_level", 1)),
            max_level=int(data.get("max_level", 20)),
            attack_progression=int(data.get("attack_progression", 0)),
            damage_progression=int(data.get("damage_progression", 0)),
            difficulty_multipliers=data.get("difficulty_multipliers", None)
            or {"easy": 0.75, "standard": 1.0, "hard": 1.25, "deadly": 1.5},
        )


@dataclass
class NPC(Serializable):
    id: str
    archetype: str
    faction_id: str
    disposition: str
    inventory: List[Item] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)
    quest_hooks: List[str] = field(default_factory=list)
    stat_block: Optional["Creature"] = None
    scaling: Optional[NPCScalingProfile] = None
    is_alive: bool = True

    def scaled_stat_block(self, player_level: int, difficulty: str = "standard") -> Optional["Creature"]:
        """Return a combat-ready copy of the NPC's stat block.

        Scaling is applied only if this NPC specifies an `NPCScalingProfile`.
        Base creatures remain authored values; this wrapper is the only layer
        that can sync levels to the player.
        """

        if self.stat_block is None:
            return None

        scaled = deepcopy(self.stat_block)
        if self.scaling is None:
            scaled.recompute_statistics()
            scaled.current_hit_points = scaled.hit_points
            scaled.is_alive = self.is_alive and scaled.is_alive
            return scaled

        scaling = self.scaling
        base_level = scaling.base_level if scaling.base_level > 0 else scaled.level

        multiplier = scaling.difficulty_multipliers.get(difficulty, 1.0)
        delta = player_level - base_level
        adjusted_delta = int(delta * multiplier)
        target_level = max(scaling.min_level, min(scaling.max_level, base_level + adjusted_delta))

        level_delta = target_level - scaled.level
        scaled.level = target_level
        scaled.recompute_statistics()

        if level_delta != 0:
            for action in scaled.actions:
                action.to_hit_bonus += level_delta * scaling.attack_progression
                action.damage_bonus += level_delta * scaling.damage_progression

        scaled.current_hit_points = scaled.hit_points if self.is_alive else 0
        scaled.is_alive = self.is_alive and scaled.is_alive
        return scaled

    def apply_damage(self, amount: int) -> None:
        if self.stat_block:
            self.stat_block.apply_damage(amount)
            if not self.stat_block.is_alive:
                self.is_alive = False
        else:
            if amount > 0:
                self.is_alive = False

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
            stat_block=(None if (block := data.get("stat_block")) is None else _load_creature(block)),
            scaling=(None if (scaling := data.get("scaling")) is None else NPCScalingProfile.from_dict(scaling)),
            is_alive=bool(data.get("is_alive", True)),
        )


def _load_creature(payload: Dict[str, object]):
    from prophecycm.characters.creature import Creature

    return Creature.from_dict(payload)
