# Concept phase — Hitman black-canvas static analysis (no build)

**Mode:** Design only. No code changes, no Ghidra project rebuilds, no harness/runtime runs.  
**Framing:** Hitman = normal commercial Emotion Engine title (**not** Alchemy / CNK). Black canvas may recur (e.g. NFS) → prefer **general GS display/draw invariants** + **small per-game knobs** + **auto-detection**, not Hitman-only hacks.  
**Learning loop:** Every wrong hypothesis or tooling mistake becomes an explicit feedback item that revises this approach.

**Lead references:** psdevwiki/PS2 · israpps ps2tek · local `E:\usr\local\sce` (for naming). Community GitHub = unofficial only.

---

## 1. Problem statement (shared across games)

**Symptom class:** Emulated GS reports high activity (prims, FPS, VU/GS busy) but the **presented** framebuffer is black/empty.

**Separation of concerns:**

| Layer | Role | Black-canvas relevance |
|-------|------|------------------------|
| Disc / HLE / Alchemy | Game-specific engine quirks | **Out of primary scope** for Hitman; do not start here |
| EE + GIF → GS | Draw into **FRAME**; tests/blends/clears | Likely |
| Privileged PCRTC | **PMODE / DISPFB / DISPLAY / BGCOLOR** select what is shown | Likely |
| Host present | Read enabled circuit’s DISPFB → canvas | Possible secondary; treat after EE/GS invariants |

**Invariant to test first (all games):**  
*Draw target (FRAME.FBP) and display source (DISPFB.FBP) can diverge.* Prim counts do not prove the displayed buffer has color.

---

## 2. Conceptual model (from priority docs)

Think in three buffers/policies, not one “screen”:

1. **Draw buffer** — `FRAME_1/2` (+ ZBUF, SCISSOR, XYOFFSET)  
2. **Pixel policy** — PRIM/PRMODE, ALPHA, TEST (ATE/DATE/ZTE), FBA, PABE, FRAME mask  
3. **Display buffer** — PMODE enables circuit 1 and/or 2; each has DISPFB + DISPLAY; BGCOLOR fills gaps  

ps2tek/psdevwiki implication: a game can “run” perfectly while displaying a cleared, masked, or never-written FBP.

**Generalizable failure modes (game-agnostic catalog):**

- A. Display FBP ≠ draw FBP (flip/bookkeeping)  
- B. Circuit enable mismatch (EN1/EN2 vs host present pick)  
- C. FRAME mask preserves black RGB  
- D. Alpha / dest-alpha rejects all fragments into the **displayed** buffer  
- E. Clear-only / BGCOLOR-only on displayed FBP  
- F. Scissor/offset exclude visible region  
- G. PSM interpretation mismatch draw vs present  
- H. Host present reading wrong circuit or stale field (last resort)

Hitman first-pass *hints* (concept only, not proven): uses display **circuit 2**; host already prefers EN2 — so **A/C/D/E** outrank **B** until proven otherwise. NFS (and others) get the **same catalog**, different which letter fires.

---

## 3. Analysis approach (paper design)

### 3.1 Mindset

- **Commercial EE game:** expect libgraph/`sceGs*` patterns, GIF packets, double-buffer flips — not middleware Alchemy object graphs.  
- **Static first:** recover *who writes* FRAME / DISPFB / PMODE / TEST / ALPHA / clear sprites.  
- **Compare, don’t special-case:** same checklist for Hitman, NFS, …; only **detection signatures** and **knobs** are per-game.

### 3.2 Static workstream (conceptual stages)

**S0 — Representation hygiene (concept)**  
Ensure the binary is reasoned about as a real EE ELF (load VA `0x00100000`, entry `0x0010001C`).  
*Feedback already:* treating a raw/misbased image as truth wasted cycles → **rule:** never trust GS addresses until load model matches ELF PH.

**S1 — Surface recovery**  
Map string/API surface (`sceGsPutDrawEnv`, `sceGsDefDispEnv`, sync-path errors) to “display env” vs “draw env” clusters.  
*Goal:* two labeled islands — **draw** and **show**.

**S2 — Register authorship map**  
For each privileged/GIF register family, list writers (conceptually): PMODE, DISPFBn, DISPLAYn, FRAME, ZBUF, ALPHA, TEST, BGCOLOR.  
*Goal:* prove whether flips update DISPFB in lockstep with FRAME.

**S3 — Clear vs shade**  
Identify full-screen / clear-like draws (sprite strips, Z+color clear idioms from ps2tek) vs mesh draws.  
*Goal:* is the **displayed** FBP only ever cleared?

**S4 — Pixel policy**  
Where TEST/ALPHA/FBA/PABE/FRAME-mask are set relative to menu/boot draws.  
*Goal:* can fragments reach RGB in the displayed buffer?

**S5 — Cross-game template**  
Freeze S1–S4 as a **checklist** reusable on NFS (and others) without redesign.

### 3.3 Host/harness (concept only — no runs)

Document (don’t execute) the present contract: enabled PMODE circuit → DISPFB → canvas.  
Use it as a **consistency check** against S2, not as a place to patch yet.

### 3.4 What we explicitly defer

- Alchemy / CNK object+0x20 / prims=2 tracks  
- Running packers, reimports-as-builds, player patches, harness shot loops  
- FPS tuning, disc-fix apply  

---

## 4. Generalization & auto-detection (design intent)

**Fix shape (future, not now):** prefer a **host or GS-present policy** that enforces or diagnoses invariants, with **per-game profiles** only where detection says so.

| Mechanism | Idea |
|-----------|------|
| **Auto-detect** | Classify title by serial/build id; optional: observe which PMODE circuit and FBP pairing the EE uses (static signature or later safe telemetry) |
| **Shared core** | Same draw-vs-display consistency checks / present-circuit selection rules for all EE games |
| **Small knobs** | Per-game: preferred circuit, FBP bias, interlacing/halve, known clear idioms — data, not forks |
| **Non-goals** | Per-title shader rewrites; Alchemy-style intercepts for Hitman |

**Feedback rule:** if a Hitman-only assumption fails on NFS, **promote** it into the shared catalog (A–H) and demote the Hitman special case.

---

## 5. Mistake → approach feedback loop

| If we learn… | Then revise… |
|--------------|--------------|
| Load/base wrong | S0 gate; discard address-based conclusions |
| “Packed” was false | Don’t invent unpack stubs; treat as stripped commercial EE |
| Circuit already correct | Deprioritize B; deepen A/C/D/E |
| Prim count ≠ pixels in DISPFB | Keep “activity ≠ visibility” as standing slogan |
| NFS differs only in which letter fires | Strengthen shared checklist; shrink per-game knobs |
| Host present was fine | Stop touching web/shim; stay in EE/GS authorship |
| Alchemy tools helped CNK only | Keep Alchemy **quarantined** from this track |

Capture each revision as a short dated note under this concept doc (still no code).

---

## 6. Success criteria for this concept phase

Caller can react to:

1. Shared failure catalog A–H  
2. Staged static method S0–S5  
3. Generalize-first / detect-and-knob philosophy  
4. Explicit feedback loop  
5. Clear **non-actions** (no build, no run, no Alchemy framing)

**Exit from concept → execution** only when caller green-lights a stage (likely S0/S1), still preferring static over runtime until asked.

---

## 7. One-page summary

Treat black canvas as a **GS draw-vs-display identity problem** common to commercial EE games. Analyze Hitman with libgraph/PCRTC mental models from ps2tek + psdevwiki + local SDK names. Build a **reusable checklist**, not a Hitman patch. Let every false trail rewrite the checklist. Do not build or run until the caller exits concept phase.
