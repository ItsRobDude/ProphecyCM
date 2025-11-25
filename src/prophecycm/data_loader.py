"""Utilities for turning authored stat cards into runtime objects.

This module provides lightweight, unit-level parsing helpers that translate the
prose-heavy stat card files in :mod:`stat_cards/` into structured dictionaries
that satisfy the game's JSON Schemas. The functions intentionally keep the
parsers permissive; they only extract well-defined, schema-supported fields and
surface validation errors with the originating file to make content iteration
fast.

Parsing expectations (examples)
-------------------------------
Creature / NPC stat cards (``*.txt``)
    Expected sections (case-insensitive):

    * Title line with the creature's display name.
    * Optional metadata lines: ``Role:``, ``Challenge Rating:``, ``Type:``,
      ``Armor Class:``, ``Hit Points:``, ``Speed:``, ``Saving Throws:``, and
      ``Skills:``.
    * ``Ability Scores`` block with lines like ``Strength: 15 (+2)`` or
      ``STR 10 (+0)``. These map to ``abilities.<name>.score`` in the
      :mod:`~docs.data-model.schemas.Creature` schema.
    * ``Actions`` / ``Attacks & Actions`` section, where each action is written
      as ``<Name>:`` followed by one or more description lines. The parser looks
      for ``+X to hit`` and ``XdY`` snippets to fill the
      ``CreatureAction.to_hit_bonus`` and ``CreatureAction.damage_dice`` fields.
    * ``Special Abilities`` or ``Traits`` section to populate ``traits``.

    ``load_creature`` returns a :class:`prophecycm.characters.creature.Creature`
    and ``load_npc`` wraps the parsed creature as ``stat_block`` inside an
    :class:`prophecycm.characters.npc.NPC`. Missing numeric fields default to a
    survivable baseline (level 1, d8 hit die, AC 10, HP 1) before validation.

Items (``*.txt``)
    * The first non-empty line is treated as ``name``.
    * A header line containing a rarity keyword (Common/Uncommon/Rare/Very
      Rare/Legendary) and an item category such as ``Weapon (Longbow)`` is
      mapped to ``rarity`` and ``item_type`` (``equipment`` when weapon/armor
      keywords are present, otherwise ``generic``).
    * Lines starting with ``Damage:``, ``Properties:``, or indented feature
      names are captured as free-form ``tags`` and ``modifiers`` snippets, which
      can be refined later.

Locations / JSON configs
    * JSON files are validated against their respective schemas before being
      passed to ``from_dict`` constructors. ``load_location`` expects the
      ``Location`` schema, while ``load_item`` also accepts JSON payloads that
      already match ``Item``/``Equipment``/``Consumable`` schemas.

The parsing helpers are intentionally simple so that they can be unit-tested in
isolation: pass a multi-line string to ``parse_creature_stat_block`` or
``parse_item_card`` and assert on the resulting dictionaries before constructing
objects. Validation failures always mention the offending file path to aid rapid
content iteration.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import jsonschema

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.npc import NPC
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, build_id, ensure_typed_id, normalize_slug
from prophecycm.items.item import Item
from prophecycm.world.location import Location


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "docs" / "data-model" / "schemas"

ABILITY_ALIASES = {
    "str": "strength",
    "strength": "strength",
    "dex": "dexterity",
    "dexterity": "dexterity",
    "con": "constitution",
    "constitution": "constitution",
    "int": "intelligence",
    "intelligence": "intelligence",
    "wis": "wisdom",
    "wisdom": "wisdom",
    "cha": "charisma",
    "charisma": "charisma",
}

RARITY_KEYWORDS = [
    "common",
    "uncommon",
    "rare",
    "very rare",
    "legendary",
    "artifact",
]


def _normalize_and_register(value: str, *, kind: str) -> str:
    typed = ensure_typed_id(value, expected_prefix=kind)
    return DEFAULT_ID_REGISTRY.register(typed, expected_prefix=kind)


@dataclass
class ParsedSection:
    name: str
    lines: List[str]


def _load_schema(schema_name: str) -> Dict[str, object]:
    schema_path = SCHEMA_ROOT / f"{schema_name}.json"
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_payload(payload: Dict[str, object], *, schema: str, source: Path) -> None:
    validator = jsonschema.Draft2020Validator(_load_schema(schema))
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        messages = [f"{source}: {error.message} (path={'/'.join(map(str, error.path)) or '<root>'})" for error in errors]
        raise jsonschema.ValidationError("; ".join(messages))


def _split_sections(lines: Iterable[str]) -> List[ParsedSection]:
    sections: List[ParsedSection] = []
    current = ParsedSection(name="root", lines=[])
    heading_pattern = re.compile(r"^[A-Za-z \-&']+:?$")
    for raw in lines:
        line = raw.rstrip()
        if heading_pattern.match(line.strip()):
            if current.lines:
                sections.append(current)
            current = ParsedSection(name=line.strip().rstrip(":"), lines=[])
        else:
            current.lines.append(line)
    if current.lines:
        sections.append(current)
    return sections


def _extract_numeric(pattern: str, text: str, default: int = 0) -> int:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else default


def _parse_abilities(lines: Iterable[str]) -> Dict[str, Dict[str, object]]:
    abilities: Dict[str, Dict[str, object]] = {}
    ability_pattern = re.compile(r"^(?P<name>[A-Za-z]{3,9})[:\s]+(?P<score>-?\d+)")
    for line in lines:
        match = ability_pattern.search(line.strip())
        if not match:
            continue
        raw_name = match.group("name").lower()
        name = ABILITY_ALIASES.get(raw_name)
        if not name:
            continue
        score = int(match.group("score"))
        abilities[name] = {"name": name, "score": score}
    return abilities


def _parse_actions(lines: Iterable[str]) -> List[Dict[str, object]]:
    actions: List[Dict[str, object]] = []
    current_name: Optional[str] = None
    buffer: List[str] = []

    def flush() -> None:
        if current_name:
            actions.append(_action_from_block(current_name, buffer))

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[A-Za-z].*:$", stripped):
            flush()
            current_name = stripped.rstrip(":")
            buffer = []
        else:
            buffer.append(stripped)
    flush()
    return actions or [CreatureAction(name="Strike").to_dict()]


def _action_from_block(name: str, lines: List[str]) -> Dict[str, object]:
    text = " ".join(lines)
    to_hit = _extract_numeric(r"\+(\d+)\s*to hit", text, default=0)
    damage_match = re.search(r"(\d+d\d+)(?:\s*[+−-]\s*(\d+))?", text)
    damage_dice = damage_match.group(1) if damage_match else "1d6"
    damage_bonus = int(damage_match.group(2)) if damage_match and damage_match.group(2) else 0
    return CreatureAction(
        name=name,
        to_hit_bonus=to_hit,
        damage_dice=damage_dice,
        damage_bonus=damage_bonus,
    ).to_dict()


def _parse_traits(lines: Iterable[str]) -> List[str]:
    traits: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(":"):
            continue
        traits.append(stripped)
    return traits


def parse_creature_stat_block(text: str, *, default_id: str) -> Dict[str, object]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    name = lines[0].strip() if lines else default_id
    identifier = _normalize_and_register(default_id or name, kind="creature")
    armor_class = _extract_numeric(r"Armor Class[:\s]+(\d+)", text, default=10)
    hit_points = _extract_numeric(r"Hit Points[:\s]+(\d+)", text, default=1)
    speed = _extract_numeric(r"Speed[:\s]+(\d+)", text, default=30)
    hit_die = _extract_numeric(r"(\d+)d(\d+)", text, default=8)
    role_match = re.search(r"Role[:\s]+([^\n]+)", text, flags=re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else ""

    sections = _split_sections(lines[1:]) if len(lines) > 1 else []
    abilities: Dict[str, Dict[str, object]] = {}
    actions: List[Dict[str, object]] = []
    traits: List[str] = []

    for section in sections:
        normalized = section.name.lower()
        if "ability" in normalized:
            abilities.update(_parse_abilities(section.lines))
        elif "action" in normalized:
            actions.extend(_parse_actions(section.lines))
        elif "special" in normalized or "trait" in normalized:
            traits.extend(_parse_traits(section.lines))

    if not abilities:
        unique_names = {name for name in ABILITY_ALIASES.values() if len(name) > 3}
        abilities = {name: {"name": name, "score": 10} for name in sorted(unique_names)}

    return {
        "id": identifier,
        "name": name,
        "level": _extract_numeric(r"Challenge Rating[:\s]+(\d+)", text, default=1),
        "role": role or "creature",
        "hit_die": hit_die,
        "armor_class": armor_class,
        "abilities": abilities,
        "actions": actions or [CreatureAction(name="Strike").to_dict()],
        "traits": traits,
        "hit_points": hit_points,
        "speed": speed,
        "alignment": _extract_alignment(text),
    }


def _extract_alignment(text: str) -> str:
    alignment_match = re.search(r"(lawful|neutral|chaotic)\s+(good|neutral|evil)", text, flags=re.IGNORECASE)
    return alignment_match.group(0).lower() if alignment_match else ""


def parse_item_card(text: str, *, default_id: str) -> Dict[str, object]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Item card is empty")
    name = lines[0]
    identifier = _normalize_and_register(default_id or name, kind="item")
    header = lines[1].lower() if len(lines) > 1 else ""
    rarity = next((word for word in RARITY_KEYWORDS if word in header), "common")
    item_type = "equipment" if any(keyword in header for keyword in ["weapon", "armor", "shield"]) else "generic"

    tags: List[str] = []
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            tags.append(f"{key.strip()}={value.strip()}")
        elif line:
            tags.append(line)

    return {
        "id": identifier,
        "name": name,
        "rarity": rarity,
        "item_type": item_type,
        "tags": tags,
    }


def load_creature(stat_path: Path | str) -> Creature:
    source = Path(stat_path)
    text = source.read_text(encoding="utf-8")
    payload = parse_creature_stat_block(text, default_id=source.stem)
    _validate_payload(payload, schema="Creature", source=source)
    return Creature.from_dict(payload)


def load_npc(stat_path: Path | str, *, archetype: str = "unique", faction: str = "neutral") -> NPC:
    source = Path(stat_path)
    creature = load_creature(source)
    payload = {
        "id": _normalize_and_register(source.stem, kind="npc"),
        "archetype": archetype,
        "faction_id": faction,
        "disposition": "neutral",
        "stat_block": creature.to_dict(),
        "inventory": [],
        "inventory_item_ids": [],
        "quest_hooks": [],
    }
    _validate_payload(payload, schema="NPC", source=source)
    return NPC.from_dict(payload)


def load_item(json_or_text_path: Path | str) -> Item:
    source = Path(json_or_text_path)
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
    else:
        payload = parse_item_card(source.read_text(encoding="utf-8"), default_id=source.stem)
    payload["id"] = _normalize_and_register(payload.get("id", source.stem), kind="item")
    _validate_payload(payload, schema="Item", source=source)
    return Item.from_dict(payload)


def load_location(json_path: Path | str) -> Location:
    source = Path(json_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["id"] = _normalize_and_register(payload.get("id", source.stem), kind="loc")
    _validate_payload(payload, schema="Location", source=source)
    return Location.from_dict(payload)


def load_resource(path: Path | str):
    source = Path(path)
    if source.is_dir():
        raise ValueError(f"Cannot load directory: {source}")

    lower_name = source.name.lower()
    if "creature" in source.parts or source.parent.name == "creatures":
        return load_creature(source)
    if "npc" in source.parts or source.parent.name == "prophecy_npc":
        return load_npc(source)
    if "item" in source.parts or source.parent.name == "items":
        return load_item(source)
    if lower_name.endswith(".json"):
        # Try to resolve based on schema availability
        payload = json.loads(source.read_text(encoding="utf-8"))
        if "biome" in payload and "connections" in payload:
            _validate_payload(payload, schema="Location", source=source)
            return Location.from_dict(payload)
        if "item_type" in payload:
            _validate_payload(payload, schema="Item", source=source)
            return Item.from_dict(payload)
        if "stat_block" in payload:
            _validate_payload(payload, schema="NPC", source=source)
            return NPC.from_dict(payload)
        _validate_payload(payload, schema="Creature", source=source)
        return Creature.from_dict(payload)

    # Default to creature parsing for text stat cards outside labeled folders.
    return load_creature(source)


__all__ = [
    "parse_creature_stat_block",
    "parse_item_card",
    "load_creature",
    "load_npc",
    "load_item",
    "load_location",
    "load_resource",
]
