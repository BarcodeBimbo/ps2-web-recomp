# Self-healing patch system (2026-11-07)

**Mandate:** After Alchemy fixes are proven, every store install is **isolated**, **diagnosed**, and **repaired** without manual steps. Chrome must play every library title flawlessly at ≥60 FPS.

## Isolation model

| Artifact | Role |
|----------|------|
| `games/<id>/` | Managed install root (disc, logs, identity) |
| `games/<id>/health.json` | `install_health` gate (missing code, prims, halt) |
| `games/<id>/install_issues.json` | **Self-heal** snapshot (symptoms + actions) |
| `build/native-<id>/` vs `build/web-<id>/` | Staleness detection (runtime newer than wasm) |
| `verification/recovery/game-fix-registry.json` | Global + per-game tracks, quarantine, smoke frames |

Each install is keyed by **32-char id**; symptoms never bleed across ids except **global runtime** fixes (e.g. GS XYOFFSET 11-bit).

## Detectors (automatic)

| Signature | Source | Meaning |
|-----------|--------|---------|
| `missing_code:*` | explore/smoke | Unrecompiled EE hole |
| `near_zero_prims` | explore/smoke | Black screen / GS stall |
| `gs_negative_draw_boxes` | capture TSV / TRACE | XYOFFSET / clip mismatch |
| `alchemy_pulse_on_non_cnk` | matrix scorer pattern | CNK virt leaked into title |
| `web_serve_or_acl` | build/harness logs | ps2web.js unreadable in panel |
| `web_build_stale` | mtime native > web | Chrome player behind runtime |
| Matrix `verdict: fail` | `matrix_phase_check.py` | Five-phase boot/read/stream break |

## Action tiers (auto vs gated)

| Tier | Action | Auto? |
|------|--------|-------|
| T0 | Global runtime already in tree (R3, R4-D1, GS XYOFFSET) | Applied at build |
| T1 | `ensure_web_build_readable` + **web-only rebuild** | **Yes** (`self_heal.py`) |
| T1 | Post-fix **smoke** via `autonomous_verify.py` | **Yes** |
| T2 | Registry **quarantine** (`disc_fix_quarantine`, alchemy track) | **Yes** on leak detect |
| T3 | Disc-fix **behavioral** patches | Board `allow_discfix_apply` (still human gate for HLE rewrite) |
| T4 | Per-game EE patches / Alchemy host hacks | **No auto** — CNK-only quarantine |

## Implementation

- **Orchestrator:** `scripts/self_heal.py` — `heal_game`, `heal_library`
- **Hook:** `panel.py` build worker calls `heal_game` after `write_health`
- **Verify:** `scripts/autonomous_verify.py` — smoke + health + matrix JSON
- **Docs:** `autonomous-pipeline-2026-11-07.md` + this file

## Next loop (continuous)

1. Prove Hitman **canvas** after GS XYOFFSET + web rebuild.
2. Run `self_heal.py --library` → fix stale web builds for all ready titles.
3. Extend detectors: **harness canvas_lum** (Chrome), **FPS < 60** from `[frame]` logs.
4. When CNK Alchemy **proven**, add detector `cnk_prims_2` → auto soft-arm observe only (no Hitman bleed).
5. Fold harness into nightly: store download → build → heal → verify → log `logs/self-heal/`.
