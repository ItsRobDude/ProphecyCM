from prophecycm.characters import NPC, PlayerCharacter
from prophecycm.combat import StatusEffect
from prophecycm.items import Consumable, Equipment, Item
from prophecycm.quests import Quest
from prophecycm.state import GameState
from prophecycm.world import Location


def test_player_character_creation():
    pc = PlayerCharacter(
        id="pc-100",
        name="Test Hero",
        background="Explorer",
        attributes={"strength": 10},
        skills=["climb"],
        inventory=[Item(id="item-1", name="Rope")],
    )
    assert pc.to_dict()["name"] == "Test Hero"


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
        attributes={},
        skills=[],
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
