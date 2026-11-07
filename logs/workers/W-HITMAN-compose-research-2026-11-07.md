# W-HITMAN compose research — DISPFB 400 vs FRAME 288 (Mode B)

**Date:** 2026-11-07  
**Game:** `a2116d2ac08a7be4db4e8455ad58d2e5` (Hitman BM)  
**Scope:** read-only — no runtime edits, rebuilds, process kills, or build-tree writes  
**Checkbox:** `DISPFB vs FRAME page split (400 vs 288): compose blit if raster non-empty but present black`

---

## Recommended fix: **(B)**

Fix the broken GS draw / sprite / textured path so pixels actually land in VRAM.  
Do **not** ship a host 288→400 blit or present-source swap first.

| Option | Verdict | Why |
|--------|---------|-----|
| **(A)** host VRAM blit 288→400 before present | **Reject (premature)** | Draw page is already near-empty at capture/present; blit would copy blackness. No L2L BITBLT 288→400 in traces. |
| **(B)** fix broken GS sprite/tex (and related write path) | **Recommend** | Draws target **both** pages; display-region residual is ~0.1% nonzero on **both**; page-400 batches use TME/ABE (compose-like textured draws) that leave sparse junk. |
| **(C)** present hybrid / `PS2_PRESENT_FRAME` | **Reject (falsified)** | Opt-in FRAME present made lum **worse** (GPU 288 empty; 400 had sparse residual). |
| **(D)** other | **Secondary only** | Keep present on DISPFB **400**; treat “compose blit” checkbox as blocked until raster non-empty. |

---

## Exact code locations (for the next implementer)

### Keep as-is (present source)

- `runtime/src/gs/gs.cpp` — `resolve_present_source` (~L1225–1271): default DISPFB; `PS2_PRESENT_FRAME` opt-in already documented as regression.
- `runtime/src/gs/gs.cpp` — `present` / `display` / `copy_frame` (~L1278–1360): call `resolve_present_source` then `gpu::present` / readback.
- `runtime/src/gs/gpu/gpu.cpp` — `present(const DisplaySource &)` (~L1840): samples `src.fbp` (DISPFB page 400 × 32).

### Primary fix surface — **(B)**

| Area | File:function / region | Why it matters for Hitman |
|------|------------------------|---------------------------|
| CPU sprite raster | `runtime/src/gs/raster.cpp` — `sprite` (~L416–438), `draw` case 6 (~L469) | Clear tiles + any SPRITE compose land here on CPU path. |
| CPU fragment gate | `runtime/src/gs/raster.cpp` — ATE switch (~L203–208), setup from TEST (~L296–298) | Ctx0 live TEST `0x5002D` = ATE **GREATER** AREF **2**. |
| GPU fragment / tex | `runtime/src/gs/gpu/gs.wgsl` — `F_TME` sample (~L754+), `F_ATE` (~L822–848) | Page-400 draws: **TME≈51 / ABE≈39** of 108 in frame-180 TSV; garbage UVs → empty/near-black texels. |
| GPU local copy (not used by Hitman today) | `runtime/src/gs/gpu/gpu.cpp` — `local_copy` (~L1534); `gs.cpp` TRXDIR==2 (~L897–904) | Host already implements L2L; traces never fire TRXDIR=2 for this title. |
| Host→local upload | `runtime/src/gs/gpu/gpu.cpp` — `image_begin` / `image_data` (~L1503+) | All captured transfers are **dir 0**; none touch DBP near FBP 288/400. |

### Deferred **(A)** only after 288 is non-empty

If display-region mean luma on `fbp120` rises but present of DISPFB 400 stays black:

1. Add an explicit page copy (reuse `gpu::local_copy` param shape) **immediately before** `gpu::present` in `gs.cpp::present`, gated on `disp_fbp==400 && frame0==288` (Hitman triad).
2. Or: call into the same copy path from a Hitman-only env (e.g. `PS2_COMPOSE_FRAME_TO_DISPFB`) — **not** as default.

Do **not** re-enable default FRAME follow in `resolve_present_source`.

---

