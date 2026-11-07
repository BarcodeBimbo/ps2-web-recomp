# W-CNK fresh — EE obj+0x20 intercept (2026-11-07 ~18:55)

**Worker:** W-CNK  
**GID:** `b49f2e769315347e8bda839feb705744`  
**Todos:** `t3-alchemy`, `cnk-alchemy-ghidra`  
**Quarantine:** no CNK Alchemy hacks on Hitman/NFS disc path; did **not** touch `web-a2116*` / `native-a2116*`.

---

## Lock status

| Lock | Result |
|------|--------|
| `logs/locks/web-b49f2e769315347e8bda839feb705744.lock` | **acquired** (no prior live holder) |
| `logs/locks/native-b49f2e769315347e8bda839feb705744.lock` | **acquired** (no prior live holder) |
| Hitman `*-a2116*` | **untouched** (live locks present; campaign owner) |

No writes to `build/web-b49f*` or `native-b49f*` this turn (RE + report only).

---

## Prims status

**Still `prims=2`.** Not claimed fixed. Prior HLE `try_restore_butanim_o20()` restores attach **after** vt+108 already ran with `+0x20=0` (`cnk-alchemy-obj20-fix-2026-11-07.md`). Master-plan §2c `prims=2` checkbox **left open**.

---

## Ghidra advance (`cnk_boot.elf` @ MCP `:8089`)

Switched program **hitman_boot.elf → cnk_boot.elf**. Decompiled:

| VA | Symbol | Role |
|----|--------|------|
| `0x005032E0` | `FUN_005032e0` | UI **vt+108** (`vt+0x6C`); gated by `obj+0xFF` |
| `0x00502D20` | `FUN_00502d20` | Child walk → each child **vt+0x78** `(child, parent)` |
| `0x0051C100` | `FUN_0051c100` | Ingest; requires `*(obj+0x20)+0x24 ≠ 0` |
| `0x00110100` | `FUN_00110100` | Finalize → `jalr vt+0x6C` (= vt+108) |
| `0x0010FCE0` | `FUN_0010fce0` | Loadgate; end-of-walk may `FUN_0051ac80` then set `+0x5DD0=1` |
| `0x0051AC80` | `FUN_0051ac80` | Bind/stream cleanup; **`sw zero,0x20(s0)` @ `0x0051AD60`** |

### Critical sequence inside vt+108 (asm)

```text
0x00503300  jal   FUN_00502d20        # child vt+0x78 walk (a1=obj preserved)
0x00503304  addiu a0,sp,0x3c
0x00503308  lw    a0,0x20(s0)         # ← ingest pointer read
0x0050330C  beq   a0,zero, skip_51c100
0x00503314  jal   FUN_0051c100        # needs *(+0x20)+0x24≠0
0x00503320  sb    1,0xFF(s0)          # sets +0xFF even when ingest skipped
```

So **`FUN_00502d20` runs before the `+0x20` load**. If any child `vt+0x78` (or earlier EE) zeros parent `+0x20`, ingest is skipped and `+0xFF=1` still latches — matches live “weak vt+108” logs.

Vtable containing this method: **`0x006E1D90`** (slot `+0x6C` → `0x5032E0`; DATA xref from `0x006E1DFC`).

`FUN_0051ac80` clear @ `0x51AD60` is on the **`iRam00725d48`** stream object after walker ≥250 — **secondary** suspect, usually *after* slot finalize. Primary surgical site remains the vt+108 gate.

---

## Concrete next patch

| Field | Value |
|-------|--------|
| **File** | `runtime/src/system.cpp` |
| **Function** | `ps2::preempt` (same EE PC-hook pattern as freelist escape @ `0x2399D8`/`0x239A80`) |
| **Symbol / PC** | **`FUN_005032e0` / `0x00503308`** (post-`FUN_00502d20`, pre-`lw a0,0x20(s0)`) |
| **Also consider** | Entry `0x005032E0` (re-plant before child walk) if watch shows clear *before* entry |
| **Action** | CNK + `g_butanim_soft_o20` gated: if `ld32(s0+0x20)==0`, restore `g_butanim_soft_o20` / `g_butanim_soft_o14` onto object; ensure `a0` non-zero before `beq` @ `0x0050330C` so `FUN_0051c100` runs |
| **Exports needed** | Read accessors for soft-arm capture from `iop/igfileio` (today file-local) |
| **Forbidden** | `host_call(0x10FCE0)`, status=1 re-arm, any Hitman/NFS path |

### Diagnostic before/with patch

```text
PS2_WATCH=<butanim_obj+0x20>,4
```

Soft-arm log already prints `obj=…`; watch that word to print **clear PC/RA** via existing `watch_hit`. Confirms whether clearer is `0x51AD60`, a child `vt+0x78`, or earlier completion code.

### Alternate (if preempt misses one-shot PC)

Sticky filter in `ps2::watched<>` / `st32`: while soft-arm live and parse not OK, **refuse store of 0** to `g_butanim_soft_obj+0x20` (log PC). Heavier but catches any clearer.

---

## Safe to test native?

**Yes, conditionally** — CNK-only native smoke after implementing the gated `preempt` hook (or watch-first diagnostic build):

- Same memory rewrite already smoke-tested late via HLE (no crash, still prims=2).
- Must stay behind Alchemy/butanim soft-arm guards.
- Do **not** ship as proven until prims ≫ 2 on real CNK `disc.iso` smoke.
- Web rebuild not required for this EE intercept proof.

**Not safe yet:** blind `host_call` of `0x5032E0` / FCE0 (tid / `0x51ACEC` history).

---

## Master plan §2c

| Checkbox | Flip? |
|----------|-------|
| dumper 28/28 | leave `[x]` |
| quarantine | leave `[x]` |
| `prims=2` / loadgate EE RE | **no** — RE advanced, playable not verified |
| proven_fixes → self-heal | **no** |
| CNK Chrome playable | **no** |

---

## Return blob

```
lock_status: acquired web-b49f + native-b49f (Hitman a2116 untouched)
prims_status: still 2 (unverified)
next_patch: runtime/src/system.cpp::preempt @ EE PC 0x00503308 (FUN_005032e0 post-502d20); symbol FUN_0051c100 ingest gate; optional PS2_WATCH on obj+0x20
native_test: SAFE if CNK-gated preempt restore only; NOT proven
```
