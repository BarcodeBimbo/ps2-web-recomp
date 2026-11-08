# W-STORE platform — 2026-11-07

**Worker:** W-STORE  
**Lane:** Store → downloader → install → ready + panel web shell  
**Heartbeat:** `logs/workers/W-STORE-platform-heartbeat.log`

## Checkboxes moved (§3)

| Item | Was | Now |
|------|-----|-----|
| Inline `autonomous_verify` smoke before `ready` | open | **[x]** opt-in gate on hot path |
| Nightly download → build → heal → verify | open | **[x]** `scripts/nightly_pipeline.py` |
| Store pull → Chrome without manual patch steps | open | **[x]** `scripts/store_ready_contract.py` DoD |

**Evidence (nightly):** `logs/autonomous-pipeline/nightly-20261108T001020Z.json` / `…T001112Z.json` / integrated `…T001502Z.json` — overall=pass (NFS 500f matrix; skip-build; chrome-serve HTTP 200; store_contract pass). Tests: `tests/nightly_pipeline.py` **6/6**. Wrapper: `scripts/run_nightly_pipeline.ps1`.

**Evidence (store→Chrome DoD):** `logs/autonomous-pipeline/store-ready-contract-20261108T001302Z.json` (library 12/12) + HTTP proof `…T001250Z.json`; `tests/store_ready_contract.py` **4/4**. Contract = ready + web + global R3/R4/XYOFFSET + panel hooks + no `patches.pending`.

## Behavior — nightly

Stages per game: **download** (ISO present) → **build** (skip if native / lock-aware) → **heal** → **verify** (`autonomous_verify`) → optional **chrome_serve** / **store_contract**.

Lock policy: never steal Hitman `web-a2116*`, NFS `web-60c82f*`, CNK `native-b49f2e*` while cmake/ninja live; never kill those processes.

## Behavior — prior inline verify

- Default: unchanged — no smoke on every install.
- `PS2_INLINE_VERIFY=1` (full installs only): runs `scripts/autonomous_verify.py` before panel sets `ready`.

## Tests

```text
py -3 tests/store_pipeline.py -v          # 17/17 OK
py -3 tests/nightly_pipeline.py -v        # 6/6 OK
py -3 tests/store_ready_contract.py -v    # 4/4 OK
```

## Open beyond §3 (not W-STORE DoD)

- NFS Chrome **flawless** / ≥60 harness still open — stale published wasm (2026-11-06); W-NFS-2 holds `web-60c82f*` rebuild (`-next`); harness `20261108T001208Z` aborted `missing code at 0x01A5C000` on stale player.
- Hitman canvas_lum / Chrome flawless — Hitman lane.

## Non-goals this turn

No Alchemy / Hitman GS / game-specific registry edits; no steal of locked cmake trees.
