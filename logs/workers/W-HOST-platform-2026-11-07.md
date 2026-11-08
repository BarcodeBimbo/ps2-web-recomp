# W-HOST — Shared host runtime (platform rebalance)

**Worker:** W-HOST  
**Date:** 2026-11-07  
**Lane:** Shared host runtime (not game-specific). No CNK Alchemy obj+0x20 surgery. Hitman DISPFB quarantine preserved.  
**Locks avoided:** `web-a2116*-next`, `native-b49f*` (no cmake/ninja kill or contend).

## Heartbeat

`logs/workers/W-HOST-platform-heartbeat.log`

## Inventory — high-leverage shared gaps (2–3)

| # | Gap | Why multi-title | Status |
|---|-----|-----------------|--------|
| 1 | **`self_heal` `fbp_triad_mismatch` blind on default present logs** | Detector only matched `PS2_PRESENT_FRAME` / mode-B strings; real `[gs] present fb: dispfb=… frame0=… frame1=… last_ctx=…` never fired | **Fixed + verified** |
| 2 | **`copy_frame` GPU height ignored `shown_lines`** | WebGPU/async readback used raw DH; `present`/`display` use CRT-visible `shown_lines` → size mismatch for interlaced titles on 2D/copy path | **Fixed in tree** (rebuild deferred — locks) |
| 3 | **WebGPU present pacing (§5 open)** | `host/web.cpp` `pace()` + `post_present` `kMaxBehind` / RAF skip at depth >2 — final optimization still open; God-track for V-Sync uncap | **Documented PR-sized (below)** |

Also noted (already closed by peer / not re-touched): `PS2_INLINE_VERIFY` + `gate_inline_verify`; `windows_port.build_web` `_rmtree_onerror` hoist (store_pipeline **17/17** OK).

§3 remaining open: nightly download→build→heal→verify scheduler; store→Chrome playable DoD.

## Change implemented

### A) `scripts/self_heal.py` — PRESENT_FB detector

- Added `PRESENT_FB` regex for default DISPFB present trace.
- `detect_fbp_triad_mismatch`: fire when `dispfb != frame{last_ctx}` (draw page ≠ present page).
- Kept mode-B / `dispfb_fbp` regex as secondary.
- Planned action remains **`auto: False`** with explicit note: keep DISPFB default (Hitman quarantine); `PS2_PRESENT_FRAME=1` experiments only.

**Verify:**

```text
detect_fbp_triad_mismatch OK
  Hitman-style dispfb=400 frame0=288 last_ctx=0 → True
  matched draw page → False
  mode-B log → True
tests/store_pipeline.py → 17/17 OK
```

### B) `runtime/src/gs/gs.cpp` — `copy_frame` height hygiene

GPU `copy_frame` path now computes height with `shown_lines(...) / magv`, matching `present`/`display`. Does **not** change `resolve_present_source` (still DISPFB unless `PS2_PRESENT_FRAME`).

**Verify:** static parity with `present()`/`display()` formulas; native/web rebuilds deferred to avoid `web-a2116` / `native-b49f` locks.

## PR-sized follow-up (not applied) — WebGPU pacing

**Files:** `host/web.cpp` (`pace`, `wait_shown`, `ps2web_set_fps_limit`); `runtime/src/gs/gs.cpp` (`post_present` `kMaxBehind` 4 emscripten / 3 native).

**Intent (additive):** measure-first library sweep; optional per-game `min_fps` allowlist in registry; **do not** flip default V-Sync off or raise uncapped EE under vsync (known hitch trains). Candidate PR: document current depth/RAF/budget constants + registry allowlist hook only — no product shell.

## Quarantine / non-goals

- No Alchemy host hacks; no Hitman FRAME-default present.
- No contention on locked Hitman/NFS builds.

## Return

**Changed:** shared `self_heal` FBP triad detector now sees default present logs (verified); `copy_frame` aligned to `shown_lines`.  
**Top remaining shared gap:** §5 WebGPU/present pacing final optimization (measure + allowlist; no V-Sync uncap without God unlock).
