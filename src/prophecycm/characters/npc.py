from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

from prophecycm.combat.status_effects import StatusEffect
from prophecycm.core import Serializable
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, ensure_typed_id
from prophecycm.items.item import Item
from prophecycm.characters.player import XP_THRESHOLDS

if TYPE_CHECKING:
    from prophecycm.characters.creature import Creature, CreatureTierTemplate
else:
    from prophecycm.characters.creature import Creature, CreatureTierTemplate


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
    tiers: List["CreatureTierTemplate"] = field(default_factory=list)

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
            tiers=[
                t
                if isinstance(t, CreatureTierTemplate)
                else CreatureTierTemplate.from_dict(t)
                for t in data.get("tiers", [])
            ],
        )


@dataclass
class NPC(Serializable):
    id: str
    archetype: str
    faction_id: str
    disposition: str
    inventory: List[Item] = field(default_factory=list)
    inventory_item_ids: List[str] = field(default_factory=list)
    status_effects: List[StatusEffect] = field(default_factory=list)
    quest_hooks: List[str] = field(default_factory=list)
    is_companion: bool = True
    stat_block: Optional["Creature"] = None
    scaling: Optional[NPCScalingProfile] = None
    is_alive: bool = True
    level: int = 0
    xp: int = 0
    auto_level: bool = True

    def __post_init__(self) -> None:
        if self.stat_block is not None:
            if self.level <= 0:
                self.level = max(1, self.stat_block.level)
            else:
                self.stat_block.level = self.level
            self.stat_block.recompute_statistics()
            self.is_alive = self.stat_block.is_alive
        elif self.level <= 0:
            self.level = 1

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

        tier_candidates = scaling.tiers or scaled.tiers
        selected_tier = scaled.select_tier_for_level(target_level, difficulty, tier_candidates)
        scaled = scaled.apply_tier(selected_tier)

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

    def recompute_statistics(self) -> None:
        if self.stat_block is None:
            return
        self.stat_block.level = max(self.level, 1)
        self.stat_block.recompute_statistics()
        self.is_alive = self.stat_block.is_alive

    def apply_auto_level(self, *, difficulty: str = "standard") -> None:
        """Bring the companion's stat block up to its tracked level."""

        if self.stat_block is None:
            return

        if self.scaling is not None:
            scaled = self.scaled_stat_block(self.level, difficulty)
            if scaled:
                self.stat_block = scaled
        else:
            self.stat_block.level = self.level
            self.stat_block.recompute_statistics()
        self.is_alive = self.stat_block.is_alive

    def gain_xp(self, amount: int) -> List[int]:
        self.xp += max(0, amount)
        leveled_up: List[int] = []
        while True:
            next_level = self.level + 1
            threshold = XP_THRESHOLDS.get(next_level)
            if threshold is None or self.xp < threshold:
                break
            self.level = next_level
            leveled_up.append(self.level)
        return leveled_up

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
        stat_block_data = data.get("stat_block")
        stat_block = None if stat_block_data is None else _load_creature(stat_block_data)
        default_level = stat_block.level if stat_block is not None else 1
        npc_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data["id"], expected_prefix="npc", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="npc",
        )
        return cls(
            id=npc_id,
            archetype=data.get("archetype", ""),
            faction_id=data.get("faction_id", ""),
            disposition=data.get("disposition", "neutral"),
            inventory=[Item.from_dict(item) for item in data.get("inventory", [])],
            inventory_item_ids=list(data.get("inventory_item_ids", [])),
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            quest_hooks=list(data.get("quest_hooks", [])),
            is_companion=bool(data.get("is_companion", True)),
            stat_block=stat_block,
            scaling=(None if (scaling := data.get("scaling")) is None else NPCScalingProfile.from_dict(scaling)),
            is_alive=bool(data.get("is_alive", True)),
            level=int(data.get("level", default_level)),
            xp=int(data.get("xp", 0)),
            auto_level=bool(data.get("auto_level", True)),
        )


def _load_creature(payload: Dict[str, object]):
    from prophecycm.characters.creature import Creature

    return Creature.from_dict(payload)
