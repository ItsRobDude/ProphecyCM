"""Minimal bootstrapping to validate object creation and serialization."""

from prophecycm.characters import AbilityScore, Class, Feat, NPC, PlayerCharacter, Race, Skill
from prophecycm.combat import StatusEffect
from prophecycm.items import Consumable, Equipment
from prophecycm.quests import Quest
from prophecycm.state import GameState, SaveFile
from prophecycm.world import Location


def demo_state() -> SaveFile:
    pc = PlayerCharacter(
        id="pc-001",
        name="Aria",
        background="Wanderer",
        abilities={
            "strength": AbilityScore(name="strength", score=8),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=12),
            "wisdom": AbilityScore(name="wisdom", score=10),
        },
        skills={
            "survival": Skill(name="survival", key_ability="wisdom", proficiency="trained"),
            "diplomacy": Skill(name="diplomacy", key_ability="charisma", proficiency="untrained"),
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
        inventory=[Equipment(id="eq-001", name="Rusty Sword", slot="hand", modifiers={"attack": 1})],
        status_effects=[
            StatusEffect(id="se-001", name="Inspired", duration=3, modifiers={"will": 2, "hit_points": 5})
        ],
        level=2,
        xp=300,
    )

    npc = NPC(
        id="npc-001",
        archetype="merchant",
        faction_id="neutral",
        disposition="friendly",
        inventory=[Consumable(id="c-001", name="Health Draught", effect="restore_health", charges=1)],
        quest_hooks=["quest-001"],
    )

    quest = Quest(
        id="quest-001",
        title="Find the Lost Relic",
        summary="Recover the relic from the ancient ruins.",
        objectives=["Travel to the ruins", "Retrieve the relic", "Return to the merchant"],
        stage=0,
    )

    location = Location(
        id="loc-001",
        name="Ancient Ruins",
        biome="desert",
        faction_control="neutral",
        points_of_interest=["collapsed_gate", "sealed_chamber"],
        encounter_tables={"day": ["scarab_swarm"], "night": ["restless_spirit"]},
    )

    state = GameState(
        timestamp="0001-01-01T00:00:00Z",
        pc=pc,
        npcs=[npc],
        locations=[location],
        quests=[quest],
        global_flags={"tutorial_completed": False},
    )

    return SaveFile(slot=1, metadata={"difficulty": "normal"}, game_state=state)


def main() -> None:
    save = demo_state()
    print(save.to_json())


if __name__ == "__main__":
    main()
