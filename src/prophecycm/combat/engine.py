from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.player import AbilityScore, PlayerCharacter
from prophecycm.core import Serializable
from prophecycm.items.item import Consumable


@dataclass
class CombatantRef(Serializable):
    kind: Literal["pc", "creature", "npc"]
    id: str


@dataclass
class TurnOrderEntry(Serializable):
    ref: CombatantRef
    initiative: int
    is_conscious: bool = True


@dataclass
class EncounterState(Serializable):
    id: str
    participants: List[CombatantRef]
    turn_order: List[TurnOrderEntry]
    active_index: int = 0
    round: int = 1
    difficulty: str = "standard"
    meta: dict[str, object] = field(default_factory=dict)


@dataclass
class TurnContext(Serializable):
    actor: CombatantRef
    remaining_ap: int = 3


@dataclass
class AttackResult(Serializable):
    hit: bool
    crit: bool
    damage: int
    target_died: bool


def roll_dice(expression: str, rng: Optional[random.Random] = None) -> int:
    """Parse and roll a simple NdM(+/-)K dice expression."""

    rng = rng or random.Random()
    match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expression.strip())
    if not match:
        return 0

    num, die, modifier = match.groups()
    total = sum(rng.randint(1, int(die)) for _ in range(int(num)))
    if modifier:
        total += int(modifier)
    return total


def roll_initiative(pc: PlayerCharacter, creatures: List[Creature], rng: random.Random) -> List[TurnOrderEntry]:
    entries: List[TurnOrderEntry] = []

    pc_init_roll = rng.randint(1, 20) + pc.initiative
    entries.append(TurnOrderEntry(CombatantRef("pc", pc.id), pc_init_roll))

    for creature in creatures:
        dex_mod = creature.abilities.get("dexterity", AbilityScore()).modifier
        init_mod = dex_mod + creature.proficiency_bonus
        roll = rng.randint(1, 20) + init_mod
        entries.append(TurnOrderEntry(CombatantRef("creature", creature.id), roll))

    entries.sort(key=lambda entry: entry.initiative, reverse=True)
    return entries


def resolve_attack(attacker: Creature, defender: Creature, action: CreatureAction, rng: random.Random) -> AttackResult:
    ability = attacker.abilities.get(action.attack_ability, AbilityScore())
    attack_mod = ability.modifier + attacker.proficiency_bonus + action.to_hit_bonus
    roll = rng.randint(1, 20)

    crit = roll == 20
    hit_roll = roll + attack_mod

    if crit or hit_roll >= defender.armor_class:
        base_damage = roll_dice(action.damage_dice, rng) + action.damage_bonus + ability.modifier
        if crit:
            base_damage *= 2
        defender.apply_damage(base_damage)
        return AttackResult(hit=True, crit=crit, damage=base_damage, target_died=not defender.is_alive)

    return AttackResult(hit=False, crit=False, damage=0, target_died=False)


def use_consumable_in_combat(
    pc: PlayerCharacter, item: Consumable, target: Creature | PlayerCharacter
) -> bool:
    if not item.usable_in_combat or item.charges <= 0:
        return False

    effect_id = item.effect_id
    healed = False
    if effect_id.startswith("heal_"):
        try:
            heal_amount = int(effect_id.split("_", 1)[1])
        except (ValueError, IndexError):
            heal_amount = 0
        healed = heal_amount > 0
        _apply_heal(target, heal_amount)
    elif effect_id in {"restore_health", "heal"}:
        healed = True
        _apply_heal(target, 25)
    else:
        # Future: map to StatusEffect templates
        healed = False

    item.charges -= 1
    if item.charges <= 0 and item in pc.inventory:
        pc.inventory.remove(item)

    return healed


def _apply_heal(target: Creature | PlayerCharacter, amount: int) -> None:
    if isinstance(target, Creature):
        target.heal(amount)
    else:
        target.heal(amount)
