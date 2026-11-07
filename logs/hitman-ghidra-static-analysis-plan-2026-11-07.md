# Ghidra static-analysis plan — Hitman black canvas (2026-11-07)

**Scope:** Static only. Do **not** run the ELF or change runtime/web player behavior.  
**Game ELF:** `games/a2116d2ac08a7be4db4e8455ad58d2e5/disc/boot.elf` (confirmed **not** ps2-packer; normal stripped EE).  
**Lead references (priority order):**

1. https://www.psdevwiki.com/ps2/ (+ Memory Map / Graphics Synthesizer)
2. https://israpps.github.io/ps2tek/ (Thomas Edward Kyle / ps2tek — GS Frame/Z, Alpha, TEST, Register list)
3. Local SDK `E:\usr\local\sce` (`ee/include/eeregs.h`, `eestruct.h`, `libgraph.h`, GS Users Manual PDFs)
4. Community GitHub (`ps2dev/*`) — reference only, never as Sony SDK

**Harness symptom:** ~60 FPS, ~865k prims, GPU busy, **canvas black** after script-load ACL fix.

---

## Phase 0 — Fix Ghidra load (blocker)

**First-pass finding:** current `boot.elf` in Ghidra is `executable_format: Raw Binary`, `image_base: 00000000`, bogus entry at ELF header `00000000`. Real ELF: `e_entry=0x0010001C`, one `PT_LOAD` `@0x00100000`.

| Step | Action |
|------|--------|
| 0.1 | Close/discard raw import |
| 0.2 | Re-import as **ELF** (auto language `r5900:LE:32:default`), image base **`0x00100000`** |
| 0.3 | Run full auto-analysis; confirm entry function at **`0x0010001C`**, sections `.text`/`.vutext`/`.data`/`.rodata` |
| 0.4 | Snapshot function count after analysis (expect ~same order as now ~17k, but **correct VAs**) |

Until 0.x is done, treat addresses from the raw import as **provisional**.

---

## Phase 1 — Deep function recovery on Hitman boot ELF

**Goal:** Recover / name everything on the GS draw → clear → display path.

| Priority | Ghidra capability | Target |
|----------|-------------------|--------|
| 1.1 | Auto-analysis + **create function** at unresolved call targets | Fill gaps beyond early ~7.6k; chase thunks into `.text` |
| 1.2 | **String → xref → rename** | `sceGsSyncPath*`, `sceGsDefDispEnv*`, `sceGsPutDrawEnv*` (already present as strings) → rename wrappers to SDK names |
| 1.3 | **Instruction search** for privileged GS stores | `lui`/`sw`/`sd` to `0x12000000` (PMODE), `…70` (DISPFB1), `…90` (DISPFB2), `…A0` (DISPLAY2), `…E0` (BGCOLOR) |
| 1.4 | **GIF path** | Writers of `GIF_CTRL`/`GIF_MODE`/`D2_*`; PATH1/2/3 feed into GS |
| 1.5 | **Decompile + call graph** | From renamed `sceGsPutDrawEnv` / display-env setters → callers (boot menu / render loop) |
| 1.6 | **Data-type apply** | Import / hand-build `tGS_PMODE`, `tGS_DISPFB`, `sceGsFrame`, `sceGsAlpha`, `sceGsTest` from local `eestruct.h`/`libgraph.h` |
| 1.7 | **Batch decompile** hot GS cluster | Export pack for offline review |
| 1.8 | **Find dead / unreachable** after rebase | Confirm black-canvas path is live (xrefs from main loop) |

**Success criteria:** Named cluster: `SetGsCrt`/`sceGs*` display + draw env, FRAME/ZBUF/ALPHA/TEST GIF packets, clear sprites, flip/DISPFB update.

---

## Phase 2 — Cross-reference SDK + psdevwiki + ps2tek

| Source | Use for |
|--------|---------|
| **ps2tek** Alpha / FRAME / TEST pages | Exact ALPHA `(((A-B)*C)>>7)+D`, FRAME mask formula, dest-alpha bit rules (PSMCT32 bit7 / PSMCT16 / PSMCT24) |
| **ps2tek** Register list + Overview | GIF regs vs privileged PCRTC; draw buffer ≠ display buffer |
| **psdevwiki** Memory Map | `12000000h` privileged GS block; GIF/DMAC addresses |
| **psdevwiki** Graphics Synthesizer | Effects list (alpha blend/test, dest-alpha, FB mask, clears) — hypotheses only |
| **Local `eeregs.h`** | `GS_PMODE_EN1/EN2/MMOD/AMOD/ALP`, `GS_DISPFB*_FBP/FBW/PSM/DBX/DBY`, `GS_DISPLAY*` |
| **Local `eestruct.h`** | `SCE_GS_FRAME_1/2`, `SCE_GS_SET_ALPHA`, `GS_TEST_*`, `SCE_GS_FBA`, `SCE_GS_PABE` |
| **Local `libgraph.h`** | `sceGsDispEnv`, `sceGsFrame`, high-level API shape for renaming |

**Workflow:** For each recovered store/GIF tag, annotate with SDK macro name + ps2tek semantics in plate comments.

---

## Phase 3 — Map web harness → emulated GS (static architecture)

Not “run the game” — document the call chain from repo sources + ELF entry.

```
Chrome harness
  → panel :8620 /play/<id>/  (shell.html inject)
  → serve_player_js: gpu_upload_compat.js prefix + ps2web.js
  → Emscripten Module / WebGPU present (host/web.cpp, gs/gpu/*)
  → recompiled EE image (Hitman) entry 0x0010001C
  → libgraph/sceGs* / GIF → GS privileged regs (PMODE/DISPFB/DISPLAY)
  → host present() reads DISPFB of enabled circuit → canvas
```

