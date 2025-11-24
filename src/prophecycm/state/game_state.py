from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from prophecycm.characters import NPC, PlayerCharacter
from prophecycm.core import Serializable
from prophecycm.quests import Quest
from prophecycm.world import Location


@dataclass
class GameState(Serializable):
    timestamp: str
    pc: PlayerCharacter
    npcs: List[NPC] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    quests: List[Quest] = field(default_factory=list)
    global_flags: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GameState":
        return cls(
            timestamp=data.get("timestamp", ""),
            pc=PlayerCharacter.from_dict(data.get("pc", {})),
            npcs=[NPC.from_dict(npc) for npc in data.get("npcs", [])],
            locations=[Location.from_dict(loc) for loc in data.get("locations", [])],
            quests=[Quest.from_dict(quest) for quest in data.get("quests", [])],
            global_flags=data.get("global_flags", {}),
        )
