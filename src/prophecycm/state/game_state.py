from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prophecycm.characters import Creature, NPC, PlayerCharacter
from prophecycm.core import Serializable
from prophecycm.quests import Quest
from prophecycm.world import Location


@dataclass
class GameState(Serializable):
    timestamp: str
    pc: PlayerCharacter
    npcs: List[NPC] = field(default_factory=list)
    creatures: List[Creature] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    quests: List[Quest] = field(default_factory=list)
    global_flags: Dict[str, Any] = field(default_factory=dict)
    current_location_id: Optional[str] = None

    def location_index(self) -> Dict[str, Location]:
        return {location.id: location for location in self.locations}

    def active_location(self) -> Optional[Location]:
        if self.current_location_id is None:
            return None
        return self.location_index().get(self.current_location_id)

    def set_flag(self, name: str, value: Any) -> None:
        self.global_flags[name] = value

    def travel_to(self, destination_id: str) -> bool:
        current = self.active_location()
        location_map = self.location_index()
        destination = location_map.get(destination_id)
        if destination is None:
            return False
        if current is not None and not current.is_connected(destination_id):
            return False
        destination.visited = True
        if current is not None:
            current.visited = True
        self.current_location_id = destination_id
        return True

    def roll_encounter(self, time_of_day: str = "day") -> Optional[str]:
        location = self.active_location()
        if location is None:
            return None
        table = location.encounter_tables.get(time_of_day) or location.encounter_tables.get("any")
        if not table:
            return None
        return table[0]

    def available_combatants(
        self, player_level: Optional[int] = None, difficulty: str = "standard"
    ) -> List[Creature]:
        """Return combat-ready stat blocks for all alive NPCs/creatures.

        NPC stat blocks can optionally scale to `player_level`; authored creature
        templates remain static and are returned as copies.
        """

        combatants: List[Creature] = []
        for npc in self.npcs:
            if not npc.is_alive:
                continue
            block = npc.scaled_stat_block(player_level or self.pc.level, difficulty=difficulty)
            if block:
                combatants.append(block)

        for creature in self.creatures:
            if creature.is_alive:
                combatants.append(deepcopy(creature))

        return combatants

    def apply_quest_step(self, quest_id: str, success: bool = True) -> None:
        quest = next((quest for quest in self.quests if quest.id == quest_id), None)
        if quest is None:
            return
        updated_flags = quest.apply_step_result(self.global_flags, success=success)
        self.global_flags.update(updated_flags)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GameState":
        return cls(
            timestamp=data.get("timestamp", ""),
            pc=PlayerCharacter.from_dict(data.get("pc", {})),
            npcs=[NPC.from_dict(npc) for npc in data.get("npcs", [])],
            creatures=[Creature.from_dict(creature) for creature in data.get("creatures", [])],
            locations=[Location.from_dict(loc) for loc in data.get("locations", [])],
            quests=[Quest.from_dict(quest) for quest in data.get("quests", [])],
            global_flags=data.get("global_flags", {}),
            current_location_id=data.get("current_location_id"),
        )
