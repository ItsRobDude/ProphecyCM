import random

import random

from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode
from prophecycm.dialogue.runner import apply_effect, get_available_choices, is_condition_met
from prophecycm.items import Item
from prophecycm.quests import Quest, QuestEffect, QuestStep
from prophecycm.state.game_state import GameState
from prophecycm.world import Location
from prophecycm.characters.player import AbilityScore, PlayerCharacter, Class, Race, Skill


def build_state() -> GameState:
    abilities = {
        "strength": AbilityScore(name="strength", score=10),
        "dexterity": AbilityScore(name="dexterity", score=10),
        "constitution": AbilityScore(name="constitution", score=10),
        "wisdom": AbilityScore(name="wisdom", score=12),
        "intelligence": AbilityScore(name="intelligence", score=10),
        "charisma": AbilityScore(name="charisma", score=10),
    }
    skills = {"perception": Skill(name="perception", key_ability="wisdom", proficiency="trained")}
    pc = PlayerCharacter(
        id="pc-aria",
        name="Aria",
        background="ranger",
        abilities=abilities,
        skills=skills,
        race=Race(id="human", name="Human"),
        character_class=Class(id="ranger", name="Ranger"),
    )
    return GameState(timestamp="t0", pc=pc)


def test_dialogue_conditions_and_effects():
    state = build_state()
    node = DialogueNode(
        id="n1",
        speaker_id="npc-1",
        text="Test",
        choices=[
            DialogueChoice(
                id="c1",
                text="Greet",
                conditions=[DialogueCondition(kind="flag_equals", params={"flag": "met", "value": False})],
                effects=[DialogueEffect(kind="set_flag", params={"flag": "met", "value": True})],
            ),
            DialogueChoice(
                id="c2",
                text="Perception",
                conditions=[DialogueCondition(kind="skill_check", params={"skill": "perception", "dc": 10})],
            ),
        ],
    )
    rng = random.Random(0)
    available = get_available_choices(node, state, rng)
    assert {choice.id for choice in available} == {"c1", "c2"}
    apply_effect(node.choices[0].effects[0], state)
    assert state.global_flags.get("met") is True


def test_dialogue_skill_variants_and_quest_effects():
    state = build_state()
    state.current_location_id = "village"
    state.locations = [
        Location(
            id="village",
            name="Village",
            biome="plains",
            faction_control="town",
            encounter_tables={"dialogue": ["boar"]},
            danger_level="high",
        )
    ]

    quest = Quest(
        id="welcome",
        title="Welcome to Town",
        summary="Earn the town's trust",
        steps=[
            QuestStep(
                id="greet",
                description="Make introductions.",
                success_effects=QuestEffect(flags={"greeted": True}, reputation_changes={"town": 3}, rewards={"xp": 25}),
            )
        ],
        status="inactive",
    )
    state.quests.append(quest)
    state.relationships["npc-elder"] = 0
    state.reputation["town"] = 0

    rng = random.Random(2)

    skill_condition = DialogueCondition(
        kind="skill_check",
        params={"skill": "perception", "dc": 1, "advantage": True, "ability_only": True, "ability": "wisdom"},
    )
    assert is_condition_met(skill_condition, state, rng)

    apply_effect(DialogueEffect(kind="start_quest", params={"quest_id": "welcome"}), state, rng)
    assert quest.status == "active"

    apply_effect(DialogueEffect(kind="advance_quest", params={"quest_id": "welcome", "success": True}), state, rng)
    assert quest.stage == 1
    assert state.global_flags.get("greeted") is True
    assert state.reputation["town"] == 3
    assert state.pc.xp >= 25

    reward_effect = DialogueEffect(
        kind="grant_reward",
        params={"xp": 10, "items": [Item(id="gift", name="Gift").to_dict()]},
    )
    apply_effect(reward_effect, state, rng)
    assert any(item.id == "gift" for item in state.pc.inventory)

    apply_effect(DialogueEffect(kind="adjust_relationship", params={"npc_id": "npc-elder", "delta": 2}), state, rng)
    assert state.relationships["npc-elder"] == 2

    apply_effect(DialogueEffect(kind="trigger_encounter", params={"context": "dialogue", "encounter_id": "boar"}), state, rng)
    assert state.global_flags.get("last_encounter") == "boar"

    apply_effect(
        DialogueEffect(
            kind="record_transcript",
            params={"speaker_id": "npc-elder", "line": "We remember your kindness.", "choice_id": "c-ally"},
        ),
        state,
        rng,
    )
    assert any(entry.get("choice_id") == "c-ally" for entry in state.transcript)
