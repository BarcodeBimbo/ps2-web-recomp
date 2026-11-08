# W-SLY platform — Sly Cooper shared GS (2026-11-07)

**Worker:** W-SLY  
**Game:** Sly Cooper USA — `c0c4527037b6168660829a0eb13df1a3`  
**Lane:** shared GS STQ / PATH3 / CLUT / missing buildings  
**Quarantine:** NOT CNK Alchemy; did not touch Hitman/CNK locks under `logs/locks/`  
**Heartbeat:** `logs/workers/W-SLY-platform-heartbeat.log`

## Seeds used

- `verification/recovery/sly-gs-vu-live-report.md`
- `verification/recovery/sly-asset-binwalk-report.md`
- `MASTER-CONTEXT.md` §11
- `verification/recovery/sly-geometry-texture-research-note.md`
- Capture: `logs/frames/sly-cap1800/draws.tsv`
- TheOnlyZac/sly1 (VU1/GIF/TEX0/CLUT) — reference only; **not** cloned

## Code changed?

**No.** Sticky-Q already present in shared path. No smallest safe fix had enough evidence that it would restore buildings without an unverified ship. RE plan below is the deliverable for the next implementation pass.

---

## Top root-cause hypothesis

**Building-scale FST=0 (STQ) tristrips are reaching GS, but shared texturing + ABE makes them invisible / sky-fogged — not “assets missing” and not VU interpret-vs-compile.**

Supporting evidence (this pass):

| Fact | Source |
|------|--------|
| Soft + GPU both miss buildings; strict VU (−143 prims) no restore | `sly-gs-vu-live-report.md` |
| Full ISO / Paris in RAM / millions of prims | `sly-asset-binwalk-report.md` |
| **Large textured batches exist** in last-frame capture (areas ≫ 6.6k px²; top ~5.5M / 479k / 275k) | `sly-cap1800/draws.tsv` re-measured |
| Those batches are **PRIM=0x07C** (tristrip, TME, FGE, ABE, FST=0), **PSMT4/8**, **CLD=1**, **CSM=0** | TEX0 decode this pass |
| Hottest candidate: TBP=`0x1480` TW=10 TH=7 PSMT4 CBP=`0x1402` CLD=1; PATH3 does 8×2 PSMCT32 uploads at DBP `0x1400`/`0x1401`/`0x1402` | draws.tsv transfers + TEX0 |
| Textured draws: **ATST=NEVER dominant** (`TEST=0x53001`, AFAIL=RGB_ONLY) + **ABE alpha=0x48** → `Cv = Cs*As/128 + Cd`; As≈0 or Cs≈0 ⇒ no visible change | histogram this pass |
| Sticky Q already in `write_packed` / `vertex`; qfix2 cut roof dark earlier | `gs.cpp`, geometry note |

Revised vs parked “almost no building-sized batches”: the **6.6k** figure was incomplete — building-scale strips **are** in the GIF→GS stream for this window; failure is **after** kick (sample / CLUT / blend / fog), still shared.

---

## Host fix-candidate map (`runtime/src/gs`)

