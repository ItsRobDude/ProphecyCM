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
