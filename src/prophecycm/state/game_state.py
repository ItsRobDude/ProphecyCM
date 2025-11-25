from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import random

from prophecycm.characters import Creature, NPC, PlayerCharacter
from prophecycm.core import Serializable
from prophecycm.quests import Condition, Quest, QuestEffect
from prophecycm.world import Faction, Location, TravelConnection


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
    reputation: Dict[str, int] = field(default_factory=dict)
    relationships: Dict[str, int] = field(default_factory=dict)
    visited_locations: List[str] = field(default_factory=list)
    current_location_id: Optional[str] = None

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
            reputation=data.get("reputation", {}),
            relationships=data.get("relationships", {}),
            visited_locations=list(data.get("visited_locations", [])),
            current_location_id=data.get("current_location_id"),
        )

    def _parse_time(self) -> datetime:
        if self.timestamp:
            try:
                return datetime.fromisoformat(self.timestamp)
            except ValueError:
                pass
        return datetime.now()

    def advance_time(self, hours: int = 0, minutes: int = 0) -> None:
        current = self._parse_time()
        updated = current + timedelta(hours=hours, minutes=minutes)
        self.timestamp = updated.isoformat()

    def set_flag(self, key: str, value: Any) -> None:
        """Set a global flag on the game state."""

        self.global_flags[key] = value

    def _compare(self, lhs: Any, comparator: str, rhs: Any) -> bool:
        if comparator == "==":
            return lhs == rhs
        if comparator == "!=":
            return lhs != rhs
        if comparator == ">=":
            return lhs >= rhs
        if comparator == "<=":
            return lhs <= rhs
        if comparator == ">":
            return lhs > rhs
        if comparator == "<":
            return lhs < rhs
        return False

    def evaluate_condition(self, condition: Condition) -> bool:
        if condition.subject == "flag":
            value = self.global_flags.get(condition.key)
        elif condition.subject == "reputation":
            value = self.reputation.get(condition.key, 0)
        elif condition.subject == "quest_stage":
            quest = next((q for q in self.quests if q.id == condition.key), None)
            value = quest.stage if quest else -1
        else:
            value = None
        return self._compare(value, condition.comparator, condition.value)

    def _conditions_met(self, conditions: List[Condition]) -> bool:
        return all(self.evaluate_condition(cond) for cond in conditions)

    def apply_effects(self, effects: QuestEffect) -> None:
        for flag, value in effects.flags.items():
            self.global_flags[flag] = value

        for faction, delta in effects.reputation_changes.items():
            self.reputation[faction] = self.reputation.get(faction, 0) + int(delta)

        for npc_id, delta in effects.relationship_changes.items():
            self.relationships[npc_id] = self.relationships.get(npc_id, 0) + int(delta)

        for reward, amount in effects.rewards.items():
            if reward == "xp":
                self.pc.xp += int(amount)
            else:
                rewards_pool = self.global_flags.setdefault("rewards", {})
                rewards_pool[reward] = rewards_pool.get(reward, 0) + int(amount)

    def progress_quest(self, quest_id: str, success: bool = True) -> Quest | None:
        quest = next((quest for quest in self.quests if quest.id == quest_id), None)
        if quest is None:
            return None

        step = quest.get_current_step()
        if step and not self._conditions_met(step.entry_conditions):
            raise ValueError(f"Entry conditions not met for step {step.id}")

        if step:
            effects = step.success_effects if success else step.failure_effects
            self.apply_effects(effects)
            next_step_id = step.success_next if success else step.failure_next
            next_index = quest.find_step_index(next_step_id)
            if next_index is not None:
                quest.stage = next_index
            else:
                quest.stage += 1
        else:
            quest.stage += 1

        if quest.stage >= len(quest.steps):
            quest.status = "completed" if success else "failed"
            quest.current_step = None
        elif 0 <= quest.stage < len(quest.steps):
            quest.current_step = quest.steps[quest.stage].id
        return quest

    def apply_quest_step(self, quest_id: str, success: bool = True) -> Quest | None:
        """Compatibility wrapper for progressing a quest by one step."""

        return self.progress_quest(quest_id, success=success)

    def _danger_chance(self, location: Location, connection: Optional[TravelConnection]) -> float:
        base = {"low": 0.2, "medium": 0.5, "high": 0.8}.get(location.danger_level, 0.2)
        if connection:
            base *= max(0.1, connection.danger)
        return min(1.0, base)

    def roll_encounter(
        self, context: str = "any", connection: Optional[TravelConnection] = None, rng: Optional[random.Random] = None
    ) -> Optional[str]:
        if rng is None:
            rng = random.Random()
        location = next((loc for loc in self.locations if loc.id == self.current_location_id), None)
        if location is None:
            return None
        table = location.get_encounter_table(context)
        if not table:
            return None
        chance = self._danger_chance(location, connection)
        if rng.random() <= chance:
            return rng.choice(table)
        return None

    def travel_to(self, destination_id: str, rng: Optional[random.Random] = None) -> Optional[str]:
        origin = next((loc for loc in self.locations if loc.id == self.current_location_id), None)
        if origin is None:
            raise ValueError("Current location is not set")

        connection = origin.get_connection(destination_id)
        if connection is None:
            raise ValueError(f"No travel path from {origin.id} to {destination_id}")

        requirements = [Condition.from_dict(req) for req in connection.requirements]
        if not self._conditions_met(requirements):
            raise ValueError(f"Travel requirements not met for path to {destination_id}")

        self.advance_time(hours=connection.travel_time)
        encounter = self.roll_encounter("travel", connection=connection, rng=rng)
        self.current_location_id = destination_id
        if destination_id not in self.visited_locations:
            self.visited_locations.append(destination_id)
        return encounter
