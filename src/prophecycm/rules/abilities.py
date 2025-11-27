"""Definitions for the core ability scores used throughout the ruleset."""

from __future__ import annotations

from typing import Dict, List

STRENGTH = "strength"
DEXTERITY = "dexterity"
CONSTITUTION = "constitution"
INTELLIGENCE = "intelligence"
WISDOM = "wisdom"
CHARISMA = "charisma"

ABILITIES: List[str] = [
    STRENGTH,
    DEXTERITY,
    CONSTITUTION,
    INTELLIGENCE,
    WISDOM,
    CHARISMA,
]

ABILITY_DISPLAY_NAMES: Dict[str, str] = {
    STRENGTH: "Strength",
    DEXTERITY: "Dexterity",
    CONSTITUTION: "Constitution",
    INTELLIGENCE: "Intelligence",
    WISDOM: "Wisdom",
    CHARISMA: "Charisma",
}

ABILITY_DESCRIPTIONS: Dict[str, str] = {
    STRENGTH: "Physical power, athletic training, and ability to exert force.",
    DEXTERITY: "Agility, reflexes, balance, and precision.",
    CONSTITUTION: "Health, stamina, and ability to resist hardship.",
    INTELLIGENCE: "Reasoning, memory, and mastery of knowledge.",
    WISDOM: "Perceptiveness, insight, and attunement to the world.",
    CHARISMA: "Force of personality, confidence, and social influence.",
}

__all__ = [
    "STRENGTH",
    "DEXTERITY",
    "CONSTITUTION",
    "INTELLIGENCE",
    "WISDOM",
    "CHARISMA",
    "ABILITIES",
    "ABILITY_DISPLAY_NAMES",
    "ABILITY_DESCRIPTIONS",
]
