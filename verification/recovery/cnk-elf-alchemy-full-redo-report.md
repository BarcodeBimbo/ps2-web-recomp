# Crash Nitro Kart — ELF / Alchemy full redo report

**Mode:** read-only. No game/runtime code edits. Quarantined from Hitman/NFS.  
**Date:** 2026-11-06  
**Game id:** `b49f2e769315347e8bda839feb705744`  
**ELF:** `games/b49f2e769315347e8bda839feb705744/disc/boot.elf`  
**Ghidra:** not running (manual MIPS + generated recomp units).

Cross-check sources: this ELF walk, `generated/b49f2e…/`, overnight crumbs `verification/host-session-2026-11-06-overnight-cnk-10p.json` / `10s.json`, `verification/recovery/cnk-nullbind-51ACEC-restart-report.md`, and chat extract `verification/recovery/08d63_full_extract.md`.

---

## 1. ELF identity

| Field | Value |
|--------|--------|
| Path | `…/disc/boot.elf` (also `disc.iso`) |
| Size | 6 234 672 bytes |
| Compiler comment | `MW MIPS C Compiler (2.4.1.01)` / `PlayStation2` |
| Entry | `0x00108D28` |
| PHDR0 LOAD | VA `0x00100000`, file off `0x80`, filesz `0x5F2000`, memsz `0x62A480`, flags `RWX` |
| PHDR1 LOAD | VA `0x0072A480`, filesz `0` (BSS marker / empty) |
| Image end (file) | VA `0x006F2000` |
| BSS | `0x006F2000` … `0x0072A480` (zero-filled by CRT0) |
| Symbols | stripped (empty `.symtab` / `.strtab`); `.comment` + `.reginfo` present |

**Bottom line:** one big RWX load, then BSS. Bind global `0x00725F50` lives in **BSS**, so it is never a file constant — only code that builds/stores a pointer at runtime matters.

---

## 2. Modules / IRX / Alchemy surface

### Boot / IOP image
- `cdrom0:\IOPRP255.IMG;1`
- Module dir string: `cdrom0:\MODULES`

### IRX names in the ELF (load list + Alchemy paths)

| Module | Notes |
|--------|--------|
| `sio2man.irx` | pad path |
| `padman.irx` | |
| `mtapman.irx` | |
| `mcman.irx` / `mcserv.irx` | memory card |
| `usbd.irx` | USB |
| `lgdevw.irx` / `lgdev.irx` | Logitech wheel |
| `libsd.irx` / `sdrdrv.irx` | sound |
| `vvaa.irx` | |
| `cri_adxi.irx` | CRI ADX audio |
| **`igFileIO.irx`** | Alchemy file IOP; host explore.log: “not an ELF module” (fail / stub) |
| **`igUKbd.irx` / `igUMouse.irx`** | same failure pattern in explore.log |
| Alchemy search paths | `/usr/local/Alchemy/iop/modules`, `c:/Alchemy/iop/modules`, `$(AlchemyRoot)` |

### Alchemy identity strings
- `Intrinsic Alchemy  v3.0 -0909 (Static/Release)`
- `Alchemy`, `ALCHEMY_BASE`, `alchemy.ini`, `_isAlchemyMemory`
- Core types (names present): `igFile`, `igIGBFile`, `igPsx2IopRpcConnection`, `igPsx2VisualContext`, huge `ig*` GUI/gfx/anim set (**673** `ig[A-Za-z0-9_]+` class-name strings)

### UI / asset paths (examples)
`gfx/ui/butanim.igb`, `ui/introtxr.igb`, fonts/csv pools, `pools.csv`, `ASSETS.GFC` / `ASSETS.GOB` (seen at runtime in explore.log).

### Explore.log module reality (runtime, not ELF)
Loads that **work:** LIBSD, USBD, LGDEVW, CRI_ADXI, SIO2MAN, PADMAN, MTAPMAN, MCMAN, MCSERV, SDRDRV, VVAA.  
Loads that **fail:** `IGFILEIO.IRX`, `IGUMOUSE.IRX`, `IGUKBD.IRX` (host cannot treat them as ELF IRX). EE still progresses far enough to park on semas — Alchemy file path is partly HLE’d on the host (`runtime/src/iop/igfileio.cpp`).

---

## 3. Entry / boot flow

Entry `0x00108D28` is **not** game `main`. It is Metrowerks / SCE CRT0:

1. **`paddw rd, zero, zero`** over GPRs (looks like `70000C28` …) — clear registers via MMI.
2. Clear HI/LO / COP1 FPRs.
3. **BSS clear** `0x006F2000` → `0x0072A480` (16-byte store loop).
4. **`syscall` SetupThread (`v1=0x3C`)** — GP `0x00709BF0`, large stack, args area `0x00729F00`.
5. **`syscall` SetupHeap (`v1=0x3D`)**.
6. `jal 0x004459A8` / `jal 0x0043CD60` (lib / cache init).
7. **EI** (`0x42000038`).
8. **`jal 0x00108F60`** — real app bring-up (this is the “main-ish” function).
9. **`j 0x00445D90`** — Exit with `main` return code.

