from __future__ import annotations

"""Utilities to derive JSON Schemas from ProphecyCM dataclasses."""

from dataclasses import MISSING, fields, is_dataclass
import json
from pathlib import Path
from enum import Enum
from types import UnionType
from typing import Any, Dict, Iterable, Tuple, Type, Union, get_args, get_origin, get_type_hints

from prophecycm.characters import (
    AbilityScore,
    CharacterCreationConfig,
    Class,
    Feat,
    GearBundle,
    PlayerCharacter,
    Race,
    Skill,
)
from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.npc import NPC, NPCScalingProfile
from prophecycm.combat.status_effects import StatusEffect
from prophecycm.items import Consumable, Equipment, Item
from prophecycm.quests import Condition, Quest, QuestEffect, QuestStep
from prophecycm.state import GameState, PartyRoster, SaveFile
from prophecycm.ui.start_menu_config import StartMenuConfig
from prophecycm.world import Faction, Location, TravelConnection


JsonSchema = Dict[str, Any]


def _type_schema(py_type: Any, defs: Dict[str, JsonSchema]) -> Tuple[JsonSchema, bool]:
    """Return a JSON schema fragment for the provided Python type.

    The boolean indicates whether ``null`` is an allowed value.
    """

    origin = get_origin(py_type)
    args = get_args(py_type)

    if origin in (Union, UnionType):
        non_none = [arg for arg in args if arg is not type(None)]
        allows_none = len(non_none) != len(args)
        if len(non_none) == 1:
            schema, _ = _type_schema(non_none[0], defs)
            return {"anyOf": [schema, {"type": "null"}]}, allows_none
        return {"anyOf": [_type_schema(arg, defs)[0] for arg in non_none]}, allows_none

    if origin in (list, List := list):
        (item_type,) = args or (Any,)
        items_schema, _ = _type_schema(item_type, defs)
        return {"type": "array", "items": items_schema}, False

    if origin in (dict, Dict := dict):
        value_type = args[1] if len(args) == 2 else Any
        value_schema, _ = _type_schema(value_type, defs)
        return {"type": "object", "additionalProperties": value_schema}, False

    if is_dataclass(py_type):
        name = py_type.__name__
        if name not in defs:
            defs[name] = {}  # placeholder to break recursion
            defs[name] = _build_dataclass_schema(py_type, defs)
        return {"$ref": f"#/$defs/{name}"}, False

    if isinstance(py_type, type) and issubclass(py_type, Enum):
        values = [member.value for member in py_type]
        json_type = "string" if all(isinstance(v, str) for v in values) else "number"
        return {"type": json_type, "enum": values}, False

    if py_type in (str,):
        return {"type": "string"}, False
    if py_type in (int,):
        return {"type": "integer"}, False
    if py_type in (float,):
        return {"type": "number"}, False
    if py_type in (bool,):
        return {"type": "boolean"}, False

    return {}, False


def _build_dataclass_schema(cls: Type[Any], defs: Dict[str, JsonSchema]) -> JsonSchema:
    properties: Dict[str, JsonSchema] = {}
    required: list[str] = []
    type_hints = get_type_hints(cls)

    for field_info in fields(cls):
        if not field_info.init:
            continue

        schema, allows_none = _type_schema(type_hints.get(field_info.name, field_info.type), defs)
        properties[field_info.name] = schema
        if field_info.default is MISSING and field_info.default_factory is MISSING and not allows_none:
            required.append(field_info.name)

    schema: JsonSchema = {
        "title": cls.__name__,
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = sorted(required)
    return schema


def build_schema_for(cls: Type[Any]) -> JsonSchema:
    """Construct a JSON Schema (draft 2020-12) for the provided dataclass."""

    definitions: Dict[str, JsonSchema] = {}
    base_schema = _build_dataclass_schema(cls, definitions)
    schema: JsonSchema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": cls.__name__,
        **base_schema,
    }
    if definitions:
        schema["$defs"] = definitions
        schema["definitions"] = definitions
    return schema


SCHEMA_TARGETS: tuple[Type[Any], ...] = (
    AbilityScore,
    Skill,
    Race,
    Class,
    Feat,
    GearBundle,
    CharacterCreationConfig,
    StatusEffect,
    CreatureAction,
    Creature,
    Item,
    Equipment,
    Consumable,
    NPCScalingProfile,
    NPC,
    TravelConnection,
    Location,
    Faction,
    QuestEffect,
    Condition,
    QuestStep,
    Quest,
    PlayerCharacter,
    GameState,
    PartyRoster,
    SaveFile,
    StartMenuConfig,
    LevelUpRequest,
    LevelUpScreenConfig,
    CompanionLevelSettings,
)


def generate_schema_files(output_dir: Path) -> Dict[str, Path]:
    """Generate JSON Schemas for core dataclasses into ``output_dir``.

    Returns a mapping of class name to written path for convenience.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}
    for cls in SCHEMA_TARGETS:
        schema = build_schema_for(cls)
        path = output_dir / f"{cls.__name__}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[cls.__name__] = path
    return written


def generate_schemas(output_dir: Path) -> Dict[str, JsonSchema]:
    """Generate schemas to disk and return their in-memory representations."""

    written_paths = generate_schema_files(output_dir)
    return {name: json.loads(path.read_text()) for name, path in written_paths.items()}


def generate_project_schemas(output_dir: Path | None = None) -> Dict[str, Path]:
    """Generate schemas into the project documentation directory by default."""

    target_dir = output_dir or Path("docs/data-model/schemas")
    return generate_schema_files(target_dir)


__all__ = [
    "build_schema_for",
    "generate_schema_files",
    "generate_schemas",
    "generate_project_schemas",
    "SCHEMA_TARGETS",
]

