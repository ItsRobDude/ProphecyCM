from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from prophecycm.combat.engine import EncounterState
from prophecycm.core import Serializable
from prophecycm.state.game_state import GameState


class GameMode(str, Enum):
    EXPLORATION = "exploration"
    DIALOGUE = "dialogue"
    COMBAT = "combat"


@dataclass
class GameSession(Serializable):
    """Encapsulates a running game session and its current activity state."""

    game_state: GameState
    mode: GameMode = GameMode.EXPLORATION
    active_dialogue_id: Optional[str] = None
    active_encounter: Optional[EncounterState] = None

    @classmethod
    def start_new_game(cls, seed_state: GameState | Dict[str, object]) -> "GameSession":
        """Begin a new game from a seed :class:`GameState` or raw payload."""

        game_state = seed_state if isinstance(seed_state, GameState) else GameState.from_dict(seed_state)
        return cls(game_state=game_state, mode=GameMode.EXPLORATION)

    @classmethod
    def load_game(cls, save_payload: Any) -> "GameSession":
        """Restore a session from a saved payload, preserving session metadata."""

        if isinstance(save_payload, cls):
            return save_payload

        if isinstance(save_payload, dict):
            payload: Dict[str, object] = save_payload
        elif hasattr(save_payload, "to_dict"):
            payload = save_payload.to_dict()
        else:
            raise TypeError("Unsupported save payload type for GameSession.load_game")

        raw_state = payload.get("game_state", payload)
        game_state = raw_state if isinstance(raw_state, GameState) else GameState.from_dict(raw_state)

        mode_value = payload.get("mode", GameMode.EXPLORATION.value)
        try:
            mode = GameMode(mode_value)
        except ValueError:
            mode = GameMode.EXPLORATION

        active_encounter_payload = payload.get("active_encounter")
        active_encounter = (
            EncounterState.from_dict(active_encounter_payload)
            if isinstance(active_encounter_payload, dict)
            else active_encounter_payload
        )

        return cls(
            game_state=game_state,
            mode=mode,
            active_dialogue_id=payload.get("active_dialogue_id"),
            active_encounter=active_encounter,
        )

    def enter_location(
        self,
        location_id: str,
        *,
        fast_travel: bool = False,
        encounter_context: str = "travel",
        difficulty_modifier: float = 1.0,
    ) -> Optional[tuple[str, Optional[str]]]:
        """Travel to a new location, resetting active session pointers."""

        self._validate_location(location_id)
        if self.game_state.current_location_id is None or self.game_state.current_location_id == location_id:
            self.game_state.current_location_id = location_id
            if location_id not in self.game_state.visited_locations:
                self.game_state.visited_locations.append(location_id)
            self._reset_to_exploration()
            return None

        encounter = self.game_state.travel_to(
            destination_id=location_id,
            fast_travel=fast_travel,
            encounter_context=encounter_context,
            difficulty_modifier=difficulty_modifier,
        )
        self._reset_to_exploration()
        return encounter

    def start_dialogue(self, npc_id: str) -> str:
        """Enter dialogue mode with a specific NPC."""

        self._validate_npc(npc_id)
        self.mode = GameMode.DIALOGUE
        self.active_dialogue_id = npc_id
        self.active_encounter = None
        return npc_id

    def start_combat(self, encounter_id: str, difficulty: Optional[str] = None) -> EncounterState:
        """Start a combat encounter and set the session into combat mode."""

        self._validate_encounter(encounter_id)
        encounter_state = self.game_state.start_encounter(encounter_id, difficulty=difficulty)
        self.mode = GameMode.COMBAT
        self.active_encounter = encounter_state
        self.active_dialogue_id = None
        return encounter_state

    def save_state(self) -> Dict[str, object]:
        """Serialize the session, preserving mode and active pointers."""

        return self.to_dict()

    def to_dict(self) -> Dict[str, object]:  # type: ignore[override]
        payload = super().to_dict()
        payload["mode"] = self.mode.value
        if self.active_encounter is not None:
            payload["active_encounter"] = self.active_encounter.to_dict()
        return payload

    def _validate_location(self, location_id: str) -> None:
        if not any(location.id == location_id for location in self.game_state.locations):
            raise ValueError(f"Unknown location id: {location_id}")

    def _validate_npc(self, npc_id: str) -> None:
        if not any(npc.id == npc_id for npc in self.game_state.npcs):
            raise ValueError(f"Unknown NPC id: {npc_id}")

    def _validate_encounter(self, encounter_id: str) -> None:
        if encounter_id not in self.game_state.encounters:
            raise ValueError(f"Unknown encounter id: {encounter_id}")

    def _reset_to_exploration(self) -> None:
        self.mode = GameMode.EXPLORATION
        self.active_dialogue_id = None
        self.active_encounter = None
