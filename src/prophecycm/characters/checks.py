from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict

from prophecycm.characters.player import PlayerCharacter
from prophecycm.rules import SKILL_TO_ABILITY


@dataclass
class SkillCheckResult:
    roll: int
    total: int
    dc: int
    success: bool
    critical: bool = False
    fumble: bool = False


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


def _roll_d20(rng: random.Random, advantage: bool, disadvantage: bool) -> int:
    first = rng.randint(1, 20)
    if advantage or disadvantage:
        second = rng.randint(1, 20)
        return max(first, second) if advantage else min(first, second)
    return first


def roll_skill_check(
    pc: PlayerCharacter,
    skill_name: str,
    dc: int,
    rng: random.Random,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
    ability_only: bool = False,
    ability: str | None = None,
) -> SkillCheckResult:
    ability_name = ability or SKILL_TO_ABILITY.get(skill_name, skill_name)
    modifier = ability_modifier(pc, ability_name) if ability_only else skill_modifier(pc, skill_name)
    roll = _roll_d20(rng, advantage, disadvantage)
    total = roll + modifier
    return SkillCheckResult(
        roll=roll,
        total=total,
        dc=dc,
        success=total >= dc,
        critical=roll == 20,
        fumble=roll == 1,
    )
