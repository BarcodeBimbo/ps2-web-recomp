# Hitman black-canvas — owner pivot (2026-11-07 ~23:47Z)

## Checkbox started
`DISPFB vs FRAME page split (400 vs 288): compose blit if raster non-empty but present black`

## Fresh evidence (post-XYOFFSET capture)

| Page | Sample PPMs | mean_lum | nonzero |
|------|-------------|----------|---------|
| FBP 288 (`fbp120`) | early + late | ~0.85–0.93 | ~0.8–0.9% |
| FBP 400 (`fbp190`) | early + late | ~0.85–0.93 | ~0.8–0.9% |

Source: `logs/hitman-capture-post-xyoffset-2026-11-07/*.ppm` via `_tmp_analyze_draws.py`.

**Verdict:** Compose/present-source swap alone **cannot** fix Chrome canvas. Both draw and display pages are already nearly empty at capture time (GPU download path). Prior `PS2_PRESENT_FRAME=1` regression (288 empty) is consistent with this.

## draws.tsv shape (vblank 180)

- 2770 batches: **1880 → FBP 288**, **890 → FBP 400**
- TEST: **1859× `0x5002D`** (ATE GREATER 2), **890× `0x20000`** (clear/no ATE)
- PRIM low types heavily **0 (POINT)** batches (~947); **TME on** ~916; **big/garbage UV** ~467
- Area boxes OK for ~1916 batches (points can still inflate AABB)

## Next root-cause lanes (ordered)

1. **PRIM type / topology** — if meshes land as points, sparse pixels match ~1% nonzero.
2. **ATE + tex alpha / broken ST/UV** — garbage UV batches + AREF=2.
3. **Only after a non-empty draw page:** host compose 288→400 / luminance-pick present.

## Locks / workers

- Hitman web lock: `logs/locks/web-a2116d2ac08a7be4db4e8455ad58d2e5.lock` (campaign-owner-fresh)
- W-NFS: background research (no Hitman tree writes)
- W-HITMAN compose research: read-only explore
