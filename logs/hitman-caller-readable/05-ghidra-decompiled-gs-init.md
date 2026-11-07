# Ghidra decompiled snippets — GS CRT + draw-context setup

Program: `hitman_boot.elf` (EE MIPS, load `0x00100000`).

---

## 1) `FUN_0028ef4c` @ `0028ef4c` — CRT / DISPFB2 / DISPLAY2

Sets PMODE, DISPFB2 (once), DISPLAY2. This is the width/page source for host present.

```c
// condensed from decompiler — mode param_2 selects NTSC/PAL-ish paths
FUN_00419050(...);          // → SetGsCrt
FUN_0028ecec(param_1, 0x200, height, 4);  // color buffer dims, format 4
FUN_0028ede8(param_1, 0x200, height, 4);  // z dims
FUN_0028ee60(param_1);      // allocate FB page words at +0xd4 / +0xc4 / …

REG_GIF_MODE = 4;
REG_GS_PMODE = 0x66;        // EN2, typical libgraph default
REG_GS_DISPFB2 = (*(uint*)(param_1 + 0xd4) >> 11) | 0x1000;
//                 FBP from alloc          FBW=8 (512px), PSM=0

// DISPLAY2: MAGH=(mag-1), DW=mag*512-1, DH=height-1, DX/DY from mode
REG_GS_DISPLAY2 = uVar5;
FUN_0028f1d0(...);          // clamp display DX/DY tweaks
FUN_0028f248(...);          // apply DX/DY offsets into DISPLAY2
```

**Host decode of observed `display2 = 0x1BF9FF0203227C`:** width **512**, height **448** (Mode A/C width failures eliminated).

**DISPFB2 observed:** `0x1190` → FBP=**400**, FBW=8, PSM=0.

Only privileged `ori …,0x90` after `lui …,0x1200` for DISPFB2 found at `0028f098` — **no later flip writes** to DISPFB2 in boot ELF.

---

## 2) `FUN_0028f2c4` @ `0028f2c4` — initial draw environment GIF

Builds a large A+D packet: FRAME/ZBUF/TEST/ALPHA/TEX/SCISSOR/XYOFFSET/…

Notable stores (see also `02-ghidra-zeroed-scissor-xyoffset.md`):

```c
// FRAME_1 from alloc
*pkt = (d4 >> 11) | ((d8 >> 6) << 16) | (psm << 24);  // reg 0x4C

// TEST_1 / TEST_2 := 0x30000
// ALPHA_1 / ALPHA_2 := 0
// SCISSOR_1 := 0          ← zero at init
// XYOFFSET_1 / _2 := 0    ← zero at init
// TEXA := 0xFF << 32
// DIMX := constant from DAT_00596598 area
```

`FUN_0028ec94(param, format)` with format **4** returns PSM **0** (PSMCT32) for the FRAME path.

---

## 3) `FUN_0028f7fc` @ `0028f7fc` — clear using FBP from `+0xd4`

```c
uVar2 = *(uint *)(param_1 + 0xd4);
FUN_0029435c(..., param_2, 1);           // build clear state (TEST 0x20000, etc.)
FUN_00296f84(..., uVar2 >> 11, 0, 0, 0); // sprite clear tiles to that FBP
```

Caller `FUN_00291710` passes **`param_2 = 0`** → **clear color black**.

Sibling `FUN_0028f6dc` clears using `+0xc4` (the other page).

---

## 4) `FUN_00291710` — wires init together

```c
FUN_0028ef4c(disp_obj, mode);   // CRT + DISPFB2 + DISPLAY2
// … PutDrawEnv-style follows …
FUN_0028f7fc(disp_obj, 0);      // black clear on display page
FUN_0028f6dc(disp_obj, 0);      // black clear on other page
```

---

## 5) Runtime state that extends beyond these snippets

After boot, TRACE shows ctx0:

- FRAME FBP **288**, FBMSK `0xFF000000`
- XYOFFSET OFX/OFY **1792 / 1824** (12.4 → `/16`)
- SCISSOR full **512×448**
- TEST **0x5002D** (ATE GREATER 2)

Ctx1 stays closer to clear/display page **400** with TEST `0x20000`.

That split is documented in `04-mode-verdict-DISPFB-vs-FRAME.md`.
