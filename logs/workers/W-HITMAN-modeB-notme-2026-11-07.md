# Mode B diagnostic — `PS2_GS_NO_TME=1` (falsified)

**When:** 2026-11-07 ~19:08 local  
**Owner:** campaign-owner (permanent overnight resume)  
**Binary:** `build/native-a2116…/ps2run.exe` mtime 19:01 (post XYOFFSET-16 + NO_TME env support)  
**Run:** 180f `--frames-dir` → `logs/autonomous-pipeline/hitman-modeB-notme-20261107T190853/`

## Hypothesis

If empty/garbage texels + TME were emptying the draw page, stripping TME (vertex RGBA only) should raise present luminance.

## Result — **falsified**

| Frame | mean_lum | nonzero / 512×448 |
|-------|---------:|------------------:|
| 60 | ~0.048 | 404 (0.18%) |
| 120 | ~0.048 | 404 |
| 180 | ~0.097 | 439 (0.19%) |

Still near-black; matches prior harness `end_lum≈0.14` / present residual. Prim count ~21.7k (healthy activity, empty pixels).

## Already ruled out (same night)

| Probe | Verdict |
|-------|---------|
| `PS2_GS_NO_ATE` | no lum change (`06-ATE-off-experiment.md`) |
| `PS2_PRESENT_FRAME` | worse (`04-mode-verdict`) |
| Host 288→400 blit | premature (both pages empty) |
| PRIM 7→SPRITE | black quads (reverted to POINT+clear FST) |
| **`PS2_GS_NO_TME`** | **no lum change (this run)** |

## TRACE prim mix (`hitman-capture-xyoffset16-20261107/draws.tsv`, n=187)

| PRIM low3 | Count | Notes |
|-----------|------:|-------|
| 0 POINT | 131 | Dominant — sparse pixels even with high kick count |
| 7 undef | 33 | Many `0x07F`/`0x7FF` with TME; host remaps → POINT + clear FST |
| 2 line-strip | 21 | |
| 6 SPRITE | 1 | |
| TME set | 68 | |

Example type7 box after OFX: `x≈-0.5..256` (plausible) but `y≈-1824..325` (OFY=1824 with near-zero verts → still off-screen in Y for part of AABB).

## Next Mode B leads (ordered)

1. **Topology / kick packing** — POINT-dominant + type7→POINT explains ~1% nonzero; W-HITMAN `type7-fst` native rebuild in flight under `native-a2116` lock.
2. **Vertex/RGBA path when untextured** — clears may be black; non-clear batches may still have A≈0 or wrong XY after OFX.
3. **Re-verify XYOFFSET in TRACE boxes** — many `-1792…` boxes remain in named xyoffset16 capture; confirm with fresh TRACE after W-HITMAN native lands.
4. Host compose blit remains **deferred** until a draw page is non-empty.

## Locks

- Did not touch Hitman `web-*-next` (cmake/ninja live).
- Native lock briefly held for smoke; W-HITMAN reclaimed for type7-fst rebuild (`owner_pid=31216`).
