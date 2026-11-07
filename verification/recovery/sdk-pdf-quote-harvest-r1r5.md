# SDK PDF quote harvest — R1–R5 Track B (round 1)

**Date:** 2026-11-07  
**Scope:** Research only — verbatim quotes from official Runtime Library 3.0.x PDF text extracts under `verification/recovery/_sdk_pdf_extract/`, plus minimal corroboration from `E:\usr\local\sce` (headers / `ee/lib/libcdvd.a` symbols).  
**Not used:** `C:\usr`, `E:\PS2_SDK`.  
**Status:** Deep harvest for the four TARGET themes; AlignReadBuffer field layout remains a **documented gap** in public PDF prose.

Extract roots referenced below are relative to `verification/recovery/_sdk_pdf_extract/`.

---

## 1) AlignReadBuffer / readee / b1len / b2len / unaligned / +16 / +80 / GetReadPos / curReadPos

### Verdict

Official Device PDFs and `cdvdtips` document **64-byte EE buffer alignment compensation** and **`sceCdGetReadPos`**, and EE-vs-IOP **completion = EE memory fill**. They do **not** name `_CdAlignReadBuffer`, `readee`, `b1len`/`b2len`, or offsets `+16`/`+80`. Those names appear in community/ps2sdk RE and in-tree HLE comments (`runtime/src/iop/cdvdfsv.cpp`), not in shipped PDF text.

### Quotes — 64-byte alignment / internal compensation

**Source:** `cdvdtips_3.0.pdf.txt` (CD(DVD)-Rom Tips 3.0)

> Be aware of 64-byte alignment when reading from the EE  
> If the address of a buffer is not 64-byte aligned, the sceCdRead() function will perform compensation  
> processing internally. An increase in speed can be obtained just by adjusting the buffer alignment properly  
> to avoid this processing.  
> To allocate a buffer area, use memalign(64, size), or __attribute__((aligned(64))) for static buffers.

Nearby context (same tips doc, IOP module load case study):

> Start-up processing that reads sio2man.irx, padman.irx, mcman.irx, mcserv.irx, and libsd.irx from the  
> disc

**Source:** `PS2_EE-Overview-Device-3.0.2.pdf.txt` (EE Overview Device — libcdvd EE vs IOP)

> Since the data flow differs in this manner, the EE library and the IOP library have the following differences:  
> • On the EE side, the completion of a data read indicates the completion of the transfer of data to EE  
> memory rather than the completion of reading data from the drive.  
> • On the EE side, the success or failure of commands issued by the various functions to the subsystem  
> are affected by SIF status in addition to the drive status. Attention must also be given to the reentry of  
> an SIF RPC.  
> • When transferring data to the EE, correction for buffer address alignment may be performed. As much  
> as possible, 64-byte alignment should be maintained.

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt` — `sceCdRead` notes

> Since this is a non-blocking function, the actual completion of the data transfer must be detected using  
> sceCdSync().  
> Note on using this function  
> When data is transferred to the EE, sometimes the library will adjust the alignment of the buffer address.  
> Therefore, in the interest of speed, it is best to use 64-byte alignment as much as possible.

Same pattern on `sceCdReadCDDA`:

> When transferring data to the EE, the library may internally adjust the alignment of the buffer address. In the  
> interest of transfer speed, it is best to align the buffer on a 64-byte boundary.

### Quotes — `sceCdGetReadPos` / progress / alignment caveat

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt` — `sceCdGetReadPos` (EE)

> sceCdGetReadPos  
> Check the progress of sceCdRead()  
> …  
> u_int sceCdGetReadPos (void)  
> …  
> A value in 16-sector units (a multiple of 32768) is returned. Because of alignment adjustment, if the read  
> buffer is other than 64-byte aligned, care should be taken when performing the last transfer of the buffer  
> area which will not be 64-byte aligned (on either side of the read buffer).  
> Return value  
> Returns the progress of the sceCdRead() function as the size (in bytes) of the data transferred to the buffer.  
> When sceCdRead() terminates, 0 is returned.

**Source:** `PS2_IOP-Reference-Device-3.0.2.pdf.txt` — `sceCdGetReadPos` (IOP; no EE-alignment caveat)

