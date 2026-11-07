# Master campaign plan — PS2Recomp / CyberArcade

**File:** `logs/master-campaign-plan-2026-11-07.md`  
**Updated:** 2026-11-07 ~10:28 local  

**Execution mandate (God ~10:28):** This plan runs **without user input, call, or wait** — full agent control. On context overflow → fresh agent + snapshot; keep executing checkboxes.  
**Repo:** `C:\PS2Recomp`  
**Companion handoff:** `verification/recovery/AGENT-CAMPAIGN-SNAPSHOT.md`, `MASTER-CONTEXT.md`

**Checkbox legend**

- `[ ]` — open (not verified working end-to-end)
- `[x] YYYY-MM-DD — one-line evidence` — built and verified; date = confirmation day

**End state:** Every library title works **flawlessly in Chrome** (panel `http://127.0.0.1:8620/`), ≥60 FPS by default (30 only where a title truly requires it).

---

## 0) Locked mandates (never rewrite — additive improvements only)

| Mandate | Policy |
|---------|--------|
| Theme / vision | CyberArcade panel, custom Windows recompiler, evidence in `logs/` + `verification/recovery/` |
| Chrome flawless | All games playable in Chrome with visible, correct UI |
| FPS bar | ≥60 almost every game; 30 only when required |
| Autonomous mode | No stopping, no idling, no routine user waits |
| Context overflow | New agent + clean context; carry snapshot only (no in-thread trim) |
| Improvement passes | Optimize + light modernization **inside** existing stack; no wholesale re-architecture (`improvement-pass-policy-2026-11-07.md`) |
| CNK Alchemy | Isolated track; **no** CNK host hacks on Hitman/NFS disc-fix |

---

## 1) Hitman foundation — four layers (wave-1 graphics)

**Game id:** `a2116d2ac08a7be4db4e8455ad58d2e5`  
**Static refs:** `logs/hitman-ghidra-static-analysis-plan-2026-11-07.md`, `logs/hitman-caller-readable/`, `logs/hitman-analysis-graphs/`

### Layer 1 — Near-black clear color

- [ ] Clear sprites / BGCOLOR path mapped to live FBP (Ghidra `FUN_0028f7fc`, black clear `param_2=0`)
- [ ] Runtime: clears land on correct page (400 vs 288), not only DISPFB display page
- [ ] Chrome: canvas luminance above harness threshold after menu boot (not near-black PPM)

### Layer 2 — Pixel format (display setup / PSM)

- [x] 2026-11-07 — Mode A/C eliminated: DISPLAY2 decodes 512×448; `logs/hitman-display2-mode-verdict-2026-11-07.md`
- [x] 2026-11-07 — DISPFB2 PSM=0, FBW=8 live trace; present path reads circuit 2 (`PMODE=0x66`)
- [ ] PSM mismatch ruled out for black canvas (draw vs present readback compare)
- [ ] Chrome wasm present uses same PSM/decode as native for Hitman

### Layer 3 — Scissor / XYOFFSET

- [x] 2026-11-07 — Init zero scissor/XYOFFSET documented; live scissor 512×448; TRACE `xy=0x720000007000` (`02-ghidra-zeroed-scissor-xyoffset.md`)
- [x] 2026-11-07 — Capture showed draws at **x ≈ −1792** (full 16-bit OFX bug) (`01c-TRACE-draws-frame180.tsv`)
- [x] 2026-11-07 — **Fix shipped:** GS XYOFFSET 11-bit OFX/OFY in `gs.hpp`, `raster.cpp`, `gpu/gpu.cpp`, `gs.cpp`
- [x] 2026-11-07 — Native rebuilt: `build/native-a2116…/ps2run.exe` (cmake build success)
- [ ] Post-fix `PS2_CAPTURE` at frame ~180: draw boxes intersect **0..511**
- [ ] ATE ruled insufficient alone (`PS2_GS_NO_ATE` lum ~0.11 unchanged) — **confirmed** (`06-ATE-off-experiment.md`) but canvas pass still open

### Layer 4 — Ghidra load hygiene (Raw Binary vs ELF)

- [ ] Phase 0: re-import Hitman `boot.elf` as **ELF** @ `0x00100000`, entry `0x0010001C` (plan Phase 0)
- [ ] PMODE/DISPFB2/FRAME writer catalog with trusted VAs
- [x] 2026-11-07 — Not ps2-packer; normal stripped EE (`logs/hitman-boot-elf-packer-check-2026-11-07.md`)

### Hitman integration gates (Chrome)

- [x] 2026-11-07 — `ps2web.js` ACL serve fix + `ensure_web_build_readable` (`hitman-web-js-content-length-fix-2026-11-07.md`)
- [x] 2026-11-07 — Harness ~865k prims, ~60 FPS, no serve abort; **canvas still black** (pre-XYOFFSET web)
- [x] 2026-11-07 — Native 400f smoke with **`disc.iso`**: **97,531** prims (`logs/autonomous-pipeline/hitman-xyoffset-400f.log`)
- [ ] Web player rebuilt after native XYOFFSET fix (wasm newer than native; was **stale** ~08:56 vs ~10:18)
- [ ] Harness `canvas_lum` pass post web rebuild
- [ ] DISPFB vs FRAME page split (400 vs 288): compose blit if raster non-empty but present black

