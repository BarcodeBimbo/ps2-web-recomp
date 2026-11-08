# W-STORE report — 2026-11-07

**Worker:** W-STORE  
**Repo:** `C:\PS2Recomp`  
**Panel:** `scripts/panel.py` `PORT = 8620`, CyberArcade branding preserved  

## Mission summary

Store → download → install → ready pipeline: post-download/post-build hooks, optional strict/inline verify, nightly orchestrator, store→Chrome DoD contract. §3 checkboxes all verified.

## Shipped

| Item | Path | Notes |
|------|------|-------|
| Hook module | `scripts/store_pipeline_hooks.py` | Manifest, jsonl, strict + inline verify |
| Nightly orchestrator | `scripts/nightly_pipeline.py` | download→build→heal→verify; lock-aware; `--chrome-serve` / `--store-contract` |
| Nightly wrapper | `scripts/run_nightly_pipeline.ps1` | Task Scheduler entry |
| Store→Chrome DoD | `scripts/store_ready_contract.py` | ready+web+global patches+hooks; no manual patch files |
| Tests | `tests/store_pipeline.py` 17/17; `tests/nightly_pipeline.py` 7/7; `tests/store_ready_contract.py` 4/4 | |

## Master plan §3 — all checked

- [x] Import pipeline + malware guard + build queue
- [x] Global R3/R4 + GS XYOFFSET
- [x] `install_health` / self_heal / finalize_post_build
- [x] Inline `autonomous_verify` (`PS2_INLINE_VERIFY=1`)
- [x] `install_manifest.json` / `PS2_STRICT_VERIFY`
- [x] Nightly log under `logs/autonomous-pipeline/` — `nightly-20261108T001020Z.json` (+ `…T001502Z` chrome+contract)
- [x] Store pull → Chrome without manual patch steps — `store-ready-contract-20261108T001302Z.json`

## Environment

- `PS2_STRICT_VERIFY=1` — warn/fail blocks ready
- `PS2_INLINE_VERIFY=1` — short autonomous_verify before ready
- Nightly: `py -3 scripts/nightly_pipeline.py --library --skip-build --store-contract --chrome-serve`

## Follow-ons (other lanes)

- NFS Chrome flawless still needs fresh web publish (W-NFS `web-60c82f*-next` cmake live); harness on stale wasm aborted `missing code @ 0x01A5C000` (`harness-runs/20261108T001208Z`).
- Hitman canvas_lum — Hitman lane.

## Non-goals

No Alchemy / Hitman GS / steal of locked cmake/ninja trees.
