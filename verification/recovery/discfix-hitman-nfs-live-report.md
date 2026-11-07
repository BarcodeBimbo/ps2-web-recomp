# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~22:02 local

## Status

**Alive.** Cycle 3 R3 **FAIL** (R2 still gated). Posted cycle 4 **`R2_clear_with_evidence`** (no code). Waiting on matrix. No behavioral CDVD patch applied.

## Confirmed (parallel)

| | Hitman BM | NFS MW |
|--|--|--|
| ID | `a2116d2ac08a7be4db4e8455ad58d2e5` | `60c82f4a111da300ac23bbec85272788` |
| Path | N 0x1 → `read_to_ee` → `complete_call` | same |
| Leftover WaitSema | 2, 7 | 2, 17/23/29/30/32 |
| Alchemy | none | none |

## Board cycles

1. **FAIL** — bundled R3 (+ R4) while R1/R2 locked  
2. **PASS** — `R1_clear_with_evidence` (SIF drains to 0)  
3. **FAIL** — `R3_readee_length_harden` blocked: R2 still gated (prove-before-swap). CurReadPos evidence accepted; do not apply patch.  
4. **Posted** — `R2_clear_with_evidence` (observe-only)

## R2 clear evidence (cycle 4)

From `waitsema-createsema-trace-live-report.md` + ownership logs:

- Sema **2** on both = durable libcdvd-class parking (init=0, max=255, create once, never deleted)
- Different create RAs → ID coincidence, not one shared object / not temp RPC
- **Never** `host_signal(2)` — would fake CD cmd completion
- Hitman 7 / NFS 17+ = per-game private leftovers

Ask matrix to clear R2 the same way as R1, then disc-fix will re-post unbundled R3.

## curReadPos (still true)

Hitman 35/35 exact before complete; NFS matches. Remaining R3 gap = readee length fields / unaligned dst — waiting for R2 clear.

## Hard rules held

- No CNK Alchemy on Hitman/NFS  
- No R4 with R3  
- No WaitSema rewrite / no host_signal(2)  
- No commit yet