## 1) Where do draws land? (288, 400, both, neither)

### TRACE present triad (steady state)

From `logs/hitman-caller-readable/01-TRACE-highlights.txt` / `04-mode-verdict-DISPFB-vs-FRAME.md`:

```
present fb: dispfb=400 frame0=288 frame1=400 last_ctx=0 fbw=8 psm=0
```

- **DISPFB2** latched once at CRT init → page **400** (`0x1190`).
- **FRAME ctx0** (primary draw, `last_ctx=0`) → page **288**.
- **FRAME ctx1** → page **400** (same as DISPFB).

### GIF draw counts (frame-180 capture TSV)

Source: `logs/hitman-caller-readable/01c-TRACE-draws-frame180.tsv`

| Target FBP | Ctx | Draw batches | Dominant TEST | Notes |
|------------|-----|-------------:|---------------|-------|
| **288** (`…80120`) | 0 | **263** | `0x5002D` (ATE GREATER 2) | TEX0 TBP=0 on all; untextured draw path |
| **400** (`…80190`) | 1 | **108** | `0x20000` (ATE off) | ALPHA `0x800000002A`; many TME/ABE |

**Verdict:** draws are **issued to both** pages (not “288 only” or “neither”).

Post-XYOFFSET capture (`logs/hitman-capture-post-xyoffset-2026-11-07/draws.tsv`, owner pivot): **1880 → 288**, **890 → 400** — same dual-target shape at larger N.

### PPM / luminance (pixels that actually stick)

Capture dumps: `logs/autonomous-pipeline/capture-post-xyoffset/` (`*_fbp120_psm00.ppm` = 288, `*_fbp190_psm00.ppm` = 400).

Display crop **512×448** (late samples `000070`–`000074`):

| Page | mean luma | nonzero pixels |
|------|----------:|---------------:|
| 288 (`fbp120`) | **~0.124** | **223 / 229376 (0.097%)** |
| 400 (`fbp190`) | **~0.111** | **435 / 229376 (0.190%)** |

Full-page (~512×2048) means ~0.9 with ~10k nonzero — still sparse; matches harness **end_lum≈0.14** when presenting 400.

**Verdict on VRAM content:** both pages are **nearly empty** (sparse residual). Raster activity ≠ filled framebuffer. Page 400 is slightly *more* nonzero than 288 in the display window — consistent with “present DISPFB” keeping the only residual, and with `PS2_PRESENT_FRAME=1` making dumps worse.

### `PS2_PRESENT_FRAME=1` experiment (already done)

`04-mode-verdict-DISPFB-vs-FRAME.md`: auto-present FRAME ctx0/288 → PPM lum **0.11 → 0.0** (“GPU page 288 empty at present; 400 had sparse residual”). Reverted as default; opt-in env retained in `resolve_present_source`.

### BITBLT / local copy

Frame-180 + post-XYOFFSET transfers: **TRXDIR histogram = {0: …} only** (HOST→LOCAL).  
**Zero** transfers with SBP/DBP near page bases `0x2400` (288×32) or `0x3200` (400×32).

**Verdict:** Hitman is **not** composing 288→400 via GS local-to-local BITBLT in these captures. Any draw→display “compose” must be **textured GIF draws** onto FRAME/DISPFB page 400 (or is simply missing because source texels/fragments die).

---

## 2) ELF / Ghidra notes — compose / sprite blit?

Program: `hitman_boot.elf` (Ghidra, image base `0x00100000`). Docs: `logs/hitman-caller-readable/05-ghidra-decompiled-gs-init.md`, `07-PMODE-DISPFB2-FRAME-writers.md`.

