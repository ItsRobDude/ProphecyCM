# Systems Architecture (baseline)

This phase locks the Python runtime and establishes where schemas and seed content live while we continue to flesh out combat, dialogue, and quest logic.

## Module layout
- `src/prophecycm/core.py`: serialization helpers shared by all dataclasses.
- `src/prophecycm/characters/`: player/NPC definitions, derived stat recalculation, equipment/status hooks.
- `src/prophecycm/items/`: item/equipment/consumable primitives and slot enums.
- `src/prophecycm/combat/`: status-effect rules (stacking, durations, dispels); combat engine hooks will attach here.
- `src/prophecycm/quests/`: quest graph primitives (conditions, effects, steps) with lightweight evaluation helpers.
- `src/prophecycm/world/`: location graph, encounter tables, and travel constraints.
- `src/prophecycm/state/`: authoritative `GameState` + `SaveFile` containers and helper methods for time/flags/travel/encounters.
- `src/prophecycm/content/`: seed data for locations, quests, and an initial save suitable for smoke tests.

## Content flow
1. **Authoring**: Content creators define locations, quests, and characters in `src/prophecycm/content/` (or external data validated against schemas).
2. **Loading**: `GameState` is constructed from seeds or deserialized from a `SaveFile`.
3. **Evaluation**: Systems read `GameState` (flags, reputation, quest stages) to gate dialogue, encounters, and travel.
4. **Serialization**: `SaveFile` snapshots the entire state for persistence, including version + schema hash.

## Characters & creatures
- Players derive stats from ability scores plus race/class/feat bonuses, equipment, and status effects; proficiency scales with level.
- NPCs remain lightweight (disposition, faction, quest hooks) but can attach a `Creature` stat block for combat participation. Level syncing happens **only** through these NPC wrappers via `NPCScalingProfile`.
- Creatures/enemies carry 5e-style stat blocks (ability scores, hit die, AC, saves, actions) plus persistent `current_hit_points`/`is_alive` flags so death persists across saves. Base creature templates are static; NPCs decide if/when to scale them.

## Next steps
- Add JSON Schema generation from dataclasses into `docs/data-model/schemas/` with CI enforcement.
- Extend combat to include actions/AP, attack resolution, and inventory usage.
- Build dialogue/choice runner that reads `QuestCondition` and `GameState` flags for branching.
- Provide data loaders that hydrate content from external files rather than code-only seeds.
