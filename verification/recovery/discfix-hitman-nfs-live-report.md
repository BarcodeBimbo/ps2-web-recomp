# Disc-fix live report — Hitman BM + NFS MW

Updated: 2026-11-06 ~22:08 local

## Status

**Alive.** R3 readee-length harden **applied** and both games re-smoked green. Posted cycle 6 `R3_post_apply_verify` for matrix. No commit yet (waiting post-verify).

## Board cycles

1. FAIL — bundled R3 (+R4)  
2. PASS — R1 clear (SIF drain)  
3. FAIL — R3 blocked by R2  
4. PASS — R2 clear (sema 2 durable parking; never host_signal(2))  
5. PASS — R3 allow → **patched `cdvdfsv.cpp`**  
6. **Posted** — post-apply verify (no new code)

## What landed (R3)

In `runtime/src/iop/cdvdfsv.cpp` `read_to_ee`:

- When dest1/dest2 are fed, write matching **b1len/b2len**
- When bounce dst is **unaligned** and no staged dest, stage head/tail in readee (+16 / +80)
- Kept curReadPos-before-complete + HLE evidence logs  
- Did **not** touch cdvd.cpp CdSync wake, WaitSema, or CNK Alchemy

## Post-apply smokes (600f)

| | Hitman | NFS |
|--|--|--|
| Log | `logs/discfix-r3-hitman-600.log` | `logs/discfix-r3-nfs-600.log` |
| Prims | 127974 | 208253 |
| Frame limit | yes | yes |
| SIF end | 0 packets | 0 packets |
| Unaligned | `dst=0x52C098 head=8 tail=8` | n/a this run |
| Alchemy | none | none |
| Leftover sema 2 | still (durable parking) | still |

## Next

Matrix verify of R3 apply. Then a separate cycle may propose R4 CdSync (not bundled here). Commit only after stable verify.

## Hard rules held

No CNK Alchemy · no R4 with R3 · no host_signal(2) · no commit yet
