from pathlib import Path

from prophecycm.characters.creation import CharacterCreationSelection, CharacterCreator
from prophecycm.content import ContentCatalog, load_start_menu_config, loaders

CONTENT_ROOT = Path("docs/data-model/fixtures")
SAMPLE_ROOT = Path("content/samples")


def _load_sample_payload(path: Path):
    payload = loaders._load_payload(path)
    selection = CharacterCreationSelection.from_dict(payload["selection"])
    expectations = payload.get("expectations", {})
    return selection, expectations


def test_sample_player_characters_build_correctly():
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(loaders._resolve_content_file(CONTENT_ROOT, "start_menu"), catalog)
    creator = CharacterCreator(start_menu.character_creation, catalog.items)

    sample_files = sorted(
        path
        for ext in (*loaders.CONTENT_EXTENSIONS, ".json")
        for path in SAMPLE_ROOT.glob(f"*{ext}")
    )
    assert sample_files, "No sample player characters found in content/samples"

    for sample_file in sample_files:
        selection, expectations = _load_sample_payload(sample_file)
        result = creator.build_character(selection)
        pc = result.character

        assert pc.hit_points == expectations.get("hit_points")
        assert pc.armor_class == expectations.get("armor_class")

        trained_skills = sorted(
            skill_name for skill_name, skill in pc.skills.items() if skill.proficiency == "trained"
        )
        assert trained_skills == sorted(expectations.get("trained_skills", []))

        feat_ids = sorted(feat.id for feat in pc.feats)
        assert feat_ids == sorted(expectations.get("feats", []))

