# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~21:48 local

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

Sema **2** on both is durable libcdvd-class parking — do not `host_signal(2)`.

## Cycle 1 — FAIL

Proposed bundled R3 (+ optional sceCdSync wake). Matrix rejected: R1/R2 still locked; R4 bundled.

## Cycle 2 — PASS

`R1_clear_with_evidence` (no code). End-of-run SIF = 0 packets on both matrix smokes. R1 marked cleared.

## curReadPos proof (new)

Logs: `logs/discfix-hitman-curpos-300.log`, `logs/discfix-nfs-curpos-300.log`

- Hitman: **35/35** completes with `curReadPos == expect` before `complete_call`
- NFS: completes match the same way (e.g. `@0x5A9C40=2048`)
- So the basic byte-count write is already working

Remaining Sony gap for R3: **readee length fields** stay 0 after memset even when dest1 is fed; Hitman also has at least one **unaligned** dst (`0x52C098`). Huge `N 0xE` counts are DiskReady probes, not real reads.

## Cycle 3 — posted (awaiting)

`R3_readee_length_harden` — unbundled:

- Fix readee b1len/b2len when dests are fed; unaligned head/tail
- Keep proven curReadPos order + evidence logs
- **No** R4 sceCdSync wake, **no** R2 WaitSema rewrite, **no** CNK hacks

## Hard rules

- No CNK Alchemy hacks
- No WaitSema / SIF-end rewrite unless matrix unlocks
- No commit until stable dual-smoke pass

## Next

1. Matrix verdict on unbundled R3  
2. If pass → apply readee length harden in `cdvdfsv.cpp` only  
3. Re-smoke both games  
4. Update board + this report
