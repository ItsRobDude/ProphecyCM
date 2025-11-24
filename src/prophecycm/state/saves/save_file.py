from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from prophecycm.core import Serializable
from prophecycm.state.game_state import GameState


@dataclass
class SaveFile(Serializable):
    slot: int
    metadata: Dict[str, Any]
    game_state: GameState
    version: str = "0.1.0"
    schema_hash: str = "dev"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot": self.slot,
            "metadata": self.metadata,
            "game_state": self.game_state.to_dict(),
            "version": self.version,
            "schema_hash": self.schema_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveFile":
        return cls(
            slot=int(data.get("slot", 0)),
            metadata=data.get("metadata", {}),
            game_state=GameState.from_dict(data.get("game_state", {})),
            version=data.get("version", "0.1.0"),
            schema_hash=data.get("schema_hash", "dev"),
        )