### Inside `0x00108F60` (app init)
Important calls (VA):
- String / path setup using `0x00610FE0+` (`IOPRP255`, `MODULES`, `igMallocMemoryPool`, …)
- `jal 0x0050CFB0`, `jal 0x004ECD40` — Alchemy / pool bring-up region
- `jal 0x00109170` — further game/Alchemy init (factory `jal 0x00508930`, etc.)
- Thread stack dump in explore.log shows frames through `0x00108EE0` / `0x00108EC0` — consistent with this CRT0 → init chain

**There is no symbol named `main`.** Treat `0x00108F60` as the primary EE application entry after CRT0.

---

## 4. Alchemy structures (ELF + how host notes map)

### 4.1 Loadgate object (function `0x0010FCE0`)

Single caller: `jal` from `0x0010F5EC`.

Layout proven from disassembly (base = gate object in `a0` / `s3`):

| Offset | Meaning (from code) |
|--------|----------------------|
| gate + 8 + i×96 | slot `i` base (`i` in 0…249) |
| slot + 0x48 (72) | state word; FCE0 requires `== 1` before `jal 0x00110100` |
| slot + 0x4C (76) | **status** enum: `1` = CD-done path, `2`/`3`/`4` used in branches |
| gate + 24008 (`0x5DC8`) | busy / “loadgate active” byte (**must stay 1** per overnight — clearing → `0x428970` spam) |
| gate + 24016 / 24020 | walker / current index (`24020` compared to 250) |

Loop: 250 slots × stride **96**.  
When +48==1 and status path matches, FCE0 calls **`0x00110100`** (the “finalize / parse kick” overnight tried to force).

**Host note alignment:** overnight `10p`/`10s` correctly treat **+76 as status** and **+24008 as sticky**.  
Earlier 08d63 line “slot+0x4C holds stream object” is **wrong vs ELF** — +0x4C is status. Stream buffer pointer is a **different** object field (runtime: stream obj `0x974358`, field +0x48 → assemble scratch **`0xBD1000`**). That stream object is heap/BSS at runtime, not a fixed ELF VA.

### 4.2 `0x0010FCE0` vs imm `0xFCE0`

Three `addiu` with imm `0xFCE0` in the binary:
- `0x00229640`, `0x0042AE68` — **`addiu sp, sp, -800`** (stack frame), **not** the FCE0 function
- `0x004BC6B8` — `addiu v0, v0, 0xFCE0` (address math)

So “FCE0” in host logs means **function VA `0x0010FCE0`**, not those immediates.

### 4.3 Bind registry global `0x00725F50` (BSS)

- **Not** in the file image; CRT0 zeroes it.
- **Installer** at `0x00520160`:
  1. `jal 0x00508930` → factory alloc (uses allocator at `*0x00725F00`, `a1=3`)
  2. Delay-slot / next: **`sw v0, 0x5F50($at)`** with `lui at, 0x72` → **stores object pointer into `0x00725F50`**
  3. Second factory alloc + `jal 0x004D28E0`, set byte `obj+0x2C = 1`, virtual call **vt+208**
  4. Reload `0x725F50`, virtual call **vt+84** with the new object as `a1` (register into the binder)
- **Teardown** at `0x00520210`: vt+80 / vt+88 / release, then **`sw zero, 0x725F50`**

Factory helper `0x00508930` (209 call sites):  
`lw a0, 0x5F00($at)` → `0x00725F00` allocator object; `jalr` **vt+8**.

Sibling BSS globals in the same Alchemy heap band: `0x725EF0`, `0x725EF8`, `0x725F00`, `0x725EE0` (many lw sites).

### 4.4 Null-bind path `0x0051AC80` … `0x0051ACEC` (ELF disassembly)

Callers of `0x51AC80`: `0x0010FF10`, `0x004EDE50`, `0x0051AD9C`.