| Priority | File | Function / site | Why |
|----------|------|-----------------|-----|
| **P0** | `gs.cpp` | `write_packed` case `0x2` (PACKED STQ); `write` case `0x01` (RGBAQ→`s.q`); `vertex` Q latch | Sticky Q present; **Q=0→`float::min()`** vs raster/gpu **Q=0→1.0** inconsistency (Inf UV risk). Only change if Q histogram shows exact zeros on building strips. |
| **P0** | `raster.cpp` | `plot` FST=0 `u=s/q`, `t=t/q`; `lerp3` S/T/Q; `attr_of` | Perspective = linear S,T,Q then divide (GS-correct). Prove Q/S distribution on TBP`1480` strips before “fixing” interpolation. |
| **P0** | `gpu/gs.wgsl` | triangle shade `at.s/q`; `vertex_tex` | Must stay bit-identical to soft for shared bugs; GPU-only ~28% noise is secondary. |
| **P1** | `gs.cpp` | `load_clut` (CSM=0, PSMT4/8, CLD=1) | Sly is CSM=0/CLD=1; PATH3 8×2→CBP matches. Dump CLUT[16] at CBP`1402` at first building draw — if A=0 across entries, ABE explains void. |
| **P1** | `gpu/gpu.cpp` | `load_clut` + `flush_image` ordering | Soft+GPU both wrong ⇒ unlikely sole cause; still verify PreOp hazard vs PATH3 image for soft≠GPU noise. |
| **P1** | `raster.cpp` / `gs.wgsl` | ABE in `plot` / shade; `make_setup` ATE/AFAIL | `alpha=0x48` + TCC + NEVER/RGB_ONLY: confirm As after TFX modulate on building texels. |
| **P2** | `raster.cpp` | `plot` FGE path; `vertex` fog/`s.fog` | PRIM `07C` has **FGE=1**. If per-vert F≈0, walls become `fogcol` (empty-city look). |
| **P2** | `gif.cpp` | PATH3 hold/`set_path3_masked` / `write_image` | Ordering already intended FIFO; audit only if CLUT dump shows stale CBP. |
| **P3** | `gs.cpp` | `kick` strip case 4 | Strip Q copy looks correct; revisit only if GIF has building verts that never kick. |

Do **not** open CNK Alchemy, Hitman WaitSema, or disc-fix for this lane.

---

## Precise RE plan (next implement pass)

### Step A — Prove building strip attributes (1 Paris gameplay frame)

1. Re-run capture recipe from live report (`--frames 1800`, formatted card, presses) with `PS2_GS=software` + existing capture, **or** extend capture to log per-vert **S,T,Q,RGBA,F** for draws whose screen∩scissor area ≥ 10k and TEX0 TBP in {`1480`,`15A0`,`1580`} family.
2. Instrument (temporary, behind env):  
   - `gs.cpp`:`vertex` / `write_packed` — histogram Q (zero / denorm / (0,1e-3] / normal / neg).  
   - `gs.cpp`:`load_clut` — on CLD≠0 && CBP∈ hotspot, dump 16/256 CLUT RGBA once per CBP per frame.  
3. Pass criteria: know whether building strips have (a) Q≈0, (b) CLUT A=0, (c) F=0 with FGE, (d) vertex RGB=0 under MODULATE.

### Step B — Smallest shared fix (pick **one** from A)

| If A shows… | Change only… |
|-------------|--------------|
| Exact Q=0 on building STQs | `gs.cpp`:`write_packed` STQ + `write` RGBAQ: Q=0 → **1.0f** (match `raster.cpp`:`plot` / `gs.wgsl`); remove `float::min()` |
| CLUT A all 0 / wrong at CBP while PATH3 wrote nonzero | `gs.cpp`:`load_clut` CSM0 4/8 layout vs upload BW; compare to GPU `gs.wgsl`:`load_clut` |
| F=0 + FGE with fogcol≈clear | Trace FOG / XYZF F in `write_packed` `0xA` / `0x4` — only fix if host drops F |
| Vertex RGB=0 + TFX modulate | Trace PACKED RGBA sticky vs STQ-only verts — host sticky already; likely guest/VU |

### Step C — Verify

1. Native soft + GPU @1800, same memcard recipe; visual: Paris buildings present.  
2. `PS2_GS=both` compare: buildings in both; note residual GPU noise separately.  
3. Do **not** claim fix without frame proof. No Hitman/CNK lock files.

### Step D — Secondary (after buildings visible)

- Soft≠GPU ~28% @1800: `gpu.cpp` decode/snapshot/CLUT vs soft on hottest TBPs.  
- FPS decode/snapshot tax stays out of this correctness lane.

---

## Explicit non-actions this shift

- No process kills  
- No Hitman / CNK lock touches  
- No Alchemy / disc-fix / WaitSema edits  
- No TheOnlyZac/sly1 tree clone  
- No GS code patch (evidence insufficient for an unverified building restore)

## Bottom line

**Hypothesis:** shared GS STQ+CLUT+ABE/FGE path draws building strips as invisible or fog-colored; assets and GIF meshes are present.  
**Code changed:** **no.**
