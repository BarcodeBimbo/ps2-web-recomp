# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~22:26 local

## Status

**Alive.** Cycle 7 **`R4_clear_with_evidence` → PASS**. No CdSync wake code landed. Disc CDVD ranked path R1–R4 is done. **No commit** (waiting on parent for joint-stable call). R5 pad/sound still gated.

## Cycle summary

| # | Proposal | Verdict |
|---|----------|---------|
| 1 | Bundled R3+R4 | FAIL |
| 2 | R1 clear | PASS |
| 3 | R3 (R2 gated) | FAIL |
| 4 | R2 clear | PASS |
| 5 | R3 re-post | PASS → applied |
| 6 | R3 post-apply verify | PASS (`verified_apply`) |
| 7 | R4 clear | **PASS** (`cleared_with_evidence`) |

## Ranked rewrite state

| ID | State |
|----|--------|
| R1 SIF end | cleared_with_evidence |
| R2 WaitSema | cleared_with_evidence (sema 2 durable parking; never host_signal(2)) |
| R3 readee | **verified_apply** in `cdvdfsv.cpp` |
| R4 CdSync | cleared_with_evidence (Hitman ~1854 mode=1 polls vs ~10 mode=0; no wake rewrite) |
| R5 pad/sound | **still gated** |

## What remains (research note)

- **Disc-fix CDVD job for Hitman/NFS:** complete for R1–R4. Post-R3 smokes green (~128k / ~208k prims @600f, SIF 0, unaligned readee fired on Hitman).
- **R5** is pad/sound RPC fidelity (NFS leftovers 17/23/32 ≈ pad; 29/30 ≈ sound; Hitman 7 ≈ callback/sound) — **not** a CDVD complete-path fix. Separate proposal if parent wants that track next.
- **Commit:** tree has only the verified R3 `cdvdfsv.cpp` change (+ diag logs). Ready for a **parent joint-stable commit ask** — disc-fix will **not** commit until told.

## Hard rules held

No CNK Alchemy · no CdSync wake · no host_signal(2) · no commit

## Heartbeat 22:26

Idle watch: board still idle_r4_pass_awaiting_parent, proposed_change=null, R5 still_gated. No soak request. No commit. No CdSync wake.
