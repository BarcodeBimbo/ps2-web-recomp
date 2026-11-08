# CNK Alchemy — what clears butanim `obj+0x20` (Ghidra)

**Date:** 2026-11-07  
**Program:** `cnk_boot.elf` (r5900) via Ghidra MCP `user-ghidra`  
**Quarantine:** CNK only — Hitman/NFS untouched  
**Scope:** Soft-arm (`obj≈0x975498`, `+0x20=0x7462F8`) → `vt+108` load @ `0x503308`

---

## Verdict (top 3 clear-site candidates)

| Rank | PC(s) | Insn / width | Function | Why |
|------|-------|--------------|---------|-----|
| **1** | **`0x0051AD60`** | `sw $zero, 0x20(s0)` — **st32** | `igAlchemy_bind_cleanup_clear_o20` (`0x51AC80`) | Only explicit Alchemy bind teardown that releases the attach ref then stores 0 into `+0x20`. Callers: FCE0 end-walk `@0x10FF10`, `FUN_0051ad80`, `FUN_004ede20`. |
| **2** | **`0x004F5AF4`**, **`0x004F5B8C`** | `sw $zero, 0x20(s2)` — **st32** | `igAlchemy_resolve_release_clear_o20` (`0x4F5690`) | Both fail and success paths **refdrop then zero `+0x20`**. Sole caller `FUN_00561b40` (vt DATA). |
| **3** | **`0x0052CEE0`** / **`0x0052CF84`** (+ kin `0x52D080`, `0x52E854`) | `sd $zero, 0x20(reg)` — **st64** | `FUN_0052ced0` / `FUN_0052cf70` / neighbors | 64-bit zero of `[+0x20,+0x27]` **bypasses** host `alchemy_o20_guard` (st32-only). Different class (matrix-ish), but matches “clear may use non-st32 path.” |