> If the media is a CD, values in 1 sector units (a multiple of 2048) will be returned. If the media is a DVD,  
> values in 16 sector units (a multiple of 32768) will be returned.  
> Return value  
> Returns the progress of the sceCdRead() function as the size (in bytes) of the data transferred to the buffer.  
> When sceCdRead() terminates, 0 is returned.

**Source:** `PS2_EE-Overview-Device-3.0.2.pdf.txt` — poll + GetReadPos usage pattern

> Use the sceCdSync() function to wait for the read to complete. The two methods that can be used are  
> blocking and polling.  
> (Blocking example)  
> ret = sceCdSync(0);  
> (Polling example)  
> while(sceCdSync(1)) {  
> /* Other processing */  
> }

Official sample corroboration (not PDF extract; `E:\usr\local\sce\ee\sample\cdvd\smp_ee\main.c`):

> `unsigned char bf[2048 * 1024] __attribute__ ((aligned(64)));`  
> `rs_flg= sceCdSync(1);`  
> `scePrintf("Cur Read Position= %d\n",sceCdGetReadPos());`

### Official binary symbols (not PDF) — closest to “readee / curReadPos”

From `nm E:\usr\local\sce\ee\lib\libcdvd.a` (Runtime 3.0.3 tree):

| Symbol | Kind | Note |
|--------|------|------|
| `_sceCd_rd_intr_data` | `D` | EE lib BSS — interrupt/align staging block (RE nicknames: readee / `_rd_intr_data`) |
| `_sceCd_Read_cur_pos` | `D` | EE lib — backing store for `sceCdGetReadPos` |
| `_sceCd_cd_read_intr` | `T` | EE lib — read completion interrupt path |
| `sceCdGetReadPos` | `T` | Public API |

**No** symbol named `AlignReadBuffer`, `_CdAlignReadBuffer`, `b1len`, `b2len`, or `readee` appears in `libcdvd.a` strings/`nm`.

### Gaps (section 1)

| Sought | In PDF extracts? | Notes |
|--------|------------------|-------|
| `_CdAlignReadBuffer` / `AlignReadBuffer` | **No** | Internal EE; public `libcdvd.h` has no declaration |
| `b1len` / `b2len` / dest1/dest2 layout | **No** | In-tree HLE uses +0/+4 counts, +8/+12 dests |
| Payload at `+16`, tail at `+80` | **No** | In-tree comment-only; not in SDK manuals |
| Name `readee` / `curReadPos` | **No** | Closest official: `_sceCd_rd_intr_data`, `_sceCd_Read_cur_pos` |
| Exact unaligned head/tail byte formula | **No** | Only “compensation” / “either side of the read buffer” |

---

## 2) `sceCdSync` mode meanings; `sceCdDiskReady` return values; finish_read / complete contracts

