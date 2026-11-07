# WORKER 3 — Alchemy 5.0 eval kit + ps2tek × CNK Alchemy xref

**Mode:** RESEARCH ONLY. No patches. `C:\usr\alchemy` read-only.  
**Date:** 2026-11-07  
**Game / binary:** Crash Nitro Kart `boot.elf` — `Intrinsic Alchemy v3.0 -0909 (Static/Release)`  
**Prior CNK reports used:**  
`cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`,  
`cnk-nullbind-51ACEC-live-report.md`, `cnk-nullbind-51ACEC-restart-report.md`

---

## 0. Kit / mirror inventory (what was actually read)

| Path | Role |
|------|------|
| `C:\usr\alchemy\Translated_copy_of_GettingStarted_djvu.txt` | OCR of Getting Started (preferred over PDF for search) |
| `C:\usr\alchemy\Translated_copy_of_UsersGuide_djvu.txt` | OCR of Users Guide |
| `C:\usr\alchemy\Alchemy_Docs.zip` → `GettingStarted.pdf`, `UsersGuide.pdf`, `AlchemyAPI.chm` | English 5.x eval docs + API CHM (CHM **string-scanned in memory** via zip; no unpack under `C:\usr\alchemy`) |
| `C:\usr\alchemy\AlchemyEvalKit\…\Alchemy50-BaseEvaluation-10-0529.exe` | Confirms **Alchemy 5.0** Base Evaluation installer (2010-05-29 naming) |
| `C:\usr\alchemy\ps2tek\PS2\**` | Mirrored israpps ps2tek HTML+MD |

**Not used as byte-truth for CNK:** Alchemy 5.0 runtime libs inside the eval EXE (not extracted). ArtistPack Maya 2.5 EXE is out of scope for EE bind/FileIO.

---

## 1. Alchemy 5.0 eval concepts that map to CNK 3.0 behavior

### 1.1 Version skew (flag first)

| Axis | Alchemy 5.0 eval kit | CNK (ELF) |
|------|----------------------|-----------|
| Product string | GettingStarted / UsersGuide dated **2010/04/06**; installer `Alchemy50-BaseEvaluation-10-0529` | **`Intrinsic Alchemy v3.0 -0909 (Static/Release)`** (Sep 9 2003) |
| Linkage | Docs emphasize Win32 DLL plugins + optional `IG_STATIC` / `*_arkRegister` | **Static/Release** baked into EE ELF; no DLL plugin loader at runtime |
| Install env | **`IG_ROOT`**, **`IG_ROOT_PS2` / `IG_ROOT_XXX`** | ELF tokens **`ALCHEMY_BASE`**, `$(AlchemyRoot)`, paths `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules` |
| Tooling stationery note | CW stationery copy path mentions **“Alchemy 3.5”** folder even in 5.0-era GettingStarted OCR | CNK compiler comment **`MW MIPS C Compiler (2.4.1.01)`** / PlayStation2 — aligns with **Psx2MW**, not 2010 toolchains |
| IGB tooling | “Fast IGB” = **target-optimized art pipeline output** (Exporter → Finalizer / optimizer.ini → Insight) | Runtime **`igIGBFile`**, loadgate slot paging, GFC/GOB packaging — **same family**, not byte-identical to 5.0 Fast IGB tool output |
| API surface (CHM) | Classes still named `igIGBFile`, `igFile`, `igFileScheduler`, `igFileContext`, `igPsx2IopRpcConnection`, `igPsx2VisualContext`, `igSceneInfo`, `igPluginHelper` | Same **name lineage** present as strings in CNK ELF; layouts / vt offsets **not proven** from 5.0 CHM |

**Rule of use:** 5.0 docs = **vocabulary + architecture**. CNK = **ELF disasm + live RAM**. Do not treat 5.0 Finalizer/Insight/Fast IGB as a drop-in for CNK loadgate/`0x110100`.

### 1.2 IGB / Fast IGB

**Kit (GettingStarted OCR):**  
Art pipeline end goal is a target-optimized **“Fast IGB”** — “IGB is the binary game data.” Exporter / Finalizer / optimizer.ini / Insight produce Fast IGB files. Scene samples hang off **`igSceneInfo`**.

**UsersGuide OCR:**  
Standard tool output IGB describes the scene database as **`igSceneInfo`**; loading IGB hands scene info to managers (`igViewerSceneInfoManager` in tool/viewer context). Introspection powers read/write and **incremental streaming**.

