# God of War USA — structural disc walk

**Mode:** research only. No patches.
**Date:** 2026-11-07
**Game id:** `695b874b308a4e5353767bb6df8ba697`
**Method:** CNK A2–style manual `mmap`/`struct` walk (not binwalk library).
**Script:** `verification/recovery/_gow_structural_walk.py`
**JSON:** `gow-structural-walk-2026-11-07.json`
**Samples:** `verification/recovery/gow-structural-samples/`

---

## 1. Disc inventory

| Path | LBA | Size | Role |
|------|----:|-----:|------|
| `SYSTEM.CNF` | 281 | 57 | Boot config |
| `SCUS_973.99` | 282 | 1,911,580 | EE ELF (= disc/boot.elf) |
| `IOPRP300.IMG` | 1216 | 278,305 | IOP reboot image |
| `SIO2MAN.IRX` | 1352 | 6,641 | IOP module |
| `DBCMAN.IRX` | 1356 | 15,653 | IOP module |
| `SIO2D.IRX` | 1364 | 11,289 | IOP module |
| `MC2_S1.IRX` | 1370 | 20,165 | IOP module |
| `DS1O_S1.IRX` | 1380 | 9,437 | IOP module |
| `MC2_D.IRX` | 1385 | 20,221 | IOP module |
| `DS2U_D.IRX` | 1395 | 11,725 | IOP module |
| `LIBSD.IRX` | 1401 | 28,573 | IOP module |
| `989NOMID.IRX` | 1415 | 178,884 | IOP module |
| `SMPD_IOP.IRX` | 1503 | 47,948 | IOP module |
| `GODOFWAR.TOC` | 1527 | 40,068 | Asset TOC into PART1.PAK |
| `PART1.PAK` | 1547 | 4,257,794,048 | Primary asset pack (~4 GiB) |

SYSTEM.CNF: `BOOT2 = cdrom0:\SCUS_973.99;1`

## 2. Alchemy absence (vs CNK)

- ASSETS.GFC: **False**
- ASSETS.GOB: **False**
- MODULES/ dir: **False**
- GODOFWAR.TOC: **True**
- PART1.PAK: **True**

## 3. EE ELF (`SCUS_973.99`)

- Size: **1,911,580** bytes; entry `0x00100008`
- PT_LOAD segments: **1**
- Intrinsic Alchemy string: **False**
- `ig*` class whole-strings: **0**
- `igFileIO` in ELF: **False**
- STBLz/STBL0/DA_FA in ELF: 0/0/0

## 4. GODOFWAR.TOC

