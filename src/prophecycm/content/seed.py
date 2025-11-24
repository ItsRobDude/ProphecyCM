from __future__ import annotations

from prophecycm.characters import (
    AbilityScore,
    Class,
    Creature,
    CreatureAction,
    Feat,
    NPC,
    NPCScalingProfile,
    PlayerCharacter,
    Race,
    Skill,
)
from prophecycm.combat import DurationType, StatusEffect
from prophecycm.items import Consumable, Equipment, EquipmentSlot
from prophecycm.quests import Quest, QuestStep
from prophecycm.state import GameState, SaveFile
from prophecycm.world import Location


def seed_locations() -> list[Location]:
    return [
        Location(
            id="silverthorn",
            name="Silverthorn",
            biome="temperate-town",
            faction_control="council",
            points_of_interest=["market_square", "old_watchtower"],
            encounter_tables={"any": ["street-brawl", "quiet-night"]},
            connections=["whisperwood"],
            danger_level="safe",
            tags=["hub", "starting-town"],
            visited=True,
        ),
        Location(
            id="whisperwood",
            name="Whisperwood / Sporefall",
            biome="corrupted-forest",
            faction_control="unknown",
            points_of_interest=["spore-choked-path", "aodhans-camp"],
            encounter_tables={"day": ["spore-wolf-pack"], "night": ["myconid-wraith"]},
            connections=["silverthorn", "durnhelm", "hushbriar-cove"],
            danger_level="volatile",
            tags=["quest-hub"],
        ),
        Location(
            id="durnhelm",
            name="Durnhelm",
            biome="mountain-pass",
            faction_control="miners-guild",
            points_of_interest=["switchback-trail", "watch-fire"],
            encounter_tables={"day": ["rockslide"], "night": ["mountain-patrol"]},
            connections=["whisperwood"],
            danger_level="guarded",
            tags=["faction-clue"],
        ),
        Location(
            id="hushbriar-cove",
            name="Hushbriar Cove",
            biome="coastal-town",
            faction_control="harbor-wardens",
            points_of_interest=["salt-market", "tide-hollows"],
            encounter_tables={"day": ["smuggler-envoy"], "night": ["dockside-ambush"]},
            connections=["whisperwood", "solasmor-monastery"],
            danger_level="tense",
            tags=["trade-route"],
        ),
        Location(
            id="solasmor-monastery",
            name="Solasmor Monastery",
            biome="clifftop-monastery",
            faction_control="solasmor-order",
            points_of_interest=["scriptorium", "lighthouse"],
            encounter_tables={"any": ["chanting-rite"]},
            connections=["hushbriar-cove"],
            danger_level="austere",
            tags=["lore", "order-stronghold"],
        ),
    ]


def seed_quests() -> list[Quest]:
    main_quest_steps = {
        "travel-whisperwood": {
            "description": "Reach Whisperwood and survey the corruption.",
            "success_next": "gather-clues",
            "success_effects": [
                {"set_flags": {"entered_whisperwood": True, "aodhan_status": "missing"}},
            ],
        },
        "gather-clues": {
            "description": "Collect evidence about Aodhan near the spore-choked paths.",
            "entry_conditions": [{"flag": "entered_whisperwood", "equals": True}],
            "success_next": "trace-artifact",
            "success_effects": [{"set_flags": {"artifact_clues": 1}}],
        },
        "trace-artifact": {
            "description": "Follow leads toward the artifact in Durnhelm or Solasmor.",
            "entry_conditions": [{"flag": "artifact_clues", "min_value": 1}],
            "success_effects": [{"set_flags": {"artifact_clues": 2}}],
        },
    }

    quest = Quest(
        id="main-quest-aodhan",
        title="Echoes in the Whisperwood",
        summary="Investigate Aodhan's fate in Whisperwood and uncover a buried artifact.",
        objectives=[
            "Travel to Whisperwood",
            "Track what happened to Aodhan",
            "Secure the artifact before rivals do",
        ],
        steps={step_id: QuestStep.from_dict({"id": step_id, **step}) for step_id, step in main_quest_steps.items()},
        current_step="travel-whisperwood",
    )
    return [quest]


