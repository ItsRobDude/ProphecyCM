import pytest

from prophecycm.characters import AbilityScore, Class, Feat, NPC, PlayerCharacter, Race, Skill
from prophecycm.combat import StackingRule, StatusEffect
from prophecycm.items import Consumable, Equipment, EquipmentSlot, Item
from prophecycm.quests import Quest
from prophecycm.state import GameState
from prophecycm.world import Location


def test_player_character_creation():
    pc = PlayerCharacter(
        id="pc-100",
        name="Test Hero",
        background="Explorer",
        abilities={
            "strength": AbilityScore(name="strength", score=12),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=13),
        },
        skills={"climb": Skill(name="climb", key_ability="strength", proficiency="trained")},
        race=Race(id="race-human", name="Human", ability_bonuses={"strength": 1}),
        character_class=Class(id="class-fighter", name="Fighter", hit_die=10, save_proficiencies=["fortitude", "will"]),
        feats=[Feat(id="feat-1", name="Tough", description="Hardier", modifiers={"hit_points": 3})],
        inventory=[Item(id="item-1", name="Rope")],
        status_effects=[StatusEffect(id="fx-2", name="Blessed", duration=1, modifiers={"will": 1})],
    )
    assert pc.to_dict()["name"] == "Test Hero"
    assert pc.hit_points > 0
    assert pc.saves["fortitude"] >= pc.abilities["constitution"].modifier


def test_status_effect_round_trip():
    effect = StatusEffect(id="fx-1", name="Poison", duration=2, modifiers={"health": -1})
    encoded = effect.to_json()
    decoded = StatusEffect.from_json(encoded)
    assert decoded.modifiers["health"] == -1


def test_game_state_composition():
    pc = PlayerCharacter(
        id="pc-200",
        name="Builder",
        background="Engineer",
        abilities={"intellect": AbilityScore(name="intellect", score=12)},
        skills={"craft": Skill(name="craft", key_ability="intellect")},
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-artisan", name="Artisan", hit_die=8),
    )
    npc = NPC(id="npc-200", archetype="trader", faction_id="neutral", disposition="friendly")
    quest = Quest(id="q-200", title="Start", summary="Test quest")
    location = Location(id="loc-200", name="Town", biome="plains", faction_control="neutral")

    state = GameState(
        timestamp="now",
        pc=pc,
        npcs=[npc],
        locations=[location],
        quests=[quest],
    )

    assert state.to_dict()["pc"]["name"] == "Builder"


def test_status_effect_stacking_rules():
    pc = PlayerCharacter(
        id="pc-300",
        name="Stack Tester",
        background="Scholar",
        abilities={"wisdom": AbilityScore(name="wisdom", score=10)},
        skills={},
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-mage", name="Mage", hit_die=6, save_proficiencies=["will"]),
    )

    baseline_will = pc.saves["will"]
    effect = StatusEffect(
        id="fx-stack",
        name="Bolstered",
        duration=3,
        modifiers={"will": 1},
        stacking_rule=StackingRule.STACK,
        max_stacks=2,
    )
    pc.add_status_effect(effect)
    pc.add_status_effect(
        StatusEffect(
            id="fx-stack",
            name="Bolstered",
            duration=2,
            modifiers={"will": 1},
            stacking_rule=StackingRule.STACK,
            max_stacks=2,
        )
    )

    assert len(pc.status_effects) == 1
    assert pc.status_effects[0].current_stacks == 2
    assert pc.saves["will"] == baseline_will + 2


def test_equip_flow_with_two_handed_constraints():
    pc = PlayerCharacter(
        id="pc-400",
        name="Equipment Tester",
        background="Warrior",
        abilities={"dexterity": AbilityScore(name="dexterity", score=12)},
        skills={},
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-fighter", name="Fighter", hit_die=10),
    )

    sword = Equipment(id="eq-sword", name="Sword", slot=EquipmentSlot.MAIN_HAND, modifiers={"armor_class": 1})
    shield = Equipment(id="eq-shield", name="Shield", slot=EquipmentSlot.OFF_HAND, modifiers={"armor_class": 2})
    greatsword = Equipment(
        id="eq-greatsword",
        name="Greatsword",
        slot=EquipmentSlot.TWO_HAND,
        modifiers={"armor_class": 3},
        two_handed=True,
    )

    base_ac = pc.armor_class
    pc.equip_item(sword)
    assert pc.armor_class == base_ac + 1

    pc.equip_item(shield)
    assert pc.armor_class == base_ac + 3

    with pytest.raises(ValueError):
        pc.equip_item(greatsword)

    pc.unequip(EquipmentSlot.OFF_HAND)
    pc.unequip(EquipmentSlot.MAIN_HAND)
    pc.equip_item(greatsword)

    assert EquipmentSlot.TWO_HAND in pc.equipment
    assert pc.equipment[EquipmentSlot.TWO_HAND].id == "eq-greatsword"
