from prophecycm.content import seed_save_file


def test_travel_graph_allows_known_paths():
    save = seed_save_file()
    state = save.game_state

    assert state.current_location_id == "silverthorn"
    assert state.travel_to("whisperwood") is True
    assert state.current_location_id == "whisperwood"

    # Cannot jump to Solasmor directly from Whisperwood
    assert state.travel_to("solasmor-monastery") is False

    # Move east to Hushbriar Cove then to Solasmor
    assert state.travel_to("hushbriar-cove") is True
    assert state.travel_to("solasmor-monastery") is True


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
