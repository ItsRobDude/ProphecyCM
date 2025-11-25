import pytest

from prophecycm.characters import AbilityScore, Class, Feat, FeatStackingRule, PlayerCharacter, Race


def _base_character(level: int = 1) -> PlayerCharacter:
    return PlayerCharacter(
        id="pc-hero",
        name="Hero",
        background="Adventurer",
        abilities={
            "strength": AbilityScore(name="strength", score=16),
            "dexterity": AbilityScore(name="dexterity", score=12),
            "intelligence": AbilityScore(name="intelligence", score=10),
        },
        skills={},
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-fighter", name="Fighter", hit_die=10),
        level=level,
    )


def test_feat_prerequisites_allow_valid_selection() -> None:
    pc = _base_character(level=2)
    feat = Feat(
        id="feat-power-strike",
        name="Power Strike",
        required_level=2,
        required_abilities={"strength": 15},
        modifiers={"attack": 1},
    )

    pc.add_feat(feat)

    assert feat in pc.feats


def test_feat_prerequisites_reject_low_level_or_stats() -> None:
    low_level_pc = _base_character(level=1)
    level_gate = Feat(
        id="feat-adept",
        name="Adept",
        required_level=3,
    )

    with pytest.raises(ValueError):
        low_level_pc.add_feat(level_gate)

    ability_gate = Feat(
        id="feat-keen-mind",
        name="Keen Mind",
        required_abilities={"intelligence": 12},
    )

    with pytest.raises(ValueError):
        low_level_pc.add_feat(ability_gate)


def test_class_and_archetype_restrictions_enforced() -> None:
    pc = _base_character(level=5)
    class_locked = Feat(
        id="feat-mage-only",
        name="Mage Tradition",
        required_classes=["class-mage"],
    )

    with pytest.raises(ValueError):
        pc.add_feat(class_locked)

    archetype_locked = Feat(
        id="feat-archetype",
        name="Archetype Specialist",
        required_archetypes=["shadow-blade"],
    )

    with pytest.raises(ValueError):
        pc.add_feat(archetype_locked)


def test_feat_stacking_rules_prevent_duplicates() -> None:
    pc = _base_character(level=4)
    unique_feat = Feat(id="feat-unique", name="Unique Feat")
    pc.add_feat(unique_feat)

    with pytest.raises(ValueError):
        pc.add_feat(unique_feat)


def test_feat_stacking_rules_allow_stackable_feats() -> None:
    pc = _base_character(level=4)
    stackable = Feat(
        id="feat-stackable",
        name="Favored Enemy",
        stacking_rule=FeatStackingRule.STACKABLE,
    )

    pc.add_feat(stackable)
    pc.add_feat(stackable)

    assert len([feat for feat in pc.feats if feat.id == "feat-stackable"]) == 2