### Quotes — EE `sceCdSync` modes (`0x00` / `0x01` only)

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt`

> sceCdSync  
> Wait for command completion  
> …  
> int sceCdSync (  
> int mode) 0x00: Wait for completion of command (blocking)  
> 0x01: Check current status and return immediately  
> (non-blocking).  
> When using this mode, the operating conditions of  
> other threads must be thoroughly considered.  
> …  
> Description  
> When mode is set to 0x00, this function waits for the command being executed to complete and returns 0.  
> When mode is set to 0x01, this function checks the execution state of the command and returns either 0 or  
> 1.  
> …  
> Return value  
> Table 2-26  
> Value Result  
> 0 Completed  
> 1 Not completed  
> See also  
> sceCdRead(), sceCdSeek(), sceCdStop(), sceCdStandby(), sceCdPause()

### Quotes — IOP `sceCdSync` modes (`0x00` / `0x01` / `0x10` / `0x11`)

**Source:** `PS2_IOP-Reference-Device-3.0.2.pdf.txt`

> int sceCdSync (  
> int mode) 0x00: Wait for completion of command (blocking)  
> 0x01: Check current status and return immediately (non-blocking)  
> …  
> 0x10: Wait for completion of command including completion of  
> command issued from the EE (blocking)  
> 0x11: Check and immediately return the current state, including  
> the state of the command issued from the EE (non-  
> blocking). …  
> Description  
> When mode is set to 0x00, this function waits for the command being executed to complete and returns 0.  
> When mode is set to 0x01, this function checks the execution state of the command and returns either 0 or  
> 1.  
> When mode is set to 0x10, this function waits for the command being executed to complete, including  
> completion of the command issued from the EE, and returns 0.  
> When mode is set to 0x11, this function checks the execution state of the command, including the state of  
> the command issued from the EE, and returns either 0 or 1.  
> …  
> Value Result  
> 0 Completed  
> 1 Not completed

### Quotes — EE/IOP independence of Sync (finish contract across SIF)

**Source:** `PS2_EE-Overview-Device-3.0.2.pdf.txt`

> A libcdvd function called from the EE and a libcdvd function called from the IOP are mutually independent.  
> The processing status of a function that was called from the EE cannot be obtained by calling sceCdSync()  
> from the IOP. In addition, if commands issued for the drive subsystem overlap, libcdvd will consider the  
> second command issue to have failed and will return the error value 0.

> • On the EE side, the completion of a data read indicates the completion of the transfer of data to EE  
> memory rather than the completion of reading data from the drive.

### Quotes — `sceCdDiskReady` modes + return values

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt` (EE; IOP Reference Device text matches)

> sceCdDiskReady  
> Check drive status  
> …  
> int sceCdDiskReady (  
> int mode) Check mode (0: blocking, 1: non-blocking)  
> …  
> Description  
> Checks the drive status and determines if a command can be issued. SCECdNotReady is returned when  
> the type of media in the drive is being determined.  
> If the mode argument is set to blocking, and the drive rotation is not stable, the function waits until the drive  
> rotation is stable, then it returns. In the non-blocking mode, the function returns immediately after the status  
> is checked.  
> …  
> Return value  
> Table 2-6  
> Value Macro Result  
> 0x02 SCECdComplete Drive state allows commands to be issued  
> 0x06 SCECdNotReady Drive cannot accept commands

**Header corroboration** (`E:\usr\local\sce\common\include\libcdvd.h`):

> `#define SCECdComplete	0x02	/* Command Complete 	  */`  
> `#define SCECdNotReady	0x06	/* Drive Not Ready	  */`  
> `int sceCdSync(int mode);`  
> `int sceCdDiskReady( int mode );`

