from pathlib import Path

from prophecycm.content import ContentCatalog, load_game_state_from_content, load_start_menu_config, validate_content_against_schemas
from prophecycm.schema_generation import generate_schema_files

CONTENT_ROOT = Path("docs/data-model/fixtures")
SCHEMA_ROOT = Path("docs/data-model/schemas")


def test_schema_snapshots_are_up_to_date(tmp_path):
    generated = generate_schema_files(tmp_path)
    for name, path in generated.items():
        committed = SCHEMA_ROOT / path.name
        assert committed.exists(), f"Missing committed schema for {name}"
        assert committed.read_text(encoding="utf-8") == path.read_text(encoding="utf-8")


def test_fixture_validation_against_schemas(tmp_path):
    problems = validate_content_against_schemas(CONTENT_ROOT, tmp_path)
    assert problems == {}


def test_game_state_loader_hydrates_start_menu_option():
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)
    assert start_menu.new_game_start is not None, "Start menu should expose a default start"
    assert start_menu.character_creation is not None
    creation = start_menu.character_creation
    assert {race.id for race in creation.races} >= {"race.human", "race.dusk-elf"}
    assert creation.gear_bundles and creation.gear_bundles[0].item_ids
    assert catalog.gazetteer_text
    assert catalog.gazetteer_path and catalog.gazetteer_path.endswith("world_gazetteer.txt")

    state = start_menu.new_game_start.save_file.game_state

    assert state.pc.name == "Aria"
    assert {loc.id for loc in state.locations} >= {"loc.silverthorn", "loc.whisperwood"}
    assert any(item.id == "item.eq-iron-sabre" for item in state.pc.inventory)
    assert "npc-scout-aodhan" not in state.party.active_companions
    assert "npc-scout-aodhan" not in state.party.reserve_companions
    assert start_menu.new_game_start.metadata.get("background_art") == "landscapes/alderics_chamber.webp"
    assert start_menu.new_game_start.metadata.get("gazetteer_text", "").startswith("Crimson Moon RPG")

    loaded_default = load_game_state_from_content(CONTENT_ROOT)
    assert loaded_default.current_location_id == start_menu.new_game_start.current_location_id
    assert loaded_default.pc.name == start_menu.new_game_start.pc.get("name")


def test_lore_npcs_are_marked_non_companions():
    catalog = ContentCatalog.load(CONTENT_ROOT)

    aodhan = catalog.npcs.get("npc.scout-aodhan")
    assert aodhan is not None
    assert aodhan.is_companion is False


def test_start_menu_exposes_content_warning_and_new_game_flow():
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)

    flow = start_menu.build_new_game_flow()

    assert flow.label == "Embark"
    assert flow.description
    assert flow.content_warning is not None
    assert "occult horror" in flow.content_warning.message
    assert flow.content_warning.accept_label == "I understand"
    assert flow.require_character_creation() is start_menu.character_creation


def test_stat_cards_are_added_to_catalog():
    catalog = ContentCatalog.load(CONTENT_ROOT)

    assert "item.aislings-corrupt-vigil" in catalog.items
    assert "npc.aine-caillte" in catalog.npcs
    assert "creature.bruno" in catalog.creatures
