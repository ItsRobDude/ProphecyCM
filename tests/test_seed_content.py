import random

import pytest

from prophecycm.content import seed_save_file


def test_travel_graph_allows_known_paths():
    save = seed_save_file()
    state = save.game_state

    assert state.current_location_id == "silverthorn"
    state.travel_to("whisperwood", rng=random.Random(0))
    assert state.current_location_id == "whisperwood"

    # Cannot jump to Solasmor directly from Whisperwood
    with pytest.raises(ValueError):
        state.travel_to("solasmor-monastery")

    # Move east to Hushbriar Cove then to Solasmor
    state.travel_to("hushbriar-cove", rng=random.Random(1))
    state.travel_to("solasmor-monastery", rng=random.Random(2))


def test_quest_step_conditions_and_effects():
    save = seed_save_file()
    state = save.game_state
    quest = state.quests[0]

    # Initial step should set visited flag when marked successful
    state.apply_quest_step(quest.id, success=True)
    assert state.global_flags.get("entered_whisperwood") is True
    assert quest.current_step == "gather-clues"

    # Next step requires flag
    quest.apply_step_result(state.global_flags, success=True)
    assert quest.current_step == "trace-artifact"
    assert state.global_flags.get("artifact_clues") == 1


def test_aodhan_is_not_recruitable_at_start():
    save = seed_save_file()
    state = save.game_state

    assert state.pc.id in state.party.active_companions
    assert state.pc.id not in state.party.reserve_companions

    aodhan = next((npc for npc in state.npcs if npc.id == "npc-scout-aodhan"), None)
    assert aodhan is not None
    assert aodhan.is_companion is False
    assert "npc-scout-aodhan" not in state.party.reserve_companions
    assert "npc-scout-aodhan" not in state.party.active_companions
