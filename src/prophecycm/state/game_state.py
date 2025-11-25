from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prophecycm.characters import Creature, NPC, PlayerCharacter
from prophecycm.combat.engine import CombatantRef, EncounterState, roll_initiative
from prophecycm.core import Serializable
from prophecycm.quests import Quest
from prophecycm.world import Location, Faction


@dataclass
class GameState(Serializable):
    timestamp: str
    pc: PlayerCharacter
    npcs: List[NPC] = field(default_factory=list)
    creatures: List[Creature] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    factions: List[Faction] = field(default_factory=list)
    quests: List[Quest] = field(default_factory=list)
    global_flags: Dict[str, Any] = field(default_factory=dict)
    current_location_id: Optional[str] = None
    visited_locations: List[str] = field(default_factory=list)
    active_encounter: Optional[EncounterState] = None
    faction_rep: Dict[str, int] = field(default_factory=dict)
    relationships: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.current_location_id and self.current_location_id not in self.visited_locations:
            self.visited_locations.append(self.current_location_id)
        for faction in self.factions:
            self.faction_rep.setdefault(faction.id, faction.base_rep)

    def location_index(self) -> Dict[str, Location]:
        return {location.id: location for location in self.locations}

    def location_by_id(self, location_id: str) -> Optional[Location]:
        return self.location_index().get(location_id)

    def active_location(self) -> Optional[Location]:
        if self.current_location_id is None:
            return None
        return self.location_index().get(self.current_location_id)

    def set_flag(self, name: str, value: Any) -> None:
        self.global_flags[name] = value

    def travel_to(self, destination_id: str, *, fast_travel: bool = False) -> bool:
        current = self.active_location()
        destination = self.location_by_id(destination_id)
        if destination is None:
            return False
        if fast_travel and destination_id not in self.visited_locations:
            return False
        if current is not None and not current.is_connected(destination_id):
            if not fast_travel:
                return False

        destination.visited = True
        if destination_id not in self.visited_locations:
            self.visited_locations.append(destination_id)
        if current is not None:
            current.visited = True
            if current.id not in self.visited_locations:
                self.visited_locations.append(current.id)

        self.current_location_id = destination_id
        return True

    def roll_encounter(self, time_of_day: str = "day", rng: Optional[random.Random] = None) -> Optional[str]:
        location = self.active_location()
        if location is None:
            return None
        table = location.encounter_tables.get(time_of_day) or location.encounter_tables.get("any")
        if not table:
            return None
        rng = rng or random.Random()
        if all(isinstance(entry, str) for entry in table):
            return rng.choice(table)

        weighted = [entry for entry in table if isinstance(entry, dict)]
        total_weight = sum(entry.get("weight", 1) for entry in weighted)
        if total_weight <= 0:
            return None
        roll = rng.uniform(0, total_weight)
        cumulative = 0.0
        for entry in weighted:
            cumulative += entry.get("weight", 1)
            if roll <= cumulative:
                return entry.get("encounter_id")
        return None

    def start_encounter(
        self, creatures: List[Creature], difficulty: str = "standard", rng: Optional[random.Random] = None
    ) -> EncounterState:
        rng = rng or random.Random()
        turn_order = roll_initiative(self.pc, creatures, rng)
        participants = [CombatantRef("pc", self.pc.id)] + [CombatantRef("creature", creature.id) for creature in creatures]
        encounter = EncounterState(
            id=f"encounter-{self.current_location_id or 'unknown'}",
            participants=participants,
            turn_order=turn_order,
            difficulty=difficulty,
        )
        self.active_encounter = encounter
        return encounter

    def adjust_faction_rep(self, faction_id: str, delta: int) -> None:
        current = self.faction_rep.get(faction_id, 0)
        self.faction_rep[faction_id] = max(-100, min(100, current + delta))

    def adjust_relationship(self, npc_id: str, delta: int) -> None:
        current = self.relationships.get(npc_id, 0)
        self.relationships[npc_id] = max(-100, min(100, current + delta))

    def step_encounter(self) -> Optional[EncounterState]:
        if self.active_encounter is None:
            return None
        encounter = self.active_encounter
        encounter.active_index = (encounter.active_index + 1) % len(encounter.turn_order)
        if encounter.active_index == 0:
            encounter.round += 1
        return encounter

    def end_encounter(self) -> None:
        self.active_encounter = None

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
            factions=[Faction.from_dict(faction) for faction in data.get("factions", [])],
            quests=[Quest.from_dict(quest) for quest in data.get("quests", [])],
            global_flags=data.get("global_flags", {}),
            current_location_id=data.get("current_location_id"),
            visited_locations=data.get("visited_locations", []),
            active_encounter=(
                None
                if (encounter := data.get("active_encounter")) is None
                else EncounterState.from_dict(encounter)
            ),
            faction_rep=data.get("faction_rep", {}),
            relationships=data.get("relationships", {}),
        )
