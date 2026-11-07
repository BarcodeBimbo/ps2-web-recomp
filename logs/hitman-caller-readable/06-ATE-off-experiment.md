# Experiment — `PS2_GS_NO_ATE=1` (ATE forced off)

**When:** 2026-11-07, after packing this folder (loop continued).

## Change

Host clears bit 0 of every GIF `TEST_1` / `TEST_2` write when `PS2_GS_NO_ATE` is set (`runtime/src/gs/gs.cpp`).

## TRACE proof it engaged

```
drawenv0 … test=0x5002C …   # was 0x5002D; ATE bit cleared
```

## Result

| Metric | Baseline (ATE on) | ATE forced off |
|--------|-------------------|----------------|
| Present FBP triad | dispfb=400, frame0=288, frame1=400 | same |
| PPM lum @ 200/400 | ~0.11 | **0.1103** |
| Nonzero pixels | ~434 | **434** |

**Verdict:** Alpha-test reject is **real in the ELF/live state** but **not sufficient** to explain the nearly-black pages — disabling ATE did not brighten the framebuffer. Next suspects: XYOFFSET/negative draw boxes, compose blit to page 400, or textured draws with empty texels.

Raw log: `06-TRACE-PS2_GS_NO_ATE-run.log`  
Frames: `ate-off-frames/`
