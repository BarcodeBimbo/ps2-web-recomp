# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~21:58 local

## Status

**BLOCKED on matrix** for cycle-3 unbundled R3. No behavioral CDVD patch applied. Diag-only `g_trace_hle` lines are in `cdvdfsv.cpp`.

## Confirmed (parallel)

| | Hitman BM | NFS MW |
|--|--|--|
| ID | `a2116d2ac08a7be4db4e8455ad58d2e5` | `60c82f4a111da300ac23bbec85272788` |
| Draws | yes (600f / 300f smokes) | yes |
| Path | N 0x1 → `read_to_ee` → `complete_call` | same |
| Leftover WaitSema | 2, 7 | 2, 17/23/29/30/32 |
| Alchemy | none | none |

Shared stall class = CDVD complete / sync parking, **not** Alchemy. Sema 2 = durable libcdvd parking — never pulse it.

## Board cycles

1. **FAIL** — bundled R3 (+ R4 sceCdSync wake) while R1/R2 locked  
2. **PASS** — `R1_clear_with_evidence` (SIF drains to 0; no code)  
3. **Awaiting** — `R3_readee_length_harden` posted ~21:48; matrix has not written a verdict (~10+ min)

## curReadPos proof

`logs/discfix-hitman-curpos-300.log` / `logs/discfix-nfs-curpos-300.log`

- Hitman **35/35** completes: `curReadPos == expect` before complete  
- NFS same pattern  
- Remaining gap: readee **length fields** left 0 after memset; one Hitman **unaligned** dst `0x52C098`  
- Huge `N 0xE` counts = DiskReady probes, not real multi-hundred-k sector reads

## Proposed R3 (not applied)

Harden readee b1len/b2len (+ unaligned head/tail) in `read_to_ee` only. No R4. No R2 rewrite. No CNK hacks.

## Blocker

Matrix worker has not updated `discfix-matrix-board.json` since cycle 2. Disc-fix protocol forbids patching until `verdict=pass`.

If matrix fails R3 because R2 is still gated, next post will be `R2_clear_with_evidence` from the WaitSema ownership report (observe-only; no `host_signal(2)`).

## Hard rules held

- No CNK Alchemy pulses  
- No WaitSema / SIF-end rewrite  
- No commit yet
