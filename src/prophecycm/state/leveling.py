from __future__ import annotations

from dataclasses import dataclass

from prophecycm.core import Serializable


@dataclass
class LevelUpRequest(Serializable):
    """Represents a pending level-up that requires player input."""

    character_id: str
    character_type: str
    target_level: int

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "LevelUpRequest":
        return cls(
            character_id=str(data.get("character_id", "")),
            character_type=str(data.get("character_type", "")),
            target_level=int(data.get("target_level", 0)),
        )


__all__ = ["LevelUpRequest"]
