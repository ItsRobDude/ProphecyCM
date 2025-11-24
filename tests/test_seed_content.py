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


def test_seed_creatures_can_scale_to_player():
    save = seed_save_file()
    state = save.game_state

    assert state.npcs, "Seed should include NPC-driven encounters"
    wolf_npc = next(npc for npc in state.npcs if npc.id == "npc-spore-wolf-alpha")

    scaled = wolf_npc.scaled_stat_block(player_level=8, difficulty="hard")

    assert scaled is not None
    assert scaled.level >= wolf_npc.stat_block.level
    assert scaled.hit_points >= wolf_npc.stat_block.hit_points


def test_combatants_use_npc_scaling_and_honor_death():
    save = seed_save_file()
    state = save.game_state

    combatants = state.available_combatants(player_level=8, difficulty="hard")
    npc_block = next(c for c in combatants if c.id == "creature-spore-wolf")
    template = next(c for c in state.creatures if c.id == "creature-spore-wolf")
    wolf_count = sum(1 for c in combatants if c.id == "creature-spore-wolf")

    assert npc_block.level >= template.level
    assert template.level == 2  # base template remains unchanged

    # Kill the template and ensure it disappears from combatants
    template.apply_damage(template.hit_points + 5)
    combatants_after = state.available_combatants(player_level=8)
    assert sum(1 for c in combatants_after if c.id == "creature-spore-wolf") == wolf_count - 1
