# R5 pad / sound — SDK API surface inventory (STILL GATED)

**Track:** A — R5 pad/sound  
**Mode:** **inventory_only** — research / observe. **No patches. No disc-fix apply. No `allow_discfix_apply` flip.**  
**SDK tree (only):** `E:\usr\local\sce` — Runtime Library Release **3.0.3** (June 2005); `common\include\libver.h` → `SCE_LIBRARY_VERSION 0x3030`.  
**Date:** 2026-11-07  

---

## Explicit gate

| Rule | Status |
|------|--------|
| R5 behavioral / HLE rewrite | **STILL GATED** |
| Disc-fix board apply | **Do not apply** (`code_change: false` observe only) |
| `host_signal` leftover WaitSema IDs | **Forbidden** (esp. Hitman 7, NFS 17/23/29/30/32) |
| CdSync wake / CDVD complete-path edits | **Out of scope** (R1–R4 done) |
| This document | Inventory + gap map only |

Board context (observe, not apply): `discfix-matrix-board.json` step 8 `R5_pad_sound_observe`; ranked `R5_pad_sound` remains in `ranked_rewrites_gated`.

---

## 1. SDK assets present (canonical paths)

### 1.1 IOP modules (primary)

| Asset | Path | Size (bytes) |
|-------|------|-------------:|
| **padman.irx** | `E:\usr\local\sce\iop\modules\padman.irx` | 45925 |
| **libsd.irx** | `E:\usr\local\sce\iop\modules\libsd.irx` | 30085 |
| sio2man.irx | `E:\usr\local\sce\iop\modules\sio2man.irx` | 5217 |
| sdrdrv.irx | `E:\usr\local\sce\iop\modules\sdrdrv.irx` | 9161 |
| sio2d.irx | `E:\usr\local\sce\iop\modules\sio2d.irx` | 11289 |
| sdhd.irx / sdsq.irx | `iop\modules\` | (related sound stack) |

Duplicates under Demo Disc / SCEE_Tools / conftool exist; **canonical research copies are under `iop\modules\`.**

### 1.2 Headers

| Header | Path | Role |
|--------|------|------|
| **libpad.h** | `E:\usr\local\sce\ee\include\libpad.h` | EE controller API (padman client) |
| libpad2.h | `E:\usr\local\sce\ee\include\libpad2.h` | Alternate pad2 / DBC path (not Hitman/NFS primary) |
| **libsd.h** | `E:\usr\local\sce\iop\include\libsd.h` | IOP SPU2 device library API |
| **libsdr.h** | `E:\usr\local\sce\ee\include\libsdr.h` | EE remote front-end to IOP sound (RPC) |
| sdrcmd.h | `E:\usr\local\sce\common\include\sdrcmd.h` | `rSd*` SIF RPC command IDs |
| sdmacro.h | `E:\usr\local\sce\common\include\sdmacro.h` | Shared SD macros / batch types |

Also mirrored: `iop\install\include\libsd.h`, `iop\gcc\...\include\libsd.h` (same surface).

### 1.3 EE static / ERX libraries

| Lib | Path |
|-----|------|
| libpad.a / libpad.erx | `E:\usr\local\sce\ee\lib\` / `ee\modules\` |
| libpad2.a / libpad2.erx | same |
| libsdr.a / libsdr.erx | `ee\lib\libsdr.a`, `ee\modules\libsdr.erx` |
| libsd.ilb | `E:\usr\local\sce\iop\lib\libsd.ilb` (IOP import lib) |

### 1.4 PDF text extracts (already under recovery)

Sound / device extracts used for R5 when deep-read opens:

| Extract | Under `verification/recovery/_sdk_pdf_extract/` |
|---------|--------------------------------------------------|
| EE Overview Sound 3.0.2 | `PS2_EE-Overview-Sound-3.0.2.pdf.txt` |
| EE Reference Sound 3.0.1 | `PS2_EE-Reference-Sound-3.0.1.pdf.txt` |
| IOP Overview Sound 3.0.1 | `PS2_IOP-Overview-Sound-3.0.1.pdf.txt` |
| IOP Reference Sound 3.0.2 | `PS2_IOP-Reference-Sound-3.0.2.pdf.txt` |
| EE Overview Device 3.0.2 | `PS2_EE-Overview-Device-3.0.2.pdf.txt` (padman / libpad / sio2man load order) |
| EE Reference Device 3.0.3 | `PS2_EE-Reference-Device-3.0.3.pdf.txt` (`scePad*`) |
| IOP Device overview/ref | `PS2_IOP-Overview-Device-3.0.pdf.txt`, `PS2_IOP-Reference-Device-3.0.2.pdf.txt` |

Keyword pass already hit `padman` / `libsd` / `scePad` / `sceSd` (see `MASTER-CONTEXT.md` §B). Deep quote harvest for pad/sound still deferred.

---

## 2. API surface inventory

### 2.1 Stack topology (Sony)

```
EE game ──libpad──SIF RPC──► padman.irx ──► sio2man.irx ──► SIO2 HW
EE game ──libsdr──SIF RPC──► sdrdrv.irx ──► libsd.irx ──► SPU2 HW
                 (rSd* cmds in sdrcmd.h)
