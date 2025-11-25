from __future__ import annotations

"""Utilities for emitting JSON Schemas from the project's dataclasses.

This module exists to give content authors a machine-verifiable contract while
allowing the codebase to continue using ``from __future__ import annotations``.
We resolve forward references with ``typing.get_type_hints`` so nested
dataclasses and Literal/Enum annotations survive schema emission.
"""

import json
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from pathlib import Path
import importlib
from typing import Any, Dict, Iterable, Literal, Optional, Type, Union, get_args, get_origin, get_type_hints

# Import dataclasses so forward references resolve during get_type_hints
from prophecycm.characters import AbilityScore, Class, Feat, NPC, Race, Skill
from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.combat.engine import CombatantRef, EncounterState, TurnOrderEntry
from prophecycm.combat.status_effects import DispelCondition, DurationType, StackingRule, StatusEffect
from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode
from prophecycm.items import Consumable, Equipment, Item
from prophecycm.quests.quest import Quest, QuestCondition, QuestEffect, QuestStep
from prophecycm.state.game_state import GameState
from prophecycm.state.saves.save_file import SaveFile
from prophecycm.world import Faction, Location

FORWARD_REF_TYPES: Dict[str, Any] = {
    cls.__name__: cls
    for cls in [
        AbilityScore,
        Class,
        Feat,
        NPC,
        Race,
        Skill,
        Creature,
        CreatureAction,
        CombatantRef,
        EncounterState,
        TurnOrderEntry,
        DispelCondition,
        DurationType,
        StackingRule,
        StatusEffect,
        DialogueChoice,
        DialogueCondition,
        DialogueEffect,
        DialogueNode,
        Consumable,
        Equipment,
        Item,
        Quest,
        QuestCondition,
        QuestEffect,
        QuestStep,
        GameState,
        SaveFile,
        Faction,
        Location,
    ]
}


def _enum_schema(enum_cls: Type[Enum]) -> Dict[str, Any]:
    values = [member.value for member in enum_cls]
    type_hint = "string" if any(isinstance(val, str) for val in values) else "integer"
    return {"type": type_hint, "enum": values}


def _type_schema(tp: Any, definitions: Dict[str, Any]) -> Dict[str, Any]:
    origin = get_origin(tp)
    args = get_args(tp)

    if tp in {str, int, float, bool}:
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
        return {"type": type_map.get(tp, "string")}

    if tp is Any:
        return {}

    if origin in {list, tuple}:
        inner = args[0] if args else Any
        return {"type": "array", "items": _type_schema(inner, definitions)}

    if origin in {dict, Dict}:
        value_type = args[1] if len(args) > 1 else Any
        return {"type": "object", "additionalProperties": _type_schema(value_type, definitions)}

    if origin is Union:
        non_none = [a for a in args if a is not type(None)]  # noqa: E721
        schemas = [_type_schema(a, definitions) for a in non_none]
        if len(non_none) != len(args):
            schemas.append({"type": "null"})
        if len(schemas) == 1:
            return schemas[0]
        return {"anyOf": schemas}

    if origin is Literal:
        literal_values = list(args)
        type_name = "string"
        if all(isinstance(val, bool) for val in literal_values):
            type_name = "boolean"
        elif all(isinstance(val, int) for val in literal_values):
            type_name = "integer"
        return {"type": type_name, "enum": literal_values}

    if isinstance(tp, type) and issubclass(tp, Enum):
        return _enum_schema(tp)

    if is_dataclass(tp):
        ref_name = tp.__name__
        if ref_name not in definitions:
            definitions[ref_name] = {}  # placeholder for recursion
            definitions[ref_name] = _dataclass_schema(tp, definitions)
        return {"$ref": f"#/definitions/{ref_name}"}

    return {}


def _dataclass_schema(cls: Type[Any], definitions: Dict[str, Any]) -> Dict[str, Any]:
    module = importlib.import_module(cls.__module__)
    annotations = get_type_hints(cls, globalns=vars(module), localns=FORWARD_REF_TYPES)
    properties: Dict[str, Any] = {}
    required: list[str] = []

    for field_info in fields(cls):
        field_type = annotations.get(field_info.name, field_info.type)
        properties[field_info.name] = _type_schema(field_type, definitions)
        if field_info.default is MISSING and field_info.default_factory is MISSING:
            required.append(field_info.name)

    schema: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def generate_schemas(output_dir: Path, roots: Optional[Iterable[Type[Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Generate JSON Schemas for key dataclasses and write them to disk.

    Returns the in-memory mapping for test assertions.
    """

    root_types = list(roots) if roots is not None else [SaveFile, GameState]
    definitions: Dict[str, Any] = {}
    rendered: Dict[str, Dict[str, Any]] = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    for root in root_types:
        definitions[root.__name__] = {}  # pre-seed to avoid recursion holes
        schema_body = _dataclass_schema(root, definitions)
        schema = {"$schema": "http://json-schema.org/draft-07/schema#", "title": root.__name__, "definitions": definitions}
        schema.update(schema_body)
        rendered[root.__name__] = schema

        out_path = output_dir / f"{root.__name__}.schema.json"
        out_path.write_text(json.dumps(schema, indent=2, sort_keys=True))

    return rendered


def main() -> None:
    output_dir = Path("docs/data-model/schemas")
    generate_schemas(output_dir)


if __name__ == "__main__":
    main()
