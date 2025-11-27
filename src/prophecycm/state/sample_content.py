from __future__ import annotations

import random
from typing import List

from prophecycm.characters import AbilityScore, Class, PlayerCharacter, Race, Skill
from prophecycm.quests import Condition, Quest, QuestEffect, QuestStep
from prophecycm.state.game_state import GameState
from prophecycm.state.party import PartyRoster
from prophecycm.world import Location, TravelConnection
from prophecycm.rules import SKILL_TO_ABILITY


def build_sample_state() -> GameState:
    """Construct a small world useful for demonstrations and tests."""

    pc = PlayerCharacter(
        id="pc-scout",
        name="Wren",
        background="Ranger",
        abilities={"wisdom": AbilityScore(name="wisdom", score=12)},
        skills={
            "survival": Skill(
                name="survival", key_ability=SKILL_TO_ABILITY["survival"], proficiency="trained"
            )
        },
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-ranger", name="Ranger", hit_die=10, save_proficiencies=["reflex", "fortitude"]),
    )

    frontier = Location(
        id="frontier-road",
        name="Frontier Road",
        biome="plains",
        faction_control="wardens",
        encounter_tables={"travel": ["wolf pack", "bandit scouts"]},
        connections=[TravelConnection(target="outpost", travel_time=2, danger=1.0)],
        danger_level="medium",
    )
    outpost = Location(
        id="outpost",
        name="Warden Outpost",
        biome="forest",
        faction_control="wardens",
        encounter_tables={"travel": ["hungry bear"]},
        connections=[TravelConnection(target="frontier-road", travel_time=2, danger=0.5)],
        danger_level="low",
    )

    quest_steps: List[QuestStep] = [
        QuestStep(
            id="scout",
            description="Scout the frontier road for threats.",
            success_next="report",
            success_effects=QuestEffect(
                flags={"frontier_scouted": True}, reputation_changes={"wardens": 3}, rewards={"xp": 50}
            ),
        ),
        QuestStep(
            id="report",
            description="Report back to the outpost captain.",
            entry_conditions=[Condition(subject="flag", key="frontier_scouted", value=True)],
            success_effects=QuestEffect(flags={"captain_impressed": True}, reputation_changes={"wardens": 2}),
        ),
    ]

    quest = Quest(
        id="quest-frontier",
        title="Frontier Safety",
        summary="Scout the frontier and report back.",
        steps=quest_steps,
    )

    state = GameState(
        timestamp="2023-01-01T08:00:00",
        pc=pc,
        npcs=[],
        locations=[frontier, outpost],
        quests=[quest],
        party=PartyRoster(leader_id=pc.id, active_companions=[pc.id], shared_resources={"supplies": 2}),
        global_flags={},
        reputation={},
        relationships={},
        current_location_id="frontier-road",
    )

    # Warm up RNG to ensure deterministic ordering for repeatable demos.
    random.seed(42)
    return state

