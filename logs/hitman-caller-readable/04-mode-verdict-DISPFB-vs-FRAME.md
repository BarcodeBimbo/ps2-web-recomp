# Hitman DISPLAY2 width-mismatch mode verdict — 2026-11-07

## Modes (from graph `02_display_width_decode.png`)

| Mode | Claim | Verdict |
|------|--------|---------|
| **A** | MAGH unread/zero → host width 2560 | **ELIMINATED** |
| **B** | DISPFB2 `\| 0x1000` stub; wrong display *area* (FBP/FBW) vs FRAME | **LEADING — acted on** |
| **C** | Early DISPLAY2 → width/height 0 → present early-return | **ELIMINATED** (steady state) |

## ELF evidence (`FUN_0028ef4c` @ `0028ef4c`)

Asm path (NTSC-ish `param_2==2` defaults used by 512×448 dumps):

- `s4=5` → `MAGH = s4-1 = 4`, `DW = s4<<9 - 1 = 2559`
- `DISPLAY2` built with `dsll … 0x17` (MAGH) and `dsll32` (DW) — **not** left zero
- Host decode: `width = (DW+1)/magh = 2560/5 = **512**`
- `DISPFB2 = (*(obj+0xd4) >> 11) \| 0x1000` → FBW=8 (512px), **PSM=0**, FBP from alloc
- **Only** privileged `DISPFB2` store found in boot ELF (`ori …,0x90` after `lui …,0x1200` at `0028f098`); no flip updates DISPFB later

## Runtime evidence eliminating A/C

- Native PPMs under `games/a2116…/shots*` are **512×448** with near-zero luminance → present/copy_frame **did** decode non-zero width/height (not A, not C).
- Graph 03 `display=0` is **not** Mode C: headless `--frames-dir` has no swapchain, so `gpu::present` never runs; raster still runs. Web harness still presents via WebGPU while canvas stays black.

## Why Mode B

Draw path writes GIF `FRAME` (possibly double-buffered pages at `+0xd4` / `+0xc4`). Display path samples **stale DISPFB2** set once at CRT init. Correct dimensions + empty page ⇒ black canvas with huge prim counts.

## Runtime check result (native 600f, `PS2_TRACE_DISPLAY=1`)

```
dispfb2 0x1190  → FBP=0x190=400, FBW=8, PSM=0
display2 0x1BF9FF0203227C → host width=512 height=448 (Mode A/C dead)
present fb: dispfb=400 frame0=288 frame1=400 last_ctx=0 fbw=8 psm=0
```

**Mode B page split confirmed:** DISPFB latched to page **400** (= FRAME ctx1); last FRAME write / primary draw page is **288** (ctx0). Width path healthy.

## Fix attempts

1. **Auto-present last FRAME (ctx0/288)** when it ≠ DISPFB — *activated* (`mode-B present` logs) but PPM luminance went **0.11 → 0.0** (GPU page 288 empty at present; 400 had sparse residual). **Reverted as default.**
2. **Kept:** TRACE triad + opt-in `PS2_PRESENT_FRAME=1` for experiments.

## Next loop (not width A/C)

Why raster with FRAME0=288 leaves GPU page 288 empty while DISPFB=400 stays nearly black — likely draw→front compose (sprite/tex blit) failing, or TEST/ALPHA/clear, not DISPLAY2 width decode.
