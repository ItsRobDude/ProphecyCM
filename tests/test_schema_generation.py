from pathlib import Path

from prophecycm.schema_generation import generate_schemas


def test_game_state_schema_includes_nested_refs(tmp_path: Path) -> None:
    output_dir = tmp_path / "schemas"
    schemas = generate_schemas(output_dir)

    game_state_schema = schemas["GameState"]
    properties = game_state_schema.get("properties", {})

    assert properties, "GameState schema should have properties"
    assert properties["pc"].get("$ref"), "pc should reference PlayerCharacter"

    player_def = game_state_schema["definitions"].get("PlayerCharacter", {})
    assert player_def.get("properties", {}), "PlayerCharacter definition should not be empty"


def test_typed_id_patterns(tmp_path: Path) -> None:
    output_dir = tmp_path / "schemas"
    schemas = generate_schemas(output_dir)

    creature_schema = schemas["Creature"]
    assert creature_schema["properties"]["id"].get("pattern", "").startswith("^(?:"), "Creature id should enforce typed prefix"

    start_menu_schema = schemas["StartMenuConfig"]
    option_def = start_menu_schema["definitions"].get("StartMenuOption", {})
    current_loc = option_def.get("properties", {}).get("current_location_id", {})
    pattern_in_anyof = any("pattern" in entry for entry in current_loc.get("anyOf", []))
    assert "pattern" in current_loc or pattern_in_anyof, "Start menu options should validate typed location ids"