---

## 2) Cross-game expansion order

### 2a) Hitman first (commercial EE / libgraph — patient zero for GS display)

- [x] 2026-11-07 — Disc-fix matrix phases pass at 500f (~118k prims); R1–R4 joint stable
- [ ] Hitman **Chrome flawless** checkbox (all Layer 1–4 + integration gates above)

### 2b) NFS Most Wanted second (`60c82f4a111da300ac23bbec85272788`)

- [x] 2026-11-07 — Disc-fix pair cleared with evidence; matrix manual pass 500f ~140k prims
- [ ] Same GS invariant checklist as Hitman (shared A–H catalog, not Hitman-only hacks)
- [ ] NFS Chrome flawless + ≥60 FPS harness
- [ ] NFS five-phase matrix scorer gap closed (`first_disc_read` / fileio searches=0)

### 2c) CNK — isolated Alchemy track (`b49f2e769315347e8bda839feb705744`)

- [x] 2026-11-07 — Custom Alchemy dumper verify **28/28** on CNK
- [x] 2026-11-07 — Quarantine: no disc-fix/R5/CNK runtime patches on Hitman/NFS (`MASTER-CONTEXT` hard bans)
- [ ] CNK `prims=2` / loadgate / bind registry EE RE (`alchemy-rebuild-*`, Ghidra MCP todos)
- [ ] Proven Alchemy fixes recorded in `game-fix-registry.json` → self-heal **observe/proven_fixes** only
- [ ] CNK Chrome playable (separate acceptance; does not block Hitman/NFS lane)

### 2d) Remaining library (after Hitman + NFS patterns)

- [ ] `autonomous_verify.py --library` green for all `native-*` + `disc.iso`
- [ ] Per-title registry entries in `game-fix-registry.json`
- [ ] GoW USA min60 browser re-verify (`695b874b…`)
- [ ] Sly / Def Jam / others from live-matrix lane

---

## 3) Store → downloader → install (patches pre-applied)

**Stack:** `scripts/store.py`, `downloader/*.mjs`, `scripts/panel.py` `import_game` → `windows_port.py`

- [x] 2026-11-07 — Import pipeline + malware guard + build queue (`panel.py`; `tests/store_pipeline.py`)
- [x] 2026-11-07 — Global runtime patches in tree: R3 readee, R4-D1 DiskReady (`discfix-matrix-board.json` verified_apply)
- [x] 2026-11-07 — GS XYOFFSET fix in runtime (all new builds inherit)
- [x] 2026-11-07 — `install_health.py` gates explore/smoke failures
- [ ] Post-download hook: auto `self_heal` + `autonomous_verify` before `ready`
- [ ] `install_manifest.json` per game (source hash, job id, timestamps)
- [ ] Optional `PS2_STRICT_VERIFY=1` blocks `ready` on verify fail
- [ ] Nightly: download → build → heal → verify log under `logs/autonomous-pipeline/`
- [ ] Store pull → playable in Chrome **without manual patch steps** (definition of done)

**Docs:** `verification/recovery/autonomous-pipeline-2026-11-07.md`

---

## 4) Self-healing patch system

**Stack:** `scripts/self_heal.py`, `games/<id>/install_issues.json`, hook in `panel.py` post-build

- [x] 2026-11-07 — Orchestrator written + panel hook
- [x] 2026-11-07 — Detectors: missing code, near-zero prims, gs_negative_draw_boxes, alchemy leak, web stale/ACL
- [x] 2026-11-07 — Auto T1: `ensure_web_build_readable`, queue web rebuild, post smoke via `autonomous_verify.py`
- [x] 2026-11-07 — Auto T2: registry quarantine on alchemy pulse
- [x] 2026-11-07 — `autonomous_verify.py` uses **`disc.iso`** (not `disc/` folder)
- [ ] Idle-aware web rebuild (poll until not `building`)
- [ ] Detectors: `canvas_black_harness`, `low_fps`, `matrix_fail`, `fbp_triad_mismatch`
- [ ] `proven_fixes[]` in `game-fix-registry.json` when Alchemy/CNK fixes verified
- [ ] `self_heal.py --library` sweep after global runtime edit
- [ ] T3 behavioral patches remain board-gated (`allow_discfix_apply=false` for HLE rewrite)

**Docs:** `verification/recovery/self-heal-patch-system-2026-11-07.md`, `game-fix-registry.json`

---

## 5) Chrome performance sweep (60 FPS bare minimum)

**Note:** Deferred God track for V-Sync/FPS-limit **research/apply** until explicitly called; **measurement** below is allowed now.

