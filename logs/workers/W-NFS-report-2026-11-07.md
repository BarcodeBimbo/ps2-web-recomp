# W-NFS worker report — NFS Most Wanted second title (2026-11-07)

**Worker:** W-NFS  
**Game:** Need for Speed: Most Wanted (`60c82f4a111da300ac23bbec85272788`)  
**Plan:** `logs/master-campaign-plan-2026-11-07.md` §2b  
**Concept ref:** `logs/hitman-black-canvas-concept-phase-2026-11-07.md` (shared A–H catalog)

---

## Mission summary

| Step | Result | Evidence |
|------|--------|----------|
| `autonomous_verify.py` smoke 500f | **pass** (health ok + matrix pass) | `logs/autonomous-pipeline/summary-20261107T153244Z.json` |
| Native smoke log | exit 0, 500 frames, **140753** prims, frame limit | `logs/autonomous-pipeline/60c82f4a111da300ac23bbec85272788-500f-20261107T153240Z.log` |
| `matrix_phase_check nfs_mw` | **verdict pass** (all 5 phases) | same log; scorer fix below |
| GS A–H vs Hitman | documented; **different symptom class** on Chrome | harness `logs/harness-runs/20261107T131057Z/summary.json` |

**Master plan §2b checked:**

- [x] Same GS invariant checklist (this report §3)
- [x] Five-phase matrix scorer gap (`fileio` disc opens for `nfs_mw`)
- [ ] NFS Chrome flawless + ≥60 FPS — **open** (harness mid-shot dip + ~13–20 FPS overlay)

---

## 1) Autonomous verify smoke

```text
python scripts/autonomous_verify.py --game 60c82f4a111da300ac23bbec85272788 --frames 500 --json
```

```json
"status": "pass",
"health": { "status": "ok", "primitives": 140753, "frames": 500, "reached_frame_limit": true },
"matrix": { "verdict": "pass", "first_fail_phase": null }
```

Disc path: `games/60c82f4a…/disc.iso` + `disc/boot.elf` (global gate). No CNK/Alchemy quarantine skip.

---

## 2) Matrix phase check (`nfs_mw`)

### Scorer fix (shared tooling, not runtime hack)

NFS loads IOP/modules via **`[fileio] open cdrom:\…`** (e.g. `IRX281A.BUN`), not `cdvdfsv] search … -> found` strings. Prior scorer reported `cdvd_searches_found: 0` and failed `first_disc_read` despite healthy boots.

**Change:** `verification/recovery/matrix_phase_check.py`

- Count `FILEIO_DISC_OPEN` toward `disc_read_signals` for `game == nfs_mw` only (Hitman still CDVD-search keyed).
- Accept stdin `-` for `autonomous_verify.py` pipe (was `FileNotFoundError` on path `-`).

Re-score of 500f smoke:

| Phase | Status |
|-------|--------|
| boot | pass |
| menu | pass |
| first_disc_read | pass (`fileio_disc_opens: 1`, `disc_read_signals: 1`) |
| streaming | pass |
| sustained_run | pass |

`alchemy_contamination: false`, `sif_packets_waiting: 0`, classified leftover semas (2,17,23,29,30,32) — same R5 classification as board, no new HLE apply.

Board updated: `verification/recovery/discfix-matrix-board.json` → `nfs_mw` mechanical pass log pointer.

---

## 3) GS behavior — shared A–H checklist (Hitman vs NFS)

**Standing invariant (both titles):** high EE/GS activity does not imply a visible framebuffer (`logs/hitman-black-canvas-concept-phase-2026-11-07.md` §1).

