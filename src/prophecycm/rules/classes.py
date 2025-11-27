"""Class-related rules and proficiency mappings."""

from __future__ import annotations

from typing import Dict, List

from .abilities import (
    CHARISMA,
    CONSTITUTION,
    DEXTERITY,
    INTELLIGENCE,
    STRENGTH,
    WISDOM,
)

CLASS_SAVE_PROFICIENCIES: Dict[str, List[str]] = {
    "barbarian": [STRENGTH, CONSTITUTION],
    "bard": [DEXTERITY, CHARISMA],
    "cleric": [WISDOM, CHARISMA],
    "druid": [INTELLIGENCE, WISDOM],
    "fighter": [STRENGTH, CONSTITUTION],
    "monk": [STRENGTH, DEXTERITY],
    "paladin": [WISDOM, CHARISMA],
    "ranger": [STRENGTH, DEXTERITY],
    "rogue": [DEXTERITY, INTELLIGENCE],
    "sorcerer": [CONSTITUTION, CHARISMA],
    "warlock": [WISDOM, CHARISMA],
    "wizard": [INTELLIGENCE, WISDOM],
}

__all__ = ["CLASS_SAVE_PROFICIENCIES"]
