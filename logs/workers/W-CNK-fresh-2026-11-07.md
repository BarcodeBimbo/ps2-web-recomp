# W-CNK-2 fresh — EE intercept obj+0x20 / prims>2 — 2026-11-07

**Worker:** W-CNK-2  
**Game:** Crash Nitro Kart `b49f2e769315347e8bda839feb705744`  
**Locks:** `logs/locks/web-b49f….lock` + `native-b49f….lock` (acquired; Hitman a2116* untouched)  
**Heartbeat:** `logs/workers/W-CNK-heartbeat.log`

---

## Return blob

| Field | Value |
|-------|--------|
| **lock status** | Acquired web+native-b49f at start; by end native lock held by **W-CNK-CRIT** (cascade); Hitman a2116* never touched |
| **prims result** | **still 2** (6000f smoke ×4) — plan checkbox **NOT** flipped |
| **crash** | no |
| **blocked_or_verified** | BREAKTHROUGH: 51C100 **does run** with live o20; prims still blocked downstream |

---

## Breakthrough (overturns prior o20-timing theory)

Prior theory: guest clears `obj+0x20` **before** vt+108 `lw` @ `0x503308`, so `0x51C100` is skipped.

**Measured (smoke3/4):** JIT probe at `L_00503308` (overlay `m_00100000_271E1240_unit_0100`):

```
[alchemy-o20] jit@0x503308 obj=0x975498 match=1 cur+20=0x7462F8 guard=0x9754B8 want=0x7462F8
```

`obj+0x20` is **LIVE** at the ingest gate. Guest **does** take the `jal 0x51C100` path.  
HLE `restored butanim … (was 0, +0xFF=1→0)` is a **post**-vt+108 clear — too late to explain skipped ingest.

Ghidra: `FUN_005032e0` (vt+108) → `ingest_51c100` when `*(obj+0x20)≠0` and `*(attach+0x24)≠0` (attach `+0x24=1` confirmed).  
`igAlchemy_bind_cleanup_clear_o20` @ `0x51AC80` clears **alchemy ctx** `+0x20` (at `0x725D48`), not butanim obj — separate path.

**Next blocker:** `0x51C100` → `FUN_0051a620` parse/bind outcome and/or loadgate `+0x5DD0` stall (prior W-CNK report) — not pre-vt108 o20 clear.

---

## What was implemented (CNK quarantine only)

1. **st32/st64/st128 o20 guard** — `memory.hpp` / `memory.cpp`  
   - Armed only from butanim soft-arm (`igfileio::note_ui_igb_soft_arm`)  
   - Suppresses guest SW-zero of soft-armed `obj+0x20`  
   - Hitman/NFS never arm → no disc-fix coupling

2. **JIT hooks in generated EE units** (CNK overlay + base unit_0100)  
   - `alchemy_o20_jit_before_lw` @ `L_00503308`  
   - `alchemy_o20_log_post_51c100` @ `L_0050331C`  
   - Files:  
     - `generated/b49f…/m_00100000_271E1240_unit_0100.cpp`  
     - `generated/b49f…/unit_0100.cpp`

3. **Soft-arm arm/disarm** — `igfileio.cpp`  
   - `alchemy_o20_guard_arm(obj+0x20, o20, o14)` on butanim soft-arm  
   - Disarm on parse-complete / `reset()`

4. **Public** `restore_butanim_attach_if_cleared()` for probe/preempt paths

---

## Smoke evidence

| Run | Log | prims | Notes |
|-----|-----|-------|-------|
| smoke1 | `W-CNK-o20-intercept-smoke-2026-11-07.log` | 2 | guard armed; no jit (overlay not rebuilt) |
| smoke2 | `…-smoke2-…` | 2 | overlay rebuilt; still no jit log (silent live path) |
| smoke3 | `…-smoke3-…` | 2 | **jit proves +20 LIVE** |
| smoke4 | `…-smoke4-…` | (pending/same) | post-51c100 log |

All: `--disc games/b49f…/disc.iso --frames 6000`, native `build/native-b49f…/ps2run.exe`.

---

## Patch files

- `runtime/include/ps2/memory.hpp`
- `runtime/src/memory.cpp`
- `runtime/src/iop/igfileio.cpp`
- `runtime/src/iop/igfileio.hpp`
- `runtime/src/dispatch.cpp` (probe restore path)
- `runtime/src/system.cpp` (preempt opportunistic restore — pre-existing wire)
- `generated/b49f2e769315347e8bda839feb705744/m_00100000_271E1240_unit_0100.cpp`
- `generated/b49f2e769315347e8bda839feb705744/unit_0100.cpp`

---

## Master plan §2c

- [ ] CNK `prims=2` — **still open** (do **not** check; evidence says ingest gate is open, downstream bind/parse/loadgate next)
- Quarantine honored: no Hitman/NFS tree or lock edits; no taskkill of Hitman builds

---

## Next (W-CNK-3+)

1. Trace `FUN_0051a620` / `FUN_00428df8` result at butanim ingest (stream `o14=0x16B06E8`).  
2. Correlate loadgate `+0x5DD0` after successful soft-arm+51c100.  
3. Keep o20 guard+JIT as safety; do not treat post-vt108 clear as the prims root cause.
