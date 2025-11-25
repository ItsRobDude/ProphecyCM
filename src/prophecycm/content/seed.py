from __future__ import annotations

from prophecycm.characters import AbilityScore, Class, Feat, NPC, PlayerCharacter, Race, Skill
from prophecycm.combat import DurationType, StatusEffect
from prophecycm.items import Consumable, Equipment, EquipmentSlot
from prophecycm.quests import Quest, QuestStep
from prophecycm.state import GameState, SaveFile
from prophecycm.state.party import PartyRoster
from prophecycm.world import Location, TravelConnection


def seed_locations() -> list[Location]:
    return [
        Location(
            id="silverthorn",
            name="Silverthorn",
            biome="temperate-town",
            faction_control="council",
            points_of_interest=["market_square", "old_watchtower"],
            encounter_tables={"any": ["street-brawl", "quiet-night"]},
            connections=[
                TravelConnection(target="whisperwood", travel_time=2, danger=0.2),
                TravelConnection(target="shadowmire-approach", travel_time=1, danger=0.15),
                TravelConnection(target="hushbriar-cove", travel_time=4, danger=0.3),
            ],
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
            connections=[
                TravelConnection(target="silverthorn", travel_time=2, danger=0.35),
                TravelConnection(target="durnhelm", travel_time=3, danger=0.4),
                TravelConnection(target="hushbriar-cove", travel_time=3, danger=0.45),
                TravelConnection(
                    target="cathedral-of-bone",
                    travel_time=1,
                    danger=0.6,
                    requirements=[
                        {
                            "subject": "flag",
                            "key": "entered_whisperwood",
                            "comparator": "==",
                            "value": True,
                        }
                    ],
                ),
                TravelConnection(target="shadowmire-approach", travel_time=1, danger=0.4),
                TravelConnection(
                    target="overseer-manor",
                    travel_time=1,
                    danger=0.55,
                    requirements=[
                        {
                            "subject": "flag",
                            "key": "entered_whisperwood",
                            "comparator": "==",
                            "value": True,
                        }
                    ],
                ),
            ],
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
            connections=[TravelConnection(target="whisperwood", travel_time=2, danger=0.3)],
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
            connections=[
                TravelConnection(target="whisperwood", travel_time=3, danger=0.45),
                TravelConnection(target="solasmor-monastery", travel_time=6, danger=0.55),
                TravelConnection(target="moonwell-glade", travel_time=2, danger=0.35),
            ],
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
            connections=[TravelConnection(target="hushbriar-cove", travel_time=6, danger=0.45)],
            danger_level="austere",
            tags=["lore", "order-stronghold"],
        ),
        Location(
            id="shadowmire-approach",
            name="Shadowmire Approach",
            biome="tainted-forest",
            faction_control="silverthorn-patrols",
            points_of_interest=["fallen-flock", "fungal-scout-corpse", "ambush-clearing"],
            encounter_tables={
                "day": ["wandering-patrol", "choking-spores"],
                "night": ["scarlet-moon-omen", "feral-corvid-swarm"],
                "corruption-surge": ["veil-of-black-spores"],
            },
            connections=[
                TravelConnection(target="silverthorn", travel_time=1, danger=0.25),
                TravelConnection(target="whisperwood", travel_time=1, danger=0.4),
            ],
            danger_level="hazardous",
            tags=["story-route", "forest-road"],
        ),
        Location(
            id="cathedral-of-bone",
            name="Cathedral of Bone",
            biome="ruined-cathedral",
            faction_control="aodhan-cabal",
            points_of_interest=["ritual-dais", "collapsed-nave", "sealed-crypt"],
            encounter_tables={
                "any": ["lurking-dreadcap", "echoing-psalm"],
                "underdark-moon": ["veil-wraith-choir", "fungal-overseer-guard"],
                "aftermath": ["spore-silence"],
            },
            connections=[
                TravelConnection(target="whisperwood", travel_time=1, danger=0.6),
                TravelConnection(
                    target="overseer-manor",
                    travel_time=1,
                    danger=0.55,
                    requirements=[
                        {
                            "subject": "flag",
                            "key": "artifact_clues",
                            "comparator": ">=",
                            "value": 1,
                        }
                    ],
                ),
            ],
            danger_level="dire",
            tags=["ritual-site", "aodhan-thread"],
        ),
        Location(
            id="overseer-manor",
            name="Ó Duibh Manor",
            biome="ruined-manor",
            faction_control="aodhan-cabal",
            points_of_interest=["sealed-study", "blue-hand-door", "hidden-ledger"],
            encounter_tables={
                "any": ["arcane-trap-runes", "weeping-spore-spirit"],
                "night": ["spectral-child-eoin", "fungal-servitor"],
            },
            connections=[
                TravelConnection(target="whisperwood", travel_time=1, danger=0.55),
                TravelConnection(target="cathedral-of-bone", travel_time=1, danger=0.6),
            ],
            danger_level="perilous",
            tags=["clue-site", "aodhan-thread"],
        ),
        Location(
            id="moonwell-glade",
            name="Moonwell Glade",
            biome="sacred-forest",
            faction_control="wood-elf-circle",
            points_of_interest=["moonwell", "hanging-cocoons", "silverthorn-patrol-tracks"],
            encounter_tables={
                "day": ["warded-hart", "restless-refugees"],
                "night": ["choldrith-hunters", "moonlit-rite"],
                "storm": ["desperate-thief-guild-scout"],
            },
            connections=[
                TravelConnection(target="hushbriar-cove", travel_time=2, danger=0.35),
                TravelConnection(target="whisperwood", travel_time=4, danger=0.5),
            ],
            danger_level="unsettled",
            tags=["sacred-site", "thieves-guild-thread"],
        ),
    ]


