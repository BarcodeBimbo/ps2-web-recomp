# Disc-fix joint-stable — R1 through R4

**Date:** 2026-11-06  
**Branch:** `windows`  
**Games:** Hitman Blood Money (`a2116d2ac08a7be4db4e8455ad58d2e5`), NFS Most Wanted (`60c82f4a111da300ac23bbec85272788`)

## What this marks

Matrix-proven disc CDVD path for the Hitman + NFS pair. Ranked rewrites R1–R4 are closed. Only behavioral code change is R3 in `runtime/src/iop/cdvdfsv.cpp`.

| Rank | Item | Outcome |
|------|------|---------|
| R1 | SIF end | cleared_with_evidence (queue drains to 0) |
| R2 | WaitSema fidelity | cleared_with_evidence (sema 2 = durable libcdvd parking; never `host_signal(2)`) |
| R3 | readee lengths / AlignReadBuffer | **verified_apply** — set `b1len`/`b2len` when dest1/dest2 fed; unaligned head/tail (+16/+80) |
| R4 | sceCdSync / finish_read wake | cleared_with_evidence — **no** CdSync wake code; mode=1 polls ≠ missing wake |

## Evidence

- Board: `verification/recovery/discfix-matrix-board.json` (through cycle 7)
- Reports: `discfix-hitman-nfs-live-report.md`, `test-matrix-live-report.md`
- Post-R3 smokes: `logs/discfix-r3-hitman-600.log`, `logs/discfix-r3-nfs-600.log`
- Hitman unaligned path: `dst=0x52C098 head=8 tail=8`

## Still gated / out of scope

- R5 pad/sound (separate track)
- CNK Alchemy quarantine (never apply to Hitman/NFS)
- No sceCdSync waiter wake landed

## Quarantine held

No CNK host_signal 16/54/55, soft-arm, FCE0 force, virt-LBA, or +24008 on this pair. No blind Wake of sema 2.
