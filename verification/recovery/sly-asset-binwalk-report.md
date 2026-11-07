# Sly Cooper asset binwalk report

**Date:** 2026-11-06  
**Game:** Sly Cooper and the Thievius Raccoonus (USA) — gid `c0c4527037b6168660829a0eb13df1a3`  
**Scope:** Read-only inventory + format research of the **entire** game folder. **No code changes.**  
**Quarantine:** No CNK Alchemy, no Hitman/NFS cdvdfsv edits.

Cross-refs:

- `verification/recovery/sly-gs-vu-live-report.md` — soft≈GPU still both missing buildings; strict VU did not restore; PATH1 heavy + PATH3/PSMT4/8/STQ
- `verification/recovery/sly-geometry-texture-research-note.md` — shared GS STQ/CLUT as primary; incomplete assets ranked **unlikely**

Sample analysis dumps (headers/strings only): `verification/recovery/sly-asset-samples/`

---

## 1) Full folder inventory (what is actually there)

Root: `games/c0c4527037b6168660829a0eb13df1a3/`  
**121 files**, ~2.86 GB total. **No** `overlays/`, `pack/`, loose `.wad`/`.wal`/`.wac`/`.brx`/`.pak`.

| Path | Size / count | What it is |
|------|----------------|------------|
| `disc.iso` | 2,802,319,360 bytes (~2.61 GiB), 1,368,320 × 2048-byte sectors | Full USA disc image. Volume label **SLY**. Almost all game art lives here as a **hidden archive**, not as ISO filenames. |
| `disc/boot.elf` | 1,712,328 bytes | EE executable (`SCUS_971.98`). Same size as ISO file. Contains game code + embedded **DVP VU overlays**. |
| `vu1/*.bin` | **100** files × 16,384 bytes | Captured VU1 micro-memory dumps from explore. Filenames `HASH_MICOFF.bin`. Only **3 unique contents** (90 + 9 + 1) — same programs snapshotted at different mic-mem offsets. |
| `explore_ram.bin` | 37,748,736 bytes (36 MiB) | EE RAM dump from explore run. Has live UI/level strings (Paris, Hideout, etc.). |
| `health.json` | small | Explore health: **status ok**, **11,816,466** prims / 3600f, **no missing_code**, frame limit reached. |
| `library.json` | small | Title metadata; status `ready`. |
| `entries.txt` | **0 bytes** | Empty — no extracted entry list left behind. |
| `shots/*.ppm` | 12 frames | Explore screenshots, **P6 640×448**. Visual evidence only (not asset banks). |
| `shots_smoke/*.ppm` | 3 frames | Smoke-run screenshots, same format. |

ISO9660 directory (only these named files — path table has **root only**):

| ISO file | LBA | Size | Role |
|----------|-----|------|------|
| `SYSTEM.CNF` | 275 | 51 | `BOOT2=cdrom0:\SCUS_971.98;1`, VER 1.00, NTSC |
| `SCUS_971.98` | 276 | 1,712,328 | Main ELF (= `disc/boot.elf`) |
| `IOPRP243.IMG` | 1113 | 253,201 | IOP reboot image |
| `SIO2MAN.IRX` | 1237 | 6553 | SIO2 |
| `PADMAN.IRX` | 1241 | 44917 | Pad |
| `MCMAN.IRX` / `MCSERV.IRX` | 1263 / 1308 | … | Memory card |
| `LIBSD.IRX` | 1312 | 25397 | Sound driver lib |
| `989SND.IRX` | 1325 | 154600 | 989 Studios sound (banks/streams) |

**~2.6 GB after the ISO file list is “ghost” data** — not listed in the directory. That matches known Sucker Punch / Sly 1 retail layout.

---

## 2) Formats found (and how the game uses them)

### A. Hidden disc archive (WAL) — level + art payload

