from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from prophecycm.characters import AbilityScore, NPC
from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.npc import NPCScalingProfile
from prophecycm.items import Consumable, Equipment, EquipmentSlot


@dataclass
class QuestNPCProfile:
    npc: NPC
    recruitable: bool = True


def _abilities(scores: Dict[str, int]) -> Dict[str, AbilityScore]:
    return {name: AbilityScore(name=name, score=value) for name, value in scores.items()}


def _aine_caillte() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-aine-caillte",
        name="Aine Caillte",
        level=10,
        role="arcane-trickster",
        hit_die=8,
        armor_class=17,
        abilities=_abilities(
            {
                "strength": 10,
                "dexterity": 18,
                "constitution": 18,
                "intelligence": 14,
                "wisdom": 14,
                "charisma": 20,
            }
        ),
        actions=[
            CreatureAction(
                name="Sorcerous Bolt",
                attack_ability="charisma",
                to_hit_bonus=8,
                damage_dice="2d10",
                damage_bonus=5,
                tags=["ranged", "fire"],
            ),
            CreatureAction(
                name="Cat Form Rake",
                attack_ability="dexterity",
                to_hit_bonus=7,
                damage_dice="1d8",
                damage_bonus=4,
                tags=["melee", "shapeshift"],
            ),
        ],
        alignment="chaotic-neutral",
        traits=["shapechanger", "fey-ancestry", "legendary-resistance"],
        save_proficiencies=["fortitude", "will"],
        speed=30,
    )

    npc = NPC(
        id="npc-aine-caillte",
        archetype="hidden-sorceress",
        faction_id="caillte-remnants",
        disposition="cautious",
        inventory=[
            Consumable(
                id="consumable-arcane-tonic",
                name="Arcane Tonic",
                effect_id="restore_health",
                charges=2,
                rarity="uncommon",
                value=60,
            ),
            Equipment(
                id="eq-sylvan-cloak",
                name="Sylvan Cloak",
                slot=EquipmentSlot.CHEST,
                modifiers={"armor_class": 1, "stealth": 1},
                rarity="rare",
                value=250,
            ),
        ],
        quest_hooks=["main-quest-aodhan", "caillte-lineage"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=10,
            min_level=6,
            max_level=18,
            attack_progression=1,
            damage_progression=1,
        ),
        level=10,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _aisling_dioltas() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-aisling-dioltas",
        name="Aisling Ní Díoltas",
        level=10,
        role="eldritch-knight",
        hit_die=8,
        armor_class=17,
        abilities=_abilities(
            {
                "strength": 16,
                "dexterity": 14,
                "constitution": 18,
                "intelligence": 12,
                "wisdom": 10,
                "charisma": 16,
            }
        ),
        actions=[
            CreatureAction(
                name="Vengeance Slash",
                attack_ability="strength",
                to_hit_bonus=7,
                damage_dice="2d8",
                damage_bonus=4,
                tags=["melee", "force"],
            ),
            CreatureAction(
                name="Revenant Bolt",
                attack_ability="charisma",
                to_hit_bonus=7,
                damage_dice="2d6",
                damage_bonus=3,
                tags=["ranged", "necrotic"],
            ),
        ],
        alignment="chaotic-neutral",
        traits=["undead", "martial-magic"],
        save_proficiencies=["fortitude", "will"],
        speed=30,
    )

    npc = NPC(
        id="npc-aisling-dioltas",
        archetype="vengeful-revenant",
        faction_id="tuama-lineage",
        disposition="prickly",
        inventory=[
            Equipment(
                id="eq-eldritch-blade",
                name="Eldritch Blade",
                slot=EquipmentSlot.MAIN_HAND,
                modifiers={"attack": 1, "damage": 1},
                rarity="uncommon",
                value=200,
            )
        ],
        quest_hooks=["tuama-restoration"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=10,
            min_level=6,
            max_level=18,
            attack_progression=1,
            damage_progression=1,
        ),
        level=10,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _aodhan_o_duibh() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-aodhan-o-duibh",
        name="Aodhan Ó Duibh",
        level=13,
        role="cabal-arcanist",
        hit_die=10,
        armor_class=17,
        abilities=_abilities(
            {
                "strength": 10,
                "dexterity": 16,
                "constitution": 20,
                "intelligence": 18,
                "wisdom": 12,
                "charisma": 20,
            }
        ),
        actions=[
            CreatureAction(
                name="Eldritch Barrage",
                attack_ability="charisma",
                to_hit_bonus=9,
                damage_dice="3d10",
                damage_bonus=5,
                tags=["ranged", "force"],
            ),
            CreatureAction(
                name="Shadow Blade",
                attack_ability="dexterity",
                to_hit_bonus=8,
                damage_dice="2d8",
                damage_bonus=4,
                tags=["melee", "psychic"],
            ),
        ],
        alignment="neutral-evil",
        traits=["mage-armor", "ritualist"],
        save_proficiencies=["will", "reflex"],
        speed=30,
    )

    npc = NPC(
        id="npc-aodhan-o-duibh",
        archetype="missing-scout",
        faction_id="aodhan-cabal",
        disposition="hostile",
        inventory=[
            Equipment(
                id="eq-blue-hand-signet",
                name="Blue Hand Signet",
                slot=EquipmentSlot.ACCESSORY,
                modifiers={"will": 1},
                rarity="rare",
                value=350,
            )
        ],
        quest_hooks=["main-quest-aodhan"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=13,
            min_level=8,
            max_level=20,
            attack_progression=1,
            damage_progression=1,
        ),
        level=13,
        auto_level=False,
    )
    return QuestNPCProfile(npc=npc, recruitable=False)


