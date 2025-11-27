# Data Model Contracts

This repository uses **Python 3.11 dataclasses** as the canonical schema for gameplay data. JSON serialization uses the `Serializable` mixin in `src/prophecycm/core.py`; any JSON produced by the runtime is treated as an interchange format for tools. All authored content lives in YAML under `docs/data-model/fixtures/`, and the JSON snapshots are generated for debugging/reference only.

## Authoring rules
- Every entity must carry a stable `id` string that is unique across its type.
- Optional fields should be omitted from JSON when empty; deserializers provide defaults.
- Prefer enums for constrained strings (e.g., `EquipmentSlot`, `DurationType`).
- Backwards compatibility is handled at the **SaveFile** layer via `version` + `schema_hash`.

## Core entities (module → class)
- `prophecycm.characters.player`
  - `AbilityScore` (score + modifier), `Skill` (key ability + proficiency tier), `Race`, `Class`, `Feat`, `PlayerCharacter` (derived stats recomputation, equipment & status effect hooks)
- `prophecycm.characters.npc`
  - `NPC` (inventory, disposition, quest hooks)
- `prophecycm.items.item`
  - `Item`, `Equipment`, `Consumable`, `EquipmentSlot`
- `prophecycm.combat.status_effects`
  - `StatusEffect` (stacking, durations, dispel rules), `DurationType`, `StackingRule`, `DispelCondition`
- `prophecycm.quests.quest`
  - `Quest`, `QuestStep`, `QuestCondition`, `QuestEffect`
- `prophecycm.world.location`
  - `Location` (connections, encounter tables, travel rules)
- `prophecycm.state.game_state`
  - `GameState` (flag helpers, travel + encounter evaluation), `current_location_id`
- `prophecycm.state.saves.save_file`
  - `SaveFile` (versioned container for a compressed `GameState`)

## JSON schema stubs
Generated schemas will live under `docs/data-model/schemas/` (additive per entity). During this phase the dataclasses themselves are the source of truth; schema generation tooling will be added later once the surface stabilizes.

To regenerate the JSON fixture snapshots, edit the YAML sources and run `tools/export_yaml_fixtures_to_json.py` from the repository root.

## Compatibility expectations
- New required fields must include sane defaults or migration logic at `SaveFile.from_dict`.
- Use `GameState` helpers (`set_flag`, `travel_to`, `roll_encounter`) instead of editing raw dicts so tests remain valid.
- Content IDs should be lowercase, kebab-case for readability (e.g., `silverthorn`, `main-quest-whisperwood`).