From [SlyMods WAL](https://slymods.info/wiki/WAL) / [BRX](https://slymods.info/wiki/BRX) / [FK](https://slymods.info/wiki/FK) (cross-checked against this ISO):

- Retail Sly 1 stores almost everything in a **hidden, encrypted WAL** on the disc.
- A **WAC** catalog (name / type / sector) exists for PS3 remasters; **PS2 retail** instead uses **hardcoded sector lookup tables in the ELF** (“ghost TOC”).
- Inside the WAL: per-level **BRX** (“binary resource archive” / “Z file”) containers — maps, scripts, textures, models — usually with **custom LZ** compression.
- Sly 1 **file kinds (FK)** the loader cares about:
  - `FK_BrxWorld` (0) — BRX level archive (geometry + textures + level scripts)
  - `FK_IcoIcon` (1) — ICO
  - `FK_BnkEffects` / `FK_BnkMusic` (2/3) — sound banks
  - `FK_VagDialog` / `FK_VagAnimation` (4/5) — VAG audio
  - `FK_PssMovie` (6) — FMV

**This ISO’s evidence:**

- After listed IOP files (~LBA 1400), most of the disc is **high-entropy** (≈255–256 unique bytes/sector) with **no plaintext** `.brx` / `.wal` / `paris` / `SShd` markers in sampled windows — consistent with **encrypted/compressed WAL**, not missing data.
- Large nonzero runs (coarse 1024-sector map), e.g. ~540 / 686 / 576 MB islands — bulk game content.
- **No loose BRX/WAL/WAC** under the game folder; extraction would require a Sly 1 level extractor / sector table walk, not opening a named pack file.

### B. Clear MPEG / PSS movies (not the building meshes)

At **LBA 1400** there is a small **125-entry table** of `(sector, size=2)` pairs starting at sector **104912**.

Following that target:

- Sector **104912** begins `00 00 01 BA` … `00 00 01 E0` → **MPEG-PS pack + PES video** (PSS/FMV style).
- Other hits (e.g. LBA 200000, 987136) also show `01 BA` / `01 BD` MPEG signatures.

So part of the “ghost” region is **cutscene streams**, indexed near the end of the ISO file list — **not** Paris building meshes.

### C. Boot ELF + VU microprograms

- `boot.elf`: single PT_LOAD at `vaddr=0x100000`.
- Strings: IOP module names, `cdrom0:`, UI (“Paris, France”, “The Hideout”, “Restart Level”), **989snd** bank-load paths, and many **`.DVP.overlay...`** tags → **VU1 microprograms embedded as DVP overlays** in the ELF.
- `vu1/` dumps: live VU1 programs the recompiler captured. Only **3 unique** programs among 100 files → a small set of microprograms reused at different mic-mem bases (filename suffix = mic offset). These feed **GIF PATH1** geometry (see GS/VU live report: ~1.4M PATH1 packed @1800 gameplay / ~3.58M explore).

### D. Runtime texture path (not a loose “texture bank” file)

There is **no** separate texture PAK in the folder. Textures travel inside **BRX → RAM → GS**:

- Live capture (cross-ref): textured draws are almost all **PSMT4 / PSMT8**, **FST=0 (STQ)**, CLUT via **CSM=0 / CLD=1**, heavy **PATH3 image** (~499k gameplay / ~510k explore) + thousands of `load_clut`.
- That is the **GS hardware format** after upload, not a desktop PNG/DDS bank.

### E. Explore artifacts (proof of load, not source assets)

| Artifact | Says about loading |
|----------|--------------------|
| `health.json` | Explore finished cleanly; **11.8M prims**; no missing overlays/code. |
| `explore_ram.bin` | Level **names and dialogue already in RAM** (“Paris, France”, “The Hideout”, “A Hazardous Path”, …). Streaming/CD path exercised (`cdrom0:`, 989snd stream strings). |
| `shots/*.ppm` | Renderer produced frames; useful for “buildings missing” visual confirm only. |
| `entries.txt` | Empty — no leftover extracted TOC. |

### F. What was **not** found in the folder

- No `overlays/` directory (VU overlays live **inside** `boot.elf` + `vu1/` dumps).
- No extracted WAD/WAL/WAC/BRX/PAK.
- No font/model/texture files as standalone desktop formats.
- No Alchemy/CNK containers (correct — wrong franchise).

---

## 3) Sample extracts (analysis dumps only)

Under `verification/recovery/sly-asset-samples/` (small headers/strings — no multi‑MB floods):

| Sample | Purpose |
|--------|---------|
| `boot-elf-*-strings.txt` | ELF path / UI / DVP overlay clues |
| `explore-ram-interesting-strings.txt` | Live level/IOP/stream strings |
| `iso-hidden-data-lba1400-hdr512.bin` | FMV sector table header |
| `iso-lba104912-hdr64.bin` | MPEG-PS (`01 BA`) movie start |
| `iso-run-lba{51200,535552,987136}-hdr256.bin` | Headers of largest high-entropy WAL-like runs |
| `vu1-sample-AA94318DC8235C55_0000.bin-first256.bin` | One unique VU1 program head |

**Not done (on purpose):** full WAL decrypt / full BRX unpack — needs dedicated Sly 1 tools + large disk; this job stayed documentary.

---

## 4) Cross-ref to GS/VU diagnosis

| Finding (this binwalk) | Matches live GS/VU reports? |
|------------------------|-----------------------------|
| Full ISO present; health ok; huge prim counts | Yes — renderer is **busy**, not starved of disc I/O |
| No missing_code / ELF boots | Yes — not “failed to load executable” |
| Level strings in `explore_ram.bin` | Yes — first-map content **reached EE memory** |
| Heavy VU1 program set + PATH1-oriented design | Yes — PATH1 packed ~millions; strict VU still no buildings |
| Textures are runtime PSMT4/8 + CLUT/PATH3, not loose files | Yes — STQ / CLUT / PATH3 called out as next shared-path work |
| Soft and GPU both missing buildings | Assets present on disc **and** in the draw path enough to make millions of prims — failure is **shared decode/texturing**, not “ISO incomplete” |

Parked geometry note #6 (“incomplete assets — unlikely”) is **confirmed** by this folder walk.

---

## 5) Why buildings are likely missing (ranked)

1. **Present assets, wrong shared GS texturing / STQ (FST=0) on strip-heavy PSMT4/8** — buildings may be submitted as tiny/degenerate or invisible textured batches; largest textured batch areas in capture were only ~6.6k px². Soft and GPU both wrong → shared path. *(Best fit; same ranking as GS/VU live report.)*

2. **PATH3 image ↔ CLUT / TEX0 CLD ordering** — half-million PATH3 images; wrong CLUT → “empty city” look even when verts exist.

3. **GIF/PATH1 mesh audit still open** — confirm building verts exist **before** GS. Strict VU (−143 prims) did **not** restore buildings, so VU interpret-vs-compile is a **weak** explanation; still worth proving meshes aren’t culled only in compiled VU.

4. **Strip/ADC/Z** — only after GIF clearly has building meshes that GS drops.

5. **Missing / corrupt disc assets** — **lowest**. Full ~2.6 GiB ISO, health ok, 11.8M explore prims, Paris strings in RAM, FMV MPEG found, WAL-sized high-entropy regions present. Not an incomplete dump.

6. **Need to “re-extract textures to fix buildings” as a runtime fix** — **wrong tool for the emulator bug**. Offline BRX extract helps **identify** expected meshes/UVs; it does not replace fixing GS STQ/PATH3 in the shared path.

---

## 6) Safe next analysis steps (still read-only / no product code)

1. **GIF/PATH1 audit on one Paris gameplay frame** — count XYZ/STQ strips; look for building-scale batches vs prop-only. Ties to ranking #1/#3.
2. **Hottest TBP / CLUT timeline** — align PATH3 uploads with TEX0 CLD on a missing-building frame.
3. **Optional offline:** run a known **Sly 1 Level Extractor** against `disc.iso` into a scratch folder (outside runtime) to dump Paris BRX headers — compare expected mesh/texture counts to GIF. Do **not** feed Alchemy/CNK tooling.
4. **ELF sector-table RE** (read-only): find hardcoded WAL offsets for `FK_BrxWorld` of Paris / hideout — document LBAs next to samples.
5. Keep **soft vs GPU ~28%** as a **secondary** noise track; buildings missing in **both** stays the correctness north star.

---

## 7) Explicit job limits

- **NO CODE CHANGES** this job.
- No CNK / Hitman / NFS edits.
- Report + small analysis dumps only.

---

## Bottom line (plain English)

Sly’s buildings are **not missing because the game folder lacks art**. The disc is a full USA ISO with a **hidden encrypted WAL** of **BRX** levels; explore already loaded Paris into RAM and drew **millions** of primitives. What you have on disk that looks “researchable” is mostly: the ISO ghost archive, the boot ELF (with VU overlays), VU1 dumps, and RAM/shots from runs — **not** loose texture/model packs. Missing buildings line up with **assets present but wrong GS/VU→GIF texturing (STQ + PATH3/CLUT)**, matching the live GS/VU reports — not with a need to invent formats or re-rip the ISO for the emulator to “find” buildings.
