"""Minimal bootstrapping to validate object creation and serialization."""

from prophecycm.characters import NPC, PlayerCharacter
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
        attributes={"strength": 8, "intellect": 12},
        skills=["survival", "diplomacy"],
        inventory=[Equipment(id="eq-001", name="Rusty Sword", slot="hand", modifiers={"attack": 1})],
        status_effects=[StatusEffect(id="se-001", name="Inspired", duration=3, modifiers={"will": 2})],
        level=1,
        xp=0,
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
