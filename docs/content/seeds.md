# Seed World (narrative scaffolding)

This seed aligns with the Whisperwood/Aodhan storyline and is used by the smoke tests to validate travel, quest gating, and serialization.

## Locations
- **Silverthorn** (`silverthorn`): starting town, connects south → Whisperwood/Sporefall.
- **Whisperwood / Sporefall** (`whisperwood`): corrupted forest hub, connects north → Durnhelm, east → Hushbriar Cove.
- **Durnhelm** (`durnhelm`): mountain settlement reachable from Whisperwood.
- **Hushbriar Cove** (`hushbriar-cove`): coastal town east of Whisperwood; connects northeast → Solasmor Monastery.
- **Solasmor Monastery** (`solasmor-monastery`): secluded monastery reachable from Hushbriar Cove.

## Main quest hook
`main-quest-aodhan`: The party is dispatched to Whisperwood to learn what happened to Aodhan. Leads toward a buried artifact whose location can surface via faction clues in Durnhelm or lore discoveries in Solasmor Monastery.

## Encounter sketch
- Whisperwood daytime: corrupted fauna (`spore-wolf-pack`), nighttime: fungal spirits (`myconid-wraith`).
- Road to Durnhelm: rockslide hazard or mountain patrol.
- Hushbriar Cove road: smugglers or traveling merchants.

## Usage
- The seed is materialized in `prophecycm.content.seed.seed_save_file()`.
- Tests in `tests/test_seed_content.py` ensure travel graph correctness and quest condition evaluation.
