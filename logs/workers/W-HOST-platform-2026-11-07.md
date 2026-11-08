# W-HOST — Shared host runtime (platform rebalance)

**Worker:** W-HOST (replacement)  
**Date:** 2026-11-07  
**Lane:** Shared host runtime (not game-specific). No CNK Alchemy obj+0x20 surgery. Hitman DISPFB quarantine preserved.  
**Locks avoided:** `web-a2116*-next`, `native-b49f*`, `web-60c82f*` (no cmake/ninja kill or contend).

## Heartbeat

`logs/workers/W-HOST-platform-heartbeat.log`

## Inventory — high-leverage shared gaps (2–3)

| # | Gap | Why multi-title | Status |
|---|-----|-----------------|--------|
| 1 | **`self_heal` `fbp_triad_mismatch` blind on default present logs** | Detector only matched `PS2_PRESENT_FRAME` / mode-B strings; real `[gs] present fb:…` never fired | **Fixed + verified** (prior) |
| 2 | **`copy_frame` GPU height ignored `shown_lines`** | WebGPU/async readback used raw DH; size mismatch for interlaced titles | **Fixed in tree** (prior; rebuild deferred — locks) |
| 3 | **WebGPU present pacing (§5) + solid-60 helpers** | Measure depth/RAF/budget; registry 30/50 allowlist; no overlay/frameskip pass; no V-Sync uncap | **Measure + helpers landed** (prior) |
| 4 | **`validate_exceptions` not wired into registry consumers** | Allowlist policy existed but verify/heal could silently accept bad rows | **Fixed + verified** (this turn) |

Also noted (already closed by peer / not re-touched): `PS2_INLINE_VERIFY` + `gate_inline_verify`; `windows_port.build_web` `_rmtree_onerror` hoist; versioned registry schema + `discfix_applied[]` objects.

§3 remaining open: store→Chrome playable DoD.  
§5 remaining open: library Chrome sweep (≥60); final pacing **apply** (God-locked).

## Change implemented (this turn)

### A) Wire `validate_exceptions` into registry path

- `load_registry_checked()` + policy `required_fields` (`reason`/`evidence`/`verified_date`)
- Incomplete/legacy/invalid fps exceptions rejected by `resolve_min_fps` (falls back to default 60)
- Registry: `schema_validators[]` + `min_fps_exception_policy.wired_into`
- `autonomous_verify.registry_exception_audit()` on every run; `--library-measure` (no cmake)
- `self_heal` detectors attach `exception_problems`

### B) Library sweep helpers (measure-only)

- `measure_library_solid60` / `--library` CLI → `logs/workers/W-HOST-solid60-library-measure-2026-11-07.json`
- Includes harness-runs fallback; reports `discfix_applied` + schema version
- `autonomous_verify --library-measure` + `--skip-locked` for safe overnight use

### C) Self-heal detector polish (unlocked)

- `find_harness_entry` prefers `cyberarcade-harness-metrics-latest.json` + per-run `metrics.json`
- `harness_observe_end_lum` reads `canvas_lum_end`
- GoW II dry-run: `exception_problems=[]` (`logs/workers/W-HOST-selfheal-gow2-dryrun-2026-11-07.json`)

**No product change** to `pace()` / `ps2web_set_vsync` / FPS ceiling.

## Verify

```text
solid_60_mandate --self-check → self_check_ok true
validate_exceptions (live empty map) → []
--library / autonomous_verify --library-measure → 14 titles; 0 pass / 2 fail / 11 no_metrics / 1 quarantined
self_heal --game GoW2 --dry-run → detectors.exception_problems []
```

## Present pacing measure (snapshot)

| Constant | Value |
|----------|-------|
| `kMaxBehind` emscripten / native | 4 / 3 |
| RAF skip when `presents_queued` | > 2 |
| `render_pending` budget | 10 ms |
| pace spin tail | 1.5 ms |
| `g_vsync` default | true |
| Uncap under V-Sync | forbidden (in-tree guard) |
| `product_changes_applied` | **false** |

## Quarantine / non-goals

- No Alchemy host hacks; no Hitman FRAME-default present.
- No contention on locked Hitman/NFS/CNK builds.
- No V-Sync uncap / FPS-limit product apply (God track).
- Library Chrome sweep checkbox **not** flipped (titles not yet ≥60).

## Master-plan flips

- §5 validate_exceptions + library measure helpers → **[x]**
- §8 versioned registry schema + discfix_applied → **[x]**

## Unlocked library smoke (this turn, no cmake)

`--skip-locked --frames 200` on 9 native-ready titles (Hitman/NFS/CNK/Sly locks skipped):

| Result | Titles |
|--------|--------|
| smoke **pass** | Ratchet 2, Def Jam, NFS UG2, Hot Shots Golf 3, RE4 |
| smoke **fail** | GoW II (0 prims), GoW USA (2 prims), GT4 (missing_code 0x01000008), Hitman 2 (LoadExec halt) |
| solid_60 | 0 pass (native logs lack `[stats]` FPS; Chrome metrics still required) |

Evidence: `logs/workers/W-HOST-unlocked-library-verify-summary-2026-11-07.json`

## Chrome solid-60 library collect (continuation)

**Run:** `20261108T001703Z` — observe 30s; expanded harness GAMES for library paths.  
**Skipped:** GoW USA (`gow-min60-browser.lock` W-GOW); Hitman BM (`/play/` 404 while web-next builds); CNK quarantine.  
**Policy:** V-Sync default on; no product uncap; overlay scraped for diagnostics only (never pass); no frameskip.

| Title | Prior | After | sustained_fps | solid-60 |
|-------|-------|-------|---------------|----------|
| Sly 1 | no_metrics | **gained** | 53.5 | FAIL (min + hitch-train) |
| GoW II | no_metrics | **gained** | 13.4 | FAIL |
| Ratchet 2 | no_metrics | **gained** | 0.6 | FAIL |
| Def Jam | no_metrics | **gained** | 23.9 | FAIL |
| GT4 | no_metrics | **gained** | 28.5 | FAIL |
| NFS UG2 | no_metrics | **gained** | 1.9 | FAIL |
| Hitman 2 | no_metrics | **gained** | n/a (abort LoadExec) | FAIL |
| Hot Shots 3 | no_metrics | **gained** | 17.1 | FAIL |
| RE4 | no_metrics | **gained** | 57.1 | FAIL (closest) |
| NFS MW | fail | fail (re-measure) | 21.1 | FAIL |
| Hitman BM | fail | fail (stale metrics) | 10.6 | FAIL |
| GoW USA | no_metrics | no_metrics | — | deferred W-GOW |
| Downhill | no_metrics | no_metrics | — | `/play/` 404 |
| CNK | quarantined | quarantined | — | — |

**Library totals:** **0 pass / 11 fail / 2 no_metrics / 1 quarantined**. **No solid-60 PASS.**

Evidence: `logs/harness-runs/20261108T001703Z/metrics.json`, `logs/workers/W-HOST-solid60-library-measure-2026-11-07.json`, `logs/workers/W-HOST-solid60-chrome-collect-2026-11-07.log`.

§5 library sweep checkbox **not** flipped.

## Return

**Changed:** Chrome solid-60 library collect for 10 ready harness paths; 9 titles newly gained metrics; still 0 PASS.  
**Top remaining shared gap:** §5 library Chrome ≥60 sweep; pacing apply still God-locked; GoW USA + Hitman BM re-measure when free.
