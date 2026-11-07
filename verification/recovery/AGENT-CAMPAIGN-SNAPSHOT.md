# Agent campaign snapshot (context rollover seed)

**Updated:** 2026-11-07 ~10:20 local (America/New_York)  
**Read this + `MASTER-CONTEXT.md` RESUME POINT on every fresh agent start.**  
**Checkbox campaign plan:** `logs/master-campaign-plan-2026-11-07.md` (update checkboxes when steps verify).

## Improvement-pass policy (refined ~10:21)

- **Additive only** for product shape: CyberArcade panel, custom Windows recompiler, evidence-first `logs/` + `verification/recovery/`, store/downloader patterns, disc-fix board, quarantine rules — **unchanged**.
- **Allowed:** optimization (faster smokes, leaner verify, better defaults where safe) and **light modernization** (JSON schemas, typed hooks, clearer APIs, harness metrics) **without** replacing those pillars.
- **Not allowed:** wholesale re-architecture, new primary UX, abandoning panel/store/cmake pipeline, or merging CNK Alchemy into Hitman/NFS disc-fix.

## Mandates (carry always)

- **Chrome flawless:** every library title playable in Chrome (panel `:8620`).
- **FPS:** ≥60 almost every game; 30 only where a title truly requires it.
- **Pipeline:** store (`scripts/store.py` + panel) → download → `import_game` → `windows_port` native/web → verify.
- **Self-heal:** `scripts/self_heal.py` per install (`install_issues.json`); hooked from `panel.py` post-build.
- **Verify:** `scripts/autonomous_verify.py` (smoke uses `boot.elf` + `--disc` → **`disc.iso`**).
- **Alchemy:** CNK quarantined; proven fixes feed registry/self-heal; **no** CNK host hacks on Hitman/NFS.
- **Mode:** autonomous continuous — execute, log, retry; no idle, no routine asks.

## Execution plan (standing)

| Wave | Focus | Status |
|------|--------|--------|
| W1 | Hitman black canvas (GS) + web rebuild for Chrome | **IN FLIGHT** |
| W2 | `self_heal.py --library` + stale web/ACL sweep | Ready after W1 web done |
| W3 | Matrix → 100% (`logs/live-matrix-2026-11-07/`) | ~90% |
| W4 | Alchemy CNK `prims=2` | Blocked guest `+0x20`; quarantine |
| W5 | GoW browser min60 re-verify | Open |
| W6 | Store nightly: download → build → heal → verify | Scaffolded |

## Latest evidence

| Item | Result |
|------|--------|
| GS **XYOFFSET 11-bit** | `gs.hpp`, `raster.cpp`, `gpu/gpu.cpp`, `gs.cpp` — Hitman was using full `0x7000` as 1792px; HW uses **0** in low 11 bits |
| Hitman **native rebuild** | `build/native-a2116…/ps2run.exe` OK (~10:18) |
| Hitman **400f smoke** (`disc.iso`) | **97,531** prims, limit reached |
| Wrong smoke (`--disc …\disc` dir) | 0 prims — **do not use** |
| Hitman **web wasm** | `ps2web.js` **08:56** vs native **10:18** — **stale**; status **`building`**; self-heal queued web rebuild |
| Harness prior | ~865k prims, 60 FPS, **canvas black** (pre-XYOFFSET web) |
| Disc-fix board | Step 10 R5 cleared_with_evidence; R3+R4D1 applied |
| Self-heal first run | ACL ok; web rebuild queued; symptom `gs_negative_draw_boxes` until capture re-run |

## Artifacts (new this campaign)

- `verification/recovery/autonomous-pipeline-2026-11-07.md`
- `verification/recovery/self-heal-patch-system-2026-11-07.md`
- `verification/recovery/game-fix-registry.json`
- `scripts/autonomous_verify.py`, `scripts/self_heal.py`

## Open leads

1. **Confirm draw boxes** post-XYOFFSET (`PS2_CAPTURE` frame ~180) — expect x in 0..511 not −1792.
2. **Chrome harness** `canvas_lum` after web rebuild completes.
3. **DISPFB vs FRAME** page 400 vs 288 — present path; not sole cause if raster empty fixed.
4. Ghidra Hitman **ELF reimport** @ `0x00100000` (static plan in `logs/hitman-ghidra-static-analysis-plan-2026-11-07.md`).
5. Extend self-heal: FPS + harness luminance detectors.

## Immediate next (new agent)

1. Wait/finish Hitman **web-only build** → `ensure_web_build_readable` → harness snapshot.
2. `python scripts/autonomous_verify.py --game a2116d2ac08a7be4db4e8455ad58d2e5 --frames 600`.
3. If canvas still black, next GS lead: compose blit to page 400 / tex empty (ATE ruled out).
