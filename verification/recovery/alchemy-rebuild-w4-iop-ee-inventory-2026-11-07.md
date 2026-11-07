# Worker 4 — CNK Alchemy IOP / EE inventory

**Mode:** RESEARCH ONLY. No disc-fix / R5 / CNK patches. Runtime read as observe-only.  
**Date:** 2026-11-07  
**Game id:** `b49f2e769315347e8bda839feb705744`  
**Sources:** `games/…/disc.iso` MODULES, `disc/boot.elf` strings, `verification/recovery/cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `logs/games/…/{smoke,explore,trace_sys}.log`, `runtime/src/iop/{sif,igfileio,cdvd,kernel}.cpp` + `runtime/src/kernel.cpp` (read-only), `C:\usr\alchemy\ps2tek\PS2\BIOS\EE_Syscalls.md` (+ Threading / IOP linking).

---

## 1. IOP modules CNK loads

### 1.1 Alchemy-branded / Alchemy-adjacent (`ig*`)

| Module (ELF string) | On retail `MODULES\`? | Runtime LoadModule path | Host fate |
|---------------------|------------------------|-------------------------|-----------|
| **`igFileIO.irx`** | **No** | `cdrom0:\MODULES\IGFILEIO.IRX;1` | Disc read empty → `[iop] cannot read module` → **`register_hle_module("IGFILEIO")`** → RPC **`0x12114`**, GFC/GOB HLE (`igfileio.cpp`). Module list shows base `0`. |
| **`igUMouse.irx`** | **No** | `…\IGUMOUSE.IRX;1` | Same empty-read → **HLE stub** RPC **`0x12112`** (ack zeros). |
| **`igUKbd.irx`** | **No** | `…\IGUKBD.IRX;1` | Same → **HLE stub** RPC **`0x12113`**. |

**ELF path / identity strings (not on disc):**

- `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules`, `$(AlchemyRoot)`
- `Intrinsic Alchemy  v3.0 -0909 (Static/Release)`, `alchemy.ini`, `ALCHEMY_BASE`
- EE class `igPsx2IopRpcConnection` (RPC binder for the above IOP helpers)
- `igFile` / `igIGBFile` (EE-side file/IGB types; not IRX names)

**Not loaded as IRX:** `igAudio` appears as a **class/string** hit in the ELF; there is **no** `igAudio*.irx` in the ELF `.irx` set or on disc MODULES. Audio on CNK goes through Sony `libsd` / `sdrdrv` + CRI `cri_adxi`.

**Older explore.log:** before HLE registration, ig\* loads retried ~10× with `is not an ELF module`. **smoke.log (current):** one fail-to-read then immediate HLE online — no retry storm.

### 1.2 Disc `MODULES\` IRX inventory (ISO path table)

Present on ISO (12 IRX):

| File | Size | Loaded in smoke/explore? |
|------|------|---------------------------|
| `CRI_ADXI.IRX` | 110760 | yes |
| `LGDEVW.IRX` | 45221 | yes |
| `LIBSD.IRX` | 28573 | yes (twice) |
| `MCMAN.IRX` | 95517 | yes |
| `MCSERV.IRX` | 7417 | yes |
| `MTAPMAN.IRX` | 11013 | yes |
| `PADMAN.IRX` | 44917 | yes |
| `SDRDRV.IRX` | 8089 | yes |
| `SIO2MAN.IRX` | 6553 | yes |
| `SMAP.IRX` | 17105 | **no** (on disc, unused in observed boot) |
| `USBD.IRX` | 34969 | yes (×3 around USB mouse/kbd probes) |
| `VVAA.IRX` | 22272 | yes |

ELF also names `lgDev.irx` / `lgdev.irx` (case variants); runtime loads **`LGDEVW.IRX`** only.

### 1.3 Generic Sony / IOPRP (not Alchemy `ig*`)

These are **not** Alchemy-branded. They come from **`cdrom0:\IOPRP255.IMG;1`** reboot or SCE MODULES IRX above.

| Family | How CNK gets it | Notes |
|--------|-----------------|-------|
| **FILEIO** | Inside IOPRP255 | smoke: `FILEIO … reports 2550, asynchronous protocol`; EE uses SIF FILEIO server `0x80000001` (open `LEGENG.TGA`, etc.). |
| **LOADFILE** | Inside IOPRP255 | SIF server `0x80000006`; all `MODULES\*.IRX` loads go through this. |
| **CDVD\*** (`cdvdman` / `cdvdfsv`) | IOPRP + host HLE | EE CD search/read for `POOLS.CSV`, `ASSETS.GFC`/`GOB`, UI IGBs via `cdvdfsv` HLE (`0x80000592`…`0x8000059C`). |
| **SIF\*** | IOPRP / kernel | EE syscalls `SifSetDma`/`SifSetDChain`/`SifSetReg`/`SifGetReg` + RPC bind/call. |
| **THREADMAN / THSEMAP** | IOP kernel image | No separate `.irx` string in ELF; EE uses kernel sema/thread **syscalls** (below). |
| **SIO2MAN / PADMAN / MTAPMAN** | MODULES IRX | Pad path. |
| **MCMAN / MCSERV** | MODULES IRX | Memory card. |
| **LIBSD / SDRDRV** | MODULES IRX | SPU2 / SDR. |
| **USBD** | MODULES IRX | USB base for Alchemy mouse/kbd probes. |

**Observed load order (smoke.log):**  
`LIBSD` → **`IGFILEIO` (HLE)** → `USBD` → `LGDEVW` → `CRI_ADXI` → `USBD` → **`IGUMOUSE` (stub)** → `USBD` → **`IGUKBD` (stub)** → `SIO2MAN` → `PADMAN` → `MTAPMAN` → `MCMAN` → `MCSERV` → `LIBSD` → `SDRDRV` → `VVAA`.

---

## 2. EE syscalls / patterns that matter for Alchemy FileIO / bind / loadgate

Syscall numbering matches **ps2tek `EE_Syscalls.md`** and this tree’s `kernel.cpp` HLE (v1 in `$v1`).

### 2.1 Themes (Alchemy-critical)

| Theme | Syscalls / path | CNK evidence |
|-------|-----------------|--------------|
| **Semaphore pump** | `CreateSema` **0x40**, `DeleteSema` **0x41**, `SignalSema` **0x42**, **`iSignalSema` 0x43**, **`WaitSema` 0x44**, `PollSema` 0x45 | `trace_sys.txt`: WaitSema ~12.6k, SignalSema ~12.6k, CreateSema 73, iSignalSema 44. End-state park: semas **2 / 45 / 47** (smoke) or **2 / 43 / 45** (explore). |
| **Alchemy timer / FINISH delay** | WaitSema on IDs stored at BSS **`0x00705F18`** (often **16**, TIM0 lock), **`0x00705C18`** (often **45**), **`0x00705C10`** (often **47**) | ELF redo report §5; `igfileio.cpp` pulses 16/54/55 while loadgate+24008 set; DisableIntc TIM0/TIM1 (`0x15`/`0x1B`) before FINISH WaitSema. `trace_sys` WaitSema top IDs include **16** heavily. |
| **Threads** | `CreateThread` **0x20**, `StartThread` **0x22**, `ChangeThreadPriority` **0x29**, `GetThreadId` **0x2F**, Exit* | CRT0 + Alchemy worker threads; GetThreadId/ChangeThreadPriority dominate raw counts; Create/Start rare in short smoke traces. Parked threads wait type=2 (sema). |
| **SIF RPC / DMA (LoadModule + igFileIO)** | `SifSetDma` **0x77**, `SifSetDChain` **0x78**, `SifSetReg` **0x79**, `SifGetReg` **0x7A**, `SifDmaStat` **0x76** | LoadModule is **not** an EE syscall — it is **SIF LOADFILE** RPC. igFileIO bind uses EE↔IOP DMA then CallRpc to **0x12114**. |
| **CRT0 bring-up** | `SetupThread` **0x3C**, `SetupHeap` **0x3D** | Entry `0x00108D28` (ELF redo §3). |
| **INTC / GS for Alchemy pumps** | Add/Enable/Disable Intc/Dmac; `GsGetIMR`/`GsPutIMR` | Host re-arms TIM0 / unmasks GS FINISH while `alchemy_asset_pending()`. |
| **SetSyscall** | **0x74** | Common stub install; not Alchemy-specific but present. |

### 2.2 ELF string honesty

ELF has **no** literal strings `CreateSema` / `WaitSema` / `LoadModule` / `FILEIO` / `cdvdman` / `threadman` — those APIs are reached via **syscall stubs** / **SIF RPC**, not printable names. Alchemy IRX names **are** printable (`igFileIO.irx`, etc.).

### 2.3 Bind / loadgate (EE code, not syscalls)

Documented in `cnk-elf-alchemy-full-redo-report.md` (cross-check only):

- Loadgate object / `0x0010FCE0` (250×96 slots; +48 state, +76 status, +24008 busy)
- Bind registry BSS **`0x00725F50`** → vt+80 / vt+84 (null-bind `ra=0x51ACEC`)
- FileIO ctx base from igFileIO **method 19**: **`0x7430C0`** (smoke: `[igfileio] init ctx=0x7430C0`) — **not** scene igctx

Syscall layer’s job for this path: keep **WaitSema/iSignalSema** and **SIF RPC completions** honest so guest Alchemy code can advance; forging FCE0 without binder init is an EE-logic failure, not a missing syscall number.

---

## 3. HLE’d in this project vs observe-only gaps

### 3.1 IOP / SIF — HLE present

| Component | Status |
|-----------|--------|
| **IOPRP FILEIO + LOADFILE** version parse + servers | HLE (`sif.cpp`) |
| **CDVDFSV** search/read / UI-IGB plant | HLE (`cdvdfsv.cpp`), cooperates with igfileio |
| **IGFILEIO** (absent IRX) | **Substantial HLE**: RPC `0x12114`; methods **19** (init ack), **0/2** open, **1** close, **3/4** read, **5** seek, **6** size; GFC/GOB index + host extract; STBL repair; loadgate sema/TIM0/FINISH pumps; optional host_call walker/bind experiments |
| **IGUMOUSE / IGUKBD** | **Stub HLE only** (RPC return 0) — enough that LoadModule “succeeds” |
| **Real MODULES IRX** (SIO2MAN, PADMAN, LIBSD, …) | Loaded as guest IOP ELF (not replaced by HLE), except ig\* |

### 3.2 EE kernel syscalls — HLE present

Sema / thread / SIF DMA / SetupThread/Heap / Intc/Dmac used by CNK Alchemy path are **implemented** in `kernel.cpp` (not observe-only). Short `trace_sys` smoke showed **0** `[sys] unhandled` lines for the exercised set.

### 3.3 Gaps / soft or observe-only (esp. igFileIO)

| Gap | Kind | Detail |
|-----|------|--------|
| **No retail `igFileIO.irx` bytes** | Structural | MODULES has no Alchemy IRX; host never runs Intrinsic’s IOP binary — only name-match HLE. |
| **igFileIO unknown RPC methods** | Soft HLE | Non-handled methods **zero-ack** so CallRpc does not hang WaitSema — behavior may diverge from real IRX. |
| **igFileIO ≠ full Alchemy FileIO+bind** | Observe / partial host | Method 19 deliberately does **not** seed ctx; bind registry / FCE0 / vt+84 still guest-driven. Overnight notes: wrong ctx seeding → jalr-null. End smoke: threads still **WaitSema(2/45/47)**. |
| **STBL inflate / IGB parse** | Partial | Host can plant/repair STBLz and pulse semas; guest parse/bind still parks (loadgate + binder). |
| **igUKbd / igUMouse** | Stub | No real USB HID Alchemy protocol — OK for CNK if pad path works; not FileIO-critical. |
| **SMAP.IRX** | Unused | On disc, never LoadModule’d in observed boots. |
| **Low-number / soft EE stubs** | Soft | ELF redo §6: some stub numbers fall through to unhandled→0 if hit; not current prims=2 blocker. |
| **Older explore without HLE** | Historical | Retry storm + “not an ELF module”; superseded by HLE registration path in current runtime. |

**Bottom line:** Sony FILEIO/LOADFILE/CDVD/SIF/sema/thread syscalls needed to *host* Alchemy are HLE’d. The Alchemy-branded IOP surface is **name-HLE’d** (`igFileIO` rich, keyboard/mouse stub). The remaining Alchemy blocker is **EE-side bind/loadgate/IGB completion**, not “missing CreateSema.”

---

## 4. Quick reference tables for rebuild workers

### `ig_irx` (Alchemy)

`igFileIO.irx`, `igUKbd.irx`, `igUMouse.irx` — ELF-referenced, **not** on ISO MODULES, HLE’d on LoadModule miss.

### `sony_irx` (generic / SCE / third-party non-ig)

**MODULES loaded:** LIBSD, USBD, LGDEVW, CRI_ADXI, SIO2MAN, PADMAN, MTAPMAN, MCMAN, MCSERV, SDRDRV, VVAA.  
**MODULES unused:** SMAP.  
**IOPRP:** FILEIO, LOADFILE (+ CDVD/SIF/thread/sema kernel stack).

### `ee_syscall_themes`

WaitSema / CreateSema / iSignalSema (IDs 2, 16, 45, 47 family); SifSetDma/DChain/Reg (RPC+LoadModule); CreateThread/StartThread/ChangeThreadPriority; SetupThread/Heap; DisableIntc TIM0/TIM1 + GS IMR around Alchemy FINISH.

### `hle_gaps`

Real igFileIO IRX absent; unknown RPC methods zero-acked; bind/FCE0/IGB parse still guest-parked; igU* stubs only.

---

## 5. Out file

This document: `verification/recovery/alchemy-rebuild-w4-iop-ee-inventory-2026-11-07.md`
