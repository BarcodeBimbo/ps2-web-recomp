# Worker 2 — CNK disc binwalk / TOC map (Alchemy)

**Mode:** research only. No patches.  
**Date:** 2026-11-07  
**Game id:** `b49f2e769315347e8bda839feb705744` (Crash Nitro Kart only)  
**Inputs:** `disc.iso`, `disc/boot.elf`, `explore_ram.bin`  
**Cross-refs:** `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`  
**Method note:** Sly binwalk report used only as scan/report shape reference — Sly content not analyzed.

**Tools:** `binwalk` CLI **not installed**. Used Python `mmap` + `struct` + `zlib` structural scans (`verification/recovery/_w2_cnk_binwalk_scan.py`). Sidecar JSON: `alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.json`. Samples: `verification/recovery/alchemy-rebuild-w2-samples/`.

---

## 1. Disc inventory (Alchemy-bearing)

No loose `ASSETS.GFC` / `ASSETS.GOB` / `.igb` under the game folder — archives live **inside** `disc.iso` only. `disc/` contains `boot.elf` alone.

| Path / ISO name | LBA | Size (bytes) | Role |
|-----------------|-----|--------------|------|
| `disc.iso` | — | 3 207 397 376 | Full USA image |
| `SYSTEM.CNF` | 7150 | 57 | Boot config |
| `SLUS_206.49` (= `disc/boot.elf`) | 7151 | 6 234 672 | EE ELF / Alchemy static |
| **`ASSETS.GFC`** | **1518969** | **222 968** | File/block TOC (Alchemy pack index) |
| **`ASSETS.GOB`** | **1519078** | **88 856 576** | STBL payload archive |
| `POOLS.CSV` | 1566103 | 562 | Memory-pool config (also mirrored in GFC) |
| `IOPRP255.IMG` | 1562465 | 264 449 | IOP reboot image |
| `MODULES/*.IRX` | 1564682+ | varies | Pad/sound/USB/… — **no** `igFileIO.irx` / `igUKbd` / `igUMouse` on disc |
| `MUSIC/`, `VIDEO/`, `VOICE/` | dirs | large | Non-Alchemy streams |
| Legal TGAs | various | ~0.5–0.6 MiB each | Front-matter art |

Byte offset of GFC in ISO ≈ `1518969 × 2048 = 3 110 848 512`. GOB immediately follows (LBA `1519078`).

---

## 2. ASSETS.GFC — directory / TOC layout

### 2.1 Header (big-endian)

| File offset | Field | Value (this disc) | Interpretation |
|-------------|-------|-------------------|----------------|
| `+0` | `u32 BE` | `0x00008008` | GFC magic (`kGfcSig` in host `igfileio.cpp`) |
| `+4` | `u32 BE` | `88 856 576` | Declared GOB size — **matches** ISO file size |
| `+8` | `u32 BE` | `4327` | Block count |
| `+12` | `u32 BE` | `1830` | File count |

### 2.2 Tables (exact fit, leftover `0`)

| Region | Offset | Stride / count | Contents |
|--------|--------|----------------|----------|
| Block table | `+16` | 12 × 4327 | `compressed_size`, `gob_byte_offset`, `next_block` (all BE) |
| Adler table | after blocks | 4 × 4327 | Per-block Adler-32 (BE) |
| File table | after adlers | 12 × 1830 | `crc32`, `uncompressed_size`, `first_block` (BE) |
| Name table | after files | **72 × 1830** | CNK extended names (NUL-padded; usable ≤64 chars) |

`next_block == 0x7FFF` (32767) = end of chain. Parse ends at file byte `222968` (= GFC size).

### 2.3 File-name / extension census

| Ext | Count | Notes |
|-----|------:|-------|
| `.vag` | 541 | Sound |
| **`.igb`** | **520** | Alchemy scene/asset binaries |
| `.csv` | 519 | Anim/audio/config tables |
| `.png` | 86 | Embedded/source images in pack |
| `.rcf` / `.gst` / `.hke` / … | smaller | Game-specific sidecars |
| `.opt` / `.ini` / `.sln` | few | Velocity tool leftovers (`velocity-win-msvc-dbg.opt`, …) |

Path prefixes (name table):

| Prefix | Count |
|--------|------:|
| `.\ps2\…` | 1017 |
| `.\common\…` | 705 |
| `.\hud\…` | 102 |

Full catalog TSV: `alchemy-rebuild-w2-samples/gfc-file-catalog.tsv`.

### 2.4 IGB chain stats (first 500 `.igb` entries)

| Stat | Value |
|------|------:|
| Min STBL blocks / file | 1 |
| Max | 61 |
| Average | ~5.05 |

Largest payloads are track IGBs (multi‑MB), e.g. `.\ps2\gfx\tracks\velorace.igb` (3 948 148 B, CRC `0C3B02C5`, first block 3727).

---

## 3. ASSETS.GOB — STBL frame map

### 3.1 Signature scan (whole GOB)

