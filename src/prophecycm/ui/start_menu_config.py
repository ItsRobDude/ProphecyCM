from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable
from prophecycm.state import SaveFile
from prophecycm.characters.creation import CharacterCreationConfig


@dataclass
class StartMenuOption(Serializable):
    """A selectable starting point in the title menu."""

    id: str
    label: str
    description: str
    save_file: SaveFile | None = None
    metadata: Dict[str, object] = field(default_factory=dict)
    timestamp: str = ""
    pc: Dict[str, object] = field(default_factory=dict)
    npc_ids: List[str] = field(default_factory=list)
    location_ids: List[str] = field(default_factory=list)
    quests: List[Dict[str, object]] = field(default_factory=list)
    global_flags: Dict[str, object] = field(default_factory=dict)
    current_location_id: str | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StartMenuOption":
        raw_save_file = data.get("save_file")
        return cls(
            id=data["id"],
            label=data.get("label", ""),
            description=data.get("description", ""),
            save_file=SaveFile.from_dict(raw_save_file) if isinstance(raw_save_file, dict) else None,
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", ""),
            pc=data.get("pc", {}),
            npc_ids=list(data.get("npc_ids", [])),
            location_ids=list(data.get("location_ids", [])),
            quests=list(data.get("quests", [])),
            global_flags=data.get("global_flags", {}),
            current_location_id=data.get("current_location_id"),
        )


@dataclass
class StartMenuConfig(Serializable):
    """Configuration for the start menu, including available save slots."""

    title: str
    subtitle: str = ""
    options: List[StartMenuOption] = field(default_factory=list)
    character_creation: CharacterCreationConfig | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StartMenuConfig":
        return cls(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            options=[StartMenuOption.from_dict(option) for option in data.get("options", [])],
            character_creation=(
                CharacterCreationConfig.from_dict(data["character_creation"]) if data.get("character_creation") else None
            ),
        )

