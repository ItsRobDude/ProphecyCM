import random

from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode
from prophecycm.dialogue.runner import apply_effect, get_available_choices
from prophecycm.state.game_state import GameState
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
