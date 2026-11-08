# Mode B — type7 → POINT + clear FST (falsified)

**When:** 2026-11-07 ~19:16–19:17 local  
**Owner:** W-HITMAN (replacement adopt)  
**Binary:** `build/native-a2116…/ps2run.exe` mtime **19:14:39** (type7-fst rebuild)  
**Runs:**
- present: `logs/autonomous-pipeline/hitman-modeB-type7fst-20261107T191649/`
- capture: `logs/hitman-capture-type7fst-180-2026-11-07/` (`W-HITMAN-type7fst-capture180.log`, 220f, **36455** prims)

## Hypothesis

Hitman `0x7FF` (type7+FST+TME) leaves UV=0 while ST/Q hold coords. Remap type7→POINT and clear FST so sticky ST/Q sampling fills texels.

## Result — **falsified** (no present / FBP288 improvement)

| Probe | frame 60 | frame 120 | frame 180 |
|-------|---------:|----------:|----------:|
| NO_TME present nz | 404 | 404 | 439 |
| type7-POINT+FST present nz | **404** | **404** | **439** |
| mean_lum (0–1, 512×448) | ~0.0003 | ~0.0003 | ~0.0004 |

Identical residual to NO_TME baseline (`logs/workers/W-HITMAN-modeB-notme-2026-11-07.md`).

### Capture display-region (512×448 crop)

| Page | nonzero | mean_lum |
|------|--------:|---------:|
| FBP 288 (`fbp120`) late | **0** | 0.0000 |
| FBP 400 (`fbp190`) late | **435** | ~0.0004 |

FBP288 still empty; present residual is FBP400 sparse junk only.

## Implication

POINT+clear-FST does not fill Mode B pages. Next probe: **`PS2_GS_PRIM7=sprite`** (topology) with same FST clear — env already in `gs.hpp::remap_undefined_prim`.

## Locks / builds

- Native rebuild finished; lock reused for PRIM7=sprite smoke.
- Web-next `cmake=29328` left LIVE (no kill).
