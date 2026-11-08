# W-STORE platform — 2026-11-07

**Worker:** W-STORE  
**Lane:** Store → downloader → install → ready + panel web shell  
**Heartbeat:** `logs/workers/W-STORE-platform-heartbeat.log`

## Checkbox moved (§3)

| Item | Was | Now |
|------|-----|-----|
| Inline `autonomous_verify` smoke before `ready` | open (CLI/nightly gap only) | **[x]** opt-in gate on hot path |
| Nightly download → build → heal → verify | open | **[x]** orchestrator + live pass log |
| Store pull → playable without manual patches | open | **[x]** contract DoD + library evidence |

**Evidence (inline):** `scripts/store_pipeline_hooks.py`; `tests/store_pipeline.py` 17/17.

**Evidence (nightly):** `scripts/nightly_pipeline.py`, `scripts/run_nightly_pipeline.ps1`, `tests/nightly_pipeline.py` 6/6; live `logs/autonomous-pipeline/nightly-20261108T001112Z.json` (and sibling `…T001020Z.json`) **overall=pass** — NFS MW 500f matrix all phases pass, skip-build / dry-heal, lock-aware.

**Evidence (store→Chrome DoD):** `scripts/store_ready_contract.py` + `tests/store_ready_contract.py` 4/4; NFS `--http` → `/play/60c82f…/` **200** (`store-ready-contract-20261108T001250Z.json`); library ready titles **12/12** pass (`…T001302Z.json`). No Hitman/CNK GS edits.

## Behavior

### Inline verify (prior)
- Default: unchanged — no smoke on every install.
- `PS2_INLINE_VERIFY=1` (full installs only): runs `scripts/autonomous_verify.py` before `ready`.

### Nightly
- Stages: download (ISO present) → build (skip if native / protected lock) → heal → verify.
- Optional `--store-contract` attaches DoD evaluation per game.
- Artifacts under `logs/autonomous-pipeline/nightly-*.{json,log}` + `store-pipeline-events.jsonl`.

### Store-ready contract (DoD)
Requires: `library.json` ready, `disc.iso`, published `ps2web.html`, global patches in tree (R3/R4-D1/XYOFFSET + registry), panel hooks wired, no `patches.pending` / `MANUAL_PATCHES*`. Optional `--http` for panel play URL.

## Tests

```text
py -3 tests/store_pipeline.py -v          → 17/17 OK
py -3 tests/nightly_pipeline.py -v        → 6/6 OK
py -3 tests/store_ready_contract.py -v    → 4/4 OK
```

## Non-goals this turn

No Alchemy / Hitman GS / game-specific registry edits. Canvas_lum flawless remains §1–§2 / self-heal T1 — contract proves **no manual patch steps** on the install→play path, not per-title visual perfection.
