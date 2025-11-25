from pathlib import Path

from prophecycm.characters.creation import AbilityGenerationMethod, CharacterCreationSelection
from prophecycm.content import ContentCatalog, load_start_menu_config


CONTENT_ROOT = Path("docs/data-model/fixtures")


def _standard_scores(config):
    return {name: score for name, score in zip(config.ability_names, config.standard_array)}


def test_new_game_flow_builds_save_file_from_selection():
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)

    flow = start_menu.build_new_game_flow()
    config = flow.require_character_creation()

    selection = CharacterCreationSelection(
        name="Selene of Silverthorn",
        background=config.backgrounds[0],
        race_id=config.races[0].id,
        class_id=config.classes[0].id,
        ability_method=AbilityGenerationMethod.STANDARD_ARRAY,
        ability_scores=_standard_scores(config),
        trained_skills=list(config.skill_catalog.keys())[: config.skill_choices],
        feat_ids=[config.feats[0].id],
        gear_bundle_id=config.gear_bundles[0].id,
    )

    save_file = start_menu.start_new_game(catalog=catalog, selection=selection, slot=3)
    game_state = save_file.game_state

    assert save_file.slot == 3
    assert game_state.pc.name == selection.name
    assert game_state.pc.race.id == selection.race_id
    assert game_state.pc.character_class.id == selection.class_id
    assert game_state.current_location_id == start_menu.options[0].current_location_id
    assert game_state.global_flags.get("entered_whisperwood") is False
    assert any(quest.id == "main-quest-aodhan" for quest in game_state.quests)
    assert game_state.party.leader_id == game_state.pc.id
    assert game_state.pc.id in game_state.party.active_companions
    assert any(item.id == "eq-iron-sabre" for item in game_state.pc.inventory)
