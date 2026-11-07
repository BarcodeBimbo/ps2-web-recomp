# W-HITMAN worker report — 2026-11-07

**Game:** `a2116d2ac08a7be4db4e8455ad58d2e5` (Hitman — Blood Money USA)  
**Disc:** `games/a2116d2ac08a7be4db4e8455ad58d2e5/disc.iso`  
**Mandate:** Four-layer GS foundation; no CNK Alchemy patches.

---

## Executed

| Action | Log / artifact |
|--------|----------------|
| Read campaign handoff | `logs/call-log-2026-11-07.md`, `logs/master-campaign-plan-2026-11-07.md` §1, `logs/hitman-caller-readable/`, `logs/hitman-ghidra-static-analysis-plan-2026-11-07.md` |
| **Layer 3** — post-XYOFFSET `PS2_CAPTURE` smoke | `logs/autonomous-pipeline/hitman-capture-180f-post-xyoffset.log` |
| Capture TSV + PPM dumps | `logs/hitman-capture-post-xyoffset-2026-11-07/draws.tsv` (2770 draw rows, 1131 images) |
| Draw-box analysis (Python) | **2018/2770** intersect x **0..511**; **1822** intersect 512×448; 752 fully off-screen x |
| Native 400f verify (`disc.iso`) | `logs/autonomous-pipeline/a2116d2ac08a7be4db4e8455ad58d2e5-400f-20261107T153624Z.log` — **97,531** prims, matrix **pass** |
| `autonomous_verify.py --json` | `logs/autonomous-pipeline/summary-20261107T153650Z.json` |
| **Layer 4** — Ghidra ELF load + switch | MCP `load_program` → `hitman_boot.elf`; `switch_program`; **ELF** `image_base=0x00100000`, entry **`0x0010001C`**, 14733 functions |
| **Layer 1** — `FUN_0028f7fc` decompile | Ghidra MCP @ `0028f7fc`: clear FBP `*(disp+0xd4)>>11`, color `param_2` |
| PPM mean luma @ frame ~180 | Capture PPMs ~**0.32–0.39%** (still near-black; threshold harness **8.0**) |
| Web rebuild (queued / in flight) | Panel status **`building`**; `build/web-a2116d2ac08a7be4db4e8455ad58d2e5-next/` ninja ~**73/931** at report time; stale published `ps2web.js` **08:56** vs native **10:18** |
| Failed duplicate web-only invoke | `logs/autonomous-pipeline/hitman-web-rebuild-w-hitman-2026-11-07.log` (WinError 32 on `.ninja_deps` — panel worker holds lock) |

---

## Checkboxes flipped (immediate)

In `logs/master-campaign-plan-2026-11-07.md` §1:

- [x] Post-fix `PS2_CAPTURE` draw boxes → **0..511** (`hitman-capture-post-xyoffset-2026-11-07/draws.tsv`)
- [x] Clear / BGCOLOR path → `FUN_0028f7fc` + FBP from `+0xd4` (Ghidra MCP)
- [x] Runtime clears on **FBP 288 + 400** (capture PPM `fbp120` / `fbp190`)
- [x] Ghidra Phase 0 ELF re-import @ `0x00100000`, entry `0x0010001C`

---

## Layer status (remaining open)

| Layer | Open items |
|-------|------------|
| **1** | Chrome canvas luma above harness threshold (~0.14 harness / ~0.36% native PPM) |
| **2** | PSM draw vs present compare; wasm PSM parity post web rebuild |
| **3** | ATE-only ruled out (prior); canvas pass still blocked on luma / FBP compose |
| **4** | PMODE/DISPFB2/FRAME writer catalog (trusted VAs) |
| **Integration** | Web player rebuild complete → `canvas_lum` ≥ 8; DISPFB 400 vs FRAME 288 compose blit if raster non-empty |

---

## Evidence highlights

**Pre-fix (regression):** `logs/hitman-caller-readable/01c-TRACE-draws-frame180.tsv` — boxes at **x ≈ −1792**.

**Post-fix:** first in-screen boxes e.g. `0.0,64.0-0.0,2016.0`; negative-x samples now positive/off-right (`1792.0,…`) not −1792.

**Chrome (stale wasm):** `summary-20261107T153650Z.json` reuses harness `run_id` **20261107T140555Z**, `canvas_lum_end` **0.1382**, `canvas_black_end` **true**, FPS ~**59**, prims ~**865k**.

---

## Next (continuous)

1. Let panel/web-next finish → `ensure_web_build_readable` → fresh `_cyberarcade_live_harness.py` → flip web rebuild + `canvas_lum` checkboxes.
2. Ghidra: DISPFB2/FRAME writer catalog on `hitman_boot.elf` (ELF-trusted VAs).
3. Layer 2 PSM parity + DISPFB/FRAME compose blit if present still reads empty page 400.

*Worker: W-HITMAN — 2026-11-07 ~10:37 local*