def _bjorn_leifson() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-bjorn-leifson",
        name="Bjorn Leifson",
        level=6,
        role="circle-of-the-moon",
        hit_die=8,
        armor_class=16,
        abilities=_abilities(
            {
                "strength": 12,
                "dexterity": 14,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 16,
                "charisma": 12,
            }
        ),
        actions=[
            CreatureAction(
                name="Primal Staff",
                attack_ability="wisdom",
                to_hit_bonus=5,
                damage_dice="1d8",
                damage_bonus=3,
                tags=["melee", "bludgeoning"],
            ),
            CreatureAction(
                name="Moonbeam Pulse",
                attack_ability="wisdom",
                to_hit_bonus=6,
                damage_dice="2d8",
                damage_bonus=3,
                tags=["ranged", "radiant"],
            ),
        ],
        alignment="neutral",
        traits=["wildshape-adapted"],
        save_proficiencies=["fortitude", "will"],
        speed=30,
    )

    npc = NPC(
        id="npc-bjorn-leifson",
        archetype="moon-druid",
        faction_id="solasmor-order",
        disposition="steadfast",
        inventory=[
            Equipment(
                id="eq-barkskin-leathers",
                name="Barkskin Leathers",
                slot=EquipmentSlot.CHEST,
                modifiers={"armor_class": 1},
                rarity="uncommon",
                value=120,
            ),
            Consumable(
                id="consumable-herbal-salve",
                name="Herbal Salve",
                effect_id="restore_health",
                charges=1,
                value=25,
            ),
        ],
        quest_hooks=["moonwell-protection"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=6,
            min_level=4,
            max_level=15,
            attack_progression=1,
            damage_progression=1,
        ),
        level=6,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _breithiun_meachan() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-breithiun-meachan",
        name="Breithiún Meáchan",
        level=6,
        role="celestial-judge",
        hit_die=8,
        armor_class=17,
        abilities=_abilities(
            {
                "strength": 14,
                "dexterity": 18,
                "constitution": 18,
                "intelligence": 16,
                "wisdom": 20,
                "charisma": 16,
            }
        ),
        actions=[
            CreatureAction(
                name="Radiant Verdict",
                attack_ability="wisdom",
                to_hit_bonus=8,
                damage_dice="2d8",
                damage_bonus=5,
                tags=["ranged", "radiant"],
            ),
            CreatureAction(
                name="Scales of Balance",
                attack_ability="dexterity",
                to_hit_bonus=7,
                damage_dice="1d10",
                damage_bonus=4,
                tags=["melee", "force"],
            ),
        ],
        alignment="lawful-neutral",
        traits=["truesight", "hover"],
        save_proficiencies=["will", "reflex"],
        speed=30,
    )

    npc = NPC(
        id="npc-breithiun-meachan",
        archetype="judge-of-balance",
        faction_id="celestial-arbitrators",
        disposition="measured",
        inventory=[
            Equipment(
                id="eq-scales-of-judgment",
                name="Scales of Judgment",
                slot=EquipmentSlot.OFF_HAND,
                modifiers={"will": 1},
                rarity="rare",
                value=400,
            )
        ],
        quest_hooks=["balance-the-ledger"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=6,
            min_level=4,
            max_level=14,
            attack_progression=1,
            damage_progression=1,
        ),
        level=6,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _bronach_o_tuama() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-bronach-o-tuama",
        name="Brónach Ó Tuama",
        level=10,
        role="guardian",
        hit_die=8,
        armor_class=15,
        abilities=_abilities(
            {
                "strength": 12,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 14,
                "wisdom": 16,
                "charisma": 15,
            }
        ),
        actions=[
            CreatureAction(
                name="Guardian Blade",
                attack_ability="strength",
                to_hit_bonus=6,
                damage_dice="1d10",
                damage_bonus=4,
                tags=["melee", "radiant"],
            ),
            CreatureAction(
                name="Ward of Sorrow",
                attack_ability="wisdom",
                to_hit_bonus=6,
                damage_dice="2d6",
                damage_bonus=3,
                tags=["ranged", "force"],
            ),
        ],
        alignment="lawful-neutral",
        traits=["undead", "guardian-vigil"],
        save_proficiencies=["will"],
        speed=30,
    )

    npc = NPC(
        id="npc-bronach-o-tuama",
        archetype="tomb-guardian",
        faction_id="tuama-lineage",
        disposition="stern",
        inventory=[
            Equipment(
                id="eq-guardian-chain",
                name="Guardian Chain",
                slot=EquipmentSlot.CHEST,
                modifiers={"armor_class": 1},
                rarity="uncommon",
                value=180,
            )
        ],
        quest_hooks=["tuama-restoration"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=10,
            min_level=6,
            max_level=18,
            attack_progression=1,
            damage_progression=1,
        ),
        level=10,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _caitriona_tuama() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-caitriona-tuama",
        name="Caitríona Tuama",
        level=9,
        role="spectral-healer",
        hit_die=8,
        armor_class=14,
        abilities=_abilities(
            {
                "strength": 8,
                "dexterity": 14,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 18,
                "charisma": 15,
            }
        ),
        actions=[
            CreatureAction(
                name="Spectral Touch",
                attack_ability="wisdom",
                to_hit_bonus=6,
                damage_dice="1d10",
                damage_bonus=2,
                tags=["melee", "necrotic"],
            ),
            CreatureAction(
                name="Soothing Wail",
                attack_ability="charisma",
                to_hit_bonus=5,
                damage_dice="2d6",
                damage_bonus=2,
                tags=["ranged", "psychic"],
            ),
        ],
        alignment="neutral",
        traits=["hover", "spectral-ward"],
        save_proficiencies=["will"],
        speed=30,
    )

    npc = NPC(
        id="npc-caitriona-tuama",
        archetype="pure-tomb",
        faction_id="tuama-lineage",
        disposition="calm",
        inventory=[
            Consumable(
                id="consumable-veil-essence",
                name="Veil Essence",
                effect_id="restore_health",
                charges=1,
                rarity="uncommon",
                value=90,
            )
        ],
        quest_hooks=["tuama-restoration"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=9,
            min_level=5,
            max_level=18,
            attack_progression=1,
            damage_progression=1,
        ),
        level=9,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _fiona_caoidheach() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-fiona-caoidheach",
        name="Fiona Caoidheach",
        level=8,
        role="white-mourning",
        hit_die=8,
        armor_class=14,
        abilities=_abilities(
            {
                "strength": 8,
                "dexterity": 14,
                "constitution": 16,
                "intelligence": 18,
                "wisdom": 12,
                "charisma": 16,
            }
        ),
        actions=[
            CreatureAction(
                name="White Wail",
                attack_ability="intelligence",
                to_hit_bonus=6,
                damage_dice="2d6",
                damage_bonus=4,
                tags=["ranged", "psychic"],
            ),
            CreatureAction(
                name="Spectral Lance",
                attack_ability="dexterity",
                to_hit_bonus=6,
                damage_dice="1d10",
                damage_bonus=3,
                tags=["melee", "necrotic"],
            ),
        ],
        alignment="neutral",
        traits=["undead", "mage-armor"],
        save_proficiencies=["will", "reflex"],
        speed=30,
    )

    npc = NPC(
        id="npc-fiona-caoidheach",
        archetype="white-mourning",
        faction_id="tuama-lineage",
        disposition="melancholic",
        inventory=[
            Equipment(
                id="eq-wraithstone-focus",
                name="Wraithstone Focus",
                slot=EquipmentSlot.ACCESSORY,
                modifiers={"attack": 1},
                rarity="uncommon",
                value=160,
            )
        ],
        quest_hooks=["tuama-restoration"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=8,
            min_level=5,
            max_level=16,
            attack_progression=1,
            damage_progression=1,
        ),
        level=8,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _liobhan_sceith() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-liobhan-sceith",
        name="Liobhan Sceith",
        level=6,
        role="gloom-stalker",
        hit_die=10,
        armor_class=16,
        abilities=_abilities(
            {
                "strength": 10,
                "dexterity": 18,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 16,
                "charisma": 10,
            }
        ),
        actions=[
            CreatureAction(
                name="Shadow Longbow",
                attack_ability="dexterity",
                to_hit_bonus=7,
                damage_dice="1d8",
                damage_bonus=4,
                tags=["ranged", "piercing"],
            ),
            CreatureAction(
                name="Hunting Shortblade",
                attack_ability="dexterity",
                to_hit_bonus=6,
                damage_dice="1d6",
                damage_bonus=4,
                tags=["melee", "slashing"],
            ),
        ],
        alignment="neutral",
        traits=["darkvision", "favored-enemy-corruption"],
        save_proficiencies=["reflex"],
        speed=35,
    )

    npc = NPC(
        id="npc-liobhan-sceith",
        archetype="gloom-stalker",
        faction_id="wood-elf-circle",
        disposition="curious",
        inventory=[
            Equipment(
                id="eq-studded-leathers-liobhan",
                name="Studded Leathers",
                slot=EquipmentSlot.CHEST,
                modifiers={"armor_class": 1},
                value=75,
            ),
            Equipment(
                id="eq-obsidian-arrowheads",
                name="Obsidian Arrowheads",
                slot=EquipmentSlot.ACCESSORY,
                modifiers={"attack": 1},
                rarity="uncommon",
                value=120,
            ),
        ],
        quest_hooks=["whisperwood-salvage"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=6,
            min_level=4,
            max_level=14,
            attack_progression=1,
            damage_progression=1,
        ),
        level=6,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _neala_creach() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-neala-creach",
        name="Neala Creach",
        level=6,
        role="gloom-stalker",
        hit_die=10,
        armor_class=16,
        abilities=_abilities(
            {
                "strength": 10,
                "dexterity": 18,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 16,
                "charisma": 10,
            }
        ),
        actions=[
            CreatureAction(
                name="Twin Arrows",
                attack_ability="dexterity",
                to_hit_bonus=7,
                damage_dice="1d8",
                damage_bonus=4,
                tags=["ranged", "piercing"],
            ),
            CreatureAction(
                name="Silent Knife",
                attack_ability="dexterity",
                to_hit_bonus=6,
                damage_dice="1d6",
                damage_bonus=4,
                tags=["melee", "slashing"],
            ),
        ],
        alignment="neutral",
        traits=["darkvision", "gloom-ambusher"],
        save_proficiencies=["reflex"],
        speed=35,
    )

    npc = NPC(
        id="npc-neala-creach",
        archetype="gloom-stalker",
        faction_id="wood-elf-circle",
        disposition="focused",
        inventory=[
            Equipment(
                id="eq-studded-leathers-neala",
                name="Studded Leathers",
                slot=EquipmentSlot.CHEST,
                modifiers={"armor_class": 1},
                value=75,
            ),
            Equipment(
                id="eq-hunters-lens",
                name="Hunter's Lens",
                slot=EquipmentSlot.ACCESSORY,
                modifiers={"perception": 1},
                rarity="uncommon",
                value=100,
            ),
        ],
        quest_hooks=["whisperwood-salvage"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=6,
            min_level=4,
            max_level=14,
            attack_progression=1,
            damage_progression=1,
        ),
        level=6,
    )
    return QuestNPCProfile(npc=npc, recruitable=True)