**CNK observed:**  
- Strings: `igIGBFile`, `igIGBFile::readFile…`, `igbUpdate…`, UI paths `*.igb`, pools.  
- Runtime assemble scratch historically `stream+0x48 → 0xBD1000`; loadgate status at slot `+0x4C`.  
- Disc pack: `ASSETS.GFC`/`ASSETS.GOB` (STBL/z) — **VV packaging around IGB**, not named in 5.0 GettingStarted OCR.

**Skew:** Fast IGB in 5.0 = **offline optimize product**. CNK “IGB parse finish” = **EE object bind + scene managers**, gated by bind registry / thread context — not documented as “loadgate” in the kit.

### 1.3 FileIO / streaming / IOP modules

**Kit:**  
- AlchemyCore: portable sync + **file system / CD-ROM / DVD** streaming with low-overhead direct I/O (GettingStarted feature overview).  
- PS2 **`iop/`** directory: modules for HW init (mouse, controller, audio).  
- **`alchemy.ini`** `[CORE]`:  
  - `sonyModulePath = c:/usr/local/sce/iop/modules`  
  - `intrinsicModulePath = c:/Alchemy/iop/modules`  
- CW sample may warn “Unable to Open File alchemy.ini”; docs say normal PS2 programs **need IOP** and alchemy.ini for module paths.  
- CHM retains **`igFile` / `igFileScheduler` / `igFileContext` / `igPsx2IopRpcConnection`**.  
- **Literal `FileIO` / `igFileIO`:** **0 hits** in GettingStarted/UsersGuide OCR and AlchemyAPI.chm string index.

**CNK observed:**  
- Module string **`igFileIO.irx`** (+ `igUKbd` / `igUMouse`); explore.log host fails ELF IRX load; host HLE path exists.  
- Class string **`igPsx2IopRpcConnection`**.  
- Loadgate pump `0x0010FCE0` + finalize `0x00110100` + CD/sema globals (`0x705F18` / `0x705C18` / `0x705C10`).

**Map:** Kit describes **Intrinsic IOP module directory + portable file/streaming services**. CNK’s **`igFileIO.irx` is the concrete 3.0 IOP helper** sitting on top of BIOS **FILEIO / CDVDFSV** (see §2). Kit docs do **not** document CNK loadgate slot layout.

### 1.4 Scene graph / plugins / registration

**Kit:**  
- Core + **scene graph** + multi-platform visual context + PS2 microcode.  
- Plugins: DLL on Win32; **static** builds call `myNewObjects_arkRegister` / `Gap::ArkCore->getPluginHelper()->loadAllPlugins("Alchemy")` (UsersGuide).  
- Managers register from **Info** objects in IGB; unregistering managers can disable features without code changes.  
- ODL / introspection: fields self-describe → serialization into IGB.

**CNK observed:**  
- ~670 `ig*` class-name strings; factory via `*0x725F00` vt+8; bind registry `*0x725F50`.  
- Null-bind path: registry **vt+80** = per-thread lookup by **GetThreadId** vs `entry+0x3C`; crash when lookup returns 0 then `*(0->vt+84)`.  
- Static/Release: registration is **compiled in**, matching kit’s static-plugin story, not Win32 DLL load.

**Map:** Kit “manager / plugin / arkRegister” ≈ CNK **factory + bind registry install (`0x520160`)**. Kit does **not** name BSS `0x725F50` or vt+80/+84.

### 1.5 `IG_ROOT` / env / CodeWarrior (Psx2MW)

**Kit:**  
- `IG_ROOT` = Base package install; `IG_ROOT_XXX` / **`IG_ROOT_PS2`** for target package.  
- Libs: `IG_ROOT\<platform>\lib` / `libdbg`; plugins under `%IG_ROOT%\plugins`.  
- Platform id: **PlayStation2 + Metrowerks CodeWarrior = Psx2MW** (also Psx2SN).  
- Create project: Alchemy stationery → **AlchemyApp**; copy `IG_ROOT\mwstationery` → CW Stationery (OCR still says **Alchemy 3.5** path).  
- Success string: “Welcome to Intrinsic Alchemy on CodeWarrior”.

**CNK observed:**  
- `ALCHEMY_BASE` / `AlchemyRoot` path tokens; `alchemy.ini`; MW 2.4.1.01; Velocity build names in embedded config.  
- No `IG_ROOT` string required at retail runtime (env was a **dev-kit** concern).

