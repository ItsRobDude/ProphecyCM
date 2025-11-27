from prophecycm.characters import AbilityScore, Class, NPC, PlayerCharacter, Race, Skill
from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.npc import NPCScalingProfile
from prophecycm.characters.player import XP_THRESHOLDS
from prophecycm.state import GameState, LevelUpRequest
from prophecycm.ui.level_up_config import LevelUpScreenConfig
from prophecycm.rules import SKILL_TO_ABILITY


def _basic_pc() -> PlayerCharacter:
    return PlayerCharacter(
        id="pc-test",
        name="Test",
        background="",
        abilities={"constitution": AbilityScore(name="constitution", score=10)},
        skills={
            "perception": Skill(
                name="perception", key_ability=SKILL_TO_ABILITY["perception"], proficiency="trained"
            )
        },
        race=Race(id="race-human", name="Human"),
        character_class=Class(id="class-warrior", name="Warrior", hit_die=10, save_proficiencies=["fortitude"]),
    )


def _companion(auto_level: bool) -> NPC:
    creature = Creature(
        id="creature-companion",
        name="Companion",
        level=1,
        role="ally",
        hit_die=8,
        armor_class=12,
        abilities={"constitution": AbilityScore(name="constitution", score=12)},
        actions=[CreatureAction(name="Slash", to_hit_bonus=2, damage_dice="1d6")],
        save_proficiencies=["fortitude"],
    )
    return NPC(
        id="npc-companion",
        archetype="guide",
        faction_id="wardens",
        disposition="friendly",
        stat_block=creature,
        scaling=NPCScalingProfile(base_level=1, attack_progression=1, damage_progression=1),
        auto_level=auto_level,
    )


def test_companion_auto_level_applies_scaling() -> None:
    pc = _basic_pc()
    companion = _companion(auto_level=True)
    base_hp = companion.stat_block.hit_points if companion.stat_block else 0

    state = GameState(timestamp="now", pc=pc, npcs=[companion])
    state.grant_party_xp(XP_THRESHOLDS[2])

    assert companion.level == 2
    assert companion.stat_block is not None
    assert companion.stat_block.level == 2
    assert companion.stat_block.hit_points > base_hp
    assert not [entry for entry in state.level_up_queue if entry.character_id == companion.id]


def test_companion_manual_level_queues_request() -> None:
    pc = _basic_pc()
    companion = _companion(auto_level=False)
    state = GameState(timestamp="now", pc=pc, npcs=[companion])

    state.grant_party_xp(XP_THRESHOLDS[2])

    queued = [entry for entry in state.level_up_queue if entry.character_id == companion.id]
    assert queued, "Manual companions should be queued for UI handling"
    assert queued[0].target_level == companion.level


def test_level_up_screen_config_exposes_party_state() -> None:
    pc = _basic_pc()
    companion = _companion(auto_level=False)
    state = GameState(timestamp="now", pc=pc, npcs=[companion])
    state.level_up_queue.append(LevelUpRequest(character_id=pc.id, character_type="pc", target_level=2))

    config = LevelUpScreenConfig.from_game_state(state)

    companion_settings = next(entry for entry in config.companions if entry.id == companion.id)
    assert companion_settings.auto_level is False
    assert companion_settings.level == companion.level
    assert config.pending and any(entry.character_id == pc.id for entry in config.pending)