### Quotes — finish / complete via Sync after Read + GetError

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt` — `sceCdRead` return notes

> After this function is successfully invoked, the following error information can be obtained by first waiting for  
> the command to complete using a function such as sceCdSync(), then calling sceCdGetError().

**Source:** same file — callback termination codes (complete contract for non-blocking)

> sceCdCallback  
> Define sceCdSync callback function  
> …  
> Sets the callback func called when a non-blocking function terminates.  
> …  
> SCECdFuncRead sceCdRead() function has terminated.

**Source:** Overview Device — read sequence (“wait for the read to finish”)

> 3. Wait for the read to finish  
> Use the sceCdSync() function to wait for the read to complete. The two methods that can be used are  
> blocking and polling.

### Gaps (section 2)

| Sought | Status |
|--------|--------|
| EE Sync modes `0x10`/`0x11` | **Absent on EE** Reference; present on **IOP** only |
| Literal name `finish_read` | **No** hit in extracts — contract expressed as Sync + EE-memory completion |
| DiskReady values other than `0x02`/`0x06` | **Not listed** in Return value tables |
| Exact HLE mapping of mode `1\|\|17` poll | PDF supports `0x01`/`0x11` as non-blocking “Not completed=1”; EE lacks `0x11` |

---

## 3) padman / scePad / SIO2 surface (API inventory quotes)

### Quotes — modules + load order

**Source:** `PS2_EE-Overview-Device-3.0.2.pdf.txt` — Controller Library overview

> Related Files  
> The following files are needed to use libpad.  
> Table 9-1  
> Category Filename  
> Library file libpad.a  
> Header file libpad.h  
> IOP Module files sio2man.irx  
> padman.irx  
> mtapman.irx (for multitap support)  
> The IOP modules should be loaded at startup by the EE program using sceSifLoadModule().

> Basic Usage  
> 1. Load IOP modules  
> Call sceSifLoadModule() to load sio2man.irx, then padman.irx.  
> 2. Initialize the library  
> Call scePadInit() to initialize the controller library.  
> 3. Open the controller port  
> Call scePadPortOpen() …  
> The work buffer is used for DMA transfers from the IOP. Due to cache issues, it must be 64-byte  
> aligned.

**Source:** `cdvdtips_3.0.pdf.txt` — same module set in boot read case study (quoted in §1).

**Source:** `PS2_EE-Overview-Sif-3.0.pdf.txt` — example load

> `sceSifLoadModule( "host0:/usr/local/sce/iop/modules/padman.irx",`

### Quotes — EE Reference API inventory (Chapter 10 TOC)

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt`

> Chapter 10: Controller Library  
> Initialization/Termination Functions  
> scePadInit  
> scePadEnd  
> Controller Control Functions  
> scePadEnterPressMode  
> scePadExitPressMode  
> scePadPortClose  
> scePadPortOpen  
> scePadSetActAlign  
> scePadSetActDirect  
> scePadSetMainMode  
> Information Acquisition Functions  
> scePadGetReqState  
> scePadGetSlotMax  
> scePadGetState  
> scePadInfoAct  
> scePadInfoComb  
> scePadInfoMode  
> scePadInfoPressMode  
> scePadRead  
> Callback Setting Function  
> scePadSetDmaCallback  
> Library System Functions  
> scePadReqIntToStr  
> scePadSetFlushRate  
> scePadSetWarrningLevel  
> scePadStateIntToStr  
> scePadGetErxEntries

### Quotes — padman.irx behavior + states + SIO2 contention

**Source:** `PS2_EE-Reference-Device-3.0.3.pdf.txt` — `scePadPortOpen`

> When the controller port is opened, padman.irx monitors the controller connection. After the connection is  
> made, the controller information is automatically obtained.  
> …  
> void* data) Work buffer, store at 64 byte alignment  
> (The required size is defined by the constant  
> PadDmaBufferMax.)

**Source:** same — `scePadGetState`

> When the port is opened, the IOP’s padman.irx module independently monitors the connection and gets  
> information about the controller. … the application can use  
> scePadGetState() to check the status of padman.irx processing. If scePadGetState() returns  
> scePadStateStable or scePadStateFindCTP1, the application can obtain button information from the  
> controller.  
> …  
> Value Macro Result  
> 0 scePadStateDiscon Controller is not connected  
> 1 scePadStateFindPad Controller was not found (processing continuing)  
> 2 scePadStateFindCTP1 Detect ed the CTP 1.0 controller  
> 5 scePadStateExecCmd Communicating with controller  
> 6 scePadStateStable Detect ed the CTP 2.0 controller  
> 7 scePadStateError Communication error detected  
> …  
> Among the states listed above, scePadStateFindCTP1 and scePadStateStable are the only ones in which a  
> request from an application can be accepted or the button state can be obtained.

**Source:** same — `scePadGetReqState` result codes

> 0 scePadReqStateComplete The function terminated normally  
> 1 scePadReqStateFaild Processing failed for some reason  
> 2 scePadReqStateBusy Executing

**Source:** same file — SIO2 resource note (memory card / other Device chapters; pattern repeated)

> Since this function makes use of the SIO2 resource, other devices that use the SIO2 such as the controller

