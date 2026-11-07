# CNK ELF Alchemy worker resume — w7

**Worker:** w7 / CNK ELF Alchemy redo (was `8c36c5b2`)  
**Resumed:** 2026-11-07  
**Prior agent:** `8c36c5b2-5cf7-4035-ad9f-cef59481ae11`  
**Pause file:** `verification/recovery/worker-pause-cnk-elf-8c36c5b2.md`  
**Status:** **RESUMED** — complete / quarantined research owner (idle)

## Confirmed on disk

| Artifact | Size | Present |
|----------|------|---------|
| `verification/recovery/cnk-elf-alchemy-full-redo-report.md` | 15369 B | yes |
| `verification/recovery/alchemy-sdk-research-report.md` | 17894 B | yes |
| `verification/recovery/_cnk_elf_xrefs.json` | 1899 B | yes |
| `verification/recovery/worker-pause-cnk-elf-8c36c5b2.md` | 753 B | yes |
| MASTER-CONTEXT.md §6 | — | aligns with reports |

**No new CNK ELF work started this resume.** Reports already written (2026-11-06); this file only re-owns the quarantine lane.

## Engine identity (brief)

- **Intrinsic Alchemy v3.0 -0909** (Static/Release), Sep 2003 — Vicarious Visions; studio pipeline **Velocity**.
- CNK EE: `games/b49f2e769315347e8bda839feb705744/disc/boot.elf` (= SLUS_206.49), entry `0x00108D28`, stripped MW MIPS.
- ~**673** `ig*` class-name strings; assets **IGB** in **ASSETS.GFC** / **ASSETS.GOB** (STBL/zlib).
- IOP helper `igFileIO.irx` (host often fails as ELF IRX; HLE compensates).
- **No Alchemy 3.0 PS2 SDK source** found — research is ELF + public CNK/Alchemy docs only.

## Key VAs (cheat sheet)

| VA | Meaning |
|----|---------|
| `0x00108D28` | CRT0 entry |
| `0x00108F60` | App init (“main-ish”) |
| `0x0010FCE0` | Loadgate pump (“FCE0”) |
| `0x00110100` | Slot finalize / parse kick |
| `0x00725F50` | Bind registry pointer (BSS) |
| `0x00520160` | Installs bind object into `0x725F50` |
| `0x0051ACEC` | RA of crashing **vt+84** after **vt+80** lookup |

Null-bind model (solved as model): forced FCE0 / `0x110100` with cold binder → `*0x725F50` vt+80 → null → jalr vt+84 → `missing code @0`, `ra=0x51ACEC`.

## Resume posture

- **Complete / quarantined research owner** for CNK ELF Alchemy map.
- **NO** new CNK patches, soft-arm, FCE0 force, pointer stuffing, or host_signal Alchemy pulses.
- **NO** apply to Hitman / NFS — quarantine held (MASTER-CONTEXT §6).
- **HARD BAN:** no Alchemy host patches.
- Read-only only if re-consulted; optional next (when parent asks): live vtable dump at `*ee32(0x725F50)` soft-arm vs forced-FCE0 — observe-only.

## Next action

Idle. Await parent/user before any further CNK ELF step. Do not reopen overnight host forgeries.