```
0051AC80  addiu sp,sp,-64
0051AC84  sd ra,32(sp)
          sq s1/s0
0051AC90  lbu v1,24(a0)          ; flag at obj+24
0051AC94  beq v1,0 -> AD64       ; already idle → return
0051AC98  move s0,a0
0051AC9C  sb zero,24(s0)         ; clear flag
0051ACA0  addiu a0,sp,60
0051ACA4  lw a1,28(s0)           ; obj+28
0051ACAC  lw t9,0(a1)            ; vtable
0051ACB0  lw t9,92(t9)           ; **** vt+92 ****
0051ACB4  jalr t9                ; a3=1
0051ACBC  lui at,0x0072
0051ACC0  lw a0,0x5F50(at)       ; **** *0x00725F50 ****
0051ACC4  lw t9,0(a0)
0051ACC8  lw t9,80(t9)           ; **** vt+80 ****
0051ACCC  jalr t9                ; delay: lw s1,32(s0)  (key / obj+32)
0051ACD4  lw t9,0(v0)            ; vtable of LOOKUP RESULT
0051ACD8  move a2,s1
0051ACDC  addiu a0,sp,56
0051ACE0  lw t9,84(t9)           ; **** vt+84 ****
0051ACE4  jalr t9                ; delay: move a1,v0
0051ACEC  jal 0x005170A0         ; <-- ra seen on crash is the jalr's return = 0x51ACEC
```

**Crash meaning (ELF-proof):**  
`ra=0x0051ACEC` is the return address of **`jalr vt+84`** on the object returned by **`(*0x725F50)->vt+80`**. If that method pointer is **0**, you get `missing code @0` with exactly this `ra`. This matches the null-bind restart report and overnight `10s`.

Related: `0x00517124` and `0x0023AFD8` / `0x00520220` use the same `725F50` → vt+80 pattern (lookup). `0x005201B4` uses vt+84 for register-into-binder.

### 4.5 ig\* “vtable map” honesty

What the ELF **does** give:
- **673** class-name strings (`igFile`, `igIGBFile`, …).
- A few **GUI meta name pointer runs** (e.g. at `0x0063ACD8`: `igAttrSet`, `igDepthStateAttr`, …).
- Runtime objects are classic C++-style: word0 = vtable, then refcount at +4 (release pattern at `0x51ACF4+` and installer).

What the ELF **does not** give easily:
- Classic Itanium RTTI (`typeinfo*`-before-vtable) for Alchemy core classes — **0 hits** with that heuristic.
- Almost **no** absolute or `lui/addiu` builds of `igIGBFile` / `igFile` string VAs (names are for meta/debug / hashed registry, not sprinkled as immediates).
- Stripped symbols → method names for vt+80/+84/+92/+108 are **not** recoverable as strings; only offsets are sure.

**Practical method index map (byte offset / 4):**

| Vtable offset | Index | Seen at |
|---------------|-------|---------|
| +8 | 2 | factory through `*0x725F00` |
| +80 | 20 | bind lookup (`51ACC8`, `520228`, …) |
| +84 | 21 | bind follow-up / register (`51ACE0`, `5201BC`) — **null crash slot** |
| +88 | 22 | teardown |
| +92 | 23 | unbind prelude (`51ACB0`) |
| +108 | 27 | overnight finalize path (`0x110100` needs live vt+108) |
| +208 | 52 | installer post-create (`5201A4`) |

To name those methods you need a live dump of `*0x725F50`’s vtable (or Ghidra with recovered types) — not present as ELF constants.

---

## 5. Sema / FCE0-related constants

### Sema IDs 16 / 45 / 47 (and friends)
These are **not** hardcoded CreateSema return immediates in a simple `li a0,16; WaitSema` pattern for the Alchemy gate. Host/runtime stores observed IDs in BSS:

| Global | Role (from `igfileio.cpp` + ELF xrefs) | ELF access examples |
|--------|------------------------------------------|---------------------|
| `0x00705F18` | TIM0 lock sema (**often id 16**) | sw `0x00426C78`, lw `0x00427488` / `0x00426B80` |
| `0x00705C18` | FINISH / delay WaitSema (**often id 45**) | sw `0x00422E0C`, lw `0x00422FEC` |
| `0x00705C10` | related gate sema (**often 47**) | sw `0x00422E28` |
| `0x00705C00` | finish counter (host); **no** direct `lui/lw` pair in ELF with that exact hi/lo (may be gp/other addressing) |

Explore.log end state: threads waiting on semas **2**, **43**, **45** — same family of Alchemy pumps.

CreateSema itself is EE syscall **`0x40`** in this tree’s HLE (`kernel.cpp`); stubs exist in the EE image via `li v1,N; syscall` tables around `0x0043C6C0+`.

### Hardcoded `a0=16/54/55`
Raw `addiu a0,zero,16` appears hundreds of times (sizes, enums, etc.) — **not** a reliable WaitSema(16) finder.  
`a0=54` / `a0=55` have only a couple of sites and do not look like the Alchemy TIM0 lock path. Prefer the **globals above** over immediates.

---

## 6. Syscall map vs HLE

### Counts
- Raw `syscall` opcodes in LOAD: **921** (earlier “~14000” was a noisy opcode collision count — discard it).
- Clean `li v1,N; syscall` stub pairs: **168**.

### Numbering
CNK uses the **same EE numbering our HLE implements** (`PS2WebRecomp/runtime/src/kernel.cpp`):  
CreateSema=`0x40`, WaitSema=`0x44`, CreateThread=`0x20`, SifSetDma=`0x77`, SetupThread=`0x3C`, SetupHeap=`0x3D`, SetSyscall=`0x74`, etc.

