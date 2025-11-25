from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.npc import NPC
from prophecycm.characters.player import AbilityScore
from prophecycm.items.item import Equipment, EquipmentSlot, Item


def _slugify(path: Path) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", path.stem.lower())
    return slug.strip("-")


def _extract_number(patterns: Iterable[str], text: str) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError, IndexError):
                continue
    return None


def _parse_abilities(text: str) -> Dict[str, int]:
    ability_map: List[Tuple[str, Iterable[str]]] = [
        ("strength", (r"Strength:?\s*(\d+)", r"STR\s*(\d+)")),
        ("dexterity", (r"Dexterity:?\s*(\d+)", r"DEX\s*(\d+)")),
        ("constitution", (r"Constitution:?\s*(\d+)", r"CON\s*(\d+)")),
        ("intelligence", (r"Intelligence:?\s*(\d+)", r"INT\s*(\d+)")),
        ("wisdom", (r"Wisdom:?\s*(\d+)", r"WIS\s*(\d+)")),
        ("charisma", (r"Charisma:?\s*(\d+)", r"CHA\s*(\d+)")),
    ]

    abilities: Dict[str, int] = {}
    for name, patterns in ability_map:
        if (value := _extract_number(patterns, text)) is not None:
            abilities[name] = value
    return abilities


def _parse_actions(lines: List[str]) -> List[str]:
    actions: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or any(stripped.lower().startswith(prefix) for prefix in ("armor class", "hit points", "speed")):
            continue
        if ":" in stripped:
            candidate = stripped.split(":", 1)[0].strip()
            if candidate and re.match(r"[A-Za-z]", candidate) and len(candidate) <= 60:
                if candidate not in actions:
                    actions.append(candidate)
    return actions


def parse_creature_card(path: Path) -> Creature:
    text = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in text.splitlines()]

    name = next((line.strip() for line in lines if line.strip()), path.stem)
    slug = _slugify(path)

    armor_class = _extract_number((r"Armor Class[:\s]*([0-9]+)", r"AC[:\s]*([0-9]+)"), text) or 10
    hit_points = _extract_number((r"Hit Points[:\s]*([0-9]+)", r"HP[:\s]*~?\s*([0-9]+)"), text) or 0

    dice_match = re.search(r"(\d+)d(\d+)", text)
    level = int(dice_match.group(1)) if dice_match else 1
    hit_die = int(dice_match.group(2)) if dice_match else 6

    role_match = re.search(r"Role:\s*(.+)", text)
    type_match = re.search(r"Type:\s*(.+)", text)
    role = (role_match.group(1) if role_match else (type_match.group(1) if type_match else "unknown")).strip()

    abilities = _parse_abilities(text)
    for ability in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
        abilities.setdefault(ability, 10)

    actions = _parse_actions(lines)

    dex_mod = (abilities.get("dexterity", 10) - 10) // 2
    base_armor_class = armor_class - dex_mod if armor_class - dex_mod >= 0 else armor_class

    creature_payload: Dict[str, object] = {
        "id": f"creature-{slug}",
        "name": name,
        "level": level,
        "role": role,
        "hit_die": hit_die,
        "armor_class": base_armor_class,
        "hit_points": hit_points,
        "abilities": {key: AbilityScore(name=key, score=value).to_dict() for key, value in abilities.items()},
        "actions": [CreatureAction(name=action).to_dict() for action in actions] or [CreatureAction(name="Attack").to_dict()],
    }

    return Creature.from_dict(creature_payload)


def parse_npc_card(path: Path) -> NPC:
    slug = _slugify(path)
    stat_block = parse_creature_card(path)
    stat_block_payload = stat_block.to_dict()
    stat_block_payload["armor_class"] = getattr(stat_block, "_base_armor_class", stat_block.armor_class)
    npc_payload: Dict[str, object] = {
        "id": f"npc-{slug}",
        "archetype": slug,
        "faction_id": "",
        "disposition": "neutral",
        "inventory": [],
        "is_companion": False,
        "stat_block": stat_block_payload,
    }
    return NPC.from_dict(npc_payload)


def _detect_slot(description: str) -> EquipmentSlot:
    lowered = description.lower()
    if "two-hand" in lowered or "longbow" in lowered or "greatsword" in lowered:
        return EquipmentSlot.TWO_HAND
    if "off-hand" in lowered or "shield" in lowered:
        return EquipmentSlot.OFF_HAND
    return EquipmentSlot.MAIN_HAND


def parse_item_card(path: Path) -> Item:
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    name = lines[0] if lines else path.stem
    slug = _slugify(path)

    rarity_match = re.search(r"\b(Common|Uncommon|Rare|Very Rare|Legendary)\b", text, flags=re.IGNORECASE)
    rarity = rarity_match.group(1).lower() if rarity_match else "common"

    item_type = "equipment" if re.search(r"weapon|armor", text, flags=re.IGNORECASE) else "generic"
    slot = _detect_slot(text)

    item_payload: Dict[str, object] = {
        "id": f"item-{slug}",
        "name": name,
        "rarity": rarity,
        "item_type": item_type,
    }

    if item_type == "equipment":
        item_payload.update({
            "slot": slot.value,
            "tags": ["stat-card"],
        })
        return Equipment.from_dict(item_payload)
    return Item.from_dict(item_payload)


__all__ = [
    "parse_creature_card",
    "parse_item_card",
    "parse_npc_card",
]
