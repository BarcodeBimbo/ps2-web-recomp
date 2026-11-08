# W-SLY Step A evidence — Sly STQ/PATH3/CLUT (2026-11-07 replacement)

**Worker:** W-SLY (replacement after stale ~19:03 heartbeat)  
**Game:** `c0c4527037b6168660829a0eb13df1a3` Sly Cooper USA  
**Lock:** `logs/locks/native-c0c452…` (diag only; no Hitman/NFS/CNK steal)  
**Quarantine:** NOT CNK Alchemy  

## Seeds / peer merge

- Peer `logs/workers/W-SLY-platform-2026-11-07.md` parked **no code change**; RE plan Step A–D.
- This pass **advances Step A** with a corrected `draws.tsv` parse (negative screen boxes) + code-path audit + diagnostic run.

## Capture re-measure (`logs/frames/sly-cap1800/draws.tsv`)

Parser: `logs/workers/_w_sly_parse_cap.py` (negative-box regex fix).

| Metric | Value |
|--------|-------|
| Textured draws (last vblank window) | 284 (282 FST=0 / 2 FST=1) |
| Dominant textured prim | `07C` tristrip TME+FGE+ABE, FST=0 |
| Building-scale top batch | **area ≈ 5,563,940** px², prims=24, TBP=`0x1480`, CBP=`0x1402`, PSMT4, TW=10 TH=7, CLD=1 CSM=0 TCC=1 TFX=0 |
| UV bbox (post S/Q) | `376.5,-92.6` → `1960.0,144.3` (finite — **not** Inf from Q≈0) |
| TEST | `0x317E1` → ATE=1 ATST=**NEVER** AFAIL=**FB_ONLY** AREF=126 |
| ALPHA | `0x44` → `(Cs−Cd)*As/128 + Cd` |
| PATH3 ahead of draws | CLUT 8×2 PSMCT32 → DBP `0x1400/1401/1402`; tex 1024×128 PSMT4 → `0x1480`; plus `0x1580`/`0x15A0` |

**Conclusion vs parked “6.6k max”:** building-scale FST=0 strips **are** in the GIF→GS stream. Failure is after kick (sample / CLUT / ABE / FGE), shared soft+GPU.

## Code map (shared GS — sticky-Q already present)

| Site | Behavior | Step A note |
|------|----------|-------------|
| `gs.cpp` `write_packed` STQ | sticky `s.q`; **Q==0 → `float::min()`** | Downstream `plot`/`wgsl` only remap **exact 0.0 → 1.0**, so min **bypasses** the guard → Inf/huge UV if exact zero ever arrives. Building top batch UVs finite ⇒ not this batch’s smoking gun. |
| `gs.cpp` `vertex` | `v.q = s.q` sticky | OK |
| `raster.cpp` `lerp3` + `plot` | lerp S,T,Q then `u=s/q` | GS-correct perspective |
| `gpu/gs.wgsl` triangle | same divide | Must stay matched to soft |
| `gpu.cpp` `texel_rect` | rejects `!(q > 0)` | Cache/decode planning only (emit_all), not a soft skip |
| `gs.cpp` `load_clut` CSM0 PSMT4 | 8×2 layout; CBP1402 matches PATH3 8×2 | Layout OK for hotspot; **content** (A=0?) unproven without dump |
| `gif.cpp` PATH3 hold/mask | FIFO hold under MSKPATH3 | No edit; audit only if CLUT dump stale |

## Ranked remaining hypotheses (after Step A)

1. **ABE + texture/CLUT alpha ≈ 0** on TBP1480 family → `Cv≈Cd` (invisible) despite FB_ONLY AFAIL still “writing.”
2. **FGE + per-vert F≈0** → full fogcol (empty-city / sky void). fogcol writes are heavy in prior run stats (`0x3D` ~265k).
3. **STQ Q distribution** on other strips (exact 0 / denorm) — fix Q0→1.0 for host consistency once histogram proves hits; not proven on the 5.56M batch.
4. Soft≠GPU ~28% noise — secondary after buildings visible.

## Diagnostic in flight

- `PS2_GS=software` + `PS2_GS_NO_TME=1`, 900f, formatted card copy, presses 300:start / 600+900:cross  
- Out: `logs/frames/sly-diag-notme-900/`, logs `logs/workers/W-SLY-diag-notme-900*.log`  
- **Pass criteria:** if untextured vertex colors show building-scale meshes → texturing/CLUT/ABE; if still void → fog/vert/cull side.

## Code changed this shift

**Not yet.** Shared `runtime/src/gs/*` left untouched while Hitman/NFS/CNK cmake/ninja are live on the same tree. Candidate when unlocked:

- `write_packed` STQ + RGBAQ: Q==0 → **1.0f** (match raster/wgsl; remove `float::min()` bypass).

## Checkbox

Master-plan §2d Sly — **still open** (no visual verify of buildings restored).
