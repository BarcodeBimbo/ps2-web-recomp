# Sly GS/VU live differentials (1800f)

**Date:** 2026-11-06  
**Game:** Sly Cooper `c0c4527037b6168660829a0eb13df1a3`  
**Prior note:** `sly-geometry-texture-research-note.md`

## What ran

| Run | Settings | Exit | Prims (1800f) |
|-----|----------|------|----------------|
| GS both+compare | `PS2_GS=both`, `PS2_GS_COMPARE=1` | 0 | **4,865,142** |
| Strict VU + software | `PS2_GS=software`, `PS2_VU_INTERPRET=1`, `PS2_VU_EXACT=1` | 0 | **4,864,999** |

Logs: `logs/sly-live-gscompare/`, `logs/sly-live-vu-exact/`

## Findings (simple)

1. **GPU vs software is no longer 0% forever.** Early frames matched (0 differs); later frames diverge (~70k–81k of 286720 pixels). Shared path still dominates early; later gameplay exposes GPU/software drift — keep hunting shared *and* GPU-side once buildings are diagnosed.
2. **Strict VU did not restore missing buildings by prim count.** Prim totals match the compare run within ~150 (~4.86M both). PATH1/PATH3 tag counts nearly identical. Strict VU alone is **not** an instant “buildings back” fix at this smoke depth.
3. Still heavy PATH1 packed + PATH3 image — consistent with prior research.

## Ranked next (still no CNK)

1. Visually compare `frame_*.png` from both runs for building silhouette (counts alone don’t prove geometry).
2. Continue STQ/Q + PATH3/CLUT on hottest TBPs.
3. Only then treat late GPU diverge as a separate WebGPU bug.
