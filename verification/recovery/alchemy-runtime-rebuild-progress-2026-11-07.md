# Alchemy runtime rebuild — progress log

**Started:** 2026-11-07 ~19:00 local (God mandate: build Alchemy operational)  
**Updated:** 2026-11-07 ~19:14 local (W-CNK-SMOKE)  
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
**Key note:** `sd $zero` clear paths bypass st32-only guard — widen to st64/st128 (done in tree).

## Runtime changes (this session)

1. Export `restore_butanim_attach_if_cleared()` from `igfileio`.
2. Widen Alchemy o20 store-guard to **st64/st128** spans that zero the guarded word.
3. JIT `probe()` restore at `0x5032E0` / `0x503300` / `0x503308`.
4. Opportunistic `preempt()` restore at those PCs.
5. `games/<cnk>/probes.txt` + `windows_port.refresh_translation` passes `--probes` when present.
6. `alchemy_o20_jit_before_lw` / `alchemy_o20_guard_arm(…,o14)` in `memory.cpp`.
7. Generated `unit_0100` / `m_…_unit_0100` contain `alchemy_o20_jit_before_lw` at `L_00503308` (sources refreshed ~19:13).

## Build status

| Item | State |
|------|-------|
| Lock | `logs/locks/native-b49f….lock` — held by `W-CNK-smoke-o20` after smoke; **respect** inflight cmake **11292** (`-j1` ps2run, m_* cascade ~168/573+) — **no kill** |
| `ps2run.exe` | **PRESENT** (~19:08–19:10 link; o20 runtime syms confirmed via nm) |
| Cascade | Still compiling generated `m_00100000_*` units after header/source churn; `unit_0100.cpp.obj` not yet re-emitted at smoke time |
| Hitman | **untouched** |

## Smoke (W-CNK-SMOKE) — **DONE** 5000f muted

| Item | Result |
|------|--------|
| Cmd | `ps2run disc/boot.elf --disc games/b49f…/disc.iso --frames 5000` (`SDL_AUDIODRIVER=dummy`, host audio muted) |
| Binary | Copy of linked exe → `logs/autonomous-pipeline/cnk-smoke-bin-20261108T001048Z/` (avoid racing cascade linker) |
| Log | `logs/autonomous-pipeline/cnk-b49f-o20-smoke-5k-20261108T001048Z.log.err` (+ `.result.txt`) |
| `[alchemy-o20] guard armed` | **YES** — `0x009754B8 value=0x007462F8 o14=0x016B06E8` |
| `[probe] 0x503308` | **ABSENT** (0 `[probe]` lines) |
| `[alchemy-o20] jit@` / `jit-restore` | **ABSENT** |
| Late HLE restore | **YES** — `restored … +0x20=0x7462F8 (was 0, +0xFF=1→0)` — classic post-vt108 / too-late |
| Prims | **2** — **not** ≫ 2 |
| Verdict | **GATE RED.** Soft-arm + guard fire; JIT/probe path **not observed** on this image. Aligns with clear-site: +0x20 dead by ingest load; late restore cannot unstick prims. |

## Next

1. Await cascade cmake/ninja finish + fresh `ps2run` link that includes hooked `unit_0100` / probes.
2. Re-smoke 3–8k frames; require `[probe] 0x503308` and/or `[alchemy-o20] jit-restore` **before** claiming progress on prims.
3. If probe/JIT fire but prims stay 2: RE child `vt+0x78` clearers / `sd $zero` bypass evidence live.
4. Do **not** host-force FCE0; Hitman trees off-limits.
