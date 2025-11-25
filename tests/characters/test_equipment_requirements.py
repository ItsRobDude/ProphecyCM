import pytest

from prophecycm.characters import AbilityScore, Class, PlayerCharacter, Race, Skill
from prophecycm.items import Equipment, EquipmentSlot


def _base_pc(**overrides) -> PlayerCharacter:
    return PlayerCharacter(
        id="pc-req-check",
        name="Requirement Checker",
        background="tester",
        abilities={"strength": AbilityScore(name="strength", score=overrides.get("strength", 10))},
        skills={"athletics": Skill(name="athletics", key_ability="strength")},
        race=Race(id="race-human", name="Human"),
        character_class=Class(
            id=overrides.get("class_id", "class-fighter"),
            name=overrides.get("class_name", "Fighter"),
            hit_die=10,
        ),
        level=overrides.get("level", 1),
    )


def test_equip_item_rejects_unmet_requirements():
    pc = _base_pc(strength=12)

    greataxe = Equipment(
        id="eq-greataxe",
        name="Greataxe",
        slot=EquipmentSlot.TWO_HAND,
        requirements={"abilities": {"strength": 16}},
        two_handed=True,
    )

    with pytest.raises(ValueError, match="strength 16"):
        pc.equip_item(greataxe)


def test_equip_item_succeeds_when_requirements_met():
    pc = _base_pc(strength=18, level=3)

    warhammer = Equipment(
        id="eq-warhammer",
        name="Warhammer",
        slot=EquipmentSlot.MAIN_HAND,
        requirements={"abilities": {"strength": 16}, "level": 2, "classes": ["class-fighter"]},
    )

    pc.equip_item(warhammer)

    assert EquipmentSlot.MAIN_HAND in pc.equipment
    assert pc.equipment[EquipmentSlot.MAIN_HAND].id == "eq-warhammer"
