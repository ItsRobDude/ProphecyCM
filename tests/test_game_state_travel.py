import random

import random

import pytest

from prophecycm.characters.player import AbilityScore, PlayerCharacter, Class, Race, Skill
from prophecycm.state.game_state import GameState
from prophecycm.world.location import Location, TravelConnection


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
    l1 = Location(id="a", name="A", biome="", faction_control="", connections=[TravelConnection(target="b")])
    l2 = Location(
        id="b", name="B", biome="", faction_control="", connections=[TravelConnection(target="a"), TravelConnection(target="c")]
    )
    l3 = Location(id="c", name="C", biome="", faction_control="", connections=[TravelConnection(target="b")])
    state = GameState(timestamp="t", pc=build_pc(), locations=[l1, l2, l3], current_location_id="a")

    with pytest.raises(ValueError):
        state.travel_to("c")

    encounter = state.travel_to("b")
    assert encounter is None

    encounter = state.travel_to("c")
    assert encounter is None
    assert "c" in state.visited_locations


def test_roll_encounter_weighting():
    l1 = Location(
        id="a",
        name="A",
        biome="",
        faction_control="",
        connections=[],
        encounter_tables={"any": ["rare", "common", "common", "common", "common", "common", "common", "common", "common", "common"]},
        danger_level="high",
    )
    rng = random.Random(0)
    state = GameState(timestamp="t", pc=build_pc(), locations=[l1], current_location_id="a")
    hits = [state.roll_encounter("any", rng=rng, difficulty_modifier=2.0) for _ in range(10)]
    encounter_ids = [hit[0] for hit in hits if hit]
    assert "common" in encounter_ids


def test_travel_encounter_rewards_and_persistence():
    pc = build_pc()
    wolf = Creature(
        id="wolf",
        name="Wolf",
        level=1,
        role="skirmisher",
        hit_die=8,
        armor_class=12,
        abilities={"strength": AbilityScore(name="strength", score=12)},
        actions=[CreatureAction(name="bite", attack_ability="strength", damage_dice="1d4")],
        hit_points=8,
    )
    origin = Location(
        id="trail",
        name="Forest Trail",
        biome="forest",
        faction_control="wilds",
        connections=[TravelConnection(target="camp", danger=2.0, travel_time=2, resource_costs={"supplies": 1})],
        encounter_tables={"travel": [{"encounter_id": "wolf-pack", "weight": 1}]},
        danger_level="high",
    )
    destination = Location(
        id="camp",
        name="Hunter Camp",
        biome="forest",
        faction_control="neutral",
        connections=[TravelConnection(target="trail", travel_time=2)],
        travel_rules={"allow_fast_travel": True, "fast_travel_time": 0},
    )

    state = GameState(
        timestamp="2023-01-01T00:00:00",
        pc=pc,
        creatures=[wolf],
        locations=[origin, destination],
        current_location_id="trail",
        encounters={"wolf-pack": {"creatures": ["wolf"], "xp": 120, "loot": {"wolf_pelt": 1}}},
        resources={"supplies": 2},
    )
    rng = random.Random(5)

    encounter_hook = state.travel_to("camp", rng=rng)
    assert encounter_hook is not None
    encounter_state = state.start_encounter(encounter_hook, rng=rng)
    encounter_creature = encounter_state.meta["creatures"][0]
    encounter_creature.apply_damage(999)
    state.complete_encounter(encounter_state)

    assert state.resources["supplies"] == 1
    assert state.pc.xp >= 120
    assert state.global_flags["rewards"]["wolf_pelt"] == 1
    stored_wolf = next(creature for creature in state.creatures if creature.id == "wolf")
    assert stored_wolf.is_alive is False
