# Disc-fix worker resume — w1

**Worker:** w1 / disc-fix Hitman+NFS (was `76656af6`)  
**Resumed:** 2026-11-07  
**Branch:** `windows`  
**Status:** **ACTIVE run complete** — R5 observe matrix PASS (no apply)

## Confirmed — R1–R4 joint-stable

- Marker: `verification/recovery/DISCFIX-R1-R4-STABLE.md`
- Commit: **`1e04172`** (readee lengths only)
- R1 SIF end — `cleared_with_evidence`
- R2 WaitSema — `cleared_with_evidence` (never `host_signal(2)`)
- R3 readee — `verified_apply` in `cdvdfsv.cpp`
- R4 CdSync — `cleared_with_evidence` (no wake code)
- **R5 pad/sound — observe PASS; apply still gated**

## Board snapshot (after 2026-11-07 observe run)

| Field | Value |
|-------|--------|
| File | `verification/recovery/discfix-matrix-board.json` |
| `updated` | `2026-11-07T07:32:00-05:00` |
| `step` | **8** |
| `phase` | **`observe_pass_awaiting_next_proposal`** |
| `discfix.status` | `observe_accepted` |
| `proposed_change` | **`R5_pad_sound_observe`** (observe-only; `code_change: false`) — matrix **pass** |
| `matrix.status` / `verdict` | **`pass`** |
| `matrix.last_completed` | `R5_pad_sound_observe` |
| `allow_discfix_apply` | **false** |
| `ranked_rewrites_gated` | `R5_pad_sound` |
| Joint-stable | `1e04172` / R1–R4 |

## Today's run (2026-11-07 ~07:29–07:32 local)

- **Mission:** OBSERVE / MATRIX only for `R5_pad_sound_observe`.
- **PATH:** `runtime-deps` + clang64 + wgpu; DLLs also beside native builds. No disc-fix code edits.
- **Smokes:** Hitman + NFS **400f** with `PS2_TRACE_SEMA` / `PS2_TRACE_PAD` / `PS2_TRACE_SPU2` / `PS2_SPU2_COUNT`.
  - Hitman: 400f / **78933** prims / SIF 0 / leftovers **2,7** / modules SIO2MAN→PADMAN→…→LIBSD
  - NFS: 400f / **73253** prims / SIF 0 / leftovers **2,17,23,29,30,32** / sio2man→padman→Sound_Device_Library→sdr_driver
- **Report:** `verification/recovery/discfix-r5-observe-matrix-2026-11-07.md`
- **Logs:** `logs/discfix-r5-observe-hitman-400.err.log`, `logs/discfix-r5-observe-nfs-400.err.log` (+ `.merged.log` copies)
- **Did NOT apply R5.** Hard ban held on `cdvdfsv.cpp` / `cdvd.cpp` / `sif.cpp`.

## Resume posture

- Watching for **next proposal only** (parent): `clear_with_evidence` **or** evidence-named narrow RPC fix.
- **R5 remains gated for apply** — no pad/sound HLE, no CDVD behavioral patches, no CNK quarantine leaks.
- No commits unless explicitly told.

## Next action

Await parent choice among board `discfix.next_options`. Do not invent an apply proposal. No apply until `allow_discfix_apply` and an explicit unlock.
