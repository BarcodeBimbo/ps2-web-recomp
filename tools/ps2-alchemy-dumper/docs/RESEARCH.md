# Upstream research notes (Phase 1)

Date: 2026-11-07  
Method: GitHub README + API directory listing (no product-tree vendoring of GPL sources).  
Local binary reference only: `E:\AI games\mkps2iso-win64\` (not invoked by this tool).

Scratch clones, if created later, must live under `tools/_refs/` and stay out of the product package.

## redumper — https://github.com/superg/redumper

**License:** GPL-3.0  
**Platforms:** Windows, Linux, macOS (C++20 modules, CMake)

### High-level layout

`main.cc`, `redumper.ixx`, `drive/`, `scsi/`, `dvd/`, `cd/`, `readers/`, `filesystem/`,
`analyzers/`, `hash/`, `utils/`, drive database in `drive.ixx`.

### Optical / sector workflow ideas (relevant)

1. Disc acquisition is a first-class pipeline (`redumper disc`) separate from later refine/split.
2. DVD/HD/BD dumping is high-level sector dumps (PS2 DVD-5/9 fits here more than CDDA).
3. Windows drive selection by letter (`--drive=E:`).
4. Retries for SCSI/C2 errors; overwrite protection; image name/path options.
5. Sample/sector state enables incremental refinement across drives (CD-heavy; DVD simpler).

### What we take

- Sector = LBA × 2048 mental model for PS2 DVD ISO payloads.
- Rip vs analyze separation; Windows drive-letter plan for Phase 4.
- Error-aware read mindset (retry notes in optical stub).

### What we strip

Full CD scrambled dump, subchannel, C2 state vectors, track split, firmware flash,
Redump packaging, OmniDrive/Xbox/Nintendo paths, and any dependency on the redumper binary.

## mkps2iso / dumps2iso — https://github.com/N4gtan/mkps2iso

**License:** GPL-2.0  
**Platforms:** Windows, Linux, macOS releases

### High-level layout

`src/dumps2iso/`, `src/mkps2iso/`, `src/shared/`, CMake presets, examples.

### UDF / LBA / file-table patterns (relevant)

1. `dumps2iso` extracts PS2 DVD images to files and documents structure (XML + LBA log spirit).
2. File order / LBA control matters for PS2 access timing (CDVDGEN lineage).
3. ISO is the interchange format for emulators and our Alchemy analysis.
4. Limitations called out upstream: no fragmented images; no CD bin/cue (use mkpsxiso).

### What we take

- ISO-first analysis path with path + LBA + size tables.
- Structured dump artifact (we emit JSON/TSV instead of XML project files).
- Awareness that PS2 DVD images are UDF+ISO9660 hybrid in practice; Phase 2 starts with
  ISO9660 PVD directory walk (sufficient for CNK root + MODULES).

### What we strip

XML rebuild authoring, boot logo crypto, Master Disc / dual-layer generation,
shipping dumps2iso/mkps2iso, and any shell-out to `E:\AI games\mkps2iso-win64\`.

## CNK research inputs (consumed, not re-derived)

- `verification/recovery/alchemy-rebuild-synthesis-a1-a4-2026-11-07.md`
- `alchemy-rebuild-w1-cnk-elf-walk-2026-11-07.md`
- `alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md`
- Kit/concepts: `C:\usr\alchemy`, `C:\usr\alchemy\ps2tek`
