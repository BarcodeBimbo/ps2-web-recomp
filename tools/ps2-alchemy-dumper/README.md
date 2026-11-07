# ps2-alchemy-dumper

Custom **Windows** CLI that opens a PS2 disc image (ISO-first) and emits a structured
**Alchemy isolation map** (`alchemy-map.json` + optional TSV) for Intrinsic Alchemy
titles (CNK and peers): disc TOC, `ASSETS.GFC`/`ASSETS.GOB`, IGB head samples, EE ELF
Alchemy surface, and MODULES vs missing `igFileIO` notes.

**This is our own CyberArcade / PS2Recomp tool.** It is a custom reimplementation.
It does **not** wrap, shell out to, or ship upstream `redumper`, `dumps2iso`, or
`mkps2iso` binaries as the product core.

## Credits (required)

| Project | Link | Role for us |
|---------|------|-------------|
| **redumper** | https://github.com/superg/redumper | Pattern source for accurate optical rip / sector workflows (GPL-3.0) |
| **mkps2iso** / **dumps2iso** | https://github.com/N4gtan/mkps2iso | Pattern source for PS2 DVD UDF/ISO LBA + file-table extract/rebuild (GPL-2.0) |

## License

This tool is licensed under **GPL-3.0-or-later** (see `LICENSE`).

- **redumper** is GPL-3.0 — any closely derived optical/sector logic inherits GPL-3.0
  obligations (copyright notices, source distribution when binaries ship).
- **mkps2iso** is GPL-2.0 — we currently use *ideas* (LBA-ordered file TOC, ISO path
  listing), not upstream source. If we later port closely derived UDF code, keep
  GPL-compatible licensing and credit.

## Platform

**Windows** is the primary product target (CyberArcade Windows branch). Optical drive
I/O is designed for Windows drive letters; ISO analysis runs anywhere Python does.

## What we adopt vs strip

### From redumper (ideas only — not vendored)

**Adopted (high-level):**

- Treat DVD dumps as sector-addressable (2048-byte user data / LBA).
- Separate *acquisition* (rip) from *analysis* (Alchemy map).
- Plan for retries / error awareness on real optical media later.
- Prefer own Windows drive path (`E:`) rather than Linux-only `/dev/sg*`.

**Stripped / not ported:**

- Full CDDA / scrambled CD (`.scram`) pipeline, subchannel, C2 state machine.
- Sample-granular dump state, refine/split workflows, BIN/CUE track split.
- Drive databases, firmware flash, OmniDrive / Xbox / Nintendo raw paths.
- CSS / title-key recovery, protection analyzers, skeleton/hash Redump packaging.
- C++20 modules tree (`drive/`, `scsi/`, `dvd/`, `readers/`, …) — we do not vendor it.
- Shelling out to the `redumper` binary.

### From mkps2iso / dumps2iso (ideas only — not vendored)

**Adopted (high-level):**

- ISO-on-disk as the primary analysis input (Alchemy rebuild needs this immediately).
- Emit a structured file table with **path, LBA, size** (dumps2iso log/XML spirit → our JSON/TSV).
- Prefer precise LBA order awareness when walking the disc.

**Stripped / not ported:**

- XML project rebuild (`mkps2iso` authoring) and 1:1 DVD rebuild.
- Boot-logo encrypt/decrypt, Master Disc sectors, dual-layer authoring.
- Obfuscated-game extract heuristics beyond what Alchemy TOC needs.
- Full UDF FID rebuild / write path (Phase 1 reader is ISO9660 primary + UDF notes).
- Shipping or invoking `dumps2iso` / `mkps2iso` binaries (`E:\AI games\mkps2iso-win64\` is local reference only).

### Alchemy-specific (ours)

Built for CNK A1–A4 research (`b49f2e769315347e8bda839feb705744`):

- `ASSETS.GFC` / `ASSETS.GOB` parse (magic, blocks, files, names, STBL).
- GFC block-table verify that GOB offsets land on `STBLz` / `STBL0`.
- Inflate priority `.igb` files and probe `DA FA` / `FA DA` heads + `ig*` meta strings.
- `boot.elf` Alchemy strings + key VA template.
- MODULES IRX list vs absent `igFileIO` / `igU*`.
- Optional `ig*` class string catalog.

## Quick start (Windows)

```powershell
cd C:\PS2Recomp\tools\ps2-alchemy-dumper
python -m ps2_alchemy_dumper map "C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso" -o out\ --save-igb-heads --verify
# or one-shot CNK gate:
python -m ps2_alchemy_dumper verify "C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso" -o out\
```

Outputs:

- `out/alchemy-map.json` — structured isolation map (schema 1.1; GOB STBL verify + IGB `DA FA`)
- `out/disc-toc.tsv` — path / LBA / size
- `out/gfc-files.tsv` — GFC name catalog when `ASSETS.GFC` present
- `out/igb-samples.tsv` — inflated IGB head probe table
- `out/class-map.tsv` — ELF `ig*` class catalog
- `out/igb_heads/*.bin` — optional first 4 KiB of each inflated IGB (`--save-igb-heads`)

List ISO root only:

```powershell
python -m ps2_alchemy_dumper list-iso path\to\disc.iso
```

Optical rip is a **stub** (`optical` subcommand documents the planned redumper-inspired
sector workflow; no drive I/O yet).

### CNK verify gate (debug-tested)

`verify` against CNK `disc.iso` currently **passes 20/20** (exit 0): GFC 1830/4327,
ext census, GOB STBL block verify, IGB `DA FA` @+0x28 (incl. butanim), ELF v3.0-0909 /
595 `ig*` / 47 raw `.igb` hits, MODULES without `igFileIO`.

## Layout

| Path | Purpose |
|------|---------|
| `DESIGN.md` | Architecture + phases |
| `docs/SCHEMA.md` | `alchemy-map.json` schema |
| `docs/RESEARCH.md` | Upstream pattern research notes |
| `ps2_alchemy_dumper/` | Own Python package (disc, ISO9660, GFC, GOB, ELF, verify, CLI) |

## Hard rules

- Do not modify `runtime/`, disc-fix, R5, or CNK game binaries from this tool.
- Do not vendor GPL upstream trees into the product without clear LICENSE + ATTRIBUTION.
- Scratch clones (if any) belong under `tools/_refs/` and are **not** the product.