| Step | Static artifact |
|------|-----------------|
| 3.1 | Document `serve_player_js` + shell halt path (already known) |
| 3.2 | Trace `host/web.cpp` → `ps2::present` / `gs::present(DisplayRegs)` |
| 3.3 | Match host circuit select `(pmode&2)?1:(pmode&1)?0` to SDK `EN1`/`EN2` |
| 3.4 | On ELF side: find writers of PMODE/DISPFB2/DISPLAY2 (Hitman uses circuit 2) |
| 3.5 | Diff: **FRAME FBP** (draw) vs **DISPFB FBP** (show) — classic black-screen mismatch |

---

## Phase 4 — Black-canvas hypotheses (static discrimination)

Ranked checks against ps2tek/psdevwiki + ELF + host (read-only):

| # | Hypothesis | What to look for statically |
|---|------------|------------------------------|
| A | **DISPFB ≠ FRAME** (draw offscreen, display empty/old) | Compare FBP in FRAME_1/2 packets vs DISPFB2.FBP at flip |
| B | **Wrong / disabled circuit** | PMODE EN1/EN2; Hitman sample already `PMODE=0x66` → EN2=1 (circuit 2) — host selects circuit 2 ✓; verify all flips stay on 2 |
| C | **FRAME mask kills RGB** | FRAME bits 32–63 all-ones or RGB-masked while prims still “count” |
| D | **Alpha / dest-alpha reject** | TEST ATE/DATE; AFAIL=RGB-only or neither; dest-alpha vs clear alpha bit |
| E | **Clear-color / BGCOLOR only** | Full-screen clear to 0; BGCOLOR; never opaque lit draws to displayed FBP |
| F | **Scissor / XYOFFSET** | SCISSOR empty or offset so draws miss displayed region |
| G | **PSM mismatch** | Draw PSMCT24/16 vs display interpret as 32 (or vice versa) |
| H | **Host present bug** (secondary) | `display()` forces `\| 0xFF000000`; unlikely pure black if RGB nonzero — check read FBP |

**Decision tree:** Prove A/B first (register xrefs), then D/E (TEST/ALPHA/clear sprites), then F/G.

---

## Phase 5 — Deliverables (still static)

1. Renamed GS function map (CSV / markdown)
2. Annotated PMODE/DISPFB/FRAME/ALPHA/TEST sites with SDK + ps2tek citations
3. Draw-vs-display FBP timeline (from decompilation, not a live trace)
4. Ranked black-canvas root-cause shortlist for a **later** runtime confirm (out of scope here)
5. Optional: Ghidra project notes / bookmarks only — no player patches in this track

---

## First-pass findings (already in hand)

### Load / packer
- **Not** ps2-packer; normal stripped EE ELF (`entry 0x0010001C`, 16 sections, `sceGs*` / `libgraph` strings).
- Current Ghidra DB is **Raw Binary @0** — **must rebase/reimport as ELF** before trusting addresses.
- Auto-analysis reached **~17,398 functions** (raw DB); early “~7600” was mid-analysis, not packing.

### Display path (provisional raw-DB decomp `FUN_0018ff4c`)
- Writes **`REG_GS_PMODE = 0x66`**, **`DISPFB2`**, **`DISPLAY2`**, **`SMODE2`**.
- Decode with local `eeregs.h`: **EN1=0, EN2=1** → output circuit **2**; MMOD/AMOD set; ALP=0.
- Host `gs.cpp` present: `(pmode&2)?1:(pmode&1)?0` → circuit **1** index = DISPFB2 — **aligned** with Hitman. Black canvas less likely “wrong circuit,” more likely **FBP/mask/alpha/clear**.

### Strings (GS SDK surface)
Present: `sceGsSyncPath:*`, `sceGsDefDispEnv:Not support displaymode…`, `sceGsPutDrawEnv: DMA Ch.2…`  
→ Recovered libgraph display/draw-env code is in the binary; rename via xrefs after ELF reimport.

### Local SDK (authoritative)
- `eeregs.h`: full PMODE/DISPFB/DISPLAY/BGCOLOR bitfields.
- `eestruct.h`: FRAME/ALPHA/TEST/FBA/PABE register IDs + setters.
- `libgraph.h`: `sceGsDispEnv`, frame/zbuf/scissor structs; alpha-test enums.

### Priority-site semantics to apply next
- **Draw buffer (FRAME)** vs **display buffer (DISPFB)** are independent (ps2tek + wiki).
- **FRAME mask:** `final = (final & ~mask) | (frame & mask)` — can preserve black RGB.
- **Dest alpha test:** PSMCT32 uses alpha **bit 7**; wrong clear alpha → all pixels fail DATE.
- **Alpha blend:** fixed `(((A-B)*C)>>7)+D` — can force black if A/B/C/D mis-set with FIX.
- ps2tek notes exotic **clears** (double-half, interleaved, VIS) — Hitman may use engine-specific clear; identify sprite clears writing FBP.

### Web shim (architecture only)
- `serve_player_js` GPU compat prefix is host-only; unrelated to EE black canvas once script loads.
- Black canvas is **post-boot GS present** problem.

---

## Suggested immediate next actions (caller can reorder)

1. **Approve Phase 0** — reimport Hitman `boot.elf` as ELF @ `0x00100000` (static project hygiene).
2. Run Phase 1.2–1.3 — name `sceGsPutDrawEnv` / DefDispEnv; list all DISPFB2/FRAME writers.
3. Phase 4.A — static draw-vs-display FBP compare (highest EV for black canvas).
4. Keep psdevwiki + ps2tek open as the naming/semantics bible; local SDK for exact macros.
