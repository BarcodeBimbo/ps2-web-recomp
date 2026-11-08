# Alchemy obj+0x20 clear sites (Ghidra map)

**Date:** 2026-11-07  
**Program:** `cnk_boot.elf` (Ghidra :8089)  
**Lane:** CNK `b49f2e769315347e8bda839feb705744` only

## Critical gate (vt+108 ingest)

`igAlchemy_vt108_ingest` @ `0x005032E0`:

| VA | Insn | Meaning |
|----|------|---------|
| `0x5032F4` | `lbu v1,0xFF(a1)` | Skip if already finalized |
| `0x503300` | `jal igAlchemy_vt108_child_walk` | Walk children **first** |
| **`0x503308`** | **`lw a0,0x20(s0)`** | Load attach ptr for ingest |
| `0x50330C` | `beq a0,zero,…` | Gate: null → skip `0x51C100` |
| `0x503314` | `jal igAlchemy_ingest_51c100` | Needs `*(obj+0x20)` live |
| `0x503320` | `sb 1,0xFF(s0)` | Mark done either way |

If `obj+0x20` is zero at `0x503308`, prims stay at 2.

## Known clear: `sw zero,0x20(s0)` @ `0x51AD60`

**Function:** `igAlchemy_bind_cleanup_clear_o20` @ `0x0051AC80`  
**Body:** `0x51AC80`–`0x51AD77`

### Semantics (decomp)

When `*(char*)(obj+0x18) != 0`:

1. Clear flag `obj+0x18 = 0`
2. Call `(*(obj+0x1c)->vt+0x5C)(…)` (unbind side)
3. Use saved `obj+0x20` with global vt+0x50 / vt+0x54 helpers
4. `FUN_005170a0(obj+0x1c)` then refcount-release `obj+0x1c` → `obj+0x1c = 0`
5. Refcount-release `obj+0x20` → **`sw zero, 0x20(s0)` @ `0x51AD60`**

Asm anchor:

```
0051ad2c  lw   a0,0x20(s0)
0051ad30  beq  a0,zero,0x51ad60
…refcount…
0051ad60  sw   zero,0x20(s0)   ; CLEAR SITE
```

### Callers of bind_cleanup

| Caller | VA | Role |
|--------|-----|------|
| `FUN_0010fce0` | `0x0010FCE0` | Loadgate / finalize path (also calls vt+0x6C) |
| `FUN_004ede20` | `0x004EDE20` | Upstream Alchemy binder |
| `igAlchemy_bind_teardown_if_armed` | `0x0051AD80` | If `obj+0x18==1` → cleanup, then clear `+0x28/+0x2c`, `FUN_00511280` |

**Label applied this turn:** `FUN_0051AD80` → `igAlchemy_bind_teardown_if_armed`.

## Child vt+0x78 hazard (pre-`0x503308`)

**Function:** `igAlchemy_vt108_child_walk` @ `0x00502D20`

```
for i in 0 .. *(parent+8)-1:
  child = FUN_004f3890(parent, i)
  (*(child->vt + 0x78))(child, parent)   ; jalr @ 0x502D54–0x502D58
```

This runs **before** `lw a0,0x20(s0)` at `0x503308`. Any child method that tears down / calls bind_cleanup on the parent (or otherwise zeros parent+0x20) will fail the ingest gate even if soft-arm previously set a valid attach.

**Open RE:** resolve concrete implementations of vt+0x78 on butanim / UI child objects; check whether any path reaches `0x51AD60` or stores zero to parent+0x20.

## Runtime countermeasures (parent session)

- Store-guard: block st / st64 / st128 that zero guarded `obj+0x20`
- `restore_butanim_attach_if_cleared()` on JIT probe PCs `0x5032E0` / `0x503300` / `0x503308`
- Soft-arm capture of `+0x20` / `+0x14` in igfileio

Smoke gate after rebuild: probe lines at `0x503308` with non-zero a0 / restored attach, and **prims ≫ 2**.

## Labels (current)

| VA | Name |
|----|------|
| `0x005032E0` | `igAlchemy_vt108_ingest` |
| `0x00502D20` | `igAlchemy_vt108_child_walk` |
| `0x0051C100` | `igAlchemy_ingest_51c100` |
| `0x00110100` | `igAlchemy_loadgate_finalize` |
| `0x0051AC80` | `igAlchemy_bind_cleanup_clear_o20` |
| `0x0051AD80` | `igAlchemy_bind_teardown_if_armed` |
