# Worker pause — CNK ELF Alchemy (`8c36c5b2`)

**Paused:** 2026-11-06 ~23:51 local  
**Agent:** `8c36c5b2-5cf7-4035-ad9f-cef59481ae11`  
**State:** Already `turn_ended` / success before pause request — no interrupt needed.

## Latest deliverables

- `verification/recovery/cnk-elf-alchemy-full-redo-report.md`
- `verification/recovery/_cnk_elf_xrefs.json`

## Findings snapshot

- Entry `0x00108D28` (CRT0); app init ≈ `0x00108F60`
- Null-bind crash path: `*0x725F50` → vt+80 → **jalr vt+84** with `ra=0x51ACEC`
- `0x725F50` is BSS bind registry (not a file constant)
- Quarantined from Hitman/NFS; read-only ELF work

## Next (when unpaused)

Live vtable dump at soft-arm vs forced-FCE0 — no pointer stuffing. No new work started at pause.
