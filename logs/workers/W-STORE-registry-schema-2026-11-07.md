# W-STORE — versioned registry schema (2026-11-07)

**Lane:** W-STORE  
**Master plan:** §8 — Versioned registry schema + machine-readable disc-fix applied list  
**No Hitman/CNK GS edits.**

## Outcome

Checkbox **verified green**.

## What landed

| Piece | Detail |
|-------|--------|
| Schema id | `ps2recomp.game_fix_registry/v1` + `schema_version: 1` |
| Machine-readable applied | `global_runtime.discfix_applied[]` objects (`id`, `status`, `board`, `board_path`, `files`, `verified_date`) |
| Legacy alias | `disc_fix_applied` id list kept in sync (validator rejects drift) |
| Board sync | Applied ids must match `discfix-matrix-board.json` → `discfix.applied` |
| Helper | `scripts/game_fix_registry.py` (`audit`, `discfix_applied_ids`, `validate_registry`) |
| Consumers | `store_ready_contract.py`, `solid_60_mandate.py` read via helper |

## Evidence

- Live audit: `logs/workers/W-STORE-registry-schema-audit-20261108T002000Z.json` (`ok: true`)
- Unit tests: `tests/game_fix_registry.py` **4/4**
- Store contract tests: `tests/store_ready_contract.py` **4/4**
- Nightly unit tests: `tests/nightly_pipeline.py` **7/7**
- Latest nightly artifact still overall=pass: `logs/autonomous-pipeline/nightly-20261108T001502Z.json`
- Library store-ready still overall=pass after registry bump (`store_ready_contract.py --library`)

## Still open (not this checkbox)

- §4 `proven_fixes[]` — blocked on CNK Alchemy verify
- §4 T3 board-gated HLE rewrite (`allow_discfix_apply=false`)
- Per-title registry seed already **[x]** (§2d)