| Signature | Count | Interpretation |
|-----------|------:|----------------|
| `STBLz` | 4040 | zlib-compressed cluster (`STBL` + tag `z` + zlib stream) |
| `STBL0` | 289 | Uncompressed cluster (`STBL` + tag `0` + raw body) |
| `STBLz`+`STBL0` | 4329 | ≈ block count 4327 (Δ2 likely false hits inside payloads) |
| `ENBL` | 4327 | End-of-cluster marks — **exact** match to `nblocks` |
| `DA FA` / `FA DA` cookies | 2967 | Mostly **inside** inflated IGB bodies (not GOB framing) |

Block compressed sizes: min 17, max 65545, avg ≈ 19378. Max aligns with ~64 KiB Alchemy slot pages (+5-byte STBL header).

### 3.2 Block-table → GOB verification (sampled)

Every sampled GFC block offset lands on a live `STBL*` head:

| Block # | Comp size | GOB offset | Next | Head |
|--------:|----------:|-----------:|-----:|------|
| 0 | 275 | 38111232 | 32767 | `STBLz` + `78 9c…` (zlib) |
| 1 | 108 | 38113280 | 32767 | `STBLz` |
| 2 | 113 | 38115328 | 32767 | `STBLz` |
| 4 | 272 | 15564800 | 32767 | `STBLz` |
| 100 / 500 / 1000 / last | … | … | … | all `STBL*` |

**Interpretation:** GOB is a flat STBL cluster store; GFC block table is the authoritative TOC (not a linear directory walk). Community “STBLz” = framing, **not** an Alchemy C++ class (no `STBL*` strings in ELF — confirmed).

### 3.3 Inflate rule (matches host + ZenHAX/Xentax)

```
STBL0 | <raw bytes…>
STBLz | <zlib deflate…>
(+ ENBL trailer in some VV GOBs; ENBL density here == nblocks)
```

---

## 4. IGB samples (Alchemy scene headers)

Priority UI/font assets inflated from GOB (first ≤128 KiB / head samples saved):

| Name | CRC32 | Size | First blk | `DA FA` @+40 | Embedded `ig*` meta strings |
|------|-------|-----:|----------:|:------------:|-----------------------------|
| `.\ps2\gfx\ui\butanim.igb` | `D4E36BE1` | 4248 | 3801 | yes | yes (meta-fields) |
| `.\ps2\ui\introtxr.igb` | `33340283` | 400437 | 4294 | yes | yes |
| `.\ps2\gfx\ui\background.igb` | `F2EC1F44` | 707676 | 3789 | yes | yes (`igActor`, `igAnimation`, …) |
| `.\ps2\gfx\ui\citadel_logo.igb` | `88C2823C` | 298792 | 3899 | yes | yes |
| `.\ps2\ui\fetextur.igb` | `60C01EE2` | 619681 | 4266 | yes | yes |
| `.\ps2\gfx\fonts\fonts.igb` | `C3994BD8` | 80812 | 2005 | yes | yes (`igBitmapFont`, …) |
| `.\common\gfx\ui\backanim.igb` | `F0E5FBF2` | 5836 | 343 | yes | yes |
| `.\common\gfx\ui\pedecam.igb` | `EA4CD4F4` | 16404 | 344 | yes | yes |

### 4.1 Recurring IGB head layout (CNK / Alchemy 3.0)

Observed on all sampled UI/font IGBs:

| Offset | Bytes / pattern | Interpretation |
|--------|-----------------|----------------|
| `0x00`–`0x27` | 10× `u32 LE` pairs | Per-file section size/count table (varies per asset) |
| `0x28` | `DA FA 00 00` | Endian / IGB cookie (MarvelMods / Xentax family) |
| `0x2C` | `05 00 00 80` (`u32 LE` `0x80000005`) | Version / flags nibble block (Alchemy 3.x era) |
| `0x30`… | more `u32` triples | Version / type directory (stable across samples) |
| later | ASCII `ig*MetaField`, `igAttr*`, `igBitmapFont`, … | Reflective meta object names baked into IGB |

This is the on-disc form of what ELF strings call `igIGBFile` / Fast IGB — **not** a raw EE vtable dump.

Head dumps: `alchemy-rebuild-w2-samples/igb_head_<CRC>_*.bin`.

---

## 5. Correlation with known EE VAs / ELF

### 5.1 Alchemy / path strings in `boot.elf` (VA ≈ `0x100000 + file_off - 0x80`)

| Needle | Approx VA | Notes |
|--------|-----------|-------|
| `Intrinsic Alchemy` | `0x006B4920` | Matches prior ELF report |
| `igIGBFile` | `0x006B2B90` | Loader class name |
| `gfx/ui/butanim.igb` | `0x00611480` | Boot/UI path (slash form) |
| `ui/introtxr.igb` | `0x006114A0` | |
| `pools.csv` | `0x00611A20` | |
| `fonts.igb` / `backanim.igb` / `citadel.igb` / … | `0x00611xxx`–`0x0063Axxx` | ≥27 basename hits in ELF |
| `ASSETS.GFC` / `ASSETS.GOB` | **absent** | Names resolved at runtime / HLE, not baked |
| `STBL` / `STBLz` / `STBL0` | **absent** | Confirms archive framing ≠ ELF types |

