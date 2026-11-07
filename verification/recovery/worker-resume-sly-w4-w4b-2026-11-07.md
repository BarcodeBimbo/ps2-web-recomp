# Worker resume — Sly w4 + w4b (2026-11-07)

**Status:** both **RESUMED-as-complete / PARKED**  
**Workspace:** `C:\PS2Recomp`  
**Hard ban honored:** no GS/runtime code changes; no STQ/PATH3/CLUT implementation; no new tracks.

---

## Disk verification

| Worker | Report | On disk |
|--------|--------|---------|
| **w4** (Sly GS/VU) | `verification/recovery/sly-gs-vu-live-report.md` | **Yes** (dated 2026-11-06) |
| **w4b** (Sly asset bin-walk) | `verification/recovery/sly-asset-binwalk-report.md` | **Yes** (dated 2026-11-06) |

Cross-check: `MASTER-CONTEXT.md` §11 lists both reports; worker table marks w4 research **Completed** / w4b **Done**; parked research row points at shared GS STQ/PATH3/CLUT.

---

## Last conclusions (unchanged)

### w4 — GS/VU live

- Paris first-map explore: health ok, ~**12M** prims (binwalk health: **11,816,466** @3600f).
- Soft and GPU **both** still missing buildings; soft≠GPU ~**28%** pixel diverge on this card path (secondary).
- Strict VU interpret+exact: **no** buildings restored (−143 prims only).
- Heavy PATH1 packed + PATH3 image / PSMT4/8 **FST=0 (STQ)** / CLUT traffic reconfirmed.

### w4b — asset bin-walk

- Full USA ISO present; art in **hidden encrypted WAL / BRX** (not loose packs).
- Level strings in RAM; renderer busy — **buildings ≠ missing / incomplete assets**.
- Offline BRX extract optional for analysis only; not a runtime fix.

### Shared next (when prioritized)

1. Shared GS **STQ** / perspective-correct texturing (FST=0 strips)
2. **PATH3** image ↔ TEX0 **CLUT** / CLD ordering
3. Then secondary soft↔GPU noise / GIF mesh audit as ranked in the reports

**Not started this resume:** STQ / PATH3 / CLUT implementation remains parked pending user priority.

---

## Resume disposition

| Worker | Disposition |
|--------|-------------|
| w4 | **RESUMED-as-complete / PARKED** — research closed; wait for priority |
| w4b | **RESUMED-as-complete / PARKED** — research closed; wait for priority |

**Gating:** next shared GS STQ/PATH3/CLUT work starts only when the user explicitly prioritizes it.