def _thalion_ebonhart() -> QuestNPCProfile:
    stat_block = Creature(
        id="creature-thalion-ebonhart",
        name="Thalion Ebonhart",
        level=12,
        role="lich-archivist",
        hit_die=10,
        armor_class=16,
        abilities=_abilities(
            {
                "strength": 10,
                "dexterity": 14,
                "constitution": 14,
                "intelligence": 20,
                "wisdom": 15,
                "charisma": 16,
            }
        ),
        actions=[
            CreatureAction(
                name="Archive Blast",
                attack_ability="intelligence",
                to_hit_bonus=8,
                damage_dice="2d10",
                damage_bonus=5,
                tags=["ranged", "necrotic"],
            ),
            CreatureAction(
                name="Grasp of the Archive",
                attack_ability="strength",
                to_hit_bonus=6,
                damage_dice="2d6",
                damage_bonus=2,
                tags=["melee", "cold"],
            ),
        ],
        alignment="neutral-evil",
        traits=["hover", "lich-phylactery"],
        save_proficiencies=["will", "reflex"],
        speed=30,
    )

    npc = NPC(
        id="npc-thalion-ebonhart",
        archetype="archive-guardian",
        faction_id="ebonhart-archive",
        disposition="calculating",
        inventory=[
            Equipment(
                id="eq-archival-focus",
                name="Archival Focus",
                slot=EquipmentSlot.ACCESSORY,
                modifiers={"spell_dc": 1},
                rarity="rare",
                value=300,
            )
        ],
        quest_hooks=["archive-secrets"],
        stat_block=stat_block,
        scaling=NPCScalingProfile(
            base_level=12,
            min_level=8,
            max_level=20,
            attack_progression=1,
            damage_progression=1,
        ),
        level=12,
        auto_level=False,
    )
    return QuestNPCProfile(npc=npc, recruitable=False)


def quest_npcs() -> List[NPC]:
    profiles = [
        _aine_caillte(),
        _aisling_dioltas(),
        _aodhan_o_duibh(),
        _bjorn_leifson(),
        _breithiun_meachan(),
        _bronach_o_tuama(),
        _caitriona_tuama(),
        _fiona_caoidheach(),
        _liobhan_sceith(),
        _neala_creach(),
        _thalion_ebonhart(),
    ]
    return [profile.npc for profile in profiles]


def quest_npc_roster() -> List[QuestNPCProfile]:
    return [
        _aine_caillte(),
        _aisling_dioltas(),
        _aodhan_o_duibh(),
        _bjorn_leifson(),
        _breithiun_meachan(),
        _bronach_o_tuama(),
        _caitriona_tuama(),
        _fiona_caoidheach(),
        _liobhan_sceith(),
        _neala_creach(),
        _thalion_ebonhart(),
    ]
