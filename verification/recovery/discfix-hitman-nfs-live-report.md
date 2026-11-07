# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~22:11 local

## Status

**Alive.** R3 **verified_apply**. Posted cycle 7 `R4_clear_with_evidence` (no code). No commit yet.

## Cycle summary

| # | Proposal | Verdict |
|---|----------|---------|
| 1 | Bundled R3+R4 | FAIL |
| 2 | R1 clear | PASS |
| 3 | R3 (R2 gated) | FAIL |
| 4 | R2 clear | PASS |
| 5 | R3 re-post | PASS → applied |
| 6 | R3 post-apply verify | PASS (`verified_apply`) |
| 7 | R4 clear | **posted** |

## R3 landed

`runtime/src/iop/cdvdfsv.cpp`: readee b1len/b2len when dest fed; unaligned head/tail. Hitman smoke showed `readee unaligned dst=0x52C098 head=8 tail=8`. Both games 600f green (~128k / ~208k prims, SIF 0, no Alchemy).

## R4 proposal (this cycle)

Clear-with-evidence only: EE reads complete via cdvdfsv; Hitman `sceCdSync(mode=1)` busy polls do not need a new FSV→finish_read wake for the success bar. If matrix wants a real wake, they should fail with the waiter case.

## Hard rules held

No CNK Alchemy · no host_signal(2) · no commit yet
