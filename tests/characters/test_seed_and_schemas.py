import json

from prophecycm.content import seed_classes_catalog, seed_races_catalog
from prophecycm.schema_generation import generate_schema_files


def test_seed_catalogs_capture_progressions() -> None:
    races = seed_races_catalog()
    classes = seed_classes_catalog()

    assert any(r.subrace_id for r in races)
    assert any(r.proficiency_packs for r in races)
    assert any(r.feature_progression for r in races)

    assert any(c.archetype_id for c in classes)
    assert any(c.spell_progression for c in classes)
    assert any(c.choice_slots for c in classes)


def test_race_and_class_schema_expose_new_fields(tmp_path) -> None:
    generated = generate_schema_files(tmp_path)
    race_schema = json.loads(generated["Race"].read_text())
    class_schema = json.loads(generated["Class"].read_text())

    race_properties = race_schema["properties"]
    class_properties = class_schema["properties"]

    assert "subrace_id" in race_properties
    assert "feature_progression" in race_properties
    assert "proficiency_packs" in race_properties

    assert "archetype_id" in class_properties
    assert "spell_progression" in class_properties
    assert "choice_slots" in class_properties
