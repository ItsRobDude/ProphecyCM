from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import random

from prophecycm.characters import Creature, NPC, PlayerCharacter
from prophecycm.combat.engine import EncounterState, roll_initiative
from prophecycm.core import Serializable
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, ensure_typed_id
from prophecycm.items import Item
from prophecycm.state.party import PartyRoster
from prophecycm.quests import Condition, Quest, QuestEffect
from prophecycm.state.leveling import LevelUpRequest
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
    party: PartyRoster = field(default_factory=PartyRoster)
    global_flags: Dict[str, Any] = field(default_factory=dict)
    reputation: Dict[str, int] = field(default_factory=dict)
    relationships: Dict[str, int] = field(default_factory=dict)
    visited_locations: List[str] = field(default_factory=list)
    current_location_id: Optional[str] = None
    resources: Dict[str, int] = field(default_factory=dict)
    encounters: Dict[str, Dict[str, object]] = field(default_factory=dict)
    transcript: List[Dict[str, object]] = field(default_factory=list)
    level_up_queue: List[LevelUpRequest] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GameState":
        pc = PlayerCharacter.from_dict(data.get("pc", {}))
        visited = [
            ensure_typed_id(loc, expected_prefix="loc", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes)
            for loc in data.get("visited_locations", [])
        ]
        current_location = data.get("current_location_id")
        if current_location is not None:
            current_location = ensure_typed_id(
                current_location,
                expected_prefix="loc",
                allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes,
            )
        return cls(
            timestamp=data.get("timestamp", ""),
            pc=pc,
            npcs=[NPC.from_dict(npc) for npc in data.get("npcs", [])],
            creatures=[Creature.from_dict(creature) for creature in data.get("creatures", [])],
            locations=[Location.from_dict(loc) for loc in data.get("locations", [])],
            factions=[Faction.from_dict(faction) for faction in data.get("factions", [])],
            quests=[Quest.from_dict(quest) for quest in data.get("quests", [])],
            party=PartyRoster.from_dict(data.get("party", {}), default_leader_id=pc.id),
            global_flags=data.get("global_flags", {}),
            reputation=data.get("reputation", {}),
            relationships=data.get("relationships", {}),
            visited_locations=visited,
            current_location_id=current_location,
            resources=data.get("resources", {}),
            encounters=data.get("encounters", {}),
            transcript=list(data.get("transcript", [])),
            level_up_queue=[LevelUpRequest.from_dict(entry) for entry in data.get("level_up_queue", [])],
        )

    def __post_init__(self) -> None:
        self.party.sync_with_pc(self.pc)
        if self.current_location_id and self.current_location_id not in self.visited_locations:
            self.visited_locations.append(self.current_location_id)
        for location in self.locations:
            if getattr(location, "visited", False) and location.id not in self.visited_locations:
                self.visited_locations.append(location.id)

    def _queue_level_up(self, character_id: str, character_type: str, target_level: int) -> None:
        for entry in self.level_up_queue:
            if entry.character_id == character_id and entry.character_type == character_type:
                entry.target_level = max(entry.target_level, target_level)
                return
        self.level_up_queue.append(
            LevelUpRequest(
                character_id=character_id,
                character_type=character_type,
                target_level=target_level,
            )
        )

    def grant_party_xp(self, amount: int, *, difficulty: str = "standard") -> Dict[str, List[int]]:
        """Grant XP to the player and companions, enqueueing manual level-ups.

        Companions with ``auto_level`` enabled will immediately apply their scaling
        templates; others will be added to the ``level_up_queue`` for UI handling.
        """

        leveled: Dict[str, List[int]] = {}

        pc_levels = self.pc.gain_xp(amount)
        if pc_levels:
            leveled[self.pc.id] = pc_levels
            self._queue_level_up(self.pc.id, "pc", self.pc.level)

        for companion in self.npcs:
            levels = companion.gain_xp(amount)
            if not levels:
                continue
            leveled[companion.id] = levels
            if companion.auto_level:
                companion.apply_auto_level(difficulty=difficulty)
            else:
                self._queue_level_up(companion.id, "companion", companion.level)

        return leveled

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

    def set_flag(self, key: str, value: Any) -> None:
        self.global_flags[key] = value

    def get_flag(self, key: str, default: Any = None) -> Any:
        return self.global_flags.get(key, default)

    def adjust_faction_rep(self, faction_id: str, delta: int) -> None:
        self.reputation[faction_id] = self.reputation.get(faction_id, 0) + int(delta)

    def apply_effects(self, effects: QuestEffect) -> None:
        for flag, value in effects.flags.items():
            self.global_flags[flag] = value

        for faction, delta in effects.reputation_changes.items():
            self.adjust_faction_rep(faction, int(delta))

        for npc_id, delta in effects.relationship_changes.items():
            self.relationships[npc_id] = self.relationships.get(npc_id, 0) + int(delta)

        for reward, amount in effects.rewards.items():
            if reward == "xp":
                self.grant_party_xp(int(amount))
            else:
                normalized_amount = int(amount)
                rewards_pool = self.global_flags.setdefault("rewards", {})
                rewards_pool[reward] = rewards_pool.get(reward, 0) + normalized_amount

    def adjust_relationship(self, npc_id: str, delta: int) -> None:
        self.relationships[npc_id] = self.relationships.get(npc_id, 0) + int(delta)

    def grant_item(self, item_payload: Dict[str, object]) -> Item:
        item = Item.from_dict(item_payload)
        self.pc.inventory.append(item)
        return item

    def record_transcript(self, entry: Dict[str, object]) -> None:
        self.transcript.append(entry)

    def get_quest(self, quest_id: str) -> Quest | None:
        return next((quest for quest in self.quests if quest.id == quest_id), None)

    def start_quest(self, quest_payload: Quest | Dict[str, object]) -> Quest:
        quest = quest_payload if isinstance(quest_payload, Quest) else Quest.from_dict(quest_payload)
        existing = self.get_quest(quest.id)
        if existing:
            existing.status = "active"
            if existing.stage < 0:
                existing.stage = 0
            return existing
        quest.status = "active"
        if quest.stage < 0:
            quest.stage = 0
        self.quests.append(quest)
        return quest

    def progress_quest(self, quest_id: str, success: bool = True) -> Quest | None:
        quest = self.get_quest(quest_id)
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

        if 0 <= quest.stage < len(quest.steps):
            quest.current_step = quest.steps[quest.stage].id
        else:
            quest.current_step = None

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

    def _weighted_encounter_pick(self, table: List[object], rng: random.Random) -> Optional[Tuple[str, str]]:
        choices: List[Tuple[float, str, str]] = []
        total_weight = 0.0
        for entry in table:
            if isinstance(entry, dict):
                encounter_id = entry.get("encounter_id") or entry.get("id") or entry.get("encounter")
                weight = float(entry.get("weight", 1))
                difficulty = str(entry.get("difficulty", "standard"))
            else:
                encounter_id = str(entry)
                weight = 1.0
                difficulty = "standard"

            if not encounter_id:
                continue
            total_weight += max(0.0, weight)
            choices.append((total_weight, encounter_id, difficulty))

        if not choices:
            return None

        roll = rng.uniform(0, total_weight)
        for threshold, encounter_id, difficulty in choices:
            if roll <= threshold:
                return encounter_id, difficulty
        return choices[-1][1], choices[-1][2]

    def roll_encounter(
        self,
        context: str = "any",
        connection: Optional[TravelConnection] = None,
        rng: Optional[random.Random] = None,
        difficulty_modifier: float = 1.0,
    ) -> Optional[Tuple[str, Optional[str]]]:
        if rng is None:
            rng = random.Random()
        location = next((loc for loc in self.locations if loc.id == self.current_location_id), None)
        if location is None:
            return None
        table = location.get_encounter_table(context)
        if not table:
            return None
        weighted_table: List[Tuple[str, Optional[str]]] = []
        uses_weights = False
        for entry in table:
            if isinstance(entry, dict):
                encounter_id = entry.get("encounter_id") or entry.get("id")
                weight = int(entry.get("weight", 1))
                uses_weights = True
                weighted_table.extend(
                    [(encounter_id, entry.get("difficulty"))] * max(1, weight)
                )
            else:
                weighted_table.append((str(entry), None))
        choices = weighted_table or [(str(entry), None) for entry in table]
        chance = self._danger_chance(location, connection) * max(0.0, difficulty_modifier)
        if uses_weights:
            chance = 1.0
        if rng.random() <= chance:
            return rng.choice(choices)
        return None

    def travel_to(
        self,
        destination_id: str,
        rng: Optional[random.Random] = None,
        *,
        fast_travel: bool = False,
        encounter_context: str = "travel",
        difficulty_modifier: float = 1.0,
    ) -> Optional[Tuple[str, str]]:
        origin = next((loc for loc in self.locations if loc.id == self.current_location_id), None)
        if origin is None:
            raise ValueError("Current location is not set")

        connection = origin.get_connection(destination_id)
        fast_travel_allowed = self.global_flags.get("fast_travel_unlocked", False) or origin.travel_rules.get(
            "allow_fast_travel", False
        )

        if fast_travel and not fast_travel_allowed:
            raise ValueError("Fast travel is not unlocked for this location")

        if fast_travel and destination_id not in self.visited_locations:
            raise ValueError("Cannot fast travel to an unvisited location")

        if connection is None and fast_travel:
            connection = TravelConnection(
                target=destination_id,
                travel_time=int(origin.travel_rules.get("fast_travel_time", 0)),
                danger=float(origin.travel_rules.get("fast_travel_danger", 0.0)),
            )

        if connection is None:
            raise ValueError(f"No travel path from {origin.id} to {destination_id}")

        requirements = [Condition.from_dict(req) for req in connection.requirements]
        if not self._conditions_met(requirements):
            raise ValueError(f"Travel requirements not met for path to {destination_id}")

        self._apply_travel_costs(connection)
        self.advance_time(hours=connection.travel_time)
        encounter = self.roll_encounter(encounter_context, connection=connection, rng=rng, difficulty_modifier=difficulty_modifier)
        self.current_location_id = destination_id
        if destination_id not in self.visited_locations:
            self.visited_locations.append(destination_id)
        return encounter

    def _apply_travel_costs(self, connection: TravelConnection) -> None:
        """Apply simple travel costs such as time or resource drain."""

        time_cost = max(0, int(connection.travel_time))
        if time_cost:
            stamina = self.resources.get("stamina", 0)
            self.resources["stamina"] = max(0, stamina - time_cost)
        for resource, cost in connection.resource_costs.items():
            current = self.resources.get(resource, 0)
            self.resources[resource] = max(0, current - int(cost))

    def _scale_creature_for_difficulty(self, creature: Creature, difficulty: str) -> None:
        multiplier = {"easy": 0.9, "standard": 1.0, "hard": 1.2, "deadly": 1.4}.get(difficulty, 1.0)
        creature.hit_points = max(1, int(creature.hit_points * multiplier))
        if creature.current_hit_points is None:
            creature.current_hit_points = creature.hit_points
        creature.current_hit_points = min(creature.current_hit_points, creature.hit_points)

    def start_encounter(
        self,
        encounter: str | Tuple[str, str],
        difficulty: Optional[str] = None,
        rng: Optional[random.Random] = None,
        allies: Optional[List[Creature]] = None,
    ) -> EncounterState:
        rng = rng or random.Random()
        encounter_id, rolled_difficulty = (encounter if isinstance(encounter, tuple) else (encounter, None))
        encounter_def = self.encounters.get(encounter_id, {})

        creatures: List[Creature] = []
        creature_ids = encounter_def.get("creatures", encounter_def.get("creature_ids", []))
        active_difficulty = difficulty or rolled_difficulty or encounter_def.get("difficulty", "standard")
        for creature_id in creature_ids:
            template = next((c for c in self.creatures if c.id == creature_id), None)
            if template is None:
                continue
            combatant = deepcopy(template)
            self._scale_creature_for_difficulty(combatant, active_difficulty)
            creatures.append(combatant)

        turn_order = roll_initiative(self.pc, creatures, rng, allies=allies)
        participants = [entry.ref for entry in turn_order]
        return EncounterState(
            id=encounter_id,
            participants=participants,
            turn_order=turn_order,
            difficulty=active_difficulty,
            meta={
                "creatures": creatures,
                "allies": allies or [],
                "xp": encounter_def.get("xp", 0),
                "loot": encounter_def.get("loot", {}),
            },
        )

    def complete_encounter(self, encounter_state: EncounterState, victory: bool = True) -> None:
        creatures = encounter_state.meta.get("creatures", [])
        for creature in creatures:
            existing = next((c for c in self.creatures if c.id == creature.id), None)
            if existing:
                existing.hit_points = creature.hit_points
                existing.current_hit_points = creature.current_hit_points
                existing.is_alive = creature.is_alive

        if not victory:
            return

        xp_reward = int(encounter_state.meta.get("xp", 0))
        if xp_reward:
            self.grant_party_xp(xp_reward)

        loot = encounter_state.meta.get("loot", {})
        for item, amount in loot.items():
            rewards_pool = self.global_flags.setdefault("rewards", {})
            rewards_pool[item] = rewards_pool.get(item, 0) + int(amount)
