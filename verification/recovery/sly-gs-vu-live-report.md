# Sly GS/VU live diagnosis report

**Date:** 2026-11-06  
**Game:** Sly Cooper (USA) — gid `c0c4527037b6168660829a0eb13df1a3`  
**Scope:** Diagnosis only. No CNK. No Hitman/NFS edits. No commit.

Artifacts under `verification/recovery/sly-live-artifacts/` (and relocated mirrors in `logs/frames/sly-live-*`).

## What I ran

Same gameplay recipe as `sly-gameplay-final`:

- memcard `logs/sly-formatted.ps2` (copied per run)
- `--frames 1800` / `--frame-every 300`
- presses: `300:start`, `600/900/1200/1500:cross`
- `--boot cdrom0:\SCUS_971.98;1`
- env: `PS2_GPU_LOW_POWER=1`, `PS2_NO_DEINTERLACE=1`

| Run | Env | Result folder |
|-----|-----|---------------|
| GS both+compare | `PS2_GS=both` + `PS2_GS_COMPARE=1` | `sly-live-gscompare` |
| Strict VU | `PS2_VU_INTERPRET=1` + `PS2_VU_EXACT=1` + `PS2_GS=software` | `sly-live-vu-exact` |
| Separate GPU | default WebGPU | `sep-gpu` |
| Separate software | `PS2_GS=software` | `sep-soft` |

Also re-checked archived `logs/frames/sly-gpusoft` soft vs GPU @1800 and `logs/frames/sly-cap1800/draws.tsv`.

## What changed (fresh evidence)

### 1) Software GS vs WebGPU — **revised**

Parked note said GPU==software **0%**. That still holds for the **old** archived pair (`sly-gpusoft`, 4,061,228 prims).

On **today’s** first-map gameplay dump (formatted card, **4,865,142** prims, identical EE cycles `8,848,470,112`):

- Fresh **sep-gpu vs sep-soft** @frame 1800: **81,006 / 286,720 pixels differ (~28.25%)**, max channel delta 46.
- `PS2_GS=both` + compare logged 6 dump-time compares; 3 nonzero; worst was the same **81006** @1800.

**Buildings are still missing in both backends.** Software looks a bit cleaner (less black triangular noise); GPU adds extra garbage. So:

- Missing buildings = **shared** path (still true).
- Extra GPU noise = **new/secondary** WebGPU divergence on this scene (parked “0% always” is outdated for this card path).

### 2) Strict VU vs compiled — **buildings do not return**

| | Compiled (sep-gpu / gameplay-final recipe) | Strict VU interpret+exact |
|--|---------------------------------------------|---------------------------|
| Prims | 4,865,142 | 4,864,999 (−143) |
| PATH1 packed | 1,397,313 | 1,397,325 |
| PATH3 image | 498,797 | 498,797 |
| Cycles | 8,848,470,112 | 8,848,470,112 |

Frame 1800 still shows floating props / one roof bit / empty city void. Strict VU did **not** bring buildings back. VU1 compile-vs-interpret is a weak explanation for the missing environment.

### 3) PATH1 / PATH3 / STQ / CLUT — reconfirmed

From live run totals (same on soft/GPU):

- PATH1 packed ≈ **1.40M** (heavy VU1 → GIF geometry path)
- PATH3 image ≈ **498,797**; GPU `load_clut` ≈ **3,760**
- Capture `sly-cap1800/draws.tsv` (last frame window): textured prims almost all **FST=0 (STQ)**, **PSMT4/8**, **CSM=0**, **CLD=1**, **TCC=1**, **MMAG=1**, mostly **tristrip**; ATE on with AFAIL mostly RGB_ONLY.
- Largest non-fullscreen textured batch area still only ~**6.6k** px²; almost no building-sized batches in that capture.

STQ sticky-Q remains relevant for texture noise / invisible surfaces. PATH3/CLUT traffic is real and large. Missing buildings line up more with “meshes never become solid textured batches” / shared STQ+upload than with VU interpret mismatch.

## Ranked next fix (still no CNK)

1. **Shared GS STQ / perspective-correct texturing for strip-heavy FST=0** — still best bet for invisible walls/roofs that soft and GPU both miss.
2. **Find why soft≠GPU now (~28% on this scene)** — GPU-only noise/artifacts; compare decode/snapshot/CLUT upload on hottest TBPs while keeping soft as reference.
3. **PATH3 image ↔ TEX0 CLD / CLUT ordering** on hottest Sly TBPs (498k PATH3 images, thousands of `load_clut`).
4. **GIF/PATH1 mesh audit** — confirm whether building verts exist before GS (VU demoted after this differential).
5. Strip/ADC/Z only if GIF clearly has building meshes that GS drops.
6. FPS / decode tax stays separate from correctness.

## Bottom line

Strict VU: **no**. Soft vs GPU: **no longer 0% on this map**, but **both still lack buildings**. Next work stays on **shared GS texturing/STQ + PATH3/CLUT**, then GPU parity for the extra noise.
