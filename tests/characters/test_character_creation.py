from pathlib import Path

import pytest

from prophecycm.characters.creation import (
    AbilityGenerationMethod,
    CharacterCreationSelection,
    CharacterCreator,
)
from prophecycm.content import ContentCatalog, load_start_menu_config
from prophecycm.items import EquipmentSlot

CONTENT_ROOT = Path("docs/data-model/fixtures")


def _load_creation_config():
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)
    assert start_menu.character_creation is not None
    return catalog, start_menu.character_creation


def _standard_scores(config):
    return {name: score for name, score in zip(config.ability_names, config.standard_array)}


def _point_buy_scores(config, inflate: bool = False):
    scores = {
        "strength": 15,
        "dexterity": 14,
        "constitution": 13,
        "intelligence": 12,
        "wisdom": 10,
        "charisma": 8,
    }
    if inflate:
        scores["dexterity"] = 15
        scores["constitution"] = 14
    return {name: scores[name] for name in config.ability_names}


def test_character_creator_builds_standard_array_character():
    catalog, config = _load_creation_config()
    creator = CharacterCreator(config, catalog.items)

    selection = CharacterCreationSelection(
        name="Kara of Silverthorn",
        background=config.backgrounds[0],
        race_id=config.races[0].id,
        class_id=config.classes[0].id,
        ability_method=AbilityGenerationMethod.STANDARD_ARRAY,
        ability_scores=_standard_scores(config),
        trained_skills=list(config.skill_catalog.keys())[: config.skill_choices],
        feat_ids=[config.feats[0].id],
        gear_bundle_id=config.gear_bundles[0].id,
    )

    pc = creator.build_character(selection)

    assert pc.race.id == selection.race_id
    assert pc.character_class.id == selection.class_id
    assert pc.hit_points == 11
    assert pc.abilities["dexterity"].modifier == 2
    assert pc.available_proficiency_packs["urban-diplomat"] == ["persuasion", "history"]
    assert EquipmentSlot.MAIN_HAND in pc.equipment
    assert any(item.id == "item.eq-iron-sabre" for item in pc.inventory)
    assert pc.choice_slots.get("languages") == 1


def test_point_buy_and_selection_limits_are_enforced():
    catalog, config = _load_creation_config()
    creator = CharacterCreator(config, catalog.items)

    too_expensive = CharacterCreationSelection(
        name="Overbuilt", 
        background=config.backgrounds[1],
        race_id=config.races[1].id,
        class_id=config.classes[1].id,
        ability_method=AbilityGenerationMethod.POINT_BUY,
        ability_scores=_point_buy_scores(config, inflate=True),
        trained_skills=list(config.skill_catalog.keys())[: config.skill_choices],
        feat_ids=[config.feats[0].id],
    )

    with pytest.raises(ValueError):
        creator.build_character(too_expensive)

    too_many_feats = CharacterCreationSelection(
        name="Greedy", 
        background=config.backgrounds[2],
        race_id=config.races[0].id,
        class_id=config.classes[0].id,
        ability_method=AbilityGenerationMethod.POINT_BUY,
        ability_scores=_point_buy_scores(config),
        trained_skills=list(config.skill_catalog.keys())[: config.skill_choices],
        feat_ids=[feat.id for feat in config.feats],
    )

    with pytest.raises(ValueError):
        creator.build_character(too_many_feats)

    too_many_skills = CharacterCreationSelection(
        name="Skillstacker", 
        background=config.backgrounds[0],
        race_id=config.races[0].id,
        class_id=config.classes[0].id,
        ability_method=AbilityGenerationMethod.STANDARD_ARRAY,
        ability_scores=_standard_scores(config),
        trained_skills=list(config.skill_catalog.keys()),
        feat_ids=[config.feats[0].id],
    )

    with pytest.raises(ValueError):
        creator.build_character(too_many_skills)