Official tree modules present under `E:\usr\local\sce\iop\modules\`: `sio2man.irx`, `sio2d.irx`, `padman.irx` (no separate public `libsio2` EE API chapter in these Device extracts).

### Gaps (section 3)

| Sought | Status |
|--------|--------|
| Dedicated SIO2 register/API reference chapter in extracted PDFs | **Thin** — SIO2 mentioned as shared resource + `sio2man.irx` dependency |
| IOP-side padman internal RPC protocol | **Not in extracts** |
| libpad2 surface | Overview Device has libpad2 notes; not fully harvested here (R5 gated inventory = libpad primary) |

---

## 4) libsd / sceSd / IOP+EE sound stack quotes

### Quotes — IOP `libsd` role

**Source:** `PS2_IOP-Overview-Sound-3.0.1.pdf.txt`

> libsd is a low level library for controlling the PlayStation 2 sound device (SPU2 and peripheral circuits).  
> Always use libsd to access the sound device.  
> libsd provides functions for accessing public SPU2 registers, transferring waveform data or sound data to  
> or from SPU2 local memory, setting up processing for interrupts from the SPU2, and setting or getting  
> effect attributes. It also provides batch functions for collecting together accesses to a series of SPU2  
> registers.  
> …  
> Register Type … Set Value Get Value  
> Basic parameter register SD_VP_*/SD_P_* sceSdSetParam() sceSdGetParam()  
> Voice control parameter register SD_S_* sceSdSetSwitch() sceSdGetSwitch()  
> Address value register SD_VA_*/SD_A_* sceSdSetAddr() sceSdGetAddr()  
> Pseudo register SD_C_* sceSdSetCoreAttr() sceSdGetCoreAttr()

### Quotes — IOP Reference API inventory (Chapter 8 TOC)

**Source:** `PS2_IOP-Reference-Sound-3.0.2.pdf.txt`

> Chapter 8: Low-Level Sound Library (for IOP)  
> Structures: sceSdBatch, sceSdEffectAttr  
> Initialization: sceSdInit  
> Register Wrapper: sceSdGetAddr, sceSdGetCoreAttr, sceSdGetParam, sceSdSetAddr, sceSdSetCoreAttr,  
> sceSdSetParam, sceSdSetSwitch, sceSdGetSwitch  
> Effect: sceSdCleanEffectWorkArea, sceSdClearEffectWorkArea, sceSdGetEffectAttr, sceSdSetEffectAttr,  
> sceSdSetEffectMode, sceSdSetEffectModeParams  
> Interrupt handlers: sceSdSetSpu2IntrHandler, sceSdSetTransIntrHandler,  
> sceSdGetSpu2IntrHandlerArgument, sceSdGetTransIntrHandlerArgument  
> Transfer: sceSdBlockTrans, sceSdBlockTransStatus, sceSdStopTrans, sceSdVoiceTrans,  
> sceSdVoiceTransStatus  
> Batch: sceSdProcBatch, sceSdProcBatchEx  
> Service: sceSdNote2Pitch, sceSdPitch2Note  
> Callbacks: sceSdSpu2IntrHandler, sceSdTransIntrHandler, sceSdBlockTransHandler

**Source:** same — `sceSdInit`

> int sceSdInit(  
> int flag) Initialization flag  
> SD_INIT_COLD Initialize all  
> SD_INIT_HOT Do not initialize voice, volume, effect,  
> pitch variation or sound source  
> specification settings  
> …  
> Initializes the sound device.  
> Also sets the interrupt controller for SPU2-related interrupts at the same time, and allocates an event flag  
> for processing the completion of transfers, which is used internally within the library.

### Quotes — EE stack: libsdr → sdrdrv.irx → libsd.irx → SPU2

**Source:** `PS2_EE-Overview-Sound-3.0.2.pdf.txt`

> To enable a CSL module to access the SPU2, use the low level library libsd (for the IOP). …  
> For a CSL module implemented on the EE, use libsdr to remotely call libsd.

> libsdr is a low-level sound library that allows the EE to remotely control the SPU2, which is connected to  
> the IOP. The libsdr routines work together with the driver module on the IOP side and provide the EE with  
> features similar to the IOP low-level sound driver library libsd.  
> …  
> Figure 3-1 … SIF / sceSdRemote() / libsdr / Driver Module sdrdrv.irx / libsd / SPU2, IOP Hardware  
> …  
> Library libsdr.a  
> Header file libsdr.h  
> Run-time module (IOP-side) sdrdrv.irx  
> libsd.irx

Remotable libsd surface via libsdr (Table 3-2 excerpt):

> sceSdInit, sceSdSetParam, sceSdGetParam, sceSdSetSwitch, sceSdGetSwitch, sceSdSetAddr,  
> sceSdGetAddr, sceSdSetCoreAttr, sceSdGetCoreAttr, sceSdProcBatch, sceSdProcBatchEx,  
> sceSdVoiceTrans, sceSdBlockTrans, sceSDStopTrans, sceSdVoiceTransStatus, sceSdBlockTransStatus,  
> sceSdSetTransCallback, sceSdSetIRQCallback, sceSdSetEffectAttr, sceSdGetEffectAttr,  
> sceSdSetEffectMode, sceSdSetEffectModeParams, sceSdClearEffectWorkArea,  
> sceSdCleanEffectWorkArea, sceSdNote2Pitch, sceSdPitch2Note

### Quotes — EE Reference libsdr API

**Source:** `PS2_EE-Reference-Sound-3.0.1.pdf.txt` — Chapter 4 TOC + `sceSdRemote`

> Chapter 4: Low-Level Sound Library (for EE)  
> sceSdRemoteInit, sceSdCallBack, sceSdRemote, sceSdRemoteCallbackInit, sceSdTransToIOP,  
> sceSdGetErxEntries, sceSdRemoteCallbackQuit

> sceSdRemote  
> Remotely execute libsd command  
> …  
> The libsd.irx API on the IOP is remotely executed from the EE according to the command. The command is  
> specified using the libsd function name with the "sce" part of the name replaced by "r". For details, refer to  
> common/include/sdrcmd.h.  
> Example: sceSdRemote( 1, rSdSetParam, SD_CORE_0|SD_P_MVOLL , 0x3fff );  
> …  
> When non-blocking is specified, control returns from the function without waiting for IOP-side processing to  
> end. Use sceSdCallBack() to set the end callback function to find out when IOP-side processing has  
> completed. If the next command is sent before IOP processing ends, an invalid operation may occur.

### Gaps (section 4)

| Sought | Status |
|--------|--------|
| Full transfer-complete interrupt contracts (VoiceTransStatus tables) | Present in IOP Reference Sound but only TOC/init sampled here — deepen if R5 HLE starts |
| `sdrdrv.irx` internals | Named in Overview; no deep protocol dump in extracts |
| Cross-link to SIF CallRpc reentry for sound | Pointed from Overview Sound (“SIF System” doc); not re-quoted here |

---

## Cross-cutting notes (SIF / tips)

- **SIF:** EE Overview SIF documents `sceSifCallRpc` re-entry rules and shows `padman.irx` load examples — relevant when EE libcdvd / libsdr share SIF with pad.  
- **Tips:** `cdvdtips_3.0.pdf.txt` is the strongest **plain-language** source that unaligned EE `sceCdRead` buffers trigger **internal compensation** (the public face of AlignReadBuffer behavior).  
- **Alchemy / Intrinsic:** no hits in the 14 extracts (per MASTER-CONTEXT §B).

---

## Quote counts by section

Approximate **verbatim quote blocks** captured above (multi-line citations counted as one block each):

| Section | Theme | Quote blocks |
|---------|--------|--------------|
| 1 | Align / GetReadPos / EE completion / tips alignment | **9** (+ 1 sample; + symbol table) |
| 2 | sceCdSync / DiskReady / finish-complete | **10** |
| 3 | padman / scePad / SIO2 | **8** |
| 4 | libsd / libsdr / IOP+EE stack | **8** |
| **Total** | | **~35** |

---

## Open gaps summary (for next harvest pass)

1. **No PDF prose** for `_CdAlignReadBuffer`, `b1len`/`b2len`, or `+16`/`+80` staging — need EE `libcdvd.a` disassembly / community ps2sdk `ncmd.c` labeled as **non-PDF**, or Docs&Training PDFs not yet extracted.  
2. EE Sync has **no** `0x10`/`0x11`; IOP does — HLE must not conflate EE client Sync with IOP Sync modes.  
3. Literal **`finish_read`** identifier absent; use Sync + “transfer to EE memory complete” language.  
4. SIO2 is **dependency/contention**, not a full API chapter in current extracts.  
5. Optional later extracts: Docs&Training, graphics/movie/network PDFs, deeper VoiceTransStatus pages.