| Mode | Hitman BM (native/chrome) | NFS MW (this run) | Shared policy |
|------|---------------------------|-------------------|---------------|
| **A** Display FBP ≠ draw FBP | Suspect (sustained black) | Not primary suspect (visible lum recovery) | Detect via static S2 + present readback; **no title-specific host hack** |
| **B** Circuit EN mismatch | Deprioritized for Hitman (concept: EN2) | Not evidenced in smoke strings | Same present-circuit rules for all EE titles |
| **C** FRAME mask / black RGB | Suspect | Unlikely (colorful boot/end shots) | Shared GS mask diagnostics |
| **D** Alpha/test reject all | Ruled weak alone on Hitman | No extra alpha shim on NFS | Shared TEST/ALPHA logging only |
| **E** Clear-only on displayed FBP | Suspect (near-black lum) | Transient mid dip only | BGCOLOR/clear-sprite analysis in Ghidra track |
| **F** Scissor/XYOFFSET | Active Hitman layer (runtime XYOFFSET fix global) | Benefits from **global** XYOFFSET fix; no NFS fork | **Shared runtime** only |
| **G** PSM draw vs present | Open on Hitman Chrome | Boot canvas_lum 20+ suggests present path often OK | Shared PSM audit |
| **H** Host present / stale field | Hitman Chrome **sustained** black (`canvas_lum≈0.14` all shots) | Chrome: boot/start **~20**, mid **~1**, end **~7.4** — activity ≠ sustained black canvas | Same harness `canvas_lum` gate |

### Native smoke GS lines (NFS 500f)

- `[gs] SetGsCrt interlace 1 mode 0x2 field 1`
- `[gs] VSINT raise … MASKED — no intc` (commercial EE pattern; not NFS-specific patch)
- Final: **140753 primitives**, rich register write histogram

### Chrome harness (`20261107T131057Z`)

| Shot | NFS `canvas_lum` | Hitman `canvas_lum` |
|------|------------------|---------------------|
| 01_boot | 20.39 | 0.18 |
| 02_observe_start | 20.45 | 0.23 |
| 03_observe_mid | 0.997 | 0.13 |
| 04_observe_end | 7.43 | 0.14 |

NFS: `max_prims` 52308, goal `gpu_boot` ok, but overlay FPS **~13–20** (below 60 bar) and `black_screen` on mid/end shots (transient, not Hitman-class sustained blackout).

**Conclusion:** Apply the **same A–H catalog** and shared runtime (R3/R4D1, XYOFFSET); do **not** port Hitman-only present hacks. NFS second-title readiness = **disc/matrix/autonomous pass** + checklist mapped; **Chrome flawless / 60 FPS** remain §2b open items.

---

## 4) Shared invariants (document for pipeline / self-heal)

1. **Commercial EE disc-fix lane** — global `R3_readee`, `R4D1_DiskReady`; **no** CNK `igfileio` / Alchemy host_signal on Hitman/NFS (`game-fix-registry.json` quarantine).
2. **Matrix profiles** — `hitman_bm` → CDVD search strings; `nfs_mw` → CDVD **or** `fileio` cdrom open counts toward disc read.
3. **Verify loop** — `autonomous_verify.py` → smoke + `install_health` + `matrix_phase_check` JSON; logs under `logs/autonomous-pipeline/`.
4. **Black canvas triage** — use A–H + `canvas_lum` harness; promote failures to shared catalog, demote per-title assumptions (concept doc §5).
5. **Leftover WaitSema waiters** — classified noise on both titles at R5; not autoranked HLE without named failure.

---

## 5) Open leads (not W-NFS close)

| Item | Owner hint |
|------|------------|
| NFS Chrome flawless + ≥60 FPS | W-CHROME60 + web rebuild / hitch (console shows 500ms+ hitches) |
| Hitman sustained black canvas | W-HITMAN L1–L4 |
| `autonomous_verify --library` | §2d after Hitman Chrome gate |

---

## 6) Files touched

| File | Change |
|------|--------|
| `verification/recovery/matrix_phase_check.py` | NFS `fileio` disc opens; stdin `-` |
| `verification/recovery/discfix-matrix-board.json` | `nfs_mw` mechanical matrix pass |
| `logs/master-campaign-plan-2026-11-07.md` | §2b two checkboxes |
| `logs/workers/W-NFS-report-2026-11-07.md` | this report |

---

*W-NFS — solve → verify → check → next.*
