# Open follow-ups

## SDK R1–R5 compliance report (2026-11-07)

Formal roll-up now exists: `verification/recovery/SDK-R1-R5-COMPLIANCE-REPORT.md` (Track E). Merges quote harvest + per-R notes (`sdk-pdf-quote-harvest-r1r5.md`, `sdk-compliance-r1-sif.md` … `r4-cdsync.md`, `sdk-compliance-r5-pad-sound-inventory.md`). Research only — no runtime patches. R5 still gated; primary observe flag = DiskReady always-`2`.

## Cut off (2026-11-06 evening)

The user started to say they were working on fixing something else, then got cut off. **Pick this up when they say what it was.**

## Active extra jobs (on top of the seven)

1. 2Captcha / 2Cap API key scrub — live worker (correction: localStorage only, not process.env)  
2. Logs relocation into dedicated folder — **done** (see `logs-relocation-report.md`)  
3. Alchemy SDK research (web + boot.elf) — live worker  

## Cut off (still open)

User started describing another fix and got cut off — pick up when they say what it was.

## Standing rules

- Workers stay alive until user says done (no self-dismiss after a step).
- Browser product work: **Chrome + Edge only**; Firefox / mobile / controls = back burner.

## CNK null-bind (resolved model)

See `cnk-nullbind-51ACEC-live-report.md`: forced FCE0 dies because registry **vt+80** returns null for the current thread (GetThreadId map miss), then code still jalrs vt+84 on null. Soft-arm leaves `0x725F50` clear / prims=2. Next: log tid vs map — no pointer stuffing.

## Landed research reports (2026-11-06)

- `cnk-elf-alchemy-full-redo-report.md` — ELF bind path / loadgate map
- `alchemy-sdk-research-report.md` — Intrinsic Alchemy 3.0 / Velocity web+ELF
- Disc-fix/matrix: **R1–R4 done** (only code: R3 readee lengths in `cdvdfsv.cpp`). Cycle 7 `R4_clear_with_evidence` **PASS**. **R5 pad/sound** still gated. Joint-stable commit OK when user asks — not auto-committed.
- `sly-gs-vu-live-report.md` — strict VU no building restore; soft vs GPU ~28% differ @1800 but buildings missing in **both**; next shared STQ/texturing (parked 0% claim outdated)
- `sly-asset-binwalk-report.md` — **DONE**: USA ISO complete; art in hidden encrypted WAL/BRX; explore already loaded Paris (~11.8M prims, health ok). Missing buildings ≠ missing assets → shared GS STQ/PATH3/CLUT (same as GS/VU). Samples under `sly-asset-samples/`