| VA / symbol | Role | Compose? |
|-------------|------|----------|
| `FUN_0028ef4c` @ `0x0028ef4c` | CRT: `PMODE=0x66`, **one-shot** `DISPFB2` from `*(disp+0xd4)>>11 \| 0x1000`, DISPLAY2 | Sets display page; **no flip updates** later in boot ELF |
| `FUN_0028f2c4` @ `0x0028f2c4` | Initial GIF draw env (FRAME/ZBUF/TEST/…) | Draw setup; live FRAME later → 288 |
| `FUN_0028f7fc` @ `0x0028f7fc` | Clear using FBP from `+0xd4` → **display page 400** | Calls `FUN_00296f84` sprite **clear tiles** with color from caller (`FUN_00291710` passes **0** = black) — **not** a copy from 288 |
| `FUN_0028f6dc` | Sibling clear using `+0xc4` (other page → **288**) | Black clear of draw page |
| `FUN_00296f84` @ `0x00296f84` | Tile loop → `FUN_00296bd0` sprite packets | Clear/fill helper only |
| `FUN_00291710` | Wires CRT + both clears | Init path |

**No Ghidra evidence** in the CRT/init cluster of a dedicated “blit draw page → DISPFB page” routine. Double-buffer pages exist (`+0xd4` / `+0xc4`); DISPFB stays on `+0xd4`’s FBP while gameplay GIF retargets FRAME to the other page.

Live “compose-like” behavior is therefore expected in **engine GIF** (ctx1 / FBP 400 / TME+ABE), not in the one-shot CRT writers — and those batches currently leave only sparse residual.

---

## 3) Option analysis (minimal host fix)

### Why not (A) now

1. Plan gate was “compose if **raster non-empty** but present black.” Display-region PPMs show raster **is empty** on 288 (~0.1% nonzero).
2. Presenting/blitting 288 was already tried via `PS2_PRESENT_FRAME` → worse.
3. No TRXDIR=2 288→400 traffic to emulate; inventing a host blit diverges from observed EE/GS behavior until writes work.

### Why (B)

1. Dual-target draws prove the Mode B **page split is real**, but blackness is **write failure / reject / bad tex**, not merely wrong present FBP.
2. Ctx0 ATE GREATER 2 + untextured batches; ctx1 textured+blend onto 400 — both paths need correct GPU/CPU fragment and sampling behavior (`gs.wgsl` / `raster.cpp`).
3. Owner pivot (`logs/workers/W-OWNER-hitman-compose-pivot-2026-11-07.md`) independently ordered: PRIM topology → ATE/UV → **only then** host compose.

### Why not (C)

Already falsified by Mode B present experiment; hybrid max(288,400) still ≈ black.

### (D) operational note

Leave `resolve_present_source` on DISPFB. Treat master-plan compose checkbox as **blocked on non-empty draw page**, then revisit (A) as a thin gated copy.

---

## 4) Evidence index

| Artifact | Path |
|----------|------|
| Mode B verdict | `logs/hitman-caller-readable/04-mode-verdict-DISPFB-vs-FRAME.md` |
| Ghidra CRT/clear | `logs/hitman-caller-readable/05-ghidra-decompiled-gs-init.md` |
| Writer catalog | `logs/hitman-caller-readable/07-PMODE-DISPFB2-FRAME-writers.md` |
| ATE decode | `logs/hitman-caller-readable/03-alpha-test-ATE-GREATER.md` |
| Frame-180 TSV | `logs/hitman-caller-readable/01c-TRACE-draws-frame180.tsv` |
| TRACE highlights | `logs/hitman-caller-readable/01-TRACE-highlights.txt` |
| Post-XYOFFSET PPMs | `logs/autonomous-pipeline/capture-post-xyoffset/*_fbp{120,190}_*.ppm` |
| Present source | `runtime/src/gs/gs.cpp` `resolve_present_source` |
| Owner pivot (agree) | `logs/workers/W-OWNER-hitman-compose-pivot-2026-11-07.md` |

---

## Bottom line

**Recommend (B).** Draws land in **both** GPU pages 288 and 400; neither holds a usable image. ELF clear sprites black both pages; DISPFB never flips; no L2L compose blit observed. Fix textured/sprite (and ATE) writes in `raster.cpp` + `gs.wgsl` (+ GPU batch path). Revisit **(A)** only after `fbp120` display-region luma is non-trivial while DISPFB 400 stays dark.

*Worker: W-HITMAN compose research — read-only — 2026-11-07*
