# Overnight watchdog inventory — 2026-11-07 ~19:05 local

**Role:** overnight-watchdog  
**Status:** `overnight-watchdog-armed`  
**UTC:** 2026-11-08T00:05:30Z  
**Authority:** `logs/campaign-owner-permanent-mode.md` + call-log §8

## Heartbeat / owner

| Item | Value |
|------|-------|
| Prior owner heartbeat | 2026-11-08T00:05:01Z `permanent-overnight-encoded` pid=18916 |
| Owner pid 18916 | **DEAD** |
| Watchdog action | Armed; wrote `campaign-owner-alive.txt` + `campaign-owner-heartbeat.json` status=`overnight-watchdog-armed` |
| Spawn | Fresh campaign owner Task (seed: AGENT-CAMPAIGN-SNAPSHOT + permanent-mode) |

## Locks (single-writer) — DO NOT CLEAR while builds live

| Lock | Stated owner | Stated pid | Pid alive? | Build live? |
|------|--------------|------------|------------|-------------|
| `web-a2116…-next.lock` | campaign-owner-fresh | 20640 | DEAD | **YES** cmake=29328 ninja=5044 → `build/web-a2116…-next` ps2web |
| `web-a2116….lock` | campaign-owner-fresh | 20640 | DEAD | (same Hitman web tree; next is live) |
| `native-a2116….lock` | campaign-owner-fresh | 20640 | DEAD | no native cmake seen |
| `web-60c82f….lock` | W-NFS-2 | 30532 | DEAD | **YES** cmake=29716 ninja=28772 + python=11016 `W-NFS-rebuild-web.py` |
| `native-60c82f….lock` | W-NFS-platform | 29612 | DEAD | smoke reported exit=0 ~19:04 |
| `native-b49f2e….lock` | alchemy-rebuild-parent | 26656 | DEAD | **YES** cmake=11292 ninja=24536 → `ps2run` |

**Rule applied:** never kill in-flight cmake/ninja/harness; leave locks until build exits then reclaim.

## Live builds (protected)

- Hitman web-next: `cmake --build build/web-a2116…-next --parallel 1 --target ps2web`
- NFS web-next: `cmake --build build/web-60c82f…-next --parallel 1 --target ps2web` (+ python rebuild wrapper)
- CNK native: `cmake --build build/native-b49f2e… --parallel 1 --target ps2run`
- clang++ workers: 8620, 23228, 28508

## Lane staffing (platform heartbeats ~19:03–19:05)

| Lane | Open checkbox (next) | Heartbeat age | Staffing |
|------|----------------------|---------------|----------|
| Hitman | canvas_lum / compose (B) sprite-tex | ~1 min | recent W-HITMAN; web-next build orphaned (owner dead) — owner respawn owns |
| NFS | Chrome ≥60 + prefetch deepen | ~1 min | W-NFS smoke done; web rebuild live under python 11016 |
| Sly | STQ/PATH3/CLUT | ~2 min | W-SLY mapping — keep |
| GoW | Chrome min60 accept | ~0 min | W-GOW advancing mash/hold |
| Host | shared runtime | ~0 min | W-HOST windows_port hoist |
| Store | nightly pipeline / store→Chrome | done inline_verify | **need next-checkbox spawn** |
| CNK | prims=2 / loadgate | ~0 min | W-CNK monitor rebuild ~682/703 |

## Open master-plan checkboxes (high priority)

- Hitman: canvas lum; PSM mismatch; harness canvas_lum; DISPFB/FRAME compose; Chrome flawless
- NFS: Chrome flawless ≥60
- CNK: prims=2; proven_fixes; Chrome playable
- Library: autonomous_verify --library; registry; GoW min60; Sly/DefJam
- Store: nightly download→build→heal→verify; store pull→Chrome without manual patches
- Self-heal: proven_fixes[]; T3 board-gated
- FPS: 30 allowlist; library ≥60 sweep; WebGPU pacing pass
- Meta: plan updates; harness metrics Hitman; registry schema

## Watchdog next ticks

1. Refresh alive + heartbeat ~every few minutes
2. If owner heartbeat age >3min or owner dead → spawn/resume owner
3. If lane worker finished → spawn replacement for next open checkbox
4. Never idle — advance docs/registry/self_heal/verify on unlocked lanes
