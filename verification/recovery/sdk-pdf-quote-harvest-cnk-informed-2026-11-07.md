# SDK PDF quote harvest — CNK-informed round (AlignReadBuffer / sceCdSync / padman / libsd)

**Date:** 2026-11-07 (~05:59 local)  
**Mode:** RESEARCH ONLY. No disc-fix / R5 / CNK patches.  
**Corpus:** 14 extracts under `verification/recovery/_sdk_pdf_extract/` (Runtime Library 3.0.x).  
**Informed by:** `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` (CNK A1–A4).  
**Companion:** Round 1 `sdk-pdf-quote-harvest-r1r5.md` (still authoritative for full quote blocks).

---

## 0. Why CNK changes the reading of these PDFs

| CNK fact (A1–A4) | PDF theme relevance |
|------------------|---------------------|
| ISO `ASSETS.GFC`/`GOB` delivered via **CDVDFSV** under Alchemy FileIO | **sceCdRead / sceCdSync / 64-byte alignment / GetReadPos** apply to shared disc HLE — not Alchemy-specific APIs |
| `igFileIO.irx` **absent** from MODULES; name-HLE only | PDFs never mention Alchemy; they document **Sony** CD/SIF contracts the HLE must respect |
| Retail **PADMAN** + **SIO2MAN** load as real IRX | R5 observe targets; **not** Alchemy `igU*` stubs |
| Retail **LIBSD** / **SDRDRV** + CRI ADX (no `igAudio.irx`) | Sound PDFs = libsd/libsdr path; Alchemy kit is unrelated |
| Blocker = EE bind/loadgate/IGB | PDFs **cannot** unlock CNK UI; they only constrain shared CDVD/pad/sound HLE |

**Re-scan of all 14 texts:** `AlignReadBuffer`, `_CdAlign`, `b1len`, `b2len`, `readee`, `curReadPos` → **0 hits**.

---

## 1) AlignReadBuffer / readee / b1len / b2len / +16 / +80

### Verdict (unchanged, now CNK-scoped)

Official PDFs document **64-byte EE buffer alignment compensation** and **`sceCdGetReadPos`**. They do **not** name AlignReadBuffer / readee / b1len/b2len / +16/+80.  
For CNK: GFC/GOB/IGB bytes still cross the same EE `sceCdRead` completion path; unaligned head/tail staging in `cdvdfsv.cpp` remains an **HLE reconstruction**, not a manual excerpt.

### Quotes — compensation (verbatim)

**`cdvdtips_3.0.pdf.txt`**

> Be aware of 64-byte alignment when reading from the EE  
> If the address of a buffer is not 64-byte aligned, the sceCdRead() function will perform compensation  
> processing internally. An increase in speed can be obtained just by adjusting the buffer alignment properly  
> to avoid this processing.  
> To allocate a buffer area, use memalign(64, size), or __attribute__((aligned(64))) for static buffers.

**`PS2_EE-Reference-Device-3.0.3.pdf.txt` — `sceCdGetReadPos`**

> A value in 16-sector units (a multiple of 32768) is returned. Because of alignment adjustment, if the read  
> buffer is other than 64-byte aligned, care should be taken when performing the last transfer of the buffer  
> area which will not be 64-byte aligned (on either side of the read buffer).

### Official binary (not PDF) — closest symbols

`nm E:\usr\local\sce\ee\lib\libcdvd.a` (reconfirmed 2026-11-07):

| Symbol | Note |
|--------|------|
| `_sceCd_rd_intr_data` | EE lib BSS staging (community “readee”) |
| `_sceCd_Read_cur_pos` | Backing for `sceCdGetReadPos` |
| `sceCdGetReadPos` | Public API |

**No** `AlignReadBuffer` / `b1len` / `b2len` / `readee` symbol names.

### CNK note

Alchemy loadgate status (+76) and assemble scratch (`0xBD1000`) are **guest Alchemy**, not libcdvd AlignReadBuffer. Do not conflate PDF “either side of the read buffer” with loadgate slot fields.

