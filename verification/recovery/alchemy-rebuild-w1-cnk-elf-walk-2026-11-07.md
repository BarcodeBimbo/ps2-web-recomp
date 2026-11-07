# Alchemy rebuild — Worker 1: CNK EE ELF walk

**Mode:** RESEARCH ONLY. No runtime / disc-fix / R5 / CNK game patches.  
**Date:** 2026-11-07  
**Game:** Crash Nitro Kart (CNK) — **not** Hitman  
**Game id:** `b49f2e769315347e8bda839feb705744`  
**Worker:** 1 (import / symbol / string walk)

Cross-check: `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `cnk-nullbind-51ACEC-live-report.md`, `MASTER-CONTEXT.md` §6.

---

## 1. ELF identity / paths

| Item | Value |
|------|--------|
| **Primary EE image** | `games/b49f2e769315347e8bda839feb705744/disc/boot.elf` |
| Size | **6 234 672** bytes |
| Disc peer | `disc.iso` (assets live here; no `ASSETS.GFC`/`ASSETS.GOB` **strings** inside the ELF) |
| `SLUS_206.49` on disc tree | **Absent** as a separate file — `boot.elf` **is** the EE binary (same size/entry as public cnk-decomp `SLUS_206.49`) |
| Native build | `build/native-b49f2e769315347e8bda839feb705744/` (`ps2run.exe`, `libps2game.a`, generated recomp units) — host binary, not a second guest ELF |
| Compiler `.comment` | `MW MIPS C Compiler (2.4.1.01)` / `PlayStation2` |
| Entry | **`0x00108D28`** |
| PHDR0 LOAD | file `0x80` → VA **`0x00100000`**, filesz `0x5F2000`, memsz `0x62A480`, flags RWX |
| PHDR1 | VA `0x0072A480`, filesz 0 (BSS end marker) |
| BSS | `0x006F2000` … `0x0072A480` |
| **Symbols / imports** | **Stripped.** `.symtab` / `.strtab` size **0**. No `.dynsym` / `.dynamic` / useful reloc sections. No import table to walk — only absolute `jal`/`j` encodings + `lui`/`lw`/`sw` patterns. |

---

## 2. Alchemy version string

| Field | Value |
|-------|--------|
| VA | `0x006B4920` |
| String | **`Intrinsic Alchemy  v3.0 -0909 (Static/Release)`** |
| Build line (next string) | `Built by rdy on Tue Sep 9 19:28:21 2003` @ `0x006B4950` |

Matches TCRF / prior redo + SDK research reports. Studio pipeline nickname **Velocity** present (`Velocity.igm` @ `0x0061099C`, `velocity-ps2-cw-dbg.elf` path in same config blob).

---

## 3. Key VAs — confirmed still present + neighbors

All prior anchors **still map** in this `boot.elf`.

| Name | VA | Region | Evidence (this walk) |
|------|-----|--------|----------------------|
| CRT0 entry | `0x00108D28` | LOAD | MMI clear loop (`paddw`-family `70000C28`…) |
| App init (“main-ish”) | `0x00108F60` | LOAD | prologue present; **1×** `jal` from `0x00108ED8` |
| Loadgate pump **FCE0** | `0x0010FCE0` | LOAD | `addiu sp,sp,-80`; slot math uses +72/+84; **sole** `jal` site `0x0010F5EC` |
| Finalize / parse kick | `0x00110100` | LOAD | prologue present; **sole** `jal` from FCE0 @ `0x0010FD3C` |
| Bind registry ptr | `0x00725F50` | **BSS** | not in file; **20** `lui 0x72` + `lw`/`sw` `0x5F50` sites |
| Bind installer | `0x00520160` | LOAD | `jal 0x508930` then **`sw v0, 0x5F50($at)`** @ `0x520180` |
| Bind teardown | `0x00520210` | LOAD | **`sw zero, 0x5F50($at)`** @ `0x5202AC` |
| Null-bind helper | `0x0051AC80` | LOAD | flag+24; vt+92; load `*0x725F50`; vt+80 then vt+84 |
| Null-bind RA | `0x0051ACEC` | LOAD | insn **after** crashing `jalr` — `jal 0x005170A0` |
| Factory | `0x00508930` | LOAD | `lw a0,[0x725F00]; a1=3; jalr vt+8` — **209** `jal` sites |

### 3.1 Neighbor notes (confirm prior disasm)

**FCE0 (`0x10FCE0`)** — still the loadgate drain: reads walker at base+24020, stride math `i*96` via `(i<<1)+i)<<5`, checks status/state words, only caller `0x10F5EC`.

**Null-bind (`0x51AC80`…`0x51ACEC`)** — unchanged vs live report:

- `0x51ACBC`/`ACC0`: `lui at,0x72` / `lw a0, 0x5F50(at)` → bind registry  
- `0x51ACC8`/`ACCC`: `jalr` registry **vt+80**  
- `0x51ACE0`/`ACE4`: `jalr` result **vt+84** (null when lookup returns 0)  
- `0x51ACEC`: next insn / RA after bad `jalr`

**Installer (`0x520160`)** — factory → store registry → second alloc → `obj+0x2C=1` → vt+208 → reload registry → vt+84. No direct `jal` to installer/teardown in the image (only jump-table-style `j` words @ `0x4D2740` / `0x4D2750`); call graph is pointer-driven.

### 3.2 BSS sibling band (still relevant)

| VA | Role |
|----|------|
| `0x00725EE0` / `EF0` / `EF8` | factory pool siblings (prior) |
| `0x00725F00` | allocator object for `0x508930` |
| `0x00725F50` | **bind registry singleton** |
| `0x00725C20` | type descriptor used by registry tid lookup (prior live report) |

### 3.3 `0x725F50` lw/sw catalog (expand)

| Access VA | Op | Notes |
|-----------|-----|--------|
| `0x0023AF20`, `AF60`, `AFD8` | lw | early consumers |
| `0x0031C0E8` | lw | |
| `0x00517124` | lw | |
| **`0x0051ACC0`** | lw | **null-bind path** |
| **`0x00520180`** | **sw** | **installer write** |
| `0x005201B4`, `220`, `23C`, `27C` | lw | post-install use / teardown path |
| **`0x005202AC`** | **sw zero** | **teardown clear** |
| `0x00535300`, `A940`, `ACF8`, `AFC4`, `B2B4`, `B5C8`, `B67C`, `B930` | lw | registry method region (~`0x53xxxx`, includes live vt+80 `@0x53B940` neighborhood) |

---

## 4. String hit counts (Alchemy surface)

Counts = distinct extracted C-strings (≥4 printable) containing the needle, unless noted as raw byte count.

| Needle | String hits | Raw bytes in ELF |
|--------|-------------|------------------|
| `Intrinsic Alchemy` | 1 | 1 |
| `Alchemy` | 10 | (broader) |
| `ALCHEMY_BASE` | 1 | 1 |
| `ABSOLUTE_BASE` | 1 | 1 |
| `APPLICATION_BASE` | 1 | 1 |
| `alchemy.ini` | 2 | 2 (`0x6B4ACD` embedded + `0x6B4B08` standalone) |
| `$(AlchemyRoot)` | 1 | 1 @ `0x006B6020` |
| `_isAlchemyMemory` | 1 | 1 @ `0x006B43A0` |
| `igFileIO` / `igFileIO.irx` | 1 | 1 @ `0x006B8F18` |
| `igUKbd` / `igUMouse` | 1 each | IRX names @ `0x6BA0E0` / `0x6BA0F0` |
| `/usr/local/Alchemy` | 1 | full path `…/iop/modules` @ `0x006B8E90` |
| `c:/Alchemy` | 1 | `c:/Alchemy/iop/modules` @ `0x006B8EB0` |
| `.igb` | **47** | 47 |
| `IGB` | 5 | (class/error text) |
| `Velocity` / `velocity` | 3 / 3 | includes `Velocity.igm` |
| `igPsx2*` class tokens | 46 | |
| `igMalloc*` | 11 | |
| `igIGBFile` | 3 | class + error strings |
| `igFile` | 4 | |
| `loadgate` | **0** | host nickname only — not an ELF string |
| `FCE0` as text | 0 | function VA only |
| `ASSETS.GFC` / `ASSETS.GOB` | **0** | on **ISO**, not baked into EE ELF |
| `GFC` / `GOB` / `STBL` / `STBLz` | 0 | same |
| `IOPRP255` | 1 | `cdrom0:\IOPRP255.IMG;1` @ `0x00611000` |
| `MODULES` | 5 | incl. `sonyModulePath = \MODULES` |

---

## 5. `ig*` class-name density

| Metric | Count | Method |
|--------|------:|--------|
| Whole-string `^ig[A-Za-z0-9_]+$` | **595** | C-strings that are exactly a class token |
| Unique `ig[A-Za-z0-9_]+` tokens anywhere | **717** | includes tokens inside messages |
| Camel `^ig[A-Z]…` tokens | **606** | class-like subset of tokens |
| Prior redo report | ~**673** | same ballpark; methodology slightly looser — treat **595–717** as the bounded range from this walk |

**Absolute pointer tables** to those class-name strings are **sparse**: only **22** absolute pointers in the LOAD image land on whole-string class names (**22** unique). Type registration is mostly factory/runtime, not a dense RTTI dump.

### Prefix density (whole-string classes, top buckets)

`Psx2` 40 · `Animation` 25 · `Texture` 15 · `Vertex` 14 · `Unsigned` 13 · `Non` 11 · `Attr`/`Blend`/`Custom`/`String` 10 · `Gui`/`Transform` 9 · …

### FileIO / stream / meta / PS2 subset (high-signal)

**Core I/O:** `igFile`, `igIGBFile`, `igFileImage`, `igFileImagePng`, `igElfFile`, `igMediaFile`, `igMemoryFile`, `igMemoryFileEntry`, `igProgramFile`, `igPsx2File`, `igPsx2WaveFile`

**Streaming:** `igStreamingSource`, `igStreamingQueue`, `igStreamingQueueList`, `igPsx2StreamingSource`, `igVertexStream`, `igPsx2VertexStream`

**PS2 / IOP RPC:** `igPsx2IopRpcConnection`, `igPsx2VisualContext`, (+ 37 other `igPsx2*`)

**Memory:** `igMallocMemoryPool`, `igMemoryPool`, `igArenaMemoryPool`, `igStackMemoryPool`

**Meta / reflect:** `igMetaObject`, `igMetaField`, large `*MetaField` set (serialization into IGB)

---

## 6. Module / FileIO path catalog

### Alchemy IOP search paths (ELF)

| VA | String |
|----|--------|
| `0x006B8E90` | `/usr/local/Alchemy/iop/modules` |
| `0x006B8EB0` | `c:/Alchemy/iop/modules` |
| `0x006B8F18` | `igFileIO.irx` |
| `0x006BA0E0` | `igUKbd.irx` |
| `0x006BA0F0` | `igUMouse.irx` |
| `0x006B6020` | `$(AlchemyRoot)` |

### Boot / Sony module surface (non-Alchemy but adjacent)

| VA / area | String |
|-----------|--------|
| `0x00611000` | `cdrom0:\IOPRP255.IMG;1` |
| config ~`0x00610AE1` | `sonyModulePath = \MODULES` + `[CLASSES_TO_VTABLE_CACHE]` (Alchemy class cache section) |

### IRX name strings present

`sio2man.irx`, `padman.irx`, `mtapman.irx`, `mcman.irx`, `mcserv.irx`, `usbd.irx`, `lgdevw.irx` / `lgdev.irx`, `libsd.irx`, `sdrdrv.irx`, `vvaa.irx`, `cri_adxi.irx`, **`igFileIO.irx`**, **`igUKbd.irx`**, **`igUMouse.irx`**.

### Asset path strings (IGB only in ELF)

**47** `.igb` path/format strings (UI/tracks/hud/fonts), e.g. `gfx/ui/butanim.igb`, `ui/introtxr.igb`, `gfx/tracks/%s.igb`.  
**No** `ASSETS.GFC` / `ASSETS.GOB` literals in the EE image — those are disc archive names observed at runtime / on ISO.

---

## 7. Imports / relocs / xrefs summary

| Kind | Result |
|------|--------|
| ELF imports / dynsym | **None** (static MW link, stripped) |
| Reloc sections | **None** useful |
| `jal` → FCE0 | **1** (`0x10F5EC`) |
| `jal` → `0x110100` | **1** (`0x10FD3C`) |
| `jal` → `0x51AC80` | **3** (`0x10FF10`, `0x4EDE50`, `0x51AD9C`) — matches prior |
| `jal` → factory `0x508930` | **209** |
| `jal` → bind installer/teardown | **0** (pointer / jump-table indirection) |
| Data xrefs to `0x725F50` | **20** lw/sw via `lui 0x72` |

---

## 8. Notes for Alchemy rebuild research

1. **Guest identity is stable:** same `boot.elf`, entry, Alchemy **3.0 -0909** Sep 9 2003 build — nothing in the EE image contradicts the 2026-11-06 redo / null-bind reports.  
2. **No public symbol surface** — rebuild work must stay string- + pattern-driven (class names, error formatters, `jal` graphs, BSS installers).  
3. **FileIO is named but not sourced:** paths + `igFileIO.irx` + `igFile`/`igIGBFile`/`igPsx2*` classes are the ELF contract; IOP module bytes are not in this ELF.  
4. **GFC/GOB are disc-side** — do not expect archive magic in the EE binary; pair this walk with ISO/`ASSETS.*` research.  
5. **“loadgate” / “FCE0”** are host nicknames for `0x10FCE0` behavior — zero string hits.  
6. **Native tree** (`build/native-b49f2e…`) is recomp host output only; do not confuse with a second Alchemy EE image.  
7. Hard ban respected: **no patches** this pass.

---

## 9. Artifacts

| File | Role |
|------|------|
| `verification/recovery/alchemy-rebuild-w1-cnk-elf-walk-2026-11-07.md` | This report |
| `verification/recovery/_tmp_w1_cnk_elf_walk.py` / `.json` | Machine-readable walk dump |
| `verification/recovery/_tmp_w1_cnk_elf_walk2.py` / `.json` | Class/FileIO supplement + full 595-name list |

**ELF path for JSON return:** `games/b49f2e769315347e8bda839feb705744/disc/boot.elf`