### 5.2 Known runtime VAs as LE32 in disc data

| VA (from null-bind / ELF redo) | In GFC? | In GOB samples? | Meaning |
|--------------------------------|---------|-----------------|---------|
| `0x0010FCE0`, `0x00110100`, `0x0051AC80`, `0x0051ACEC`, `0x00520160`, `0x00508930` | no | no | Code VAs — not asset constants |
| `0x00725F50`, `0x00725F00`, `0x00705C18`, `0x00705F18` | no | no | BSS / sema globals — runtime only |
| `0x00BD1000` | 1 coincidental hit @ GFC `+51433` | no | Assemble scratch is **heap**; GFC hit is noise |
| `0x006B4920` / `0x006B2B90` | no | no | String VAs live in ELF image, not GOB |

**Bottom line:** Disc TOC does **not** embed the bind-registry / loadgate pointer tables. Those are built in EE BSS/heap (`0x725F50` installer path). GFC/GOB supply **named IGB bytes** that `igIGBFile` later binds.

### 5.3 `explore_ram.bin` snapshot

| Probe | Result |
|-------|--------|
| `STBL*` | **0** hits — explore dump did not retain live GOB clusters |
| GFC magic `00 00 80 08` | Multiple hits (`0x1F049E`, `0x288916`, …) — likely catalog/copy or collision |
| Path / Alchemy strings | Not present as plaintext in this 36 MiB dump |
| Aligned LE32 of `0x725F50` / `0xBD1000` / `0x10FCE0` | No hits |

Useful for “what was in RAM at explore end,” not for reconstructing GOB TOC (use ISO GFC instead).

### 5.4 MODULES vs ELF Alchemy IOP list

Disc `MODULES/` has working IRX set (LIBSD, USBD, CRI_ADXI, VVAA, pad/mc, …). **Missing on disc:** `igFileIO.irx`, `igUKbd.irx`, `igUMouse.irx` — consistent with explore.log load failures and host HLE of FileIO RPC `0x12114`.

---

## 6. TOC highlight map (how Alchemy finds a scene)

```
ISO ASSETS.GFC
  hdr 0x00008008 / gob_size / nblocks / nfiles
  → block[i] = {comp, gob_off, next} + adler[i]
  → file[j]  = {crc, size, first} + name[j] (72 B)
        │
        ▼
ISO ASSETS.GOB + gob_off
  → STBLz|STBL0 cluster (≤~64KiB page)
  → chain via next until 0x7FFF
  → concatenate inflate → IGB bytes
        │
        ▼
IGB @+0x28: DA FA … version … ig* meta / scene graph
        │
EE ELF: igIGBFile::readFile / loadgate 0x10FCE0 → finalize 0x110100
        │
Bind registry *0x725F50 (BSS) vt+80 / vt+84  ← not on disc
```

UI entry points called out by ELF strings map cleanly onto GFC names:

| ELF string VA | GFC asset | CRC |
|---------------|-----------|-----|
| `0x611480` `gfx/ui/butanim.igb` | `.\ps2\gfx\ui\butanim.igb` | `D4E36BE1` |
| `0x6114A0` `ui/introtxr.igb` | `.\ps2\ui\introtxr.igb` | `33340283` |
| `0x61132A` `fonts.igb` | `.\ps2\gfx\fonts\fonts.igb` | `C3994BD8` |

---

## 7. What this does / does not prove for rebuild

**Proven on disc:**

1. Complete GFC↔GOB TOC (1830 files / 4327 STBL blocks / 520 IGB).  
2. CNK name stride 72; zlib `STBLz` dominant.  
3. Inflated IGB heads share Alchemy `DA FA` / `0x80000005` version block + `ig*` meta names.  
4. Boot UI paths in ELF resolve to real GFC entries.

**Not on disc (still EE/runtime):**

- Bind registry object / vtables at `0x725F50`  
- Loadgate slot array / `+24008` sticky flag  
- Stream assemble buffer `0xBD1000`  
- Method names for vt+80/+84/+108  

Those remain ELF + live RAM problems (null-bind `0x51ACEC`), not missing ISO assets.

---

## 8. Artifacts produced

| Path | Contents |
|------|----------|
| `verification/recovery/alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md` | This report |
| `verification/recovery/alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.json` | Machine-readable scan |
| `verification/recovery/alchemy-rebuild-w2-samples/gfc-file-catalog.tsv` | Full 1830-file TOC |
| `verification/recovery/alchemy-rebuild-w2-samples/igb_head_*.bin` | First 4 KiB of priority IGBs |
| `verification/recovery/_w2_cnk_binwalk_scan.py` | Reproducible scanner (no patches) |

---

*End of Worker 2 report.*
