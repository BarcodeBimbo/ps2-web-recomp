# CNK Alchemy rebuild — combined picture (A1–A4)

**Mode:** RESEARCH ONLY. No disc-fix / R5 / CNK patches.  
**Date:** 2026-11-07  
**Game:** Crash Nitro Kart — id `b49f2e769315347e8bda839feb705744`  
**Sources:**  
`alchemy-rebuild-w1-cnk-elf-walk-2026-11-07.md`,  
`alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md`,  
`alchemy-rebuild-w3-kit-ps2tek-xref-2026-11-07.md`,  
`alchemy-rebuild-w4-iop-ee-inventory-2026-11-07.md`  
(+ prior `cnk-elf-alchemy-full-redo-report.md`, null-bind live notes)

---

## One-line picture

CNK ships **Intrinsic Alchemy v3.0 -0909 (Static/Release)** baked into a **stripped** EE `boot.elf`. Scene/UI bytes live in ISO **`ASSETS.GFC`→`ASSETS.GOB`** (STBL pages → **IGB**). Alchemy IOP helpers (`igFileIO` / `igU*`) are **named in the ELF but absent from retail MODULES** and are **name-HLE’d**. The remaining stall is **EE bind registry + loadgate finalize + IGB object graph**, not missing Sony CreateSema / padman / libsd.

---

## 1. Imports / symbols (A1)

| Fact | Detail |
|------|--------|
| EE image | `games/…/disc/boot.elf` = SLUS_206.49 (no separate `SLUS_206.49` file) |
| Linkage | **Stripped** — empty `.symtab`/`.strtab`; **no** dyn imports / useful relocs |
| “Imports” in practice | Absolute `jal`/`j` + `lui`/`lw`/`sw` patterns only |
| Version | `Intrinsic Alchemy  v3.0 -0909 (Static/Release)` @ `0x006B4920` (built Tue Sep 9 2003) |
| `ig*` density | ~**595** whole-string class names; ~**717** unique tokens; prior redo ~673 (same ballpark) |
| Asset literals in ELF | **47** `.igb` path strings; **0** `ASSETS.GFC`/`GOB`/`STBL*` strings |

---

## 2. Vtables / bind / loadgate (A1 + prior ELF redo + A3)

| Mechanism | VA / layout | Role |
|-----------|-------------|------|
| Factory | `0x00508930` via `*0x00725F00` **vt+8** (209 `jal`s) | Alloc Alchemy objects |
| Bind registry | BSS `*0x00725F50` | Per-thread manager map |
| Install / clear | `0x00520160` / `0x00520210` | `sw` / `sw zero` into `0x725F50` |
| Null-bind path | `0x0051AC80`…`ra=0x0051ACEC` | Registry **vt+80** (tid lookup) → result **vt+84**; null → `missing code @0` |
| Loadgate pump | `0x0010FCE0` (“FCE0”) | 250 slots × stride **96**; slot+48 state, +76 status, gate+24008 busy |
| Finalize | `0x00110100` | Called from FCE0 when slot ready |
| Live note | Registry vt slots can be non-null | Crash often = **tid not in map** (`v0==0`), not stuffed zero methods |

**Kit gap (A3):** Alchemy 5.0 eval docs give vocabulary (IGB, plugins, `igPsx2*`) but **do not** document loadgate slots, `0x725F50`, or vt+80 tid maps. Treat kit as concepts only vs CNK 3.0 static.

---

## 3. TOC structures (A2)

```
ISO ASSETS.GFC (LBA 1518969, 222968 B)
  magic BE 0x00008008 | gob_size | nblocks=4327 | nfiles=1830
  block table (12×4327) + Adler + file table (12×1830) + names (72×1830)
        │
        ▼
ISO ASSETS.GOB (LBA 1519078, ~84.7 MiB)
  STBLz (4040) / STBL0 (289) / ENBL (4327) — ~64 KiB Alchemy pages
        │
        ▼
IGB body: @+0x28 DA FA | @+0x2C 0x80000005 | later ig* meta strings
```

| Census | Count |
|--------|------:|
| Files in GFC | 1830 |
| `.igb` | **520** |
| `.vag` / `.csv` | 541 / 519 |

