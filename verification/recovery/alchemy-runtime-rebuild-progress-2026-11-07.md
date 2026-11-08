# Alchemy runtime rebuild — progress log

**Started:** 2026-11-07 ~19:00 local (God mandate: build Alchemy operational)  
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

Critical gate asm: `jal child_walk` → `lw a0,0x20(s0)` @ **`0x503308`**.

## Runtime changes (this session)

1. Export `restore_butanim_attach_if_cleared()` from `igfileio`.
2. Widen Alchemy o20 store-guard to **st64/st128** spans that zero the guarded word.
3. JIT `probe()` restore at `0x5032E0` / `0x503300` / `0x503308`.
4. Opportunistic `preempt()` restore at those PCs.
5. `games/<cnk>/probes.txt` + `windows_port.refresh_translation` passes `--probes` when present.

## Next

- Rebuild CNK native with probes + runtime.
- Smoke `--disc games/.../disc.iso`; gate = prims ≫ 2 + no crash.
- Continue structure map / IGB object graph reconstruction after gate moves.
