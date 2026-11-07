# Worker resume — BIOS zip reference (w6)

**Worker:** w6 / BIOS zip reference (was `2fa08b23`)  
**Resumed:** 2026-11-07  
**Prior agent:** `2fa08b23-fc60-42ef-8713-1b2571f32b91`  
**Pause file:** `verification/recovery/worker-pause-bios-2fa08b23.md`  
**Status:** **RESUMED-as-complete** (idle; no new work)

## Confirmations

| Check | Result |
|-------|--------|
| Live reference report | **Yes** — `verification/recovery/bios-reference-live-report.md` |
| Hybrid restart report | **Yes** — `verification/recovery/bios-zip-hybrid-restart-report.md` |
| Pause note | **Yes** — already `turn_ended` / complete before pause |
| MASTER-CONTEXT §12 | Aligns — reference-only; labels **70012** / **77001** |
| BIOS binaries in repo | **None** — scan was offline; temp extracts deleted; hard ban held |
| Executed / loaded BIOS | **No** — never into browser, ps2run, or runtime |

## Standing rules (unchanged)

- **REFERENCE ONLY** — behavioral oracle for HLE contracts (CDVD complete, SIF end, WaitSema fidelity).
- Preferred sets: **SCPH-70012** (CDVDFSV mid-gen default), **SCPH-77001** (stub ROMVER-era).
- **HARD BAN:** Do **not** load/execute BIOS; do **not** copy/vendor BIOS blobs into the repo.
- Source zip stays user-local: `e:\AI Browser Games\ps2-bios-usa.zip` (outside tree).

## Deliverable already done

ROM0 → HLE map and disc-fix audit targets (R1–R4) are documented in `bios-reference-live-report.md`. Key correction targets remain handoff-only for disc-fix owners:

1. `cdvdfsv` `read_to_ee` — payload → dst; readee preserve; **nbytes → curReadPos**; then complete  
2. `sif::complete_call(0x80000595)` on deferred N/stream/IOP reads  
3. `cdvd` Sync / DiskReady=2 / Status coherent with FSV  
4. `thsemap` WaitSema/iSignalSema fidelity — no CNK `host_signal` bleed  

## Resume posture

- **Complete.** Research track closed for this worker.  
- **No** new BIOS scans, extracts, or notes started this resume.  
- Re-open only if parent explicitly asks for additional **reference-only** notes.

## Next action

Idle. Await parent/user. Do not execute or vendor BIOS.
