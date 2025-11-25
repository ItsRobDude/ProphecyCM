from prophecycm.characters import AbilityScore, Class, PlayerCharacter, Race, Skill
from prophecycm.combat.status_effects import StatusEffect
from prophecycm.items import Equipment, EquipmentSlot


def _build_pc() -> PlayerCharacter:
    return PlayerCharacter(
        id="pc-test",
        name="Rowan",
        background="wanderer",
        abilities={"dexterity": AbilityScore(name="dexterity", score=14)},
        skills={"perception": Skill(name="perception", key_ability="wisdom")},
        race=Race(id="race-human", name="Human"),
        character_class=Class(
            id="class-ranger",
            name="Ranger",
            hit_die=10,
            save_proficiencies=["reflex"],
        ),
    )


def test_equipment_and_effects_apply_and_revert_modifiers():
    pc = _build_pc()

    base_ac = pc.armor_class
    base_initiative = pc.initiative

    agility_band = Equipment(
        id="eq-agility-band",
        name="Agility Band",
        slot=EquipmentSlot.ACCESSORY,
        modifiers={"dexterity": 2},
    )
    shield = Equipment(
        id="eq-training-buckler",
        name="Training Buckler",
        slot=EquipmentSlot.OFF_HAND,
        modifiers={"armor_class": 2},
    )

    pc.equip_item(agility_band)
    pc.equip_item(shield)

    assert pc.armor_class == base_ac + 3
    assert pc.initiative == base_initiative + 1

    ward = StatusEffect(id="status-ward", name="Protective Ward", duration=2, modifiers={"armor_class": 1})
    pc.add_status_effect(ward)

    assert pc.armor_class == base_ac + 4

    removed_shield = pc.unequip(EquipmentSlot.OFF_HAND)
    assert removed_shield == shield
    assert pc.armor_class == base_ac + 2

    pc.dispel_status_effects()
    assert pc.armor_class == base_ac + 1

    pc.unequip(EquipmentSlot.ACCESSORY)
    assert pc.armor_class == base_ac
    assert pc.initiative == base_initiative
