import random

from prophecycm.characters.player import AbilityScore, PlayerCharacter, Class, Race, Skill
from prophecycm.state.game_state import GameState
from prophecycm.world.location import Location


def build_pc() -> PlayerCharacter:
    abilities = {
        "strength": AbilityScore(name="strength", score=10),
        "dexterity": AbilityScore(name="dexterity", score=10),
        "constitution": AbilityScore(name="constitution", score=10),
        "wisdom": AbilityScore(name="wisdom", score=10),
        "intelligence": AbilityScore(name="intelligence", score=10),
        "charisma": AbilityScore(name="charisma", score=10),
    }
    skills = {"perception": Skill(name="perception", key_ability="wisdom", proficiency="trained")}
    return PlayerCharacter(
        id="pc-aria",
        name="Aria",
        background="ranger",
        abilities=abilities,
        skills=skills,
        race=Race(id="human", name="Human"),
        character_class=Class(id="ranger", name="Ranger"),
    )


def test_travel_requires_connection_or_fast_travel():
    l1 = Location(id="a", name="A", biome="", faction_control="", connections=["b"])
    l2 = Location(id="b", name="B", biome="", faction_control="", connections=["a", "c"])
    l3 = Location(id="c", name="C", biome="", faction_control="", connections=["b"])
    state = GameState(timestamp="t", pc=build_pc(), locations=[l1, l2, l3], current_location_id="a")

    assert not state.travel_to("c")
    assert state.travel_to("b")
    assert state.travel_to("c")
    assert "c" in state.visited_locations


def test_roll_encounter_weighting():
    l1 = Location(
        id="a",
        name="A",
        biome="",
        faction_control="",
        connections=[],
        encounter_tables={"any": [{"encounter_id": "rare", "weight": 1}, {"encounter_id": "common", "weight": 9}]},
    )
    rng = random.Random(0)
    state = GameState(timestamp="t", pc=build_pc(), locations=[l1], current_location_id="a")
    hits = [state.roll_encounter(rng=rng) for _ in range(10)]
    assert "common" in hits