- Size: **40,068** @ LBA 1527
- Layout: **1669** × 24-byte records (`name[16]` + `u32` + `u32`) + 12-byte trailer
- Ext census: `{'wad': 587, 'vpk': 507, 'vag': 436, 'pss': 67, 'psw': 53, 'txt': 19}`
- Field semantics: **name[16] confirmed**. Two `u32`s act like size/offset for many WAD/VPK rows (`R_PERM.WAD` @0 → `WAD_R_Perm`), but PSS/PSW often have nonzero high size bytes and some offsets land on nested markers (`MDLX_R_Perm` @1777) — size/offset **partially reverse-engineered**.
- Offset monotonic rows (raw u32 #2): **1668/1669**

| idx | name | size | pak_offset |
|----:|------|-----:|-----------:|
| 0 | `R_PERM.WAD` | 3,638,576 | 0 |
| 1 | `BONUS03.PSS` | 566,018,052 | 1,777 |
| 2 | `TIT1E1_2.VPK` | 2,959,360 | 278,154 |
| 3 | `BONUS06.PSS` | 249,954,308 | 279,599 |
| 4 | `BONUS10.PSS` | 106,184,708 | 401,648 |
| 5 | `BONUS12.PSS` | 173,146,116 | 453,497 |
| 6 | `BONUS14.PSS` | 166,592,516 | 538,042 |
| 7 | `BONUS16.PSS` | 58,638,340 | 619,387 |
| 8 | `BONUS17.PSS` | 104,464,388 | 648,020 |
| 9 | `BONUS18.PSS` | 41,811,972 | 699,029 |
| 10 | `BONUS24.PSS` | 18,825,220 | 719,446 |
| 11 | `BONUS25.PSS` | 68,288,516 | 728,639 |
| 12 | `CREDITS1.VPK` | 5,285,888 | 761,984 |
| 13 | `R_SHELL.WAD` | 3,599,632 | 764,565 |
| 14 | `R_SAVEPT.WAD` | 475,488 | 766,323 |
| 15 | `TIT1E1_2.VPK` | 2,959,360 | 766,556 |

### Largest entries

| name | size | offset |
|------|-----:|-------:|
| `BONUS03.PSS` | 566,018,052 | 1,777 |
| `BONUS06.PSS` | 249,954,308 | 279,599 |
| `SEMO10.PSS` | 185,794,564 | 305,135 |
| `SEMO10.PSW` | 185,581,572 | 214,518 |
| `SEMO08.PSW` | 175,390,724 | 682,595 |
| `SEMO08.PSS` | 175,308,804 | 770,485 |
| `BONUS12.PSS` | 173,146,116 | 453,497 |
| `BONUS14.PSS` | 166,592,516 | 538,042 |
| `SEMO06.PSS` | 132,644,868 | 1,229,593 |
| `SEMO06.PSW` | 132,513,796 | 1,164,888 |
| `SEMO07.PSS` | 130,596,868 | 1,034,382 |
| `SEMO07.PSW` | 129,679,364 | 971,061 |

## 5. PART1.PAK

- ISO size: **4,257,794,048** @ LBA 1547
- Head sample: 8,388,608 bytes; `WAD_` marker @ head: **True**
- Sig counts in head sample: `{'STBLz': 0, 'STBL0': 0, 'DA_FA': 115, 'FA_DA': 136, 'IGB': 0, 'PNG': 0, 'MPEG_PS_pack': 290, 'VAG': 1, 'RIFF': 0}`
- TOC landings in head sample: **24**

| name | offset | size | head ascii |
|------|-------:|-----:|------------|
| `R_PERM.WAD` | 0 | 3,638,576 | `x.......WAD_R_Perm......` |
| `BONUS03.PSS` | 1,777 | 566,018,052 | `...0...MDLX_R_Perm......` |
| `TIT1E1_2.VPK` | 278,154 | 2,959,360 | `..............;....../..` |
| `BONUS06.PSS` | 279,599 | 249,954,308 | `.... ....2\.._K....|=...` |
| `BONUS10.PSS` | 401,648 | 106,184,708 | `.......;... ..A...;.....` |
| `BONUS12.PSS` | 453,497 | 173,146,116 | `0........2.%............` |
| `BONUS14.PSS` | 538,042 | 166,592,516 | `..?.....................` |
| `BONUS16.PSS` | 619,387 | 58,638,340 | `-..@..3Ao..#1...\\ 0....` |
| `BONUS17.PSS` | 648,020 | 104,464,388 | `..Q......>.././....."..-` |
| `BONUS18.PSS` | 699,029 | 41,811,972 | `.............A]%.... 2.4` |
| `BONUS24.PSS` | 719,446 | 18,825,220 | `..^...N..=>.............` |
| `BONUS25.PSS` | 728,639 | 68,288,516 | `...........#;.!........+` |
| `CREDITS1.VPK` | 761,984 | 5,285,888 | `/..... .?.../_.....N../.` |
| `R_SHELL.WAD` | 764,565 | 3,599,632 | `.?BO4.#E2..!N!....CQ.0..` |
| `R_SAVEPT.WAD` | 766,323 | 475,488 | `...B.........3./........` |
| `TIT1E1_2.VPK` | 766,556 | 2,959,360 | `..." .M..... ..0.....#N.` |
| `TIT1Q1_2.VPK` | 768,001 | 313,344 | `..Q....4!9.....2..S.....` |
| `OLY1E2_2.VPK` | 768,154 | 4,073,472 | `..#$;....... /.>....!../` |
| `EXTHOLLP.VPK` | 770,143 | 4,360,192 | `#./.......2!........... ` |
| `R_HERO0.WAD` | 772,272 | 1,966,896 | `...0......0...$ ...0..3.` |
| `R_HERO1.WAD` | 773,233 | 1,793,808 | `............d....Lt.....` |
| `R_HERO2.WAD` | 774,109 | 1,886,800 | `..../..........0........` |
| `R_HERO3.WAD` | 775,031 | 1,902,528 | `..E........@....B.,"....` |
| `R_HERO4.WAD` | 775,960 | 1,863,392 | `{..p.w.g.x.x...uxxx...|.` |

## 6. IOP modules

- `SIO2MAN.IRX` — 6,641 B @ LBA 1352
- `DBCMAN.IRX` — 15,653 B @ LBA 1356
- `SIO2D.IRX` — 11,289 B @ LBA 1364
- `MC2_S1.IRX` — 20,165 B @ LBA 1370
- `DS1O_S1.IRX` — 9,437 B @ LBA 1380
- `MC2_D.IRX` — 20,221 B @ LBA 1385
- `DS2U_D.IRX` — 11,725 B @ LBA 1395
- `LIBSD.IRX` — 28,573 B @ LBA 1401
- `989NOMID.IRX` — 178,884 B @ LBA 1415
- `SMPD_IOP.IRX` — 47,948 B @ LBA 1503

## 7. Verdict

God of War is **not** an Intrinsic Alchemy title. Packaging is 
**GODOFWAR.TOC → PART1.PAK** (WAD/VPK/PSS/VAG). Zero GFC/GOB/IGB/`ig*` class surface.
