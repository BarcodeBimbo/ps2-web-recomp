# Alchemy runtime rebuild — progress log

**Started:** 2026-11-07 ~19:00 local (God mandate: build Alchemy operational)  
**Updated:** 2026-11-07 ~19:12 local (W-CNK-ALCHEMY)  
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

**Clear-site map:** `verification/recovery/alchemy-o20-clear-ghidra-2026-11-07.md`.

## Runtime changes (this session)

1. Export `restore_butanim_attach_if_cleared()` from `igfileio`.
2. Widen Alchemy o20 store-guard to **st64/st128** spans that zero the guarded word.
3. JIT `alchemy_o20_jit_before_lw` injected at `L_00503308` in generated `unit_0100.cpp`.
4. `probe()` restore hooks in `dispatch.cpp` for `0x5032E0` / `0x503300` / `0x503308`.
5. `games/<cnk>/probes.txt` present — **but generated units have zero `probe()` calls** (refresh_translation --probes not reflected in current `generated/…/unit_*.cpp`).

## Build status

| Item | State |
|------|-------|
| Lock | Cooperated with `native-b49f….lock` (no second writer started by this worker) |
| First link | FAILED — raced stale `memory.cpp.obj` / archive missing o20 + restore symbols |
| Recovery | Recompile refreshed `libps2runtime.a`; symbols present in final `ps2run.exe` |
| **ps2run** | **READY** — `build/native-b49f…/ps2run.exe` (~81 MB); nm has `alchemy_o20_guard_armEjjj`, `alchemy_o20_jit_before_lw`, `restore_butanim_attach_if_cleared` |

## Smoke (W-CNK-ALCHEMY)

```
ps2run games/b49f…/disc/boot.elf --disc games/b49f…/disc.iso --frames 3000
log: logs/autonomous-pipeline/b49f2e769315347e8bda839feb705744-alchemy-smoke-W-CNK-ALCHEMY-20261107T1910Z.log
exit: 0
```

| Check | Result |
|-------|--------|
| Crash | no |
| `[alchemy-o20] guard armed` | **yes** — `0x009754B8` value=`0x7462F8` o14=`0x16B06E8` |
| `[alchemy-o20] blocked clear` | **0** (clear bypassed or never hit guarded `st32`) |
| `[alchemy-o20] jit-restore` | **0** |
| `[probe] 0x503308` | **absent** (probes not compiled into units) |
| HLE `restored butanim … (was 0, +0xFF=1→0)` | **yes** — classic late restore after vt+108 finalized |
| **prims** | **2** (gate still closed) |

## Next leads (do not claim fixed)

1. Re-run `refresh_translation --probes` so `[probe] 0x503308` lines appear; confirm whether `L_00503308` / ingest is entered.
2. Why store-guard never logged a block while HLE later saw `+0x20=0` — find actual clearer (child vt+0x78 vs `0x51AD60` vs bulk/path outside `st32`/`st64`/`st128`).
3. If clear is `st32` @ `0x51AD60` with matching s0, instrument unconditional log on stores to `g_alchemy_o20_guard_addr` (any value).
