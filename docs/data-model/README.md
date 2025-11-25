# Data Model Contracts

This repository uses **Python 3.11 dataclasses** as the canonical schema for gameplay data. JSON serialization uses the `Serializable` mixin in `src/prophecycm/core.py`; any JSON produced by the runtime is treated as an interchange format for tools.

## Authoring rules
- Every entity must carry a stable `id` string that is unique across its type.
- Optional fields should be omitted from JSON when empty; deserializers provide defaults.
- Prefer enums for constrained strings (e.g., `EquipmentSlot`, `DurationType`).
- Backwards compatibility is handled at the **SaveFile** layer via `version` + `schema_hash`.

## Core entities (module → class)
- `prophecycm.characters.player`
  - `AbilityScore` (score + modifier), `Skill` (key ability + proficiency tier), `Race`, `Class`, `Feat`, `PlayerCharacter` (derived stats recomputation, equipment & status effect hooks)
- `prophecycm.characters.npc`
  - `NPC` (inventory, disposition, quest hooks, optional combat stat block, optional `NPCScalingProfile` for level sync)
- `prophecycm.characters.creature`
  - `Creature` (enemy stat block; static templates with current HP + death), `CreatureAction` (attack entry)
- `prophecycm.items.item`
  - `Item`, `Equipment`, `Consumable`, `EquipmentSlot`
- `prophecycm.combat.status_effects`
  - `StatusEffect` (stacking, durations, dispel rules), `DurationType`, `StackingRule`, `DispelCondition`
- `prophecycm.combat.engine`
  - `CombatantRef`, `TurnOrderEntry`, `EncounterState`, `TurnContext`, `AttackResult`, `roll_dice`, `roll_initiative`, `resolve_attack`, `use_consumable_in_combat`
- `prophecycm.quests.quest`
  - `Quest`, `QuestStep`, `QuestCondition`, `QuestEffect`
- `prophecycm.dialogue`
  - `DialogueCondition`, `DialogueEffect`, `DialogueChoice`, `DialogueNode` with runner helpers for conditional choices
- `prophecycm.world.location`
  - `Location` (connections, encounter tables, travel rules)
- `prophecycm.world.faction`
  - `Faction` (id, ideology, base reputation)
- `prophecycm.state.game_state`
  - `GameState` (flag helpers, travel + encounter evaluation, faction/relationship reputation, active encounters), `current_location_id`, `visited_locations`
- `prophecycm.state.saves.save_file`
  - `SaveFile` (versioned container for a compressed `GameState`)

## JSON schemas
- Generate schemas from dataclasses with `PYTHONPATH=src python -m prophecycm.schema_generation` (or after installing the packag
e).
- Schemas are written under `docs/data-model/schemas/` and should be committed when contracts change.
- These schemas exist to validate authored JSON content in CI and to keep external tools aligned with the Python dataclasses.

## Compatibility expectations
- New required fields must include sane defaults or migration logic at `SaveFile.from_dict`.
- Use `GameState` helpers (`set_flag`, `travel_to`, `roll_encounter`) instead of editing raw dicts so tests remain valid.
- Content IDs should be lowercase, kebab-case for readability (e.g., `silverthorn`, `main-quest-whisperwood`).
