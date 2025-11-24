from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict

from prophecycm.characters.player import PlayerCharacter


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
    if skill is None:
        return 0
    ability_mod = pc.abilities.get(skill.key_ability).modifier if skill.key_ability in pc.abilities else 0
    prof_tier = PROFICIENCY_MULTIPLIER.get(skill.proficiency, 0)
    return ability_mod + prof_tier * pc.proficiency_bonus


def roll_skill_check(pc: PlayerCharacter, skill_name: str, dc: int, rng: random.Random) -> SkillCheckResult:
    modifier = skill_modifier(pc, skill_name)
    roll = rng.randint(1, 20)
    total = roll + modifier
    return SkillCheckResult(
        roll=roll,
        total=total,
        dc=dc,
        success=total >= dc,
        critical=roll == 20,
        fumble=roll == 1,
    )
