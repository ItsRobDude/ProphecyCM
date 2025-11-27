from pathlib import Path

from prophecycm.characters.creation import AbilityGenerationMethod, CharacterCreationSelection
from prophecycm.content import ContentCatalog, load_start_menu_config, loaders


CONTENT_ROOT = Path("docs/data-model/fixtures")


def _standard_scores(config):
    return {name: score for name, score in zip(config.ability_names, config.standard_array)}


def _start_new_game(slot: int = 3):
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(loaders._resolve_content_file(CONTENT_ROOT, "start_menu"), catalog)

    flow = start_menu.build_new_game_flow()
    config = flow.require_character_creation()

    selection = CharacterCreationSelection(
        name="Selene of Silverthorn",
        background_id=config.backgrounds[0].id,
        race_id=config.races[0].id,
        class_id=config.classes[0].id,
        ability_method=AbilityGenerationMethod.STANDARD_ARRAY,
        ability_scores=_standard_scores(config),
        trained_skills=["stealth", "survival"],
        feat_ids=[config.feats[0].id],
        gear_bundle_id=config.gear_bundles[0].id,
    )

    save_file = start_menu.start_new_game(catalog=catalog, selection=selection, slot=slot)
    return save_file, start_menu, selection


def test_new_game_flow_builds_save_file_from_selection():
    save_file, start_menu, selection = _start_new_game(slot=3)
    game_state = save_file.game_state

    assert save_file.slot == 3
    assert game_state.pc.name == selection.name
    assert game_state.pc.race.id == selection.race_id
    assert game_state.pc.character_class.id == selection.class_id
    assert game_state.current_location_id == start_menu.new_game_start.current_location_id
    assert game_state.global_flags.get("entered_whisperwood") is False
    assert any(quest.id == "quest.main-quest-aodhan" for quest in game_state.quests)
    assert game_state.party.leader_id == game_state.pc.id
    assert game_state.pc.id in game_state.party.active_companions
    assert any(item.id == "item.eq-iron-sabre" for item in game_state.pc.inventory)


def test_travel_step_leaves_whisperwood_flag_unset_until_travel():
    save_file, _, _ = _start_new_game(slot=4)
    game_state = save_file.game_state
    quest = next(q for q in game_state.quests if q.id == "quest.main-quest-aodhan")

    # Progress through briefing, chamber inspection, rumor chasing, then pause at the travel prompt
    for _ in range(3):
        game_state.apply_quest_step(quest.id, success=True)

    assert game_state.global_flags.get("entered_whisperwood") is False
    assert game_state.current_location_id == "loc.alderics-chambers"