```

Guest titles (Hitman / NFS / CNK notes) typically **load real IRX from disc** (`SIO2MAN`, `PADMAN`, `LIBSD`, `SDRDRV`); host does **not** replace those module servers the way CDVD does.

### 2.2 EE `libpad` (`libpad.h`) — controller client

**Init / lifecycle**

- `scePadInit`, `scePadEnd`
- `scePadPortOpen`, `scePadPortClose`
- `scePadGetSlotMax`, `scePadSetWarningLevel`
- `scePadInitGun`, `scePadEndGun`
- `scePadGetErxEntries`

**Read / state**

- `scePadRead`
- `scePadGetState`, `scePadGetReqState`
- `scePadReqIntToStr`, `scePadStateIntToStr`

**Mode / actuators / pressure**

- `scePadInfoMode`, `scePadInfoAct`, `scePadInfoComb`
- `scePadSetMainMode`
- `scePadSetActDirect`, `scePadSetActAlign`
- `scePadInfoPressMode`, `scePadEnterPressMode`, `scePadExitPressMode`
- `scePadSetDmaCallback`, `scePadSetFlushRate`

**State constants (observe mapping):** `scePadStateDiscon` … `scePadStateStable` / `Error` / `Closed`; req states Complete / Failed / Busy.

**SDK load order (Device Overview extract):** `sio2man.irx` before `padman.irx`; padman may load before/after mcman/mcserv as long as after sio2man. Do not co-resident padman with pad2 module.

### 2.3 IOP `libsd` (`libsd.h`) — SPU2 device API

**Core param / switch / addr / attr**

- `sceSdInit`
- `sceSdSetParam` / `sceSdGetParam`
- `sceSdSetSwitch` / `sceSdGetSwitch`
- `sceSdSetAddr` / `sceSdGetAddr`
- `sceSdSetCoreAttr` / `sceSdGetCoreAttr`

**Pitch helpers**

- `sceSdNote2Pitch`, `sceSdPitch2Note`

**Batch**

- `sceSdProcBatch`, `sceSdProcBatchEx`

**Transfers**

- `sceSdVoiceTrans`, `sceSdVoiceTransStatus`
- `sceSdBlockTrans`, `sceSdBlockTransStatus`, `sceSdStopTrans`

**Effects**

- `sceSdSetEffectAttr` / `sceSdGetEffectAttr`
- `sceSdClearEffectWorkArea` / `sceSdCleanEffectWorkArea`
- `sceSdSetEffectMode` / `sceSdSetEffectModeParams`

**IRQ handlers**

- `sceSdSetSpu2IntrHandler`, `sceSdSetTransIntrHandler`
- `sceSdGetSpu2IntrHandlerArgument`, `sceSdGetTransIntrHandlerArgument`

IOP Reference Sound extract indexes the same surface (`sceSdBatch` … `sceSdBlockTransHandler`).

### 2.4 EE `libsdr` + `sdrcmd.h` — remote / RPC façade

**EE calls (`libsdr.h`)**

- `sceSdRemoteInit`, `sceSdRemote`
- `sceSdRemoteCallbackInit` / `Quit`
- `sceSdCallBack`
- `sceSdTransToIOP`
- `sceSdGetErxEntries`

**RPC command IDs (`sdrcmd.h`) — map 1:1 to libsd ops**

| Cmd | ID |
|-----|-----|
| rSdInit | 0x8000 |
| rSdSetParam / GetParam | 0x8010 / 0x8020 |
| rSdSetSwitch / GetSwitch | 0x8030 / 0x8040 |
| rSdSetAddr / GetAddr | 0x8050 / 0x8060 |
| rSdSetCoreAttr / GetCoreAttr | 0x8070 / 0x8080 |
| rSdNote2Pitch / Pitch2Note | 0x8090 / 0x80a0 |
| rSdProcBatch / ProcBatchEx | 0x80b0 / 0x80c0 |
| rSdVoiceTrans / BlockTrans | 0x80d0 / 0x80e0 |
| rSdVoiceTransStatus / BlockTransStatus | 0x80f0 / 0x8100 |
| rSdSetEffectAttr / GetEffectAttr | 0x8130 / 0x8140 |
| rSdClearEffectWorkArea | 0x8150 |
| rSdSetTransIntrHandler / SetSpu2IntrHandler | 0x8160 / 0x8170 |
| rSdStopTrans | 0x8180 |
| rSdCleanEffectWorkArea | 0x8190 |
| rSdSetEffectMode / ModeParams | 0x81a0 / 0x81b0 |
| rSdProcBatch2 / ProcBatchEx2 | 0x81c0 / 0x81d0 |
| rSdChangeThreadPriority | 0x8f10 |
| rSdUserCommand0…F | 0x9000…0x90f0 |

Plus `sceSdrSetUserCommandFunction` for user command slots.

### 2.5 Prior title evidence (observe classification targets — not proven pad/sound yet)

From `waitsema-createsema-trace-live-report.md` + board `R5_pad_sound_observe`:

| Game | Leftover WaitSema | Board hypothesis |
|------|-------------------|------------------|
| Hitman BM | **7** | callback / sound-ish (unproven) |
| NFS MW | **17, 23, 32** | pad-class factories (same create_ra) — unproven |
| NFS MW | **29, 30** | sound-class gates (30 max=253) — unproven |

**Sema 2** = libcdvd-class (R2 cleared) — **not** R5.  
**NFS SND RPC poll** already fixed generically (`docs/NFS_RPC_FIX.md`) — SIF `sceSifGetNextRequest` / `ExecRequest`; **not** a padman/libsd HLE module.

---

## 3. Runtime gap map (CyberArcade / `runtime/`)

### 3.1 What exists (hardware / host injection — not module HLE)

| Layer | Files | Notes |
|-------|-------|-------|
| **SIO2 MMIO + pad inject** | `runtime/src/iop/sio2.cpp`, `sio2.hpp` | Register window `0x1F808200`–`0x1F808280`; `set_buttons` / `set_axis` / `set_pressure` / rumble / cards |
| **Host pad plumbing** | `runtime/src/system.cpp` | Forwards UI → `iop::sio2::*` |
| **SPU2 MMIO** | `runtime/src/iop/spu2.cpp`, `spu2.hpp` | Device-level SPU2 HLE; voice dump / mute / levels |

### 3.2 Trace / observe env (existing)

| Env | Where | Purpose |
|-----|-------|---------|
| `PS2_TRACE_PAD` | `sio2.cpp` | Pad path trace |
| `PS2_TRACE_MC` | `sio2.cpp` | Memory-card path on SIO2 |
| `PS2_TRACE_SPU2` | `spu2.cpp` | SPU2 activity |
| `PS2_SPU2_COUNT` / `MUTE` / `LEVELS` | `spu2.cpp` | Count / mute / level observe |
| `PS2_DUMP_AUDIO` | `spu2.cpp` | Audio dump |
| `PS2_TRACE_SEMA` | EE kernel (prior WaitSema work) | Sema ownership for R5 classify |

### 3.3 What does **NOT** exist (gap vs CDVD)

Comparable CDVD pattern today:

- `register_hle_library("cdvdman", …)` + export table in `runtime/src/iop/cdvd.cpp`
- `install_cdvdfsv()` + multiple `sif::register_hle_server(0x8000059x)` in `cdvdfsv.cpp`
- Wired from `install_sif()` in `sif.cpp`

**Confirmed absent (grep / install path):**

| Expected Sony module / library | HLE `register_hle_library` / `register_hle_module` / dedicated SIF padman·libsd server |
|--------------------------------|----------------------------------------------------------------------------------------|
| **padman** | **None** |
| **libsd** | **None** |
| **sdrdrv** / libsdr RPC server | **None** (guest IRX + SPU2 MMIO only) |
| **sio2man** as HLE library | **None** (SIO2 is MMIO HLE only) |

`install_libraries()` / `install_sif()` register kernel, SIF, CDVD, and title IG* modules — **no padman/libsd twin**.

**Implication for R5:** fidelity work (when ungated) is **not** “swap in a CDVD-style complete HLE module set” by default; guest IRX already runs. Observe must classify parks against **guest padman/libsd + SIF RPC + SIO2/SPU2 MMIO**, not invent host_signal wakes for leftover semas.

---

## 4. Inventory conclusions

1. **SDK complete for R5 research** at `E:\usr\local\sce`: padman + libsd IRX, libpad / libsd / libsdr headers, sdrcmd RPC map, Sound + Device PDF extracts on disk.  
2. **API surface** is three-tier: EE libpad ↔ padman; EE libsdr (`rSd*`) ↔ sdrdrv ↔ IOP libsd ↔ SPU2.  
3. **Runtime** already has **SIO2 + SPU2 hardware HLE** and **pad/SPU2 trace env**; it does **not** have a **padman/libsd HLE module set comparable to CDVD**.  
4. Leftover WaitSema IDs remain **unclassified** as pad vs sound vs other — observe evidence only; **no apply**.  
5. **STILL GATED / do not apply** — this file does not unlock disc-fix R5; no patches landed with this inventory.

---

## 5. Next (still gated — parent must unlock)

When parent/matrix opens R5 beyond observe:

1. Classify Hitman 7 / NFS 17·23·29·30·32 with `PS2_TRACE_PAD` + `PS2_TRACE_SPU2` + SIF RPC tags vs create_ra modules.  
2. Quote-harvest Device/Sound PDF extracts against live call sites.  
3. Only then propose a **narrow** evidence-named change — never blind sema wake.

Until then: **inventory_only; gated:true.**