### Top stub immediates (examples)
| v1 | Name (HLE) | Notes |
|----|------------|--------|
| `0x74` | SetSyscall | most common stub |
| `0x5A` / `0x5B` | GetEntryAddress (`0x5B`); `0x5A` unnamed in HLE |
| `0x3C` / `0x3D` | SetupThread / SetupHeap | CRT0 |
| `0x10`/`0x12` | AddIntc/DmacHandler | |
| `0x20`… | Thread API | |
| `0x40`… | Sema API | via stub table |

Negative `li v1` values are **interrupt-safe** variants (`n = -imm`); HLE already accepts high-bit / negated forms.

### Gaps / soft stubs in HLE
Several low numbers (`0x00`,`0x03`,`0x08`–`0x0F`, …) and a few mid ones (`0x56`,`0x57`,`0x59`,`0x5A`, …) appear as stubs but fall through to **`[sys] unhandled` → return 0** unless a custom syscall table entry is installed. Not the current CNK prims=2 blocker (sema/bind/IGB parse is).

---

## 7. Cross-check vs overnight / 08d63 / null-bind

| Claim | ELF verdict |
|--------|-------------|
| `ra=0x51ACEC` is vt+84 after `*0x725F50` vt+80 | **Confirmed** in `0x51AC80` disassembly |
| `0x725F50` is bind registry pointer | **Confirmed**; BSS; installed at `0x520180` |
| Forcing FCE0/`0x110100` without full binder → null jalr | **Consistent**: FCE0→`0x110100` can advance slot state into code that later hits `0x51AC80` unbind/lookup |
| Soft-arm +45, no host FCE0, prims=2 | Runtime only; ELF shows why +48 must be 1 before `0x110100` |
| +24008 must stay set | **Confirmed** as gate flag in FCE0 (`sb`/`lbu` `0x5DC8`) |
| Assemble scratch `stream+0x48 → 0xBD1000` | Runtime heap; not a fixed ELF symbol; **do not confuse** with loadgate slot+0x48 (state) or +0x4C (status) |
| `igFileIO.irx` missing as ELF IRX | String present; explore.log load fails; host HLE compensates |
| Literal / lui build of `0x0051ACEC` | **0** — it is a code address (return site), not a relocated constant |
| imm `0xFCE0` sites = FCE0 function | **False** — stack adjusts; real function only at VA `0x0010FCE0` |

**Alive conclusion (ELF + overnight agree):**  
Bytes in `BD1000` + status 1 are not enough. Parse/finalize needs a **fully initialized bind registry** (`0x725F50` → object whose vt+80 returns an object with **non-null vt+84**). Host-forcing FCE0 without that init reproduces the null bind.

---

## 8. Open questions / next ELF steps (still read-only)

1. **Dump live vtable** at `*ee32(0x725F50)` under soft-arm vs forced-FCE0 (as null-bind report asked): compare method slots 20/21/27.
2. **Identify factory type** for `0x508930` allocations (what class is stored in `0x725F50`) via constructor / string nearby in a debugger — ELF strings alone did not bind.
3. **Map stream object** fields: find which loadgate/slot pointer leads to runtime `0x974358` and confirm +0x48 buffer vs ELF status fields (avoid mixing layouts).
4. **`0x00110100` / vt+108** disassembly path when +48≠1 vs =1 (why overnight FCE0 at status 1 returned early `FD6C→FF34`).
5. Optional: start Ghidra on `boot.elf` with BSS size `0x62A480` and label `0x725F50`, `0x51AC80`, `0x10FCE0`, `0x520160`.
6. Do **not** blind-patch function pointers; do **not** clear +24008; keep CNK disc-fix quarantined.

---

## 9. Key address cheat sheet

| VA | What |
|----|------|
| `0x00108D28` | CRT0 entry |
| `0x00108F60` | App init (“main-ish”) |
| `0x0010FCE0` | Loadgate pump / FCE0 |
| `0x00110100` | Slot finalize called from FCE0 |
| `0x00508930` | Alchemy factory via `*0x725F00` |
| `0x00520160` | Install bind object into `0x725F50` |
| `0x00520210` | Tear down / null `0x725F50` |
| `0x0051AC80` | Unbind / registry lookup sequence |
| `0x0051ACEC` | Return site of crashing vt+84 `jalr` |
| `0x00725F00` | Allocator / factory root object (BSS) |
| `0x00725F50` | Bind registry object\* (BSS) |
| `0x00705F18` | TIM0 lock sema id storage |
| `0x00705C18` | FINISH WaitSema id storage |
| `0x00BD1000` | Runtime IGB assemble scratch (not ELF) |

---

*End of report.*
