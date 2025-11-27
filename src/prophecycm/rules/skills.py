"""Central registry of 5e-style skills and their governing abilities."""

from __future__ import annotations

from typing import Dict, List

from .abilities import CHARISMA, DEXTERITY, INTELLIGENCE, STRENGTH, WISDOM

SKILL_IDS: List[str] = [
    "acrobatics",
    "animal_handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight_of_hand",
    "stealth",
    "survival",
]

SKILL_TO_ABILITY: Dict[str, str] = {
    "acrobatics": DEXTERITY,
    "animal_handling": WISDOM,
    "arcana": INTELLIGENCE,
    "athletics": STRENGTH,
    "deception": CHARISMA,
    "history": INTELLIGENCE,
    "insight": WISDOM,
    "intimidation": CHARISMA,
    "investigation": INTELLIGENCE,
    "medicine": WISDOM,
    "nature": INTELLIGENCE,
    "perception": WISDOM,
    "performance": CHARISMA,
    "persuasion": CHARISMA,
    "religion": INTELLIGENCE,
    "sleight_of_hand": DEXTERITY,
    "stealth": DEXTERITY,
    "survival": WISDOM,
}

__all__ = ["SKILL_IDS", "SKILL_TO_ABILITY"]
