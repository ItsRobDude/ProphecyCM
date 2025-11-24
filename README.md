# ProphecyCM

## Vision
ProphecyCM is a narrative-first RPG framework focused on consequential choices and a living world state. The project aims to provide a modular toolkit for building campaigns with branching narratives, reactive NPCs, and systemic gameplay that rewards player agency.

## Core Pillars
- **Player agency with consequences:** Decisions ripple through factions, locations, and quests, updating the shared world state.
- **Systemic storytelling:** Dialogue, combat, and exploration systems share the same data model so quests and encounters can react to changing conditions.
- **Extensibility:** Clear data contracts and modular subsystems make it straightforward to add new content, mechanics, and integrations.
- **Playability + tooling:** Robust save/load, debugging hooks, and testable logic enable rapid iteration on content and balance.

## Data Model
All gameplay systems consume the same set of serializable objects. Suggested core entities:

| Object | Key Fields | Notes |
| --- | --- | --- |
| `PC` (Player Character) | `id`, `name`, `background`, `attributes`, `skills`, `traits`, `inventory`, `statusEffects`, `factionReputation`, `questFlags`, `level`, `xp`, `progressionChoices` | Single active player character; supports multi-build saves. |
| `NPC` | `id`, `archetype`, `factionId`, `disposition`, `schedule`, `dialogueNodes`, `inventory`, `statusEffects`, `questHooks`, `aiProfile` | Behaviors driven by disposition, schedule, and AI profile; can promote to companion. |
| `Faction` | `id`, `name`, `ideology`, `territory`, `relationships`, `standingRules`, `questLog`, `assets` | Tracks inter-faction relationships and territory control; influences dialogue and encounter tables. |
| `Location` | `id`, `name`, `biome`, `pointsOfInterest`, `population`, `factionControl`, `encounterTables`, `resources`, `fastTravelRules` | Holds encounter and POI data; supports dynamic ownership and state. |
| `Quest` | `id`, `title`, `summary`, `stage`, `objectives`, `triggers`, `failStates`, `rewards`, `relatedFactions`, `relatedNPCs`, `dependencies` | Stage-based progression with triggers and fail states tied to world events. |
| `Item` | `id`, `type`, `rarity`, `stats`, `effects`, `requirements`, `craftingRecipes`, `value`, `equipSlots`, `durability` | Supports equipment, consumables, crafting components, and quest items. |
| `StatusEffect` | `id`, `name`, `duration`, `stackRules`, `modifiers`, `source`, `tags`, `expiryRules` | Centralized modifier container for combat and non-combat systems. |
| `GameState` | `timestamp`, `pc`, `npcs`, `factions`, `locations`, `quests`, `globalFlags`, `worldClock`, `rngSeed`, `difficulty`, `sessionTelemetry` | Single authoritative snapshot of current world state. |
| `SaveFile` | `slot`, `metadata`, `compressedGameState`, `checksums`, `version`, `schemaHash`, `playtime`, `lastLocation`, `platform`, `mods` | Versioned serialization layer for portability and backwards compatibility. |

## Gameplay Systems
- **Character creation:** Background selection, attribute/skill allocation, and trait picks validate against starting builds and set initial faction reputations.
- **Leveling and progression:** XP thresholds per level; progression choices unlock skills, perks, and crafting specializations while recalculating derived stats.
- **Combat:** Turn/phase-based engine with action economy, initiative, cover, line-of-sight, damage types, resistances, and status effects; AI profiles consume NPC + faction data.
- **Dialogue and choice flow:** Node/graph-driven dialogues with conditions (flags, reputations, stats) and outcomes (quest updates, faction changes, combat triggers, rewards). Supports interruptions and re-entry after state changes.
- **World state simulation:** Time-of-day and calendar advance schedules, faction territory shifts, location-specific encounter tables, and systemic responses to quests and player actions.
- **Saving/loading:** Deterministic serialization via `SaveFile` schema; schema hashes prevent incompatible loads. Includes quicksave/autosave hooks and integrity checks.

