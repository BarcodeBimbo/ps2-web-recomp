# Alchemy runtime rebuild — progress log

**Started:** 2026-11-07 ~19:00 local (God mandate: build Alchemy operational)  
**Updated:** 2026-11-07 ~19:08 local (W-CNK-ALCHEMY)  
**Game:** CNK `b49f2e769315347e8bda839feb705744`  
**Mode:** Implement + verify (CNK quarantined; Hitman/NFS untouched)

## Ghidra (`cnk_boot.elf` @ :8089)

| VA | New name | Role |
|----|----------|------|
| `0x005032E0` | `igAlchemy_vt108_ingest` | UI vt+108; gated by `obj+0xFF` |
| `0x00502D20` | `igAlchemy_vt108_child_walk` | Child vt+0x78 walk **before** `+0x20` load |
| `0x0051C100` | `igAlchemy_ingest_51c100` | Needs `*(obj+0x20)+0x24≠0` |
| `0x00110100` | `igAlchemy_loadgate_finalize` | Calls vt+0x6C |
| `0x0051AC80` | `igAlchemy_bind_cleanup_clear_o20` | `sw zero,0x20(s0)` @ `0x51AD60` |
| `0x0051AD80` | `igAlchemy_bind_teardown_if_armed` | If `+0x18==1` → bind_cleanup; clear `+0x28/+0x2c` |

Critical gate asm: `jal child_walk` → `lw a0,0x20(s0)` @ **`0x503308`**.

**Clear-site map:** `verification/recovery/alchemy-o20-clear-ghidra-2026-11-07.md` (W-CNK-ALCHEMY).

## Runtime changes (this session)

1. Export `restore_butanim_attach_if_cleared()` from `igfileio`.
2. Widen Alchemy o20 store-guard to **st64/st128** spans that zero the guarded word.
3. JIT `probe()` restore at `0x5032E0` / `0x503300` / `0x503308`.
4. Opportunistic `preempt()` restore at those PCs.
5. `games/<cnk>/probes.txt` + `windows_port.refresh_translation` passes `--probes` when present.
6. `alchemy_o20_jit_before_lw` / `alchemy_o20_guard_arm(…,o14)` in `memory.cpp`.

## Build status (W-CNK-ALCHEMY)

| Item | State |
|------|-------|
| Lock | `logs/locks/native-b49f….lock` — owner `alchemy-rebuild-parent` (pid 26656 gone; cooperated, no second writer) |
| First link (~702/703) | **FAILED** — raced stale `memory.cpp.obj` / `libps2runtime.a` missing `alchemy_o20_*` + `restore_butanim_attach_if_cleared` |
| Archive after recompile | `libps2runtime.a` **has** `alchemy_o20_guard_armEjjj`, `alchemy_o20_jit_before_lw`, `restore_butanim_attach_if_cleared` (mtime ~19:05) |
| In flight | Two cmake/ninja (`-j8` + `-j1`) still compiling generated units after header churn; **ps2run.exe absent** pending successful link |
| Smoke | **PENDING** — `--disc games/b49f…/disc.iso` ~2–4k frames; look for probe `0x503308` + prims ≫ 2 |

## Next

- Await single successful `ps2run` link (do not kill in-flight ninjas).
- Smoke with disc; capture probe/prims.
- If gate still fails: RE child vt+0x78 impls that may clear parent+0x20 during `igAlchemy_vt108_child_walk`.