ELF path strings (`gfx/ui/butanim.igb`, `ui/introtxr.igb`, …) resolve to GFC CRC entries. **Bind/loadgate VAs are not in the TOC** — EE-only.

---

## 4. IOP modules (A2 + A4)

### Alchemy-branded (ELF only)

| Module | On ISO MODULES? | Host |
|--------|-----------------|------|
| `igFileIO.irx` | **No** | HLE RPC **`0x12114`** (GFC/GOB + FileIO methods) |
| `igUKbd.irx` / `igUMouse.irx` | **No** | Stub HLE `0x12113` / `0x12112` |

Search paths in ELF: `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules`, `$(AlchemyRoot)`.

### Retail MODULES (real IOP ELFs)

Loaded: LIBSD, USBD, LGDEVW, CRI_ADXI, SIO2MAN, **PADMAN**, MTAPMAN, MCMAN, MCSERV, SDRDRV, VVAA.  
Unused on disc: SMAP.  
IOPRP255 supplies FILEIO / LOADFILE / CDVD / SIF / thread-sema kernel stack.

**Audio:** no `igAudio*.irx` — Sony **libsd**/sdrdrv + **CRI ADX**.

---

## 5. EE syscalls / patterns (A4 + ps2tek via A3)

| Theme | Syscalls / services | CNK use |
|-------|---------------------|---------|
| Sema pump | CreateSema `0x40`, WaitSema `0x44`, iSignalSema `0x43`, … | Park on **2 / 16 / 45 / 47** family; BSS `0x705F18` / `0x705C18` / `0x705C10` |
| Threads | Create/Start/ChangePriority; **GetThreadId `0x2F`** | Bind registry keyed by tid |
| SIF | SifSetDma/DChain/Reg `0x77`–`0x7A` | LoadModule + igFileIO RPC |
| CRT0 | SetupThread `0x3C`, SetupHeap `0x3D` | Entry `0x00108D28` |
| CD path | CDVDFSV RPC `0x80000592`… | Deliver GFC/GOB/IGB bytes under FileIO |

**Blocker (A4):** EE bind/loadgate/IGB completion — **not** “missing CreateSema.” Sony FILEIO/CDVD/sema/thread needed to *host* Alchemy are already HLE’d; Alchemy IRX is name-HLE only.

---

## 6. Layer diagram

```
[Disc TOC] GFC → GOB STBL → IGB (DA FA / ig* meta)     ← A2
     │  CDVDFSV / FILEIO (Sony)                          ← A3/A4 + SCE PDFs
     ▼
[IOP] igFileIO HLE 0x12114 (no retail IRX) + real pad/libsd IRX
     │  SIF RPC / DMA                                    ← A4
     ▼
[EE Alchemy] igFile / igIGBFile / igPsx2IopRpcConnection  ← A1
     │
     ▼
[Loadgate] 0x10FCE0 → 0x110100                            ← A1 (kit GAP)
     │
     ▼
[Bind *0x725F50] vt+80(tid) → vt+84                       ← A1/A3
     │
     ▼
[Scene / UI graph] → igPsx2VisualContext → VU/GIF         ← after bind
```

---

## 7. Implications for Hitman/NFS / SDK audit (quarantine)

- CNK Alchemy pulses (virt LBA, soft-arm, FCE0 force, host_signal 16/54/55) stay **quarantined** from Hitman/NFS disc-fix.
- CNK **does** use shared Sony CDVD completion for asset delivery — so **AlignReadBuffer / sceCdSync / DiskReady** PDF harvest still informs **shared** `cdvdfsv` HLE correctness, without applying CNK-only hacks.
- CNK **padman** / **libsd** are **retail MODULES IRX**, same family as R5 observe targets — Alchemy is **not** a substitute pad/sound stack.

---

## 8. Artifacts index

| Worker | Report |
|--------|--------|
| A1 | `alchemy-rebuild-w1-cnk-elf-walk-2026-11-07.md` |
| A2 | `alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md` (+ JSON / samples) |
| A3 | `alchemy-rebuild-w3-kit-ps2tek-xref-2026-11-07.md` |
| A4 | `alchemy-rebuild-w4-iop-ee-inventory-2026-11-07.md` |
| This synthesis | `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` |
