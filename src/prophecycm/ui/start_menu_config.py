from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable
from prophecycm.state import SaveFile


@dataclass
class StartMenuOption(Serializable):
    """A selectable starting point in the title menu."""

    id: str
    label: str
    description: str
    save_file: SaveFile
    metadata: Dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StartMenuOption":
        return cls(
            id=data["id"],
            label=data.get("label", ""),
            description=data.get("description", ""),
            save_file=SaveFile.from_dict(data.get("save_file", {})),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StartMenuConfig(Serializable):
    """Configuration for the start menu, including available save slots."""

    title: str
    subtitle: str = ""
    options: List[StartMenuOption] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StartMenuConfig":
        return cls(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            options=[StartMenuOption.from_dict(option) for option in data.get("options", [])],
        )

