# WaitSema / CreateSema ownership — live trace (Hitman BM + NFS MW)

**Track:** WaitSema / CreateSema (#6). Observe-only. No wake patches, no `host_signal(2)`, no CNK pulses.  
**Prior:** `waitsema-hitman-nfs-restart-report.md`  
**Logs:** `logs/waitsema-createsema-hitman-2k.log`, `logs/waitsema-createsema-nfs-2k.log`

## Bottom line

**Sema 2 on both games is durable libcdvd-class parking (init=0, max=255, created once, never deleted).** Same *shape*, different create RAs → **ID coincidence**, not one shared handle and not temp RPC. Hitman **7** and NFS **17/23/29/30/32** stay per-game private. Do **not** blind-wake id 2.

## What we added (logging only)

In `runtime/src/kernel.cpp` (EE `CreateSema` / `WaitSema` / `DeleteSema` / end dump):

- Tag each EE sema with **create_ra** (plus existing init/max).
- Log `[createsema] id=… init=… max=… attr=… option=… ra=… thr=…`
- Log `[waitsema] … create_ra=… init=… max=…` for leftover IDs (2, 7, 17, 23, 29, 30, 32).
- Log `[deletesema]` for those IDs (proves churn vs durable).
- End dump: `[sema] N … create_ra=… init=… max=…`

**Flag:** `PS2_TRACE_SEMA=1` logs every CreateSema (smokes used this). Without it, leftover IDs still log; other creates are capped (~48). Harmless observe-only; left on.

No `cdvdfsv` edits.

## Smokes

| Game | Frames | Prims | Leftover waiters |
|------|--------|-------|------------------|
| Hitman BM (`a2116d2…`) | 2000 | 586246 | **2**, **7** |
| NFS MW (`60c82f4…`) | 2000 | 1153253 | **2**, **17**, **23**, **29**, **30**, **32** |

SIF queue drained on both (same soft-park picture as triage).

## Ownership map

### Shared: sema **2** = libcdvd-class durable (ID coincidence)

| | Hitman BM | NFS MW |
|---|-----------|--------|
| Create | **once** | **once** |
| Delete | **never** | **never** |
| init / max | **0 / 255** | **0 / 255** |
| create_ra | `0x001038CC` | `0x00495EA8` |
| WaitSema ra (park) | `0x001037F8` (thr 2) | `0x00495DE8` (thr 2) |

**Why libcdvd-class, not temp RPC**

1. Classic Sony CD cmd-queue shape: **init=0, max=255**.
2. Created **third** after two init=1/max=1 locks (id 0,1) — early boot/lib init order.
3. Create RA and Wait RA sit ~0xC0–0xD4 apart in the **same** module on each title (create just after wait site) — lib-local pair, not a one-shot RPC gate.
4. **Different** create RAs across games → same *class*, not one global id-2 object.
5. Contrast Hitman **id 13**: **140** create/delete cycles (init=0 max=1) — that *is* temp RPC-style. Sema 2 has **zero** deletes.

### Hitman private: sema **7**

| Field | Value |
|-------|-------|
| Final create_ra | `0x001008FC` |
| init / max | 0 / 1 |
| Wait park | thr 3, WaitSema ra `0x001008A0` |
| Note | Slot 7 was reused earlier by short-lived max=1 creates (`0x00105B74` / `0x00105E30`); leftover owner is the durable `0x001008FC` gate |

### NFS private leftovers

| ID | create_ra | init/max | Notes |
|----|-----------|----------|-------|
| **17** | `0x00490224` | 0 / 1 | Same factory as 23/32; thr 3 parks Wait ra `0x00490308` |
| **23** | `0x00490224` | 0 / 1 | Same factory; thr 4 |
| **32** | `0x00490224` | 0 / 1 | Same factory; thr 7 |
| **29** | `0x0046A208` | 0 / 3 | Small counting gate; thr 5, Wait ra `0x00469E00` |
| **30** | final `0x0046B748` | 0 / **253** | Early max=1 create/delete churn at `0x004978F0` / `0x00497B9C`, then durable max=253 owner; thr 6 parks |

## Verdict for future R2

| Claim | Proven? |
|-------|---------|
| Sema 2 = durable libcdvd-class parking | **Yes** |
| Sema 2 = temp RPC ID reuse | **No** |
| Same numeric id across Hitman/NFS = same object | **No** (coincidence) |
| Safe to `host_signal(2)` / CNK-style pulse | **No** — would fake CD cmd completion |
| Hitman 7 / NFS 17+ = per-game private | **Yes** |

**Next (still observe / prove-before-swap):** under-load SIF end assert; disc-search `readee`/`curReadPos` path; private semas last. No wake hacks.
