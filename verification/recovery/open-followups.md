# Open follow-ups

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
- Matrix cycle 1 **FAIL** on bundled R3; disc-fix now proposes **R1 clear with evidence** (board step 2)
- `sly-gs-vu-live-report.md` — strict VU no building restore; soft vs GPU ~28% differ @1800 but buildings missing in **both**; next shared STQ/texturing (parked 0% claim outdated)
- `sly-asset-binwalk-report.md` — **DONE**: USA ISO complete; art in hidden encrypted WAL/BRX; explore already loaded Paris (~11.8M prims, health ok). Missing buildings ≠ missing assets → shared GS STQ/PATH3/CLUT (same as GS/VU). Samples under `sly-asset-samples/`
