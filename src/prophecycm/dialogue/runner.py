from __future__ import annotations

import random
from typing import List

from prophecycm.characters.checks import roll_skill_check
from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode
from prophecycm.state.game_state import GameState


def _compare(lhs: object, comparator: str, rhs: object) -> bool:
    if comparator == "==":
        return lhs == rhs
    if comparator == "!=":
        return lhs != rhs
    if comparator == ">=":
        return lhs >= rhs
    if comparator == "<=":
        return lhs <= rhs
    if comparator == ">":
        return lhs > rhs
    if comparator == "<":
        return lhs < rhs
    return False


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
        result = roll_skill_check(
            state.pc,
            str(skill),
            dc,
            rng,
            advantage=bool(params.get("advantage", False)),
            disadvantage=bool(params.get("disadvantage", False)),
            ability_only=bool(params.get("ability_only", False)),
            ability=str(params.get("ability")) if params.get("ability") else None,
        )
        return result.success
    if kind == "ability_check":
        ability = params.get("ability")
        dc = int(params.get("dc", 10))
        if ability is None:
            return False
        result = roll_skill_check(
            state.pc,
            str(ability),
            dc,
            rng,
            ability_only=True,
            advantage=bool(params.get("advantage", False)),
            disadvantage=bool(params.get("disadvantage", False)),
        )
        return result.success
    if kind == "quest_stage":
        quest_id = params.get("quest_id")
        comparator = params.get("comparator", "==")
        expected = int(params.get("value", 0))
        quest = state.get_quest(str(quest_id)) if quest_id else None
        stage = quest.stage if quest else -1
        return _compare(stage, comparator, expected)
    if kind == "relationship":
        npc_id = params.get("npc_id")
        comparator = params.get("comparator", ">=")
        threshold = int(params.get("value", 0))
        value = state.relationships.get(str(npc_id), 0)
        return _compare(value, comparator, threshold)
    if kind == "reputation":
        faction_id = params.get("faction_id")
        comparator = params.get("comparator", ">=")
        threshold = int(params.get("value", 0))
        value = state.reputation.get(str(faction_id), 0)
        return _compare(value, comparator, threshold)
    return True


def apply_effect(effect: DialogueEffect, state: GameState, rng: random.Random | None = None) -> None:
    if rng is None:
        rng = random.Random()
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
    elif kind == "adjust_relationship":
        npc_id = params.get("npc_id")
        delta = int(params.get("delta", 0))
        if npc_id:
            state.adjust_relationship(str(npc_id), delta)
    elif kind == "grant_reward":
        xp = int(params.get("xp", 0))
        if xp:
            state.grant_party_xp(xp)
        for item_payload in params.get("items", []):
            if isinstance(item_payload, dict):
                state.grant_item(item_payload)
    elif kind == "start_quest":
        quest_payload = params.get("quest")
        quest_id = params.get("quest_id")
        if quest_payload:
            state.start_quest(quest_payload)
        elif quest_id:
            existing = state.get_quest(str(quest_id))
            if existing:
                state.start_quest(existing)
    elif kind == "advance_quest":
        quest_id = params.get("quest_id")
        success = bool(params.get("success", True))
        if quest_id:
            state.progress_quest(str(quest_id), success=success)
    elif kind == "trigger_encounter":
        context = params.get("context", "dialogue")
        encounter = params.get("encounter_id")
        if encounter is None:
            encounter = state.roll_encounter(context, rng=rng)
        state.global_flags["last_encounter"] = encounter
    elif kind == "record_transcript":
        entry = {
            "speaker_id": params.get("speaker_id"),
            "line": params.get("line"),
            "choice_id": params.get("choice_id"),
        }
        state.record_transcript(entry)


def get_available_choices(node: DialogueNode, state: GameState, rng: random.Random) -> List[DialogueChoice]:
    return [
        choice
        for choice in node.choices
        if all(is_condition_met(condition, state, rng) for condition in choice.conditions)
    ]