def seed_quests() -> list[Quest]:
    main_quest_steps = {
        "travel-whisperwood": {
            "description": "Reach Whisperwood and survey the corruption.",
            "success_next": "gather-clues",
            "success_effects": {"flags": {"entered_whisperwood": True, "aodhan_status": "missing"}},
        },
        "gather-clues": {
            "description": "Collect evidence about Aodhan near the spore-choked paths.",
            "entry_conditions": [
                {"subject": "flag", "key": "entered_whisperwood", "comparator": "==", "value": True}
            ],
            "success_next": "trace-artifact",
            "success_effects": {"flags": {"artifact_clues": 1}},
        },
        "trace-artifact": {
            "description": "Follow leads toward the artifact in Durnhelm or Solasmor.",
            "entry_conditions": [
                {"subject": "flag", "key": "artifact_clues", "comparator": ">=", "value": 1}
            ],
            "success_effects": {"flags": {"artifact_clues": 2}},
        },
    }

    step_map = {step_id: QuestStep.from_dict({"id": step_id, **step}) for step_id, step in main_quest_steps.items()}
    quest = Quest(
        id="main-quest-aodhan",
        title="Echoes in the Whisperwood",
        summary="Investigate Aodhan's fate in Whisperwood and uncover a buried artifact.",
        objectives=[
            "Travel to Whisperwood",
            "Track what happened to Aodhan",
            "Secure the artifact before rivals do",
        ],
        steps=[QuestStep.from_dict({"id": step_id, **step}) for step_id, step in main_quest_steps.items()],
        current_step="travel-whisperwood",
    )
    return [quest]


def seed_races_catalog() -> list[Race]:
    return [
        Race(
            id="race-human",
            name="Human",
            subrace_id="human-variant",
            ability_bonuses={"wisdom": 1},
            bonuses={"initiative": 1},
            traits=["versatile"],
            proficiency_packs={
                "urban-diplomat": ["persuasion", "history"],
                "wild-trekker": ["survival", "athletics"],
            },
            feature_progression={
                1: {
                    "features": ["adaptable-talent"],
                    "modifiers": {"skill_points": 1},
                    "choice_slots": {"languages": 1},
                },
                3: {"features": ["resilient-focus"], "modifiers": {"will": 1}},
            },
            spell_progression={1: {"cantrip": 1}},
            choice_slots={"bonus_language": 1},
        ),
        Race(
            id="race-dusk-elf",
            name="Dusk Elf",
            subrace_id="shadowborn",
            ability_bonuses={"dexterity": 2},
            bonuses={"perception": 1},
            traits=["darkvision", "fey-ancestry"],
            proficiency_packs={"woodland": ["stealth", "nature"]},
            feature_progression={
                1: {
                    "features": ["shadow-step"],
                    "modifiers": {"reflex": 1, "stealth": 1},
                    "spell_slots": {"1": 1},
                },
                5: {"features": ["faerie-dust"], "spell_slots": {"2": 1}},
            },
            spell_progression={},
            choice_slots={"languages": 1},
        ),
    ]


def seed_classes_catalog() -> list[Class]:
    return [
        Class(
            id="class-ranger",
            name="Ranger",
            archetype_id="gloom-stalker",
            hit_die=10,
            save_proficiencies=["fortitude", "reflex"],
            ability_bonuses={"dexterity": 1},
            bonuses={"armor_class": 1},
            proficiency_packs={
                "scout-weapons": ["longbow", "shortsword"],
                "tracker-tools": ["thieves-tools", "navigation-kit"],
            },
            feature_progression={
                1: {"features": ["favored-enemy", "natural-explorer"], "modifiers": {"survival": 2}},
                2: {"features": ["fighting-style"], "choice_slots": {"fighting_styles": 1}},
                3: {"features": ["primeval-awareness"], "spell_slots": {"1": 1}},
            },
            spell_progression={2: {"1": 2}, 3: {"1": 3, "2": 1}},
            choice_slots={"trained_skills": 1},
        ),
        Class(
            id="class-battle-cleric",
            name="Battle Cleric",
            archetype_id="war-domain",
            hit_die=8,
            save_proficiencies=["fortitude", "will"],
            ability_bonuses={"wisdom": 1},
            bonuses={},
            proficiency_packs={"temple-rites": ["religion", "insight"]},
            feature_progression={
                1: {"features": ["channel-divinity"], "spell_slots": {"1": 2}},
                2: {"features": ["guided-strike"], "modifiers": {"attack": 1}},
                5: {"features": ["spiritual-ward"], "modifiers": {"will": 1}},
            },
            spell_progression={3: {"2": 2}, 5: {"3": 2}},
            choice_slots={"domain-spells": 1},
        ),
    ]


def seed_characters() -> tuple[PlayerCharacter, list[NPC]]:
    races = seed_races_catalog()
    classes = seed_classes_catalog()
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
            **races[0].to_dict(),
        ),
        character_class=Class(**classes[0].to_dict()),
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
                effect_id="restore_health",
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
        is_companion=False,
    )

    return pc, [npc]


def seed_save_file() -> SaveFile:
    pc, npcs = seed_characters()
    recruitable_companions = [npc.id for npc in npcs if npc.is_companion]
    game_state = GameState(
        timestamp="0001-01-01T00:00:00Z",
        pc=pc,
        npcs=npcs,
        locations=seed_locations(),
        quests=seed_quests(),
        party=PartyRoster(
            leader_id=pc.id, active_companions=[pc.id], reserve_companions=recruitable_companions
        ),
        global_flags={"entered_whisperwood": False, "artifact_clues": 0, "aodhan_status": "unknown"},
        current_location_id="silverthorn",
    )
    return SaveFile(slot=1, metadata={"difficulty": "normal"}, game_state=game_state)