**Recommended host hook (even if clearer is #3 or child `vt+0x78`):** restore attach at **`PC=0x00503308`** (`lw a0,0x20(s0)`), after `igAlchemy_vt108_child_walk` (`0x502D20`) and before `beq a0,zero` skip of `ingest_51c100`. Width: rewrite **4 bytes** at `s0+0x20` (and optionally `s0+0x14`). Also widen guard to **st64/st128** spans covering the guarded word.

---

## Gate chain (confirmed)

```
soft-arm (host)     obj+0x20 = 0x7462F8, +0x14, +0x2D(+45)=1, +0xFF=0
        │
        ▼  (guest EE burst — clearer lives here)
loadgate FCE0 0x10FCE0
        │
        ▼
loadgate_finalize 0x110100
        │  jalr  vt+0x6C  on *(slot+0x50)  [= host soft-arm obj @ slot+0x58]
        ▼
igAlchemy_vt108_ingest 0x5032E0
  0x503300  jal  igAlchemy_vt108_child_walk   ; each child vt+0x78(child,parent)
  0x503308  lw   a0, 0x20(s0)                 ; ← ingest ptr (DEAD if cleared)
  0x50330C  beq  a0, zero → skip ingest
  0x503314  jal  ingest_51c100                ; needs *(a0)+0x24 ≠ 0
  0x503320  sb   1, 0xFF(s0)                  ; latches even on skip
```

Child walk has **no** direct `sw zero,0x20`; any clear inside it is via child `vt+0x78` (indirect). Parent class `vt+0x78` @ `0x5036B0` clears parent `+0xE8/+0xF4/+0xF8`, not `+0x20`.

---

## Alchemy-band `sw $zero, 0x20(*)` census (`0x4F0000–0x520000`)

| VA | Function | Notes |
|----|----------|-------|
| `0x4F5AF4` | `igAlchemy_resolve_release_clear_o20` | Fail path — **candidate #2a** |
| `0x4F5B8C` | same | Success path — **candidate #2b** |
| `0x4F823C` | `FUN_004f8230` | `piVar2[8]=0` dtor-like; DATA vt only |
| `0x50E63C` | `FUN_0050e600` | Ctor field wipe — unlikely mid soft-arm→vt108 unless realloc |
| `0x50F8D4` | `FUN_0050f7f0` | Ctor field wipe |
| `0x51AD60` | `igAlchemy_bind_cleanup_clear_o20` | **candidate #1** |

No other `sw $zero,0x20` in `0x502xxx` / `0x51Cxxx` / finalize itself.

---

## Candidate details

### #1 — `0x0051AD60` (primary surgical)

```text
; igAlchemy_bind_cleanup_clear_o20
lw   a0, 0x20(s0)
… refdrop / maybe FUN_00511940 …
sw   zero, 0x20(s0)    @ 0x51AD60
```

Pseudo: if `obj+0x18≠0`: unbind vt paths, release `+0x1c` and `+0x20`, store 0.

**FCE0 timing caveat:** `@0x10FF10` runs when walker index `>0xF9`, typically **after** slot finalize. Still the canonical clear insn for this field; can also fire earlier via `FUN_0051ad80` / `FUN_004ede20` if bind flag set.

**Hook:** EE PC `0x51AD60`, **st32**, skip store when `s0 == g_butanim_soft_obj` (or when `s0+0x20 == g_alchemy_o20_guard_addr`).

### #2 — `0x004F5AF4` / `0x004F5B8C`

`igAlchemy_resolve_release_clear_o20` always ends by zeroing `param+0x20` after consuming the plugin/attach at that slot (fail → 0; success → handoff then 0).

Callee of `FUN_00561b40` with `*(0x725D40+0x3C)` as `param` — may not be butanim UI obj; still a hard clear of the same offset pattern on Alchemy managers.

**Hook:** st32 at both PCs; log `s2` vs butanim obj to confirm live hit.

### #3 — `sd $zero` bypass class (`0x52CEE0` …)

```text
0x52CEE0  sd zero, 0x20(a0)   ; also zeros +0x24 via 8-byte store
0x52CF84  sd zero, 0x20(a0)
```

Host `write_slow` guard is `sizeof(T)==4` only → **st64/st128 miss**. Explains armed guard with `blocks==0` while `+0x20` still goes 0.

**Hook:** extend `alchemy_o20_guard` to reject zeroing stores whose span covers the guarded word (4/8/16). Optionally PC-filter these VAs.

---

## AlignReadBuffer / soft-arm note

Host soft-arm (virt-GFC) arms `+0x2C/+0x2D` because retail `_CdAlignReadBuffer` never runs (`ee1 dest=0`). Attach setters that **write** UI `+0x14/+0x20` live in `FUN_0051ae30` / `FUN_0051b100` (`sw …,0x20(v0)` @ `0x51B080` / `0x51B350`) — wire-up, not clear. Clear is the release/teardown side (#1/#2) or a non-st32 wipe (#3).

---

## Ghidra labels applied this pass

| VA | Name |
|----|------|
| `0x5032E0` | `igAlchemy_vt108_ingest` |
| `0x110100` | `loadgate_finalize` |
| `0x51C100` | `ingest_51c100` |
| `0x4F5690` | `igAlchemy_resolve_release_clear_o20` |
| (prior) `0x51AC80` | `igAlchemy_bind_cleanup_clear_o20` |
| (prior) `0x502D20` | `igAlchemy_vt108_child_walk` |

Comments set at `0x51AD60`, `0x4F5AF4`, `0x4F5B8C`, `0x52CEE0`, `0x503308`.

---

## Recommended next host action (CNK-gated)

1. **Must:** restore at **`0x503308`** (and/or entry `0x5032E0` / post-jal `0x503300`) from soft-arm capture — closes child-walk and unknown-clearer races.  
2. **Surgical:** suppress `sw` @ **`0x51AD60`** when target is butanim `+0x20`.  
3. **Guard fix:** block **st64/st128** zero spans over guarded addr; watch-log PC on first hit to confirm #1 vs #3 vs child path.

**Do not:** `host_call(0x10FCE0)`, status=1 re-arm, Hitman/NFS disc changes.

---

## Return blob

```
top3:
  1) 0x0051AD60 sw-zero st32  igAlchemy_bind_cleanup_clear_o20
  2) 0x004F5AF4 / 0x004F5B8C sw-zero st32  igAlchemy_resolve_release_clear_o20
  3) 0x0052CEE0 / 0x0052CF84 sd-zero st64 (guard bypass)  + restore-hook 0x00503308
recommended_hook: PC 0x00503308 restore 4B (st32); widen guard to st64/st128; optional suppress 0x51AD60
renames: igAlchemy_vt108_ingest, loadgate_finalize, ingest_51c100
```
