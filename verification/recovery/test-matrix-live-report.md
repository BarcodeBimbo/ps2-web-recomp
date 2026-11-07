# Test-matrix live report

Updated: 2026-11-06 ~21:32 local

## Status

**Blocked on disc-fix proposal.** Matrix is watching the shared board. No `proposed_change` yet, so no gate cycle has run.

## Games

| Game | ID | Runner | Boot |
|------|-----|--------|------|
| Hitman Blood Money | `a2116d2ac08a7be4db4e8455ad58d2e5` | ready | `cdrom0:\SLUS_211.08;1` |
| NFS Most Wanted | `60c82f4a111da300ac23bbec85272788` | ready | `cdrom0:\SLUS_212.67;1` |

## Five phases (Sony-tied)

1. **boot** — EE frames; SIF IOP reboot + LOADFILE; no hard halt
2. **menu** — prims climb; menu assets load; pad still works
3. **first_disc_read** — CDVD complete; `curReadPos` / `readee` behavior; WaitSema not falsely pulsed (no Alchemy 16/54/55)
4. **streaming** — more disc reads; SIF queue drains
5. **sustained_run** — frame limit; prims keep moving; ~60-class draw

## Prove-before-swap gate

Ranked rewrites stay locked until earlier phases pass with real evidence:

- R1 SIF end → after boot + menu pass
- R2 WaitSema fidelity → after R1 + first disc read
- R3 readee → after R2 + streaming evidence
- R4 CdSync → after R3
- R5 pad/sound → after sustained run

## Quarantine

No CNK Alchemy contamination on Hitman/NFS (host_signal 16/54/55, soft-arm, FCE0, virt-LBA, +24008).

## Baseline (pre-proposal, prior logs only)

- Hitman explore: 3600 frames, ~148k prims, searches BOOTMENU / ERRORMES / HITMANBL; leftover WaitSema **2** and **7**
- NFS smoke: 500 frames, ~135k prims; leftover WaitSema **2, 17, 23, 29, 30, 32**
- These are observations, not a pass on a disc-fix patch

## Next

When disc-fix posts `proposed_change` + evidence, matrix will smoke both games across all five phases and write `pass` or `fail` + plain notes to `board.matrix`.
