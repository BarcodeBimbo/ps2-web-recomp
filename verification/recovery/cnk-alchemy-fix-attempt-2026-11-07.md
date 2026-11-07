# CNK Alchemy fix attempt — guest FCE0 / +0x5DD0 (2026-11-07)

**GID:** `b49f2e769315347e8bda839feb705744`  
**Mode:** Implement (observe-only ban lifted for Target 3).  
**Quarantine:** Alchemy / virt-GFC / `alchemy_stbl_pending()` only — Hitman/NFS disc-fix path untouched.

---

## Verdict

**BLOCKED** on drawable production — not on the +0x5DD0 skip gate alone.

Guest `0x10F560→0x10FCE0` now runs on mapped tids after soft-arm (no `host_call` FCE0, no `ra=0x51ACEC`). Intro hold keeps BUTANIM bytes in shared scratch `0xBD1000`. **Prims remain 2.**

---

## Before → after

| Probe | Before (obs / soft-arm) | After (smoke E, 8k) |
|-------|-------------------------|---------------------|
| Prims | **2** | **2** |
| Crash | none (soft); forced FCE0 → `ra=0x51ACEC` | **none** (no `51ACEC`, no missing@0) |
| `+0x5DD0` | **1** (FCE0 skipped) | **0** (cleared; pump allowed) |
| Walker `+0x5DD4` | 0 | **3** (guest FCE0 progressed) |
| `BD1000` | INTROTXR (clobber) | **BUTANIM** (hold held) |
| Tid map | `{1}` | **`{1, 4}`** |
| Soft obj `+0xFF` / `+0x20` | n/a | `+0xFF=1`, **`+0x20=0`** (weak vt+108) |

---

## What we changed (smallest safe, CNK-gated)

### `runtime/src/iop/igfileio.cpp` / `.hpp`
- Track soft-armed BUTANIM obj + plant size.
- **Do not** latch `ui_igb_parse_attempted` on soft-arm `+45` (that released intro too early).
- Latch only when `+0xFF` **and** `+0x20≠0` **and** assemble still matches butanim plant (vt+108 alone sets `+0xFF` even when `0x51C100` is skipped).
- Keep clearing loadgate `+24016` (`+0x5DD0`) while Alchemy STBL pending so guest `0x10F560` can call `0x10FCE0` on tid1 — **no** `host_call(0x10FCE0)`.
- Restore butanim plant into scratch if intro ever lands early.
- **Removed** aggressive status/obj re-arm after an intermediate crash (`missing @0x974768`, `ra=0x110224`) from forcing status back to 1 post-finalize.

### `runtime/src/iop/cdvdfsv.cpp`
- Intro hold until `ui_igb_parse_attempted()` (real parse gate), not `+45`.
- Re-arm hold at butanim file-done; long backstop (20k iters).
- Clear `+0x5DD0` at soft-arm; `note_ui_igb_soft_arm` / plant size.
- Soft-arm clears stale `obj+0xFF` on recycled heap objects.

All paths sit behind virt-GFC UI IGB / `alchemy_stbl_pending()` (STBL0 scratch). Hitman/NFS never plant those.

---

## Evidence (smoke E)

Log: `logs/cnk-alchemy-fix-2026-11-07.log` (= `logs/cnk-alchemy-fix-8k-e-2026-11-07.log`)  
RAM: `logs/ram/cnk-alchemy-fix-e-2026-11-07.ram`  
Rebuild: `logs/cnk-alchemy-fix-rebuild5-2026-11-07.log`

```
noted butanim soft-arm obj=0x975498 ... +20=0x7462F8 assemble_butanim=1
butanim vt+108 weak (+20=0, plant ok); hold intro, no re-arm
hold intro read ... (iters 1..8+)
butanim pump-wait slot0 st=3 ... (+5DD0 clear, no host FCE0)
[gs] 2 primitives drawn
[ee] stopped after 8000 frames ... frame limit reached
```

End-RAM: `BD1000==butanim`, `5DD0=0`, walker=3, registry tids **1+4**.

---

## Exact remaining blocker

1. Soft-arm + guest FCE0 reach finalize / vt+108 (`0x5032E0`) with butanim bytes present.
2. vt+108 sets `obj+0xFF` but by poll time **`obj+0x20==0`**, so the durable ingest path (`0x51C100`, needs `*(+0x20)+0x24≠0`) does not stick / does not yield drawables.
3. Retail `_CdAlignReadBuffer` never arms the object graph (ee1 dest stays 0) — soft-arm only sets `+44/+45`.
4. Forcing slot status back to 1 to “retry” finalize **crashes** (`ra=0x110224` → heap `0x974768`) — do not re-arm that way.

**Next (when approved):** wire or observe the AlignReadBuffer-equivalent fields (`obj+0x14/+0x20` → live stream/attach with `+0x24`) *before* guest FCE0/vt+108, still without `host_call` FCE0 and still CNK-gated — or find why `+0x20` (noted as `0x7462F8` at soft-arm) is cleared before ingest completes.

---

## Return blob

```
prims_before: 2
prims_after: 2
crash: no (no ra=0x51ACEC; prior re-arm attempt had ra=0x110224 — reverted)
files: runtime/src/iop/igfileio.cpp, igfileio.hpp, cdvdfsv.cpp
log: logs/cnk-alchemy-fix-2026-11-07.log
ram: logs/ram/cnk-alchemy-fix-e-2026-11-07.ram
blocked_or_verified: BLOCKED — guest FCE0/+5DD0/hold fixed; prims stuck on weak vt+108 (+20 cleared, no AlignReadBuffer object wiring)
```
