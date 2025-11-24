from prophecycm.characters import AbilityScore, Class, Feat, NPC, PlayerCharacter, Race, Skill
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
