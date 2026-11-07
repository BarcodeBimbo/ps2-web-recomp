# Worker resume — WaitSema / CreateSema (w5)

**Worker:** w5 — WaitSema / CreateSema ownership  
**Resumed:** 2026-11-07  
**Mode:** **RESUMED observe-only**  
**Hard ban:** No kernel / sema runtime edits. No wake patches. No `host_signal(2)`.

## Confirmations

| Check | Result |
|-------|--------|
| Ownership report present | **Yes** — `verification/recovery/waitsema-createsema-trace-live-report.md` |
| MASTER-CONTEXT R2 | `cleared_with_evidence` (never `host_signal(2)`); SDK line-audit still pending |
| MASTER-CONTEXT §4 | Sema 2 = libcdvd durable parking; never blind `host_signal(2)` |

## Key rule (standing)

**WaitSema(2) = libcdvd-class durable parking (init=0, max=255, create-once, never deleted).**  
**Never blind `host_signal(2)`** — that would fake CD cmd completion. Same numeric id across Hitman/NFS is ID coincidence, not one shared object.

## Posture this resume

- Observe-only; ownership work already **DONE**.
- No semantic patches; no `runtime/src/kernel.cpp` / sema behavior changes.
- Logging already present (`PS2_TRACE_SEMA`, leftover-ID wait logs) — leave as-is.
- Private leftovers (Hitman **7**, NFS **17/23/29/30/32**) remain per-game observe targets only.

## Next (still observe / prove-before-swap)

Under-load SIF end assert; disc-search `readee`/`curReadPos`; private semas last. Optional later: IOP Kernel PDF WaitSema line-audit for R2 compliance write-up (research only).

## Status

`RESUMED` — observe-only. Track complete for ownership; idle until asked for further observation or formal SDK compliance notes.