**Skew:** Env **name** differs (`IG_ROOT*` vs `ALCHEMY_BASE` / `AlchemyRoot`). Concept (install root → iop modules + libs) matches.

### 1.6 PS2 microcode / visual context

**Kit:** Alchemy VU0/VU1 microcode: on-demand load, geometry, async texture paging, visual context hierarchy.  
**CNK:** `igPsx2VisualContext` string; UI/gfx `ig*` attrs; prims stuck at 2 until IGB/UI path completes — render path exists but is **downstream** of FileIO/bind.

---

## 2. ps2tek pages that underpin Alchemy on PS2

Concrete pages (prefer `.md` mirrors under `C:\usr\alchemy\ps2tek\PS2\`):

| Subsystem | Page(s) | Why it matters for Alchemy / CNK |
|-----------|---------|----------------------------------|
| **Memory map** | `memory_maps.md`, `IO_Maps.md` | EE image VA `0x00100000+`, BSS bind globals `0x00725Fxx`, IOP RAM window `0x1C000000`, scratchpad — frames where CNK objects and SIF buffers live |
| **SIF RPC** | `SIF/RPC_Basics.md`, `SIF/RPC_Cmds.md`, `SIF/RPC_System_services.md`, `SIF/Structs_and_definitions.md` | EE↔IOP: `SifBindRpc` / `SifCallRpc`. BIOS **FILEIO** server `0x80000001`, heap via FILEIO `0x80000003`, **CDVDFSV** `0x80000592`…`0x8000059A`. Alchemy `igFileIO` / `igPsx2IopRpcConnection` are **clients** of this layer (plus custom RPC if registered) |
| **SIF DMA** | `SIF/DMA.md`, `SIF/Registers.md` | Payload move for RPC/file bytes; EE `SifSetDma` family used by loaders |
| **BIOS FILEIO** | (service documented in `RPC_System_services.md`; no separate FILEIO page) | Host “igFileIO.irx missing” still needs EE↔IOP file semantics HLE’d against FILEIO/CDVD behavior |
| **BIOS CDVDFSV** | `RPC_System_services.md` + `IOP/CDVD/Seek_and_Read.md`, `NCMD.md`, `SCMD.md`, `IO_Ports.md` | Disc reads behind GOB/IGB streaming / loadgate CD-done status |
| **THREADMAN-class EE threads** | `BIOS/EE_Threading.md`, `BIOS/EE_Syscalls.md` (`CreateThread` `0x20`, **`GetThreadId` `0x2F`**, …) | Null-bind: registry vt+80 keys off **GetThreadId**; host `host_call` / wrong `g_current` → empty lookup |
| **THSEMAP-class EE semas** | `EE_Threading.md` (SemaParam), `EE_Syscalls.md` (`CreateSema` `0x40` … **`WaitSema` `0x44`**) | CNK TIM0/FINISH waits (`0x705F18`≈16, `0x705C18`≈45, `0x705C10`≈47); soft-arm +45; explore.log waits |
| **IOP module load** | `BIOS/IOP_Module_linking.md`, `BIOS/IOP_REBOOT.md`, `BIOS/BootProcess.md` | How `igFileIO.irx` would link exports/imports if present; CNK also loads `IOPRP255.IMG` + MODULES |
| **DMAC** | `DMAC/README.md`, `IO.md`, `Chain_mode.md`, `Interrupts.md` | EE DMA to GIF/VIF/SIF/CD paths used under Alchemy visual + file pumps |
| **VU / GIF** | `VU/README.md` (+ Architecture…), `GIF/README.md`, `GIFtags.md`, `PATH3_Masking.md` | Alchemy PS2 microcode → VU; draw submission → GIF PATH1/2/3 — after IGB bind succeeds |

**Note:** ps2tek documents **Sony BIOS services**, not Intrinsic class names. Connection is: Alchemy FileIO/RPC wrappers **call into** FILEIO/CDVDFSV/SIF; Alchemy threads/semas **are** EE THREADMAN/THSEMAP syscalls.

---

## 3. Mapping table — CNK observed → Alchemy 5 doc → ps2tek

| # | CNK observed behavior / VA | Alchemy 5.0 eval concept (or **GAP**) | ps2tek page |
|---|----------------------------|----------------------------------------|-------------|
| 1 | Version string `Intrinsic Alchemy v3.0 -0909 (Static/Release)` @ ~`0x6B4920` | Kit is **5.0** eval (2010 docs / `Alchemy50-BaseEvaluation…`). **SKEW** — concept docs only | — (product identity) |
| 2 | `igIGBFile` / IGB UI assets / `readFile` errors | IGB + **Fast IGB** art pipeline; `igSceneInfo` in UsersGuide; CHM `igIGBFile` | CDVD seek/read for delivery; GIF/VU after parse |
| 3 | Loadgate `0x0010FCE0`, finalize `0x00110100`, 250×96 slots, `+0x4C` status, `+24008` busy | Kit: streaming / file I/O / incremental IGB — **GAP:** no “loadgate” API or slot layout in OCR/CHM index | `IOP/CDVD/Seek_and_Read.md`; SIF RPC FILEIO/CDVDFSV |
| 4 | Assemble scratch runtime `0xBD1000` (stream+0x48) | Kit: direct I/O into memory / streaming buffers — **GAP:** no fixed VA | `memory_maps.md` (EE RAM) |
| 5 | Bind registry BSS `*0x00725F50`; install `0x520160`; teardown clears | Plugin/manager **registration** / static `*_arkRegister` / `igPluginHelper` — **GAP:** no BSS address | `EE_Threading.md` (object lives in EE user RAM) |
| 6 | Null-bind `0x51AC80`…`ra=0x51ACEC`: vt+80 lookup → vt+84 on result; **v0==0** if tid missing | Kit: multithreaded Core + registered managers — **GAP:** no per-thread bind map docs | `EE_Syscalls.md` **`GetThreadId` `0x2F`**; `EE_Threading.md` |
| 7 | Registry list match `entry+0x3C` ↔ tid (live RAM) | **GAP** in 5.0 GettingStarted/UsersGuide OCR | EE threading / current thread identity |
| 8 | Factory `0x508930` via `*0x725F00` vt+8; memory pools | AlchemyCore **memory pools** / object model (GettingStarted) | `memory_maps.md` |
| 9 | `igFileIO.irx` string + module search paths | `intrinsicModulePath` / `iop/` modules + portable file services — **GAP:** name `igFileIO` absent from OCR/CHM | `RPC_Basics.md`, `RPC_System_services.md` (FILEIO `80000001h`); `IOP_Module_linking.md` |
| 10 | `igPsx2IopRpcConnection` | CHM class present; GettingStarted IOP path narrative — **GAP:** RPC ID table not in kit OCR | `SIF/RPC_Basics.md`, `RPC_Cmds.md`, `SIF/DMA.md` |
| 11 | Host fails `IGFILEIO.IRX` as ELF; HLE compensates | Kit assumes Intrinsic IOP modules available from install tree | FILEIO/CDVDFSV services still required semantically |
| 12 | Sema globals `0x705F18` / `0x705C18` / `0x705C10` (ids ~16/45/47); WaitSema parks | Core **synchronization primitives** (portable) | `EE_Syscalls.md` CreateSema/`WaitSema`; `EE_Threading.md` SemaParam |
| 13 | Soft-arm +45 / forced FCE0 interplay | **GAP** (host research technique, not Alchemy API) | Sema + thread pages above |
| 14 | `alchemy.ini`, `ALCHEMY_BASE`, `AlchemyRoot` | **`IG_ROOT` / `IG_ROOT_PS2`**, alchemy.ini `[CORE]` module paths — **SKEW** env names | `BootProcess.md`, `IOP_Module_linking.md` |
| 15 | MW MIPS 2.4.1.01 / PlayStation2 | **Psx2MW** + AlchemyApp stationery; OCR “Alchemy 3.5” stationery path **SKEW** vs 5.0 package year | `EE/EE_Architecture.md` (context) |
| 16 | `igPsx2VisualContext` + gfx `ig*` attrs; prims=2 until UI parse | Visual context + scene graph traverse/draw; PS2 **microcode** | `VU/*`, `GIF/*`, `DMAC/*` |
| 17 | `ASSETS.GFC` / `ASSETS.GOB` / STBL | **GAP** in Alchemy 5.0 GettingStarted/UsersGuide (VV archive, not Core IGB) | CDVD NCMD/SCMD + Seek_and_Read |
| 18 | Studio name **Velocity** / `Velocity.igm` | **GAP** in eval kit OCR (VV packaging) | — |
| 19 | CRT0 entry `0x00108D28`; SetupThread/`SetupHeap` | Not Alchemy-specific; SCE/MW CRT | `EE_Syscalls.md` `0x3C`/`0x3D`; `BootProcess.md` |
| 20 | Static/Release (no DLL plugins on EE) | UsersGuide: static plugin packages still `arkRegister` | — |

**Counts:** 20 mapping rows. **GAP** (or major skew) rows: **3, 4, 5(partial), 7, 9(name), 13, 17, 18** → treat as research gaps, not kit-proven APIs.

---

## 4. How the three layers connect (loadgate / FileIO / null-bind)

```
[Disc] ASSETS.GOB frames / .igb
        │  ps2tek: CDVDFSV + CDVD Seek_and_Read
        ▼
[IOP]  FILEIO / CDVDFSV  (+ optional igFileIO.irx custom RPC)
        │  ps2tek: SIF RPC_Basics / RPC_System_services / SIF DMA
        ▼
[EE Alchemy File / stream objects]  igFile* / igPsx2IopRpcConnection
        │  kit: Core file+streaming; alchemy.ini intrinsicModulePath
        ▼
[Loadgate] 0x10FCE0 → status/slots → 0x110100 finalize     ★ kit GAP (mechanism)
        │
        ▼
[Bind registry *0x725F50]  vt+80(GetThreadId) → per-thread ctx → vt+84
        │  kit: manager/plugin registration (concept only)
        │  ps2tek: GetThreadId / EE threads  ★ null-bind root
        ▼
[IGB object graph / igSceneInfo family] → visual context → VU microcode → GIF
        kit: scene graph + Fast IGB vocabulary; ps2tek: VU/GIF/DMAC
```

**Operational takeaway (research, not a patch plan):**  
Finishing CNK UI/IGB is not “apply Alchemy 5 Fast IGB.” It is: keep FileIO/CD path semantically alive, let **guest** install bind registry entries for the **thread that runs FCE0**, then allow loadgate finalize — matching null-bind live report (`v0==0` when tid ∉ map).

---

## 5. Gaps summary (explicit)

1. **No Alchemy 3.0 PS2 SDK** in local kit — only **5.0 eval** docs/CHM/installer.  
2. **`igFileIO.irx` / loadgate / `0x725F50` / vt+80 tid map** are **CNK-ELF/RAM facts**, not described in GettingStarted/UsersGuide OCR.  
3. **Fast IGB** ≠ CNK runtime loadgate parser.  
4. **GFC/GOB/STBL** and **Velocity** absent from eval OCR.  
5. Env token **`IG_ROOT*` vs `ALCHEMY_BASE`/`AlchemyRoot`** naming skew.  
6. CHM proves **class-name continuity** (`igIGBFile`, `igPsx2IopRpcConnection`, …) but not **vtable layouts** for CNK 3.0.  
7. ps2tek has **no Alchemy pages** — platform substrate only.

---

## 6. Kit docs used / ps2tek pages cited (machine list)

**kit_docs_used:**  
- `Translated_copy_of_GettingStarted_djvu.txt`  
- `Translated_copy_of_UsersGuide_djvu.txt`  
- `Alchemy_Docs.zip` / `AlchemyAPI.chm` (in-memory strings)  
- `Alchemy_Docs.zip` / GettingStarted.pdf + UsersGuide.pdf (presence / pairing)  
- `AlchemyEvalKit/.../Alchemy50-BaseEvaluation-10-0529.exe` (version marker)  
- Prior: `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `cnk-nullbind-51ACEC-live-report.md`, `cnk-nullbind-51ACEC-restart-report.md`

**ps2tek_pages_cited:**  
`PS2/memory_maps.md`, `PS2/IO_Maps.md`,  
`PS2/SIF/RPC_Basics.md`, `RPC_Cmds.md`, `RPC_System_services.md`, `DMA.md`, `Registers.md`,  
`PS2/BIOS/EE_Threading.md`, `EE_Syscalls.md`, `BootProcess.md`, `IOP_Module_linking.md`, `IOP_REBOOT.md`,  
`PS2/IOP/CDVD/Seek_and_Read.md`, `NCMD.md`, `SCMD.md`, `IO_Ports.md`,  
`PS2/DMAC/README.md` (+ IO/Chain_mode/Interrupts),  
`PS2/VU/README.md`, `PS2/GIF/README.md` (+ GIFtags/PATH3_Masking)

---

*End of WORKER 3 research report. No code or `C:\usr\alchemy` modifications.*
