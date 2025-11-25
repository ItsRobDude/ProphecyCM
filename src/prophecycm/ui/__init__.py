from __future__ import annotations

from prophecycm.ui.level_up_config import CompanionLevelSettings, LevelUpScreenConfig
from prophecycm.ui.start_menu_config import StartMenuConfig, StartMenuOption


class GameUI:
    """Placeholder UI surface for future expansion."""

    def render_summary(self, message: str) -> str:
        return f"[UI] {message}"


__all__ = [
    "CompanionLevelSettings",
    "GameUI",
    "LevelUpScreenConfig",
    "StartMenuConfig",
    "StartMenuOption",
]
