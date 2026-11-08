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
| 3 | **WebGPU present pacing (§5) + solid-60 helpers** | Measure depth/RAF/budget; registry 30/50 allowlist; no overlay/frameskip pass; no V-Sync uncap | **Measure + helpers landed** (this turn) |

Also noted (already closed by peer / not re-touched): `PS2_INLINE_VERIFY` + `gate_inline_verify`; `windows_port.build_web` `_rmtree_onerror` hoist (store_pipeline **17/17** OK when PYTHONPATH=scripts).

§3 remaining open: nightly download→build→heal→verify scheduler; store→Chrome playable DoD.  
§5 remaining open: library Chrome sweep; final pacing **apply** (God-locked).

## Change implemented (this turn)

### A) `scripts/solid_60_mandate.py` — measure + mandate helpers

- Static measure of `host/web.cpp` + `gs.cpp` pacing constants → `logs/workers/W-HOST-present-pacing-measure-2026-11-07.json`
- `resolve_min_fps` / `validate_exceptions` for registry allowlist (`30`/`50` + required reason)
- `evaluate_solid_60`: stats/harness FPS only; **rejects fps_overlay-only**; **rejects frameskip/uncap signals**
- CLI: `--measure`, `--self-check`, `--validate-exceptions`, `--game`

**Verify:**

```text
solid_60_mandate --self-check → self_check_ok true
constants: kMaxBehind 4/3, RAF skip >2, budget 10ms, spin 1.5ms, g_vsync true, uncap guard true
overlay-only synthetic → fail; frameskip keyword → fail; stats 60 → pass
Hitman live metrics → fail (min 10.6 + hitch-train maxMs) — expected, measure only
```

### B) Registry + wire-up

- `game-fix-registry.json`: `min_fps_exception_policy` (allowed 30/50, helpers path, no-overlay / no-frameskip / no-uncap rules); `min_fps_exceptions` still `{}`
- `self_heal.min_fps_target` → `resolve_min_fps`; `detect_low_fps` **ignores** `fps_overlay`; report attaches `detectors.solid_60`
- `autonomous_verify.verify_game` attaches `solid_60` (measure/report; does not flip smoke status)

**No product change** to `pace()` / `ps2web_set_vsync` / FPS ceiling.

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

## Return

**Changed:** solid-60 helpers + pacing measure + registry allowlist policy; self_heal/verify wire-up.  
**Top remaining shared gap:** §5 library Chrome ≥60 sweep; pacing apply still God-locked after measure.
