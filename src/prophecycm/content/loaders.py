from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

try:  # Optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - fallback when PyYAML is missing
    yaml = None

try:  # Optional dependency
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - fallback when jsonschema is missing
    Draft202012Validator = None

from prophecycm.characters import PlayerCharacter
from prophecycm.characters.npc import NPC
from prophecycm.items import Item
from prophecycm.quests import Quest
from prophecycm.schema_generation import generate_schema_files
from prophecycm.state import GameState, PartyRoster, SaveFile
from prophecycm.characters.creation import CharacterCreationConfig
from prophecycm.ui.start_menu_config import ContentWarning, StartMenuConfig, StartMenuOption
from prophecycm.world import Location


CONTENT_EXTENSIONS: Sequence[str] = (".yaml", ".yml", ".json")


def _resolve_content_file(root: Path, stem: str) -> Path:
    for ext in CONTENT_EXTENSIONS:
        if ext in {".yaml", ".yml"} and yaml is None:
            continue
        candidate = root / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not locate content file for '{stem}' in {root}")


def _load_payload(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            alt_json = path.with_suffix(".json")
            if alt_json.exists():
                return json.loads(alt_json.read_text(encoding="utf-8"))
            raise RuntimeError("PyYAML is required to load YAML content.")
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _as_dicts(items: Iterable[Item]) -> List[Dict[str, object]]:
    return [item.to_dict() if hasattr(item, "to_dict") else item for item in items]


@dataclass
class ContentCatalog:
    """In-memory cache of authored content for reuse across loaders."""

    items: Dict[str, Item]
    locations: Dict[str, Location]
    npcs: Dict[str, NPC]

    @classmethod
    def load(cls, root: Path) -> "ContentCatalog":
        items = {item.id: item for item in load_items(_resolve_content_file(root, "items"))}
        locations = {loc.id: loc for loc in load_locations(_resolve_content_file(root, "locations"))}
        npcs = {npc.id: npc for npc in load_npcs(_resolve_content_file(root, "npcs"), items)}
        return cls(items=items, locations=locations, npcs=npcs)


def load_items(path: Path) -> List[Item]:
    payload = _load_payload(path)
    return [Item.from_dict(dict(item)) for item in payload]


def load_locations(path: Path) -> List[Location]:
    payload = _load_payload(path)
    return [Location.from_dict(dict(entry)) for entry in payload]


def load_npcs(path: Path, items: Mapping[str, Item] | None = None) -> List[NPC]:
    payload = _load_payload(path)
    catalog_items = items or {}
    hydrated: List[NPC] = []
    for npc_entry in payload:
        npc: MutableMapping[str, object] = dict(npc_entry)
        inventory_ids = list(npc.pop("inventory_item_ids", []))
        inventory_payload = list(npc.get("inventory", []))
        inventory_payload.extend([catalog_items[item_id].to_dict() for item_id in inventory_ids if item_id in catalog_items])
        npc["inventory"] = inventory_payload
        npc["inventory_item_ids"] = inventory_ids
        hydrated.append(NPC.from_dict(npc))
    return hydrated


def _hydrate_pc(pc_data: Dict[str, object], catalog: ContentCatalog) -> PlayerCharacter:
    inventory_ids = list(pc_data.pop("inventory_item_ids", []))
    inventory_payload = list(pc_data.get("inventory", []))
    inventory_payload.extend([catalog.items[item_id].to_dict() for item_id in inventory_ids if item_id in catalog.items])
    pc_data["inventory"] = inventory_payload
    return PlayerCharacter.from_dict(pc_data)


def _select_locations(option: Dict[str, object], catalog: ContentCatalog) -> List[Location]:
    requested_ids = option.get("location_ids")
    if not requested_ids:
        return list(catalog.locations.values())
    return [catalog.locations[loc_id] for loc_id in requested_ids if loc_id in catalog.locations]


def build_save_file(option_data: Dict[str, object], catalog: ContentCatalog, slot: int) -> SaveFile:
    pc = _hydrate_pc(dict(option_data.get("pc", {})), catalog)
    npc_ids = option_data.get("npc_ids", [])
    npcs = [catalog.npcs[npc_id] for npc_id in npc_ids if npc_id in catalog.npcs]
    quests = [Quest.from_dict(quest) for quest in option_data.get("quests", [])]

    party_payload = option_data.get("party") if isinstance(option_data.get("party"), dict) else None
    party = PartyRoster.from_dict(party_payload or {}, default_leader_id=pc.id)
    party.sync_with_pc(pc)
    for companion_id in (npc.id for npc in npcs):
        party.ensure_member(companion_id, active=True)

    game_state = GameState(
        timestamp=option_data.get("timestamp", ""),
        pc=pc,
        npcs=npcs,
        creatures=[],
        locations=_select_locations(option_data, catalog),
        factions=[],
        quests=quests,
        party=party,
        global_flags=option_data.get("global_flags", {}),
        reputation=option_data.get("reputation", {}),
        relationships=option_data.get("relationships", {}),
        current_location_id=option_data.get("current_location_id"),
    )

    return SaveFile(
        slot=slot,
        metadata=option_data.get("metadata", {}),
        game_state=game_state,
        version=option_data.get("version", "0.1.0"),
        schema_hash=option_data.get("schema_hash", "dev"),
    )


def load_start_menu_config(path: Path, catalog: ContentCatalog) -> StartMenuConfig:
    payload = _load_payload(path)
    options: List[StartMenuOption] = []
    for idx, option in enumerate(payload.get("options", []), start=1):
        save_file = build_save_file(option, catalog, slot=idx)
        options.append(
            StartMenuOption(
                id=option["id"],
                label=option.get("label", option["id"]),
                description=option.get("description", ""),
                save_file=save_file,
                metadata=option.get("metadata", {}),
                timestamp=option.get("timestamp", ""),
                pc=dict(option.get("pc", {})),
                npc_ids=list(option.get("npc_ids", [])),
                location_ids=list(option.get("location_ids", [])),
                quests=list(option.get("quests", [])),
                global_flags=dict(option.get("global_flags", {})),
                current_location_id=option.get("current_location_id"),
            )
        )
    creation_config = None
    warning = None
    if payload.get("character_creation"):
        creation_config = CharacterCreationConfig.from_dict(payload["character_creation"])
    if payload.get("content_warning"):
        warning = ContentWarning.from_dict(payload["content_warning"])
    return StartMenuConfig(
        title=payload.get("title", ""),
        subtitle=payload.get("subtitle", ""),
        options=options,
        character_creation=creation_config,
        new_game_label=payload.get("new_game_label", "New Game"),
        new_game_description=payload.get("new_game_description", ""),
        content_warning=warning,
    )


def load_game_state_from_content(root: Path, start_option_id: str | None = None) -> GameState:
    """Load a ``GameState`` from the authored content bundle.

    ``root`` should point to the directory containing ``items.yaml``,
    ``locations.yaml``, ``npcs.yaml``, and ``start_menu.yaml``.
    """

    catalog = ContentCatalog.load(root)
    start_menu = load_start_menu_config(_resolve_content_file(root, "start_menu"), catalog)
    if start_option_id:
        for option in start_menu.options:
            if option.id == start_option_id:
                return option.save_file.game_state
        raise ValueError(f"Start menu option '{start_option_id}' not found")
    if not start_menu.options:
        raise ValueError("No start menu options were loaded")
    return start_menu.options[0].save_file.game_state


def validate_content_against_schemas(content_root: Path, schema_output: Path) -> Dict[str, List[str]]:
    """Validate fixture files against the freshly generated schemas.

    Returns a mapping of file name to a list of validation error strings.
    """
    schemas = generate_schema_files(schema_output)
    problems: Dict[str, List[str]] = {}

    fixtures = {
        "items": (
            [schemas["Item"], schemas["Equipment"], schemas["Consumable"]],
            _resolve_content_file(content_root, "items"),
        ),
        "locations": ([schemas["Location"]], _resolve_content_file(content_root, "locations")),
        "npcs": ([schemas["NPC"]], _resolve_content_file(content_root, "npcs")),
        "start_menu": ([schemas["StartMenuConfig"]], _resolve_content_file(content_root, "start_menu")),
    }

    def _resolve_ref(schema: Dict[str, object], ref: str) -> Dict[str, object]:
        name = ref.split("/")[-1]
        return schema.get("$defs", {}).get(name, {}) if isinstance(schema, dict) else {}

    def _validate_instance(instance: object, schema: Dict[str, object], root: Dict[str, object], path: str = "") -> List[str]:
        errors: List[str] = []
        if "$ref" in schema:
            schema = _resolve_ref(root, str(schema["$ref"]))
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if not _validate_instance(instance, option, root, path):
                    return []
            errors.append(f"{path}: value did not match anyOf options")
            return errors

        schema_type = schema.get("type")
        if schema_type == "object":
            if not isinstance(instance, dict):
                return [f"{path}: expected object"]
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    errors.append(f"{path}: missing required property '{key}'")
            props = schema.get("properties", {})
            for key, value in instance.items():
                if key in props:
                    errors.extend(_validate_instance(value, props[key], root, f"{path}.{key}" if path else key))
        elif schema_type == "array":
            if not isinstance(instance, list):
                return [f"{path}: expected array"]
            item_schema = schema.get("items", {})
            for idx, value in enumerate(instance):
                errors.extend(_validate_instance(value, item_schema, root, f"{path}[{idx}]") )
        elif schema_type == "integer" and not isinstance(instance, int):
            errors.append(f"{path}: expected integer")
        elif schema_type == "number" and not isinstance(instance, (int, float)):
            errors.append(f"{path}: expected number")
        elif schema_type == "boolean" and not isinstance(instance, bool):
            errors.append(f"{path}: expected boolean")
        elif schema_type == "string" and not isinstance(instance, str):
            errors.append(f"{path}: expected string")
        return errors

    for name, (schema_paths, data_path) in fixtures.items():
        schema_documents = [json.loads(path.read_text(encoding="utf-8")) for path in schema_paths]
        schema_content = schema_documents[0] if len(schema_documents) == 1 else {"anyOf": schema_documents}
        data = _load_payload(data_path)
        if name == "start_menu":
            entries = data
        else:
            entries = data if isinstance(data, list) else data.get("options", [])
        errors: List[str] = []
        if Draft202012Validator is not None:
            validator = Draft202012Validator(schema_content)
            if name == "start_menu":
                for error in validator.iter_errors(entries):
                    errors.append(error.message)
            else:
                for idx, entry in enumerate(entries):
                    for error in validator.iter_errors(entry):
                        errors.append(f"{data_path.name}[{idx}]: {error.message}")
        else:
            if name == "start_menu":
                errors.extend(_validate_instance(entries, schema_content, schema_content))
            else:
                for idx, entry in enumerate(entries):
                    entry_errors = _validate_instance(entry, schema_content, schema_content)
                    errors.extend([f"{data_path.name}[{idx}]: {err}" for err in entry_errors])
        if errors:
            problems[data_path.name] = errors
    return problems


__all__ = [
    "ContentCatalog",
    "build_save_file",
    "load_game_state_from_content",
    "load_items",
    "load_locations",
    "load_npcs",
    "load_start_menu_config",
    "validate_content_against_schemas",
]

