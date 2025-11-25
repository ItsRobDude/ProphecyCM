from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from prophecycm.core import Serializable
from prophecycm.state.leveling import LevelUpRequest

if TYPE_CHECKING:
    from prophecycm.state import GameState


@dataclass
class CompanionLevelSettings(Serializable):
    id: str
    level: int
    xp: int
    auto_level: bool = True


@dataclass
class LevelUpScreenConfig(Serializable):
    pc_level: int
    pc_xp: int
    companions: List[CompanionLevelSettings] = field(default_factory=list)
    pending: List[LevelUpRequest] = field(default_factory=list)

    @classmethod
    def from_game_state(cls, state: "GameState") -> "LevelUpScreenConfig":
        return cls(
            pc_level=state.pc.level,
            pc_xp=state.pc.xp,
            companions=[
                CompanionLevelSettings(
                    id=npc.id,
                    level=npc.level,
                    xp=npc.xp,
                    auto_level=npc.auto_level,
                )
                for npc in state.npcs
            ],
            pending=[
                entry if isinstance(entry, LevelUpRequest) else LevelUpRequest.from_dict(entry)
                for entry in state.level_up_queue
            ],
        )


__all__ = ["CompanionLevelSettings", "LevelUpScreenConfig"]
