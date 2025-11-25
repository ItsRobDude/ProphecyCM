from __future__ import annotations

import random
from typing import List

from prophecycm.characters.checks import roll_skill_check
from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode
from prophecycm.state.game_state import GameState


def is_condition_met(condition: DialogueCondition, state: GameState, rng: random.Random) -> bool:
    kind = condition.kind
    params = condition.params
    if kind == "flag_equals":
        flag = params.get("flag")
        expected = params.get("value")
        return state.global_flags.get(flag, False) == expected
    if kind == "skill_check":
        skill = params.get("skill")
        dc = int(params.get("dc", 10))
        if skill is None:
            return False
        result = roll_skill_check(state.pc, str(skill), dc, rng)
        return result.success
    return True


def apply_effect(effect: DialogueEffect, state: GameState) -> None:
    kind = effect.kind
    params = effect.params
    if kind == "set_flag":
        flag = params.get("flag")
        value = params.get("value")
        if flag:
            state.set_flag(str(flag), value)
    elif kind == "adjust_rep":
        faction_id = params.get("faction_id")
        delta = int(params.get("delta", 0))
        if faction_id:
            state.adjust_faction_rep(str(faction_id), delta)


def get_available_choices(node: DialogueNode, state: GameState, rng: random.Random) -> List[DialogueChoice]:
    return [
        choice
        for choice in node.choices
        if all(is_condition_met(condition, state, rng) for condition in choice.conditions)
    ]
