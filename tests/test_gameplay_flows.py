import random

import pytest

from prophecycm.quests import Condition, Quest, QuestEffect, QuestStep
from prophecycm.state import GameState, build_sample_state
from prophecycm.world import Location, TravelConnection


def test_travel_and_encounter_resolution():
    state = build_sample_state()

    rng = random.Random(1)
    encounter = state.travel_to("outpost", rng=rng)

    assert state.current_location_id == "outpost"
    assert encounter == "wolf pack"
    assert state.timestamp.startswith("2023-01-01T10:00:00")


def test_branching_quest_progression():
    quest_steps = [
        QuestStep(
            id="investigate",
            description="Investigate rumors of a cult.",
            success_next="report",
            success_effects=QuestEffect(flags={"cult_found": True}, reputation_changes={"town": 5}, rewards={"xp": 75}),
            failure_next="reassure",
            failure_effects=QuestEffect(relationship_changes={"mayor": -2}),
        ),
        QuestStep(
            id="reassure",
            description="Reassure the townsfolk despite lack of evidence.",
        ),
        QuestStep(
            id="report",
            description="Report findings to the mayor.",
            entry_conditions=[Condition(subject="flag", key="cult_found", comparator="==", value=True)],
            success_effects=QuestEffect(flags={"cult_quest_complete": True}, reputation_changes={"town": 2}),
        ),
    ]

    quest = Quest(id="cult-quest", title="Signs of Trouble", summary="Track down cult rumors", steps=quest_steps)

    state = GameState(
        timestamp="2023-01-01T08:00:00",
        pc=build_sample_state().pc,
        npcs=[],
        locations=[
            Location(
                id="square",
                name="Town Square",
                biome="urban",
                faction_control="town",
                connections=[TravelConnection(target="square")],
            )
        ],
        quests=[quest],
        current_location_id="square",
    )

    state.progress_quest("cult-quest", success=True)
    assert state.global_flags["cult_found"] is True
    assert state.reputation["town"] == 5
    assert state.pc.xp >= 75
    assert quest.stage == 2

    state.progress_quest("cult-quest", success=True)
    assert state.global_flags["cult_quest_complete"] is True
    assert quest.status == "completed"


def test_travel_requirement_blocks_without_flags():
    guarded = Location(
        id="gate",
        name="City Gate",
        biome="urban",
        faction_control="city",
        connections=[
            TravelConnection(
                target="keep",
                travel_time=1,
                requirements=[{"subject": "flag", "key": "gate_pass", "value": True}],
            )
        ],
    )
    keep = Location(
        id="keep",
        name="Inner Keep",
        biome="urban",
        faction_control="city",
        connections=[TravelConnection(target="gate", travel_time=1)],
    )

    state = GameState(
        timestamp="2023-01-01T12:00:00",
        pc=build_sample_state().pc,
        locations=[guarded, keep],
        current_location_id="gate",
    )

    with pytest.raises(ValueError):
        state.travel_to("keep")

    state.global_flags["gate_pass"] = True
    encounter = state.travel_to("keep", rng=random.Random(5))
    assert state.current_location_id == "keep"
    assert encounter is None
