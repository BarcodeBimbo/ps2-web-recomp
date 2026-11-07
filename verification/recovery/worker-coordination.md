# Worker coordination (corrected scope)

Updated: 2026-11-06 — **partial unpark only**.

## PARKED (do not launch / stop if started)

- Mobile / multi-platform UI redesign — deferred until **after** disc-fix
- Software renderer ×10 speedup
- Crash Bandicoot research/dev

## ACTIVE tracks (parallel, no blocking between them)

| # | Track | Role |
|---|--------|------|
| 1 | **Disc-fix** | Hitman BM + NFS MW hybrid accurate CDVD end-to-end (`cdvdfsv.cpp` / `cdvd.cpp` wake). Generic only. |
| 2 | **Test-matrix** | Five-phase matrix; prove-before-swap; validates each disc-fix step via shared board before next patch. |
| 3 | **CNK ELF Alchemy** | Full redo bin walk of `boot.elf` — vtables, addresses, structure map. Read-only preferred until map is solid. |
| 4 | **CNK null-bind** | `0x51ACEC` / `0x725F50` / vt+80/+84 — quarantine from Hitman/NFS. |
| 5 | **Sly GS/VU** | Diagnosis from parked research note; differentials. No CNK. |
| 6 | **WaitSema / CreateSema** | Ownership tracing for Hitman+NFS leftovers. Observe-first; no blind `host_signal(2)`. |
| 7 | **BIOS zip** | Reference-only research. Do not execute or copy BIOS into the repo. |

## Priority pair handoff

Board file: `verification/recovery/discfix-matrix-board.json`

1. Disc-fix posts proposed change + evidence (both games).
2. Matrix runs phases → posts pass/fail in plain English.
3. Disc-fix applies next patch **only** after matrix pass.
4. Commit only when a stable build is reached — then commit freely.

### Game IDs
- Hitman Blood Money: `a2116d2ac08a7be4db4e8455ad58d2e5`
- NFS Most Wanted: `60c82f4a111da300ac23bbec85272788`
- CNK: `b49f2e769315347e8bda839feb705744`
- Sly: `c0c4527037b6168660829a0eb13df1a3`

## Hard quarantine
CNK Alchemy pulses (16/54/55, soft-arm, FCE0 force, virt-LBA, +24008) must **never** be applied as Hitman/NFS fixes.