- [x] 2026-11-07 — Hitman harness reported ~60 FPS with high prims (pre-fix canvas)
- [x] 2026-11-07 — GoW native 3600f smoke ~19.2M prims (`logs/gow-patientzero-smoke/`)
- [ ] Parse FPS / frame timing in `autonomous_verify` summary JSON
- [ ] Harness `metrics.json`: canvas_lum, FPS, BOOTMENU/menu regex
- [ ] Per-game **30 FPS allowlist** in registry (true 50/60 Hz exceptions only)
- [ ] Library sweep: every title ≥60 in Chrome (or allowlisted 30) for sustained window
- [ ] Final optimization pass: WebGPU path, present pacing (additive only; no new product shell)

---

## 6) Resources (reference — do not replace primary SDK path)

| Resource | Use | Path / link |
|----------|-----|-------------|
| **Ghidra 12.1.2 + EE Reloaded + MCP** | Hitman/NFS/CNK EE static analysis, GS VAs | USR Ghidra; `:8089`; `logs/hitman-ghidra-static-analysis-plan-2026-11-07.md` |
| **SCE SDK 3.0.3** | Authoritative macros (`eeregs.h`, `libgraph.h`) | **`E:\usr\local\sce` only** |
| **ps2tek / psdevwiki** | GS register semantics, FRAME/TEST/ALPHA | Research bible in Hitman plan |
| **Alchemy 5.0 kit** | Vocabulary only (not CNK byte-identical) | `C:\usr\alchemy`, archive.org kit |
| **Custom PS2 Alchemy dumper** | ISO → `alchemy-map.json` | `tools/ps2-alchemy-dumper/` |
| **binwalk / TOC** | CNK GFC·GOB·IGB | `alchemy-rebuild-w2-*` |
| **PS2Dev** | Homebrew reference patterns (not Sony SDK) | GitHub `ps2dev/*` — never substitute for `E:\usr\local\sce` |
| **Matrix / disc-fix board** | Patch protocol | `verification/recovery/discfix-matrix-board.json` |

- [x] 2026-11-07 — SDK research path rule: `.cursor/rules/ps2-sdk-research-path.mdc`
- [x] 2026-11-07 — Redumper/dumper README credit rules in workspace rules

---

## 7) Autonomous continuous mode + fresh-agent handoff

- [x] 2026-11-07 — Standing orders in `MASTER-CONTEXT.md` (execute, no routine ask, verify-each-fix)
- [x] 2026-11-07 — Rule: `.cursor/rules/agent-context-rollover.mdc` (no in-thread trim; spawn new agent)
- [x] 2026-11-07 — Snapshot seed: `verification/recovery/AGENT-CAMPAIGN-SNAPSHOT.md`
- [ ] **This file** updated on every verified checkbox (date + evidence line)
- [ ] Pre-rollover ritual: refresh snapshot + this plan + MASTER RESUME POINT

**On new agent start:** Read this plan → snapshot → MASTER RESUME → execute top open `[ ]` in Hitman Chrome gate, then NFS, then library verify.

---

## 8) Improvement-pass policy (additive optimize / modernize)

- [x] 2026-11-07 — Documented: `verification/recovery/improvement-pass-policy-2026-11-07.md`
- [ ] GS regression / invariant catalog JSON
- [ ] Harness metrics + golden capture for Hitman draws
- [ ] Versioned registry schema + machine-readable disc-fix applied list

---

## 9) At-a-glance status (counts)

| Section | Checked | Open |
|---------|---------|------|
| Hitman foundation (all sub-items) | 11 | 12 |
| Hitman Chrome gate | 3 | 3 |
| NFS expansion | 2 | 3 |
| CNK track | 3 | 3 |
| Store pipeline | 4 | 5 |
| Self-heal | 6 | 5 |
| Chrome FPS sweep | 2 | 5 |
| Handoff / policy docs | 4 | 2 |
| Improvement-pass extras | 1 | 3 |

**Current focus (do not idle):** Finish Hitman **web rebuild** → harness **canvas_lum** → check Layer 3 capture boxes → then NFS shared GS checklist.

---

## 10) Immediate commands (copy-paste)

```powershell
# Hitman verify (after web build completes)
$env:PATH = "C:\PS2Recomp\runtime-deps;C:\PS2Recomp\tools\msys64\clang64\bin;C:\PS2Recomp\third_party\wgpu-native\lib;" + $env:PATH
python C:\PS2Recomp\scripts\autonomous_verify.py --game a2116d2ac08a7be4db4e8455ad58d2e5 --frames 600 --json

# Self-heal one title or library
python C:\PS2Recomp\scripts\self_heal.py --game a2116d2ac08a7be4db4e8455ad58d2e5
python C:\PS2Recomp\scripts\self_heal.py --library
```

**When marking a checkbox:** use today's date (local) and one line pointing at log/file/metric that proved it.
