# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~21:42 local

## Status

**Waiting on matrix** for cycle-3 unbundled R3. R1 cleared. Behavioral CDVD fix not applied yet (diag logs only).

## What we confirmed (parallel)

Both games share the same CDVD path, not Alchemy:

| | Hitman Blood Money | NFS Most Wanted |
|--|--|--|
| ID | `a2116d2ac08a7be4db4e8455ad58d2e5` | `60c82f4a111da300ac23bbec85272788` |
| Disc-fix HLE 600f | ~128k prims | ~208k prims |
| Matrix 600f | ~78k prims | ~50k prims |
| Path | `cdvdfsv` N 0x1 → `read_to_ee` → `complete_call` | same |
| Leftover WaitSema | **2**, 7 | **2**, 17/23/29/30/32 |
| Alchemy pulses | none | none |

Hitman also hammers IOP `sceCdStatus` / `sceCdSync` while EE reads go through cdvdfsv. Sema **2** on both is durable libcdvd-class parking (ownership report) — do not `host_signal(2)`.

Logs: `logs/discfix-hitman-bm-600-hle.log`, `logs/discfix-nfs-mw-600-hle.log`, `logs/matrix-hitman-600.log`, `logs/matrix-nfs-600.log`.

## Cycle 1 — FAIL

Proposed `R3_generic_complete_path` (payload + readee + curReadPos + optional sceCdSync wake).

Matrix rejected apply because:

1. Prove-before-swap: R1 and R2 still locked, so R3 cannot land first
2. Proposal bundled R4-style sceCdSync wake with R3
3. Logs did not yet show explicit curReadPos/readee write lines

No files were patched. Quarantine held.

## Cycle 2 — posted

Proposed `R1_clear_with_evidence` (no code):

- End-of-run SIF queue is **0 packets** on both matrix smokes
- No held RPC “waiting for reply” lines
- Ask matrix to clear R1 so an **unbundled R3** (readee + curReadPos only, no CdSync wake) can be proposed next

## Hard rules still in force

- No CNK Alchemy hacks (16/54/55, soft-arm, FCE0, virt-LBA, +24008)
- No WaitSema / SIF-end rewrite unless matrix unlocks that rewrite
- No commit until a stable dual-smoke pass

## Next

1. Wait for matrix verdict on R1 clear  
2. If pass → post unbundled R3 with stronger curReadPos/readee evidence  
3. Only after that pass → patch `cdvdfsv.cpp` (+ `cdvd.cpp` only if matrix allows R4 later)  
4. Re-smoke both games (prims move, ~60 FPS feel, graphics menu untouched)
