from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict

from prophecycm.characters.player import PlayerCharacter
from prophecycm.rules import SKILL_TO_ABILITY


@dataclass
class RollResult:
    label: str
    dc: int
    roll: int
    modifier: int
    total: int
    success: bool
    breakdown: str


PROFICIENCY_MULTIPLIER: Dict[str, int] = {
    "untrained": 0,
    "trained": 1,
    "expert": 2,
}


def skill_modifier(pc: PlayerCharacter, skill_name: str) -> int:
    skill = pc.skills.get(skill_name)
    key_ability = (skill.key_ability if skill else SKILL_TO_ABILITY.get(skill_name)) or ""
    ability_mod = pc.abilities.get(key_ability).modifier if key_ability in pc.abilities else 0
    prof_tier = PROFICIENCY_MULTIPLIER.get(skill.proficiency, 0) if skill else 0
    return ability_mod + prof_tier * pc.proficiency_bonus


def ability_modifier(pc: PlayerCharacter, ability_name: str) -> int:
    ability = pc.abilities.get(ability_name)
    return ability.modifier if ability else 0


def roll_d20(
    rng: random.Random | None = None, *, advantage: bool = False, disadvantage: bool = False
) -> int:
    if rng is None:
        rng = random.Random()

    first = rng.randint(1, 20)
    if advantage and disadvantage:
        return first

    if advantage or disadvantage:
        second = rng.randint(1, 20)
        return max(first, second) if advantage else min(first, second)
    return first


def roll_skill_check(
    pc: PlayerCharacter,
    skill_name: str,
    dc: int,
    rng: random.Random | None = None,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
    ability_only: bool = False,
    ability: str | None = None,
) -> RollResult:
    ability_name = ability or SKILL_TO_ABILITY.get(skill_name, skill_name)
    modifier = ability_modifier(pc, ability_name) if ability_only else skill_modifier(pc, skill_name)
    roll = roll_d20(rng, advantage=advantage, disadvantage=disadvantage)
    total = roll + modifier
    breakdown = (
        f"{ability_name.title()} check: d20 roll {roll} + modifier {modifier:+} = {total} vs DC {dc}"
    )
    return RollResult(
        label=ability_name,
        dc=dc,
        roll=roll,
        modifier=modifier,
        total=total,
        success=total >= dc,
        breakdown=breakdown,
    )


def _perform_check(
    modifier: int,
    dc: int,
    label: str,
    rng: random.Random | None = None,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    roll = roll_d20(rng, advantage=advantage, disadvantage=disadvantage)
    total = roll + modifier
    breakdown = f"{label} check: d20 roll {roll} + modifier {modifier:+} = {total} vs DC {dc}"
    return RollResult(
        label=label,
        dc=dc,
        roll=roll,
        modifier=modifier,
        total=total,
        success=total >= dc,
        breakdown=breakdown,
    )


def ability_check(
    pc: PlayerCharacter,
    ability: str,
    dc: int,
    rng: random.Random | None = None,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    label = str(ability).title()
    modifier = pc.get_ability_modifier(ability)
    return _perform_check(
        modifier,
        dc,
        label,
        rng,
        advantage=advantage,
        disadvantage=disadvantage,
    )


def skill_check(
    pc: PlayerCharacter,
    skill: str,
    dc: int,
    rng: random.Random | None = None,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    label = str(skill).title()
    modifier = pc.get_skill_modifier(skill)
    return _perform_check(
        modifier,
        dc,
        label,
        rng,
        advantage=advantage,
        disadvantage=disadvantage,
    )


def saving_throw(
    pc: PlayerCharacter,
    ability: str,
    dc: int,
    rng: random.Random | None = None,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    ability_label = str(ability).title()
    label = f"{ability_label} Save"
    aggregated_modifiers = getattr(pc, "_cached_modifiers", None)
    modifier = pc.get_save_modifier(ability, aggregated_modifiers)
    return _perform_check(
        modifier,
        dc,
        label,
        rng,
        advantage=advantage,
        disadvantage=disadvantage,
    )
