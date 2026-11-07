# Design — ps2-alchemy-dumper

## Goal

Produce a reusable **Alchemy isolation file** from a PS2 disc image so CyberArcade can
extract everything needed for Alchemy rebuild work without re-deriving TOC / ELF maps
by hand each time.

Primary consumer today: **Crash Nitro Kart** (`b49f2e769315347e8bda839feb705744`)
alongside A1–A4 research under `verification/recovery/`.

## Phases

| Phase | Status | Scope |
|-------|--------|-------|
| **1 — Research** | Done | redumper + mkps2iso patterns; adopt/strip list (`docs/RESEARCH.md`) |
| **2 — ISO-first map** | Done | Own ISO9660 reader → TOC; GFC parse; ELF Alchemy surface; `alchemy-map.json` |
| **3 — GOB/IGB + class map** | Done | STBL inflate via GFC block table; IGB `DA FA` heads; `class-map.tsv`; `verify` gate |
| **4 — Optical rip** | Stub | Windows SCSI/MMC DVD sector read inspired by redumper *ideas*; own I/O |
| **5 — Multi-title** | Later | Parameterize VA templates beyond CNK; auto-detect Alchemy version string |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│ Optical stub    │     │ Existing ISO     │
│ (Phase 4)       │────▶│ disc.iso         │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ disc.py        │  LBA / path access
                        │ iso9660.py     │
                        └───────┬────────┘
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
           ┌──────────┐  ┌──────────┐  ┌──────────────┐
           │ gfc.py   │  │ gob.py   │  │ elf_alchemy  │
           │ TOC/GFC  │  │ STBL/IGB │  │ class map    │
           └────┬─────┘  └────┬─────┘  └──────┬───────┘
                │             │               │
                └─────────────┼───────────────┘
                              ▼
                   ┌────────────────────┐
                   │ schema + verify    │
                   │ alchemy-map.json   │
                   └────────────────────┘
```

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `disc` | Unified ISO open, TOC, boot/MODULES find, GOB byte reader |
| `iso9660` | PVD + directory walk; path/LBA/size |
| `gfc` | Parse `ASSETS.GFC` magic / block / Adler / file / name tables |
| `gob` | STBL inflate, block verify, IGB head `DA FA` probe |
| `elf_alchemy` | Version string, key VAs, `ig*` catalog, GFC↔ELF path corr |
| `verify` | CNK expectation suite (exit ≠0 on failure) |
| `optical` | Stub: Windows drive-letter DVD read plan |
| `cli` | `map` / `list-iso` / `verify` / `optical` |
| `schema` | Assemble JSON + TSV writers |

## CNK key VA template (default)

| Name | VA |
|------|-----|
| entry | `0x00108D28` |
| loadgate FCE0 | `0x0010FCE0` |
| finalize | `0x00110100` |
| factory | `0x00508930` |
| bind install / clear | `0x00520160` / `0x00520210` |
| null-bind | `0x0051AC80` … `0x0051ACEC` |
| bind registry BSS | `0x00725F50` |
| Alchemy version string | `0x006B4920` |

## Debug gate

```text
python -m ps2_alchemy_dumper verify <cnk-disc.iso> -o out-cnk\
# expect: verify 20/20, exit 0
```

## Non-goals

- Wrapping upstream dumpers  
- Patching host runtime / disc-fix / R5 / game files  
- Full Redump-submission packaging  
- 1:1 ISO rebuild (mkps2iso’s job — we only *analyze*)
