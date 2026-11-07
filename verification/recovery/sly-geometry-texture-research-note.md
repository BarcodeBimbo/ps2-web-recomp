# Sly Cooper geometry / texture research note (parked)

**Date:** 2026-11-06  
**Game:** Sly Cooper (USA) — gid `c0c4527037b6168660829a0eb13df1a3`  
**Status:** Research only — **no code changes**. Quarantined from CNK Alchemy / Hitman WaitSema.  
**Source worker:** [Sly research](642b4234-a4ec-482a-aba0-8a003a1f7ddd)

## Executive summary

Sly is **not** a dead renderer: explore ends with **~11.8M** primitives / 3600f, GIF **PATH1 packed ≈3.58M**, **PATH3 image ≈510k**, heavy VIF1 MSCAL/UNPACK. Prior session notes **GPU==software 0% diff** on broken frames (`verification/host-session-2026-11-06-final.json`), so the fault is in the **shared GS path** (`gs.cpp` vertex/STQ/CLUT/upload + shared setup), not a WebGPU-only shader fork. STQ sticky-Q already landed and cut roof dark pixels; gameplay still shows missing/collapsed first-map buildings with residual texture noise. FPS pressure lines up with gameplay **decode ≈65–100/frame** + **snapshot ≈21–31/frame** and clip/FINISH/pacing work — not Alchemy/CNK.

## Geometry / texture hypotheses (ranked)

1. **Indexed texture + STQ/Q** (partially mitigated; still primary for noise / invisible surfaces)  
   - Cap: almost all textured prims **PSMT4/PSMT8**, **FST=0**, TCC=1, MMAG=1 (`logs/sly-cap1800`).  
   - Sticky Q in `runtime/src/gs/gs.cpp` (`write_packed` / `vertex`); divide in `gs.wgsl` / `raster.cpp`.  
   - Progress: roof dark **0.148→0.0** @1800 after qfix2; residual noise still in `logs/sly-gameplay*/frame_01800.png`.  
   - CSM2 CLUT fix exists but this capture is **CSM=0** for all textured draws.

2. **VU1 / clip / microprogram dropping environment meshes** (best fit for “buildings gone, props remain”)  
   - PATH1-heavy; many VU1 blobs under `games/.../vu1/`.  
   - Largest textured tris only ~6k px²; **269** area&lt;1 batches — meshes missing or degenerate.  
   - Docs: Menu → VU reference + software GS for missing geometry. Clip-latency (`701d64b` / `e1e049b`) title-sensitive.

3. **PATH3 image / CLUT upload ordering vs TEX0 CLD**  
   - Explore: PATH3 image **510,592**, `load_clut` **12,194**.  
   - Shared-path hazard would match GPU==software if CPU reads same VRAM.

4. **Vertex / PRIM topology** — strips dominate; heavy XYZ3 vs XYZ2; ADC in strip window.

5. **Z / scissor / ATE** — weaker alone; AFAIL=ZB_ONLY rare.

6. **Incomplete assets** — **unlikely** (health ok, full ISO, high prim counts).

## FPS regression (host cost, not EE clock)

| Run | prims/f | decode/f | snapshot/f | raster/f |
|-----|---------|----------|------------|----------|
| audit 900f | 218 | 0 | 90 | 154 |
| sly-gameplay 1800f | 2256 | 65 | 21 | 34 |
| explore 3600f | 3282 | 101 | 31 | 54 |

EE `cyc/f ≈ 4.915e6` stays NTSC-nominal. Likely: GS decode/snapshot tax; VU clip-flag stalls; GS FINISH ack queue; host pacing; IPU/FMV stretches. Local Windows tree squashed (`e99ef4a`) — no clean GS bisect.

## Differentials to prove (when unparked)

1. Same save/frame: `PS2_GS=software` vs WebGPU (+ compare). Expect 0% → stay on shared path.  
2. Strict VU (`PS2_VU_INTERPRET=1` + `PS2_VU_EXACT=1`) vs compiled VU1.  
3. STQ/Q histogram on one gameplay frame.  
4. PATH3/CLUT inspect hottest TBPs; optional `PS2_DECODE=0`.  
5. ATE/AFAIL / Z checks.  
6. FPS isolate via `PS2_GPU_PROFILE` + decode off; optional upstream bisect.

## Recommended fix order (still no implementation)

1. Confirm shared-path vs VU (software GS + strict VU) on first Paris map.  
2. Finish STQ/Q + perspective for strip-heavy FST=0.  
3. Audit PATH3 ↔ CLUT ↔ TEX0 for hottest Sly TBPs.  
4. VU1 clip / XGKICK if strict VU restores buildings.  
5. Strip/ADC/Z only if meshes exist in GIF but not on screen.  
6. FPS: profile decode/snapshot; keep pacing separate from correctness.

## Open / unverified

- No interactive paced FPS for “when it was solid.”  
- GPU==software 0% from session notes, not re-measured this pass.  
- Cap may not include exact missing-building draws if VU culled earlier.  
- No link to CNK Alchemy null-bind or Hitman WaitSema — quarantine holds.
