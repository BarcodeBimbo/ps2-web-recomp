# Autonomous pipeline — store → install → patch → verify (2026-11-07)

**Standing order:** continuous until every library title is playable at ≥60 FPS (30 only when hardware requires). Hitman black canvas is **wave-1 graphics**; disc-fix/matrix/Alchemy/FPS run in parallel lanes.

**Improvement-pass (refined):** Optimize and modernize **inside** the existing stack (panel, `store.py`, `windows_port`, runtime GS/CDVD, self-heal, verify scripts). Add detectors, metrics, gates, and performance — **do not** replace the core vision or swap the architecture for a new product shape.

## Architecture (as found in repo)

| Stage | Component | Path / API |
|-------|-----------|------------|
| **Store UI** | CyberArcade panel | `scripts/panel.py` — library, play URLs, `/api/*` |
| **Catalog + download** | Romsfun + torrent index | `scripts/store.py`, `downloader/*.mjs`, `torrents/` |
| **Import hook** | `import_game` → `enqueue` | `panel.py` — malware guard, explore/build queue |
| **Recompile** | eerecomp + cmake | `scripts/windows_port.py` `refresh_translation` |
| **Install health** | Smoke/explore log gate | `scripts/install_health.py` → `games/<id>/health.json` |
| **Disc-fix protocol** | Propose → matrix → apply | `verification/recovery/discfix-matrix-board.json` |
| **Five-phase matrix** | Hitman/NFS scorer | `verification/recovery/matrix_phase_check.py` |
| **Live matrix lane** | Batch native smokes | `logs/live-matrix-2026-11-07/` |
| **Per-game registry** | Knobs + quarantine | `verification/recovery/game-fix-registry.json` (**new**) |
| **Autonomous verify** | Smoke + health + matrix JSON | `scripts/autonomous_verify.py` (**new**) |

**Download → playable chain (today):** Store job completes → `import_game` (malware guard + `install_manifest.json` stub) → build worker runs explore + native/web builds → `install_health` + `self_heal` → optional `PS2_STRICT_VERIFY=1` → `ready`. Matrix/disc-fix boards still manual for Hitman/NFS.

### Store hooks (2026-11-07, W-STORE)

| Hook | Location | Behavior |
|------|----------|----------|
| Post-download | `import_game` + `store_pipeline_hooks.note_post_download` | Job id from store transfer id; append `logs/autonomous-pipeline/store-pipeline-events.jsonl` |
| Manifest stub | `games/<id>/install_manifest.json` | `source.sha256`, `download_job_id`, import/build timestamps, health snapshot |
| Post-build | `panel.build` → `finalize_post_build` | Updates manifest; `PS2_STRICT_VERIFY=1` blocks `ready` on health **warn** or **fail** (full installs) |
| Inline smoke | `finalize_post_build` → `gate_inline_verify` | **`PS2_INLINE_VERIFY=1`** runs short `autonomous_verify.py` before `ready` (full installs); frames via `PS2_INLINE_VERIFY_FRAMES` (default 200). Default **off** so hot path stays fast. |
| Nightly | `scripts/nightly_pipeline.py` + `run_nightly_pipeline.ps1` | download (ISO present) → build (skip if native / lock) → heal → `autonomous_verify`; artifacts `logs/autonomous-pipeline/nightly-*.{json,log}`; lock-aware (never steal Hitman `web-a2116*`, NFS `web-60c82f*`, CNK `native-b49f2e*`) |
| **Gap** | Chrome harness `canvas_lum` at install | Requires web rebuild + browser job; see self-heal T1 / store→Chrome DoD |

## Patch layers (every new install)

1. **Runtime (global):** R3 readee, R4-D1 DiskReady (`cdvdfsv.cpp` / `cdvd.cpp`) — already `verified_apply`; never CNK Alchemy on Hitman/NFS.
2. **GS (global):** XYOFFSET 11-bit OFX/OFY (`runtime/src/gs/*`) — **applied 2026-11-07** for Hitman negative draw boxes.
3. **Web publish:** `ensure_web_build_readable` / ACL on `ps2web.js` (Hitman js serve fix).
4. **Per-game env (experiments):** `PS2_PRESENT_FRAME`, `PS2_GS_NO_ATE`, `PS2_TRACE_DISPLAY` — prefer detection in registry, not defaults.
5. **Quarantine:** CNK Alchemy paths in `igfileio.cpp` gated; matrix scorer ignores false `FCE0` in CreateSema attrs.

## Execution plan (sequenced, self-chaining)

| Step | Action | Success |
|------|--------|---------|
| E1 | **GS XYOFFSET fix** + rebuild all `native-*` | Hitman PPM/canvas luminance >> 0.11; draw boxes intersect 0..511 |
| E2 | **`autonomous_verify.py`** on full library | JSON summary; failures queue fix wave |
| E3 | **Wire panel post-build** to call `autonomous_verify` (or health+) | [x] 2026-11-07 — `PS2_INLINE_VERIFY=1` → `gate_inline_verify` before `ready` (opt-in; default off) |
| E4 | **Hitman Ghidra ELF reimport** @ `0x00100000` | Trust VAs for GS init; fold into registry notes |
| E5 | **Rebuild web** for titles with `web_rebuild_required_after_runtime` | Harness canvas_lum threshold |
| E6 | **Matrix → 100%** | CNK + NFS scorer gaps closed (`live-matrix` SUMMARY) |
| E7 | **FPS lane** | GoW 3600f min60 browser; extend `autonomous_verify` with frame timing |
| E8 | **Store automation test** | [x] 2026-11-07 — `tests/store_pipeline.py` 14/14; nightly catalog pull still optional |

**Loop rule:** after each step passes evidence gate, promote fixes to `game-fix-registry.json` + `discfix-matrix-board.json` (if behavioral), then pick next failing game from `autonomous_verify` summary.

## Started executing (this session)

| Item | Status |
|------|--------|
| `game-fix-registry.json` | Written |
| `autonomous_verify.py` | Written |
| GS `xyoffset_component` (11-bit) | **Patched** `gs.hpp`, `raster.cpp`, `gpu.cpp`, `gs.cpp` |
| Native rebuild + Hitman 200f smoke | **In flight** below |

## Evidence targets (Hitman)

- Before: `01c-TRACE-draws-frame180.tsv` boxes at **x ≈ −1792** (full 16-bit OFX `0x7000`).
- After fix: OFX effective **0** (`0x7000 & 0x7FF`), draws should intersect scissor **0..511**.
- Pass: `install_health` not `near_zero_prims`; harness `canvas_lum` above threshold; ≥60 FPS sustained.