def seed_characters() -> tuple[PlayerCharacter, list[NPC]]:
    pc = PlayerCharacter(
        id="pc-aria",
        name="Aria",
        background="Scout of Silverthorn",
        abilities={
            "strength": AbilityScore(name="strength", score=10),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=12),
            "intelligence": AbilityScore(name="intelligence", score=12),
            "wisdom": AbilityScore(name="wisdom", score=13),
            "charisma": AbilityScore(name="charisma", score=11),
        },
        skills={
            "survival": Skill(name="survival", key_ability="wisdom", proficiency="trained"),
            "stealth": Skill(name="stealth", key_ability="dexterity", proficiency="trained"),
            "persuasion": Skill(name="persuasion", key_ability="charisma", proficiency="untrained"),
        },
        race=Race(
            id="race-human",
            name="Human",
            ability_bonuses={"wisdom": 1},
            bonuses={"initiative": 1},
            traits=["versatile"],
        ),
        character_class=Class(
            id="class-ranger",
            name="Ranger",
            hit_die=10,
            save_proficiencies=["fortitude", "reflex"],
            ability_bonuses={"dexterity": 1},
            bonuses={"armor_class": 1},
        ),
        feats=[
            Feat(
                id="feat-keen-senses",
                name="Keen Senses",
                description="Alert to danger",
                modifiers={"initiative": 2},
            )
        ],
        inventory=[
            Equipment(
                id="eq-iron-sabre",
                name="Iron Sabre",
                slot=EquipmentSlot.MAIN_HAND,
                modifiers={"attack": 1},
                value=25,
                rarity="uncommon",
            ),
            Consumable(
                id="consumable-tonic",
                name="Forest Tonic",
                effect="restore_health",
                charges=1,
                value=15,
            ),
        ],
        status_effects=[
            StatusEffect(
                id="inspired",
                name="Inspired",
                duration=2,
                modifiers={"will": 1, "hit_points": 3},
                duration_type=DurationType.ENCOUNTER,
            )
        ],
        level=2,
        xp=300,
    )

    npc = NPC(
        id="npc-scout-aodhan",
        archetype="missing-scout",
        faction_id="silverthorn-rangers",
        disposition="unknown",
        inventory=[],
        quest_hooks=["main-quest-aodhan"],
    )

    return pc, [npc]


def seed_creatures() -> list[Creature]:
    spore_wolf = Creature(
        id="creature-spore-wolf",
        name="Spore Wolf",
        level=2,
        role="skirmisher",
        hit_die=8,
        armor_class=12,
        abilities={
            "strength": AbilityScore(name="strength", score=13),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=12),
            "wisdom": AbilityScore(name="wisdom", score=11),
        },
        actions=[
            CreatureAction(
                name="Infected Bite",
                attack_ability="strength",
                to_hit_bonus=2,
                damage_dice="1d6",
                damage_bonus=2,
                tags=["melee", "poison"],
            )
        ],
        alignment="feral",
        save_proficiencies=["fortitude", "reflex"],
        traits=["pack-tactics"],
    )

    myconid_wraith = Creature(
        id="creature-myconid-wraith",
        name="Myconid Wraith",
        level=4,
        role="controller",
        hit_die=10,
        armor_class=14,
        abilities={
            "strength": AbilityScore(name="strength", score=10),
            "dexterity": AbilityScore(name="dexterity", score=12),
            "constitution": AbilityScore(name="constitution", score=14),
            "wisdom": AbilityScore(name="wisdom", score=15),
        },
        actions=[
            CreatureAction(
                name="Spore Burst",
                attack_ability="wisdom",
                to_hit_bonus=3,
                damage_dice="1d8",
                damage_bonus=3,
                tags=["ranged", "psychic"],
            )
        ],
        alignment="corrupted",
        save_proficiencies=["will", "fortitude"],
        traits=["spore-cloud", "flying"],
    )

    return [spore_wolf, myconid_wraith]


def seed_save_file() -> SaveFile:
    pc, npcs = seed_characters()
    creatures = seed_creatures()

    spore_wolf_template = next((creature for creature in creatures if creature.id == "creature-spore-wolf"), None)
    if spore_wolf_template:
        npcs.append(
            NPC(
                id="npc-spore-wolf-alpha",
                archetype="creature-encounter",
                faction_id="corrupted-fauna",
                disposition="hostile",
                stat_block=spore_wolf_template,
                scaling=NPCScalingProfile(base_level=2, attack_progression=1, damage_progression=1),
            )
        )

    game_state = GameState(
        timestamp="0001-01-01T00:00:00Z",
        pc=pc,
        npcs=npcs,
        creatures=creatures,
        locations=seed_locations(),
        quests=seed_quests(),
        global_flags={"entered_whisperwood": False, "artifact_clues": 0, "aodhan_status": "unknown"},
        current_location_id="silverthorn",
    )
    return SaveFile(slot=1, metadata={"difficulty": "normal"}, game_state=game_state)