## Directory Structure (proposed)
```
ProphecyCM/
├─ README.md                 # Project overview and contributor guide
├─ docs/                     # Design references, diagrams, and deep dives
│  ├─ systems/               # System-specific specs (combat, dialogue, AI)
│  └─ data-model/            # JSON schemas or protobuf definitions
├─ src/                      # Engine/runtime code
│  ├─ core/                  # Game loop, state container, serialization
│  ├─ content/               # Data packs for quests, NPCs, items, locations
│  ├─ systems/               # Combat, dialogue, quest, AI, progression
│  └─ platform/              # Platform bindings, persistence, telemetry
├─ tools/                    # Content pipelines, validators, CLI utilities
├─ tests/                    # Unit + integration tests
└─ examples/                 # Sample campaigns and fixtures
```

## Build & Run Prerequisites
- **Runtime:** Node.js 20+ or Python 3.11+ (select per implementation path); Git for version control.
- **Tooling:** Package manager (npm/pnpm or Poetry/pip), linter/formatter (e.g., ESLint/Prettier or Ruff/Black), and test runner (Jest/Vitest or PyTest).
- **Optional:** Docker for reproducible builds; Graphviz/Draw.io for diagrams; protobuf/JSON schema toolchain for data model validation.

### Setup (JavaScript/TypeScript path)
1. Install Node.js 20+ and npm/pnpm.
2. `pnpm install` (or `npm install`) to restore dependencies.
3. `pnpm run lint && pnpm test` to validate the workspace.
4. `pnpm run dev` to start a hot-reload development server (if applicable).

### Setup (Python path)
1. Install Python 3.11+ and Poetry (or pip + venv).
2. `poetry install` (or `pip install -r requirements.txt`).
3. `poetry run pytest` to execute tests.
4. `poetry run python -m prophecycm` to launch a sample session (entrypoint TBD).

### Environment Configuration
- Use `.env.example` to document environment variables (e.g., save path, telemetry opt-in, feature flags).
- Enable strict linting/typing (TypeScript `strict`, Python `mypy/pyright`) to keep data contracts stable.
- Provide seed data for quests/NPCs/factions under `src/content` and validate via schema checks in CI.

## Contribution Guide
1. **Fork and branch:** Create a feature branch per change.
2. **Design first:** Update or add specs under `docs/` for new systems, data contracts, or major features before coding.
3. **Code quality:** Follow lint/format conventions; add tests for systems, data mutations, and serialization.
4. **Content guidelines:** Ensure new quests/NPCs/items reference valid IDs, tag appropriately, and include localization-ready strings.
5. **Testing:** Run linting, unit tests, and scenario simulations before opening a PR.
6. **Review:** Use small, focused PRs with clear test results and screenshots/recordings for UI changes.
7. **Documentation:** Keep README and `docs/` aligned with new mechanics or data fields.

## Design References
- **Narrative systems:** [Versu](https://www.versu.com) for social AI inspiration; [Disco Elysium postmortems](https://www.eurogamer.net/disco-elysium-how-its-been-made-article) for dialogue structures.
- **Combat systems:** [Gloomhaven](https://boardgamegeek.com/boardgame/174430/gloomhaven) and [Into the Breach](https://subsetgames.com/itb.html) for deterministic, information-rich tactics.
- **Data modeling:** [Protobuf design guide](https://developers.google.com/protocol-buffers/docs/style) and [JSON Schema](https://json-schema.org/) for schema rigor.
- **World simulation:** [Dwarf Fortress](http://www.bay12games.com/dwarves/) legends mode for emergent history tracking.

## Roadmap Seeds
- Minimal vertical slice: character creation, small hub location, 2–3 quests, and a single faction conflict.
- Deterministic combat prototype with logged decision trees for debugging.
- Dialogue editor in `tools/` to author branching conversations with validation.
- Save migration tool to upgrade `SaveFile` schemas across versions.

