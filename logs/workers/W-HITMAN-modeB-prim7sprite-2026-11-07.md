# Mode B — `PS2_GS_PRIM7=sprite` + clear-FST (falsified)

**When:** 2026-11-07 ~19:19 local  
**Binary:** `native-a2116` ps2run mtime 19:14:39  
**Run:** `logs/autonomous-pipeline/hitman-modeB-prim7sprite-20261107T191942/`  
**Env:** `PS2_GS_PRIM7=sprite` (FST still cleared in gpu/raster for type7)

## Result — **falsified**

| Frame | mean_lum | nonzero |
|------:|---------:|--------:|
| 60/120/180 | ~0.0003–0.0004 | 404 / 404 / 439 |

**Bit-identical** `frame_00180.ppm` hash to NO_TME and type7→POINT+clearFST runs  
(`B7709B042B17FE5D…`). Prim count ~21753 / 180f — same ballpark as prior.

Topology remap of undefined PRIM7 does not change the present residual. Residual is not produced (or not altered) by the type7 path.

## Next

Measure **FBP288 under `PS2_GS_NO_ATE`** with capture (prior ATE-off experiment only scored present/DISPFB400).
