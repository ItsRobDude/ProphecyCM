from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.characters.creation import CharacterCreationConfig
from prophecycm.core import Serializable
from prophecycm.state import SaveFile


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
class ContentWarning(Serializable):
    """Safety warning surfaced before beginning a new game."""

    title: str
    message: str
    bullet_points: List[str] = field(default_factory=list)
    accept_label: str = "Continue"
    decline_label: str = "Back"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ContentWarning":
        return cls(
            title=data.get("title", ""),
            message=data.get("message", ""),
            bullet_points=list(data.get("bullet_points", [])),
            accept_label=data.get("accept_label", "Continue"),
            decline_label=data.get("decline_label", "Back"),
        )


@dataclass
class StartMenuNewGameFlow(Serializable):
    """Context for launching a new game from the start menu."""

    label: str
    description: str = ""
    content_warning: ContentWarning | None = None
    character_creation: CharacterCreationConfig | None = None

    def require_character_creation(self) -> CharacterCreationConfig:
        if not self.character_creation:
            raise ValueError("Start menu missing character creation configuration for new game flow")
        return self.character_creation


@dataclass
class StartMenuConfig(Serializable):
    """Configuration for the start menu, including available save slots."""

    title: str
    subtitle: str = ""
    options: List[StartMenuOption] = field(default_factory=list)
    character_creation: CharacterCreationConfig | None = None
    new_game_label: str = "New Game"
    new_game_description: str = ""
    content_warning: ContentWarning | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StartMenuConfig":
        warning = data.get("content_warning")
        return cls(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            options=[StartMenuOption.from_dict(option) for option in data.get("options", [])],
            character_creation=(
                CharacterCreationConfig.from_dict(data["character_creation"]) if data.get("character_creation") else None
            ),
            new_game_label=data.get("new_game_label", "New Game"),
            new_game_description=data.get("new_game_description", ""),
            content_warning=ContentWarning.from_dict(warning) if isinstance(warning, dict) else None,
        )

    def build_new_game_flow(self) -> StartMenuNewGameFlow:
        """Compose a ready-to-render new game block, including the warning modal."""

        return StartMenuNewGameFlow(
            label=self.new_game_label,
            description=self.new_game_description,
            content_warning=self.content_warning,
            character_creation=self.character_creation,
        )
