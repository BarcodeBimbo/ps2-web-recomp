# W-HEAL report — 2026-11-07

**Worker:** W-HEAL (self-heal detectors + idle web rebuild)  
**Mission:** Extend `scripts/self_heal.py`; registry/docs additive; verify Hitman + library dry-run.

## Solve

| Item | Change |
|------|--------|
| Detectors | `canvas_black_harness` (harness `end_lum` & black_screen), `low_fps` (`[stats]` + harness FPS), `matrix_fail` (`matrix_phase_check` stdin), `fbp_triad_mismatch` (DISPFB vs FRAME FBP stub), explicit `web_build_stale` |
| Idle rebuild | `poll_until_build_idle()` after successful `panel.enqueue`; `wait_idle` on `queue_web_rebuild` |
| Registry | `global_runtime.self_heal` gains `min_canvas_lum`, detector list, poll timeouts |
| Docs | `verification/recovery/self-heal-patch-system-2026-11-07.md` detector table + idle note |
| Fix | Matrix stdin UTF-8 on Windows; log tail cap 500k for matrix score |

## Verify

### Hitman `a2116d2ac08a7be4db4e8455ad58d2e5`

**Dry-run** (`15:33:06Z`):

- Symptoms: `gs_negative_draw_boxes`, `web_build_stale`, `canvas_black_harness`, `low_fps`
- Detectors: `harness_end_lum=2.87`, `matrix_verdict=pass` (matrix scoped to game smoke / latest autonomous log only), `min_canvas_lum=5.0`
- Planned stubs: `fps_optimize_pass` (auto false), `chrome_canvas_gs_invariants`

**Live** (`15:33:28Z`):

- Web rebuild **skipped** (`reason: busy` — panel already `building`)
- ACL ok; post smoke **pass** (200f, matrix 5/5 pass)
- Wrote `games/a2116d2ac08a7be4db4e8455ad58d2e5/install_issues.json` + `logs/self-heal/a2116d2ac08a7be4db4e8455ad58d2e5-*.json`

### Library dry-run

- **13** native-ready ids scanned; no exceptions after UTF-8 matrix fix
- Stale web: Hitman, NFS `60c82f…`, CNK `b49f2e…`, + others with `web_build_stale`
- Harness black canvas: Hitman, CNK (end_lum &lt; 5)

## Check (master plan §4)

- [x] **Idle-aware web rebuild** — `poll_until_build_idle` wired on successful queue; evidence: live Hitman busy-skip (rebuild already in flight)
- [x] **Detectors** — Hitman dry-run lists `canvas_black_harness`, `low_fps`; matrix scorer integrated; `fbp_triad_mismatch` stub (plan-only action tier)
- [x] **`--library` sweep** — dry-run 13 titles 2026-11-07
- [ ] `proven_fixes[]` — unchanged (Alchemy not proven)
- [ ] T3 board gate — unchanged

## Next

- When Hitman panel build completes: re-run live `self_heal` to exercise **poll** + web-only rebuild completion
- Re-harness Hitman for `canvas_lum` ≥ 5 after GS/web alignment
- Wire `matrix_fail` evidence on a title with known matrix `verdict: fail` smoke
