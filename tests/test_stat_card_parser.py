from pathlib import Path

from prophecycm.content.stat_card_parser import parse_creature_card, parse_item_card, parse_npc_card
from prophecycm.items.item import EquipmentSlot


def test_parse_creature_card_bruno():
    creature = parse_creature_card(Path("stat_cards/creatures/bruno.txt"))

    assert creature.id == "creature.bruno"
    assert creature.name.startswith("Bruno")
    assert creature.armor_class == 14
    assert creature.hit_die == 10
    assert creature.level == 10
    assert creature.abilities["strength"].score == 21
    assert any(action.name == "Bite" for action in creature.actions)


def test_parse_npc_card_creates_stat_block():
    npc = parse_npc_card(Path("stat_cards/prophecy_npc/aine_caillte.txt"))

    assert npc.id == "npc.aine-caillte"
    assert npc.archetype == "aine-caillte"
    assert npc.stat_block is not None
    assert npc.stat_block.armor_class == 17
    assert npc.stat_block.abilities["dexterity"].score == 18


def test_parse_item_card_detects_rarity_and_slot():
    item = parse_item_card(Path("stat_cards/items/aislings_corrupt_vigil.txt"))

    assert item.id == "item.aislings-corrupt-vigil"
    assert item.rarity == "uncommon"
    assert item.item_type == "equipment"
    assert getattr(item, "slot", "") in {EquipmentSlot.TWO_HAND, "two_hand"}