---

## 2) sceCdSync / sceCdDiskReady

### Quotes — EE Sync modes

**`PS2_EE-Reference-Device-3.0.3.pdf.txt`**

> int sceCdSync (  
> int mode) 0x00: Wait for completion of command (blocking)  
> 0x01: Check current status and return immediately  
> (non-blocking).  
> …  
> Value Result  
> 0 Completed  
> 1 Not completed

### Quotes — DiskReady returns

**`PS2_EE-Reference-Device-3.0.3.pdf.txt`**

> 0x02 SCECdComplete  Drive state allows commands to be issued

> SCECdComplete is the drive state that allows commands to be issued, and SCECdNotReady is the state  
> …

### CNK note

CNK FileIO/CD plant path still depends on honest **finish_read / Sync** so IGB pages arrive before FCE0 finalize. Host always returning DiskReady=`2` remains an **observe flag** for titles that need NotReady — separate from Alchemy bind. Round 1 already has IOP Sync `0x10`/`0x11` EE-inclusive modes.

---

## 3) padman / scePad (R5 + CNK MODULES)

### Quotes — load order

**`PS2_EE-Overview-Device-3.0.2.pdf.txt`**

> Call sceSifLoadModule() to load sio2man.irx, then padman.irx.  
> …  
> Call scePadInit() to initialize the controller library.

> padman.irx can be loaded before or after mcman.irx or mcserv.irx as long as it is loaded after  
> sio2man.irx

> padman.irx, mcman.irx, and mcserv.irx use functions provided by mtapman.irx to communicate with  
> …

**`cdvdtips_3.0.pdf.txt`** (startup case study lists pad among disc-loaded IRX):

> Start-up processing that reads sio2man.irx, padman.irx, mcman.irx, mcserv.irx, and libsd.irx from the  
> disc

### CNK note (A4)

Observed load: `SIO2MAN` → `PADMAN` → `MTAPMAN` (after Alchemy FileIO HLE + USB probes). Matches SCE order (sio2man before padman). CNK `igUKbd`/`igUMouse` are **stubs**; pad path is **padman**, not Alchemy HID.

---

## 4) libsd / libsdr (R5 + CNK MODULES)

### Quotes — EE remote libsd

**`PS2_EE-Overview-Sound-3.0.2.pdf.txt`**

> libsdr is a low-level sound library that allows the EE to remotely control the SPU2, which is connected to  
> the IOP. The libsdr routines work together with the driver module on the IOP side and provide the EE with  
> features similar to the IOP low-level sound driver library libsd. Most of the processing takes place in the IOP

> The following files are required to use libsdr:  
> …  
> libsd.irx

### CNK note (A4)

CNK loads **LIBSD.IRX** (twice in smoke) + **SDRDRV** + **CRI_ADXI**. No Alchemy audio IRX. R5 sound observe = Sony libsd path (+ CRI separately); do not look to Alchemy 5.0 kit for SPU2 contracts.

---

## 5) Harvest outcome summary

| Theme | PDF prose? | Closest official | CNK coupling |
|-------|------------|------------------|--------------|
| AlignReadBuffer / b1len / +16/+80 | **Absent** | 64-byte compensation + `_sceCd_rd_intr_data` | Shared CDVD HLE only |
| sceCdSync modes | **Strong** | EE 0/1; IOP +0x10/0x11 | Asset delivery before loadgate |
| sceCdDiskReady | **Strong** | SCECdComplete=`2` | Observe always-2 flag |
| padman | **Strong** | sio2man→padman; scePadInit | Real MODULES IRX on CNK |
| libsd | **Strong** | libsd.irx + libsdr/sceSdRemote | Real MODULES; ≠ Alchemy |

**Still no Alchemy / Intrinsic / igFileIO / GFC strings** in the 14 SCE PDF extracts (reconfirmed).

**Next research (not this file):** optional Docs&Training PDFs / more tips beyond `cdvdtips` if AlignReadBuffer prose is ever sought; CNK bind/loadgate remains ELF+RAM work.
