# MASTER-CONTEXT — CyberArcade / PS2Recomp handoff

**Updated:** 2026-11-07 (~07:30 local)  
**Repo root:** `C:\PS2Recomp`  
**Branch posture:** `windows` branch — keep it clean. No commits until a stable build; then commit freely. **When a stage is proven safe (won’t break Hitman/NFS R1–R4 or other stable paths), commit to GitHub.**

This file is the single handoff for humans and agents. Detailed evidence lives under `verification/recovery/` and `logs/`. Prefer those reports over re-deriving.

**Stasis lifted:** 2026-11-07 ~05:26 — paused workers + SDK audit tracks restarted (research/observe only; no disc-fix/R5/CNK patches). Theme UI folder `jarvis-cursor-ui` removed separately. **Safe to reload Cursor.**

### Standing instructions (agents) — LOCKED 2026-11-07 ~06:05

1. **Execute the next stage now.** Prepare, plan, and **start executing immediately**. Do **not** stop until that stage is **working**. Keep the caller updated on **every move** as it happens.
2. **Full control / full direction.** Do **not** ask for approval on routine decisions. Bring something up only if it is truly important and needs discussion; after discussion, the **agent still makes the final call**.
3. **Keep this file current.** Periodically update MASTER-CONTEXT with steps **completed** and **in progress** (workers, audits, downloads, blockers) so a crash or reload can resume without re-asking.
4. **Safe commits.** When a stage reaches a point where committing to GitHub is appropriate and **will not break** existing stable functionality, **commit** (user standing order). Still no force-push / no hook skips unless explicitly asked.
5. **Hard bans this stage:** Do **not** patch **disc-fix**, **R5**, or **CNK** (including Alchemy host hacks). Research/observe for those tracks only.
6. **FPS bar:** **60 FPS minimum** for non-CNK games (higher preferred). **God of War is patient zero** for the FPS track.
7. **Evidence first.** Prefer `verification/recovery/` + `logs/` over re-deriving. Product browser target remains **Chrome + Edge**.

---

## RESUME POINT — pick up here (do not ask the user to re-explain)

**Session cut-off (prior):** 2026-11-06 ~23:51 local. **Unpaused:** 2026-11-07 ~05:26. **Now (~07:03):** Standing instructions LOCKED. Master was **stale at ~06:32** (no Ghidra/MCP five-todo block) — refreshed here.

**Background still true:** (1) GoW USA patient-zero 60 FPS — native 3600f smoke ~19.2M prims (`logs/gow-patientzero-smoke/`); browser min60 re-verify still open. (2) Custom PS2 Alchemy dumper Phase 1–3 — **verify 28/28 PASS** exit 0 on CNK (~07:18, includes Ghidra prologue locks); schema 1.1; optical stub (§9). **No** disc-fix/R5/CNK runtime patches.

### G) Continuous loop — CNK 2-prims + disc-fix (2026-11-07 ~07:27) — **PRIMARY RESUME**

Five-todo Ghidra/Alchemy chain **closed** (MCP dual-ELF, ISO, VA 6/6, verify **28/28**, MASTER). God (~07:27): **do not idle** — loop continues past closed todos until 100% operational.

| Track | Status | Exact next |
|-------|--------|------------|
| **CNK prims=2** | **IN PROGRESS** observe | Soft-arm 20k reconfirm **prims=2** (`logs/cnk-2prims-observe-2026-11-07/`); diagnose note `cnk-2prims-gate-diagnose-2026-11-07.md`. Tid-map / FCE0 stall still open. |
| **Disc-fix Hitman/NFS** | **IN PROGRESS** observe | Board step 8 `R5_pad_sound_observe`; matrix observe in flight. No R5 apply. |
| **GoW DLL PATH smoke** | **DONE ~07:30** | 600f exit 0; **6,964,754** prims; ~122 host f/s; no DLL miss. `gow-dll-path-smoke-2026-11-07.md`. |
| **Ghidra MCP** | **UP** | `http://127.0.0.1:8089` PID 3152; `gow_boot.elf`+`cnk_boot.elf`; `ghidra-mcp-restart-2026-11-07.md`. |
| Prior §G todos p0–p1 | **DONE** | Alchemy verify 28/28. |

**DLL restore (~07:18):** wgpu/SDL2/libc++ were **not** deleted by git cleanup (sources still in `third_party/wgpu-native/lib` + `tools/msys64/clang64/bin`). Bare `ps2run` without PATH → `STATUS_DLL_NOT_FOUND` (−1073741515). Copied deps to `runtime-deps\`, repo root, and all `build/native-*/`. Product entry remains **`Setup.cmd`** / `PS2Recomp.cmd` (no in-repo `PS2Recomp.exe`). Verify: `ps2run --help` loads (exit 1 = bad args, not DLL miss).

**Continuous loop standing order (God, ~07:08):** debug → run → verify → repeat until 100% operational. No stop/ask. Master is Bible. Sub-agents plan next **iteration**, not an end.

**Abort/resume note (same morning):** user abort killed MCP pid 18316 + watchers; then “do not abort / resume”; then “stop screen share only”; then autonomous resume of all five todos. Do **not** treat abort as final state — MCP is back up.

**Silent pipeline evidence:** `logs/ghidra-ps2/silent-pipeline.log` (PIPELINE COMPLETE ~06:42); restart `mcp-restart` / `resume-todos.log`; ELF dir `C:\Users\joshy\ghidra_exports\ps2-elves\` (`gow_boot.elf`, `cnk_boot.elf`).

### A) R1–R5 official SDK audit (research only)

| Item | Product status | SDK audit status | Where left off |
|------|----------------|------------------|----------------|
| **R1** SIF end | `cleared_with_evidence` (joint-stable `1e04172`) | **Notes written** → `sdk-compliance-r1-sif.md` | Orphan end-packet HLE may synthesize success REND on soft reset (flagged; queue drains) |
| **R2** WaitSema fidelity | `cleared_with_evidence` (never `host_signal(2)`) | **Notes written** → `sdk-compliance-r2-waitsema.md` | Never `host_signal(2)` on Hitman/NFS; CNK igfileio pulse quarantined |
| **R3** readee / AlignReadBuffer | **`verified_apply`** in `runtime/src/iop/cdvdfsv.cpp` | **Notes written** → `sdk-compliance-r3-readee.md` | AlignReadBuffer absent from public `libcdvd.h`; Device PDF = 64B align compensation; CNK virt/Alchemy paths quarantined |
| **R4** sceCdSync / finish_read | `cleared_with_evidence` (no wake code) | **Notes written** → `sdk-compliance-r4-cdsync.md` | `sceCdDiskReady` HLE always returns `2` (SCECdComplete), ignores mode — flag if titles need NotReady |
| **R5** pad / sound | **still gated** (no disc-fix apply) | **Inventory written** (2026-11-07) — still not an apply/HLE rewrite | See `verification/recovery/sdk-compliance-r5-pad-sound-inventory.md`. SDK assets present; runtime has SIO2/SPU2 + `PS2_TRACE_PAD`, **no** padman/libsd HLE module set comparable to CDVD. Board step 8 observe-only; do not apply |

**Audit rules:** research only; **flag deviations, do not patch** unless user asks. Official tree: **`E:\usr\local\sce` only**.

**Next resume action for audit:** Compliance rollup complete. Research-only flags stand; do not patch unless user asks. R5 remains gated.

### B) PDF extraction (`verification/recovery/_sdk_pdf_extract/`)

**Done — 14 PDFs → `.txt`:**

| Extracted | Keyword hits (script) |
|-----------|------------------------|
| `cdvdtips_3.0.pdf.txt` | padman, libsd, sceSif, sceCdRead |
| `PS2_EE-Overview-Device-3.0.2.pdf.txt` | sceCdSync, DiskReady, padman, scePad, sceSif, CallRpc, GetReadPos |
| `PS2_EE-Reference-Device-3.0.3.pdf.txt` | sceCdSync (many), DiskReady, scePad, sceCdRead |
| `PS2_EE-Overview-Sif-3.0.pdf.txt` | sceSif, CallRpc |
| `PS2_EE-Reference-Sif-3.0.2.pdf.txt` | sceSif, CallRpc |
| `PS2_IOP-Overview-Kernel-3.0.pdf.txt` | WaitSema |
| `PS2_IOP-Reference-Sif-3.0.2.pdf.txt` | sceSif, CallRpc |
| `PS2_EE-Overview-Sound-3.0.2.pdf.txt` | libsd, sceSd |
| `PS2_EE-Reference-Sound-3.0.1.pdf.txt` | libsd, sceSd |
| `PS2_IOP-Overview-Sound-3.0.1.pdf.txt` | libsd, sceSd |
| `PS2_IOP-Reference-Sound-3.0.2.pdf.txt` | libsd, sceSd (heavy) |
| `PS2_IOP-Overview-Device-3.0.pdf.txt` | sceSif |
| `PS2_IOP-Reference-Device-3.0.2.pdf.txt` | sceCdSync, DiskReady, sceCdRead |
| `PS2_EE-Overview-Kernel-3.0.2.pdf.txt` | WaitSema |

**Hunt status:** extractor keyword pass done. **No Alchemy / Intrinsic hits** in those extracts.  
**Quote harvests:**  
- Round 1 → `sdk-pdf-quote-harvest-r1r5.md` (~35 blocks).  
- **CNK-informed round (2026-11-07 ~06:00)** → `sdk-pdf-quote-harvest-cnk-informed-2026-11-07.md` — re-scan + CNK coupling notes (GFC/GOB via CDVDFSV; padman/libsd = retail MODULES, not Alchemy).  
**Confirmed gaps:** no PDF prose for AlignReadBuffer / b1len / b2len / +16 / +80 (closest: 64-byte compensation + `libcdvd.a` `_sceCd_rd_intr_data` / `_sceCd_Read_cur_pos`). Strong: sceCdSync modes, DiskReady=`2`, padman load order, libsd/libsdr.

**Not extracted yet (optional later):** graphics/movie/network EE+IOP overviews/refs, Docs&Training PDFs under `E:\usr\local\sce\Docs&Training\`, tips beyond `cdvdtips` (only if hunting AlignReadBuffer prose further).

**Helper script:** `verification/recovery/_extract_sdk_pdfs.py` (needs Python 3.10 + `pypdf`).

**Next resume action (audit):** Harvests + compliance report complete. Do not patch unless asked. R5 remains gated.

### C) Active workers — last known state (**RESUMED** 2026-11-07)

| ID | Track | Last known |
|----|--------|------------|
| w1 | Disc-fix Hitman/NFS | **ACTIVE ~07:27** — R5 observe matrix run in flight (no apply); R1–R4 `1e04172`; see `worker-resume-discfix-w1-2026-11-07.md` |
| w2 | Test-matrix | **ACTIVE ~07:27** — same board step 8; matrix observe smokes with disc-fix worker; see `worker-resume-matrix-w2-2026-11-07.md` |
| w3 | CNK null-bind `51ACEC` / 2-prims | **ACTIVE ~07:27** — deep diagnose soft-arm stall + tid map (observe); soft-arm still prims=2; `worker-resume-cnk-nullbind-w3-2026-11-07.md` |
| w4 / w4b | Sly GS/VU + asset bin-walk | **RESUMED-as-complete/parked** — next STQ/PATH3/CLUT when prioritized; `worker-resume-sly-w4-w4b-2026-11-07.md` |
| w5 | WaitSema / CreateSema | **RESUMED** observe-only; `worker-resume-waitsema-w5-2026-11-07.md` |
| w6 | BIOS zip reference | **RESUMED-as-complete**; `worker-resume-bios-w6-2026-11-07.md` |
| w7 | CNK ELF Alchemy redo | **RESUMED** complete/quarantined research owner; `worker-resume-cnk-elf-w7-2026-11-07.md` |

#### CNK Alchemy rebuild research (launched 2026-11-07 ~05:45) — observe only

**Target game:** Crash Nitro Kart only — id `b49f2e769315347e8bda839feb705744` (**not** Hitman). No disc-fix/R5/CNK patches.

| Worker | Track | Status |
|--------|--------|--------|
| A1 | CNK ELF Alchemy walk (strings / symbols / VAs) | **DONE** → `alchemy-rebuild-w1-cnk-elf-walk-2026-11-07.md` (~595 `ig*` whole-string classes; v3.0-0909; stripped; key VAs confirmed). Prior deep map: `cnk-elf-alchemy-full-redo-report.md` |
| A2 | CNK disc binwalk / Alchemy TOC (GFC·GOB·IGB) | **DONE** → `alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md` — GFC 1830 files / 4327 STBL / 520 `.igb`; IGB `DA FA` / `0x80000005` |
| A3 | Cross-ref vs Alchemy 5.0 kit + ps2tek mirror | **DONE** → `alchemy-rebuild-w3-kit-ps2tek-xref-2026-11-07.md` — kit=concepts only; gaps loadgate / igFileIO name / `0x725F50` |
| A4 | Alchemy-related IOP modules + EE syscall inventory | **DONE** → `alchemy-rebuild-w4-iop-ee-inventory-2026-11-07.md` — ig* absent from MODULES (HLE); blocker = bind/loadgate/IGB |

**Synthesis written** → `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md`. Still **no** CNK Alchemy host patches unless asked.

Prior pause index: `verification/recovery/worker-pause-all-four-2026-11-06.md`. Tracks A + B + E **done** (`SDK-R1-R5-COMPLIANCE-REPORT.md`).

### D) cortana-cursor-ui (drivers; junction from former jarvis-cursor-ui name)

| Item | Value |
|------|--------|
| Folder | `C:\PS2Recomp\cortana-cursor-ui\` (junction → on-disk `jarvis-cursor-ui\` until Cursor unlocks rename) **v0.5.4+** |
| VSIX | Prefer `cortana-cursor-ui-0.5.4+.vsix`; never reinstall `jarvis-cursor-ui-*` extensions |
| Install | Prefer `cursor --install-extension` on the `.vsix` (folder path install **fails** — CLI wants ID or `.vsix`) |
| Visual target | **`media/reference-command-center.png`** — exact match; also used as **Cursor boot/loading screen** |
| Mechanism | **Custom CSS / workbench injection required**; overlays **out** |
| Fail-safes | (1) Auto-disable on Cursor update, (2) auto-disable if inject breaks, (3) caller self-rebuild — official support N/A |
| Branding | Full CORTANA UI copy; spoken channel = **Cursor** voice (not CORTANA TTS persona) |
| Plan | `C:\Users\joshy\.cursor\plans\jarvis_pro_recreation_a1985356.plan.md` |
| Activate | Reload after install; select suit theme + injection boot path per plan |

### E) In-flight terminals / installs

| Item | State |
|------|--------|
| `C:\usr` delete | **Done** (removed); do not recreate |
| `E:\PS2_SDK` poll | Finished **empty** — obsolete target |
| PDF extract job | **Succeeded** (14 docs) |
| cursor.cmd locate | Found: `C:\Program Files\cursor\resources\app\bin\cursor.cmd` |
| VSIX install | **Succeeded** exit 0 |
| R1–R5 compliance report | **Written** → `verification/recovery/SDK-R1-R5-COMPLIANCE-REPORT.md` (R1–R4 no blocking Hitman/NFS gaps; DiskReady always-2 observe flag; R5 gated) |
| Alchemy 5.0 eval kit (`C:\usr\alchemy`) | **Complete** — all **44** Internet Archive `alchemy-kit` files (~**265 MB** / 277,806,630 B item payload); includes `AlchemyKit.zip`, `Alchemy_Docs.zip`, `AlchemysReset.zip`, `GOBtools.zip`, Maya artist pack `.exe`, torrent, sqlite/xml, translated PDFs + CHOCR/HOCR/full text, JPEGs; extracted `AlchemyEvalKit\` |
| ps2tek mirror (`C:\usr\alchemy\ps2tek`) | **Complete** — **277** files (~3.2 MB); live HTML mirror + GitHub markdown sources (`index.html`, `PS2/**/*.md` + split `.html`) |
| CNK Alchemy research A1–A4 | **DONE + synthesized** → `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` |
| CNK-informed PDF quote harvest | **Written** → `sdk-pdf-quote-harvest-cnk-informed-2026-11-07.md` (AlignReadBuffer still absent from PDFs) |
| **GoW patient-zero 60 FPS** | Native 3600f smoke **completed** (`logs/gow-patientzero-smoke/`, ~19.2M prims) — browser min60 re-verify still open; no disc-fix/R5/CNK patches |
| **Custom PS2 Alchemy dumper** | **Phase 1–3 VERIFIED** — `python -m ps2_alchemy_dumper verify` on CNK → **20/20 PASS**; schema 1.1 + `class-map.tsv`; optical stub; see §9 |
| **USR Ghidra 12.1.2 + EE Reloaded + MCP** | **UP** — `Run-SilentGhidraPs2.ps1`; MCP `:8089` pid 3152; dual-ELF re-verify **in flight** (see §G) |
| **CNK ELF source** | AI Browser `_cnk_extract\Crash Nitro Kart (USA).iso` → SHA256 `FA37C064…E204` ≡ `ghidra_exports\ps2-elves\cnk_boot.elf` (Downloads had no CNK ISO) |
| No other intentional long-running installs | — |

### F) One-liner for next agent

1. Read this **RESUME POINT** — especially **§G five-todo chain** — + **Standing instructions**.  
2. **Primary now:** finish **p0-mcp** dual-ELF verify (MCP already on `:8089`), then **p1-ghidra-vas** CNK key VAs, then **p1-plan** + **p1-docs**. **p0-iso** already closed (AI Browser ISO ≡ library boot SHA).  
3. SDK audit A/B/E complete — see `verification/recovery/SDK-R1-R5-COMPLIANCE-REPORT.md`.  
4. Do **not** patch disc-fix/R5 or apply CNK Alchemy host hacks unless asked.  
5. Parallel/parked: GoW USA patient-zero 60 FPS (`695b874b…`) browser min60 re-verify — no disc-fix/R5/CNK patches.  
6. Alchemy isolation tool: `tools/ps2-alchemy-dumper/` — Phase 1–3 **verify 20/20**; optical Phase 4 later.  
7. Hard bans: disc-fix / R5 / CNK patches. FPS bar ≥60 non-CNK.  
8. Periodically refresh this file; safe-commit when stage won’t break R1–R4.

---

## 1. What this project is

**CyberArcade / PS2Recomp** — a PlayStation 2 recompiler / host runtime that runs recompiled EE game code on PC (native builds + web/GPU paths). Engine-generic HLE preferred over game-specific hacks.

**Product browser target:** **Chrome + Edge only.** Firefox, mobile UI, and controls redesign are back-burner.

---

## 2. Priority stack (current)

| Priority | Track | Status |
|----------|--------|--------|
| **Main** | Hitman Blood Money + NFS Most Wanted **disc-fix** (shared CDVD / `cdvdfsv`) | R1–R4 joint-stable; R5 gated; SDK compliance audit in progress |
| **Patient zero (fps)** | God of War (USA) **60 fps** — `695b874b308a4e5353767bb6df8ba697` | **ACTIVE STAGE** — restore/verify; hard ban disc-fix/R5/CNK patches |
| **Main game choice** | NFS **or** CNK as long-term flagship | Undecided; CNK Alchemy research continues in quarantine |
| **Parked** | CNK deep play / Crash Bandicoot / software-renderer ×10 / mobile UI | Do not launch unless unparked |
| **Parked research** | Sly Cooper texture / GS (buildings) | Research done; implementation next is shared GS STQ/PATH3/CLUT |
| **Dropped** | PCSX2-as-oracle workflow | Do not reopen as primary truth source |
| **Reference-only** | BIOS zip (`70012` / `77001` family) | Never execute BIOS; never copy into repo as a ship artifact |
| **P2** | Self-healing runtime | Priority 2 — after disc-fix stability |
| **Proposed** | Install-time ELF walking | Proposed; not landed as product default |
| **Future** | Linux back-compat with fixes | Logged — not started |
| **Future** | Full TypeScript rewrite; C++ (+ inline ASM) for hot paths | Logged — not started |
| **Future** | Alchemy 3.0 rebuild from ELF knowledge (no source available) | Logged — research only; isolation map tool scaffolded (`tools/ps2-alchemy-dumper/`) |
| **Tooling** | Custom Windows PS2 Alchemy dumper (ISO→`alchemy-map.json`) | **SCAFFOLDED** — see §9; not a disc-fix/R5 track |

**Standing rule:** Workers stay up until the user says done (no self-dismiss after one step). Currently **stasis**.

---

## 3. Game IDs

| Game | ID |
|------|-----|
| Hitman Blood Money | `a2116d2ac08a7be4db4e8455ad58d2e5` |
| NFS Most Wanted | `60c82f4a111da300ac23bbec85272788` |
| Crash Nitro Kart (CNK) | `b49f2e769315347e8bda839feb705744` |
| Sly Cooper and the Thievius Raccoonus | `c0c4527037b6168660829a0eb13df1a3` |

---

## 4. Disc-fix (Hitman + NFS) — main track

**Board:** `verification/recovery/discfix-matrix-board.json`  
**Reports:** `discfix-hitman-nfs-live-report.md`, `test-matrix-live-report.md`, `waitsema-createsema-trace-live-report.md`  
**Stable marker:** commit `1e04172` + `verification/recovery/DISCFIX-R1-R4-STABLE.md`

### Problem model (simple)

- Disc **readers** were not correctly setting **readee length** fields and/or not waking **waiters** the Sony way.
- BIOS / reference reading confirms a **shared CDVD complete** contract (not Alchemy).
- Leftover **WaitSema(2)** is **libcdvd durable parking** — **never** blind `host_signal(2)`.
- Hitman and NFS share the same `cdvdfsv` path: N `0x1` → `read_to_ee` → `complete_call`. Not CNK Alchemy.

### Ranked rewrite gates (prove-before-swap)

| Rank | Item | Status |
|------|------|--------|
| R1 | SIF end | **cleared_with_evidence** (queue drains to 0) |
| R2 | WaitSema fidelity | **cleared_with_evidence** (sema 2 = observe parking; never pulse) |
| R3 | readee lengths / AlignReadBuffer | **verified_apply** in `runtime/src/iop/cdvdfsv.cpp` |
| R4 | sceCdSync / finish_read wake | **cleared_with_evidence** (no wake code needed) |
| R5 | pad / sound | **still gated** (separate from CDVD) |

### Matrix protocol

1. Disc-fix posts `proposed_change` + evidence on the board.  
2. **Test-matrix** runs **5 phases** (boot → menu → first disc read → streaming → sustained run) with Sony-style pass checks.  
3. Disc-fix applies **only after** `verdict=pass` / `allow_discfix_apply`.  
4. **Prove-before-swap** before any R1–R5 behavioral rewrite.

### Board cycles so far

1. FAIL — bundled R3 + R4 while R1/R2 locked  
2. PASS — `R1_clear_with_evidence`  
3. FAIL — `R3_readee_length_harden` while R2 gated  
4. PASS — `R2_clear_with_evidence`  
5. PASS — allow R3 apply  
6. PASS — `R3_post_apply_verify` (Hitman unaligned `dst=0x52C098 head=8 tail=8`; both games 600f green)
7. PASS — `R4_clear_with_evidence` (no CdSync wake code; mode=1 polls ≠ missing wake)

**R3 landed (only behavioral CDVD code so far):** set `b1len`/`b2len` when dest1/dest2 fed; unaligned head/tail staging (+16/+80). Did **not** touch CdSync wake, WaitSema, or CNK.

**SDK compliance audit (2026-11-06 night):** in progress against `E:\usr\local\sce` — see **RESUME POINT §A**. Research only; flag deviations; do not patch yet.

**Quarantine:** Never apply CNK Alchemy host_signal 16/54/55, soft-arm, FCE0 force, virt-LBA, or +24008 hacks to Hitman/NFS.

---

## 5. Test-matrix worker

- Five phases + board protocol (above).  
- Prove-before-swap for R1–R5.  
- Lives in `verification/recovery/test-matrix-live-report.md`.  
- Last state: idle after R4 clear; watching for next proposal / optional R5.

---

## 6. CNK / Alchemy (quarantined from Hitman/NFS)

**Prior reports:** `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `cnk-nullbind-51ACEC-live-report.md`  
**A1–A4 + synthesis (2026-11-07):** `alchemy-rebuild-w1-…` … `w4-…`, **`alchemy-rebuild-synthesis-a1-a4-2026-11-07.md`**  
**Isolation tool:** `tools/ps2-alchemy-dumper/` → ISO `alchemy-map.json` (see §9)  
**Overnight crumbs:** `verification/host-session-2026-11-06-overnight-cnk-10p.json` / `10s.json`

### Combined picture (A1–A4)

| Layer | What CNK has |
|-------|----------------|
| **EE / “imports”** | Stripped `boot.elf`; **Intrinsic Alchemy v3.0 -0909 Static/Release**; ~**595** whole-string `ig*` classes (~717 tokens); no dyn imports |
| **Vtables / bind** | Factory `0x508930` (`*0x725F00` vt+8); bind registry BSS `*0x725F50`; null-bind `0x51AC80`→**vt+80**(tid)→**vt+84**; loadgate `0x10FCE0` (250×96) → finalize `0x110100` |
| **TOC** | ISO-only `ASSETS.GFC` (1830 files / 4327 blocks / **520 `.igb`**) → `ASSETS.GOB` STBLz/0 → IGB `@+0x28 DA FA`, `@+0x2C 0x80000005` |
| **IOP** | `igFileIO`/`igU*` **not on MODULES** → name-HLE (`0x12114` / stubs); retail **PADMAN**, **LIBSD**, CRI, … load as real IRX |
| **EE syscalls** | WaitSema/iSignalSema (2/16/45/47), GetThreadId, Sif* for LoadModule/RPC; CRT0 SetupThread/Heap |
| **Blocker** | EE bind/loadgate/IGB completion — **not** missing CreateSema |
| **5.0 kit** | Vocabulary only (skew vs 3.0); gaps: loadgate, igFileIO name, `0x725F50` tid map |

### Key addresses

| VA | Meaning |
|----|---------|
| `0x00108D28` | ELF / CRT0 entry (`boot.elf` = SLUS_206.49) |
| `0x00108F60` | App init (“main-ish”) |
| `0x0010FCE0` | Loadgate pump (“FCE0”) |
| `0x00110100` | Slot finalize / parse kick |
| `0x00725F50` | **Bind registry** pointer (BSS — zero until installer) |
| `0x00520160` | Installs bind object into `0x725F50` |
| `0x0051ACEC` | RA of crashing **vt+84** after **vt+80** lookup |

### Null-bind model (solved as a model)

- Forced FCE0 / `0x110100` without a live binder → lookup via `*0x725F50` **vt+80** returns null → **jalr vt+84** → `missing code @0`, `ra=0x51ACEC`.  
- Soft-arm without host FCE0: often **stuck at prims=2**.  
- **Live vtable dump (2026-11-07, offline RAM):** registry vt `0x6DF110` vt+80/`+84` **non-null** when installed; crash is **tid map miss** (`r2=0`), not stuffed slots. Soft-arm-hold clears `0x725F50`; arm45soft can keep registry with tid1 only.  
- **Next (observe only):** mid-site GetThreadId/`g_current` vs map at `0x51ACD4` only with explicit diagnostic approval — **no pointer stuffing** / no Alchemy host patches.

### Web / SDK research

| Source | Use |
|--------|-----|
| [YacaloX-Studios/cnk-decomp](https://github.com/YacaloX-Studios/cnk-decomp) | Best public CNK RE |
| TCRF CNK page | Exact Alchemy version strings |
| [mateon1 IGB gist](https://gist.github.com/mateon1/b123a53d824305767989ebc2ba3e5814) | Alchemy **3.2** IGB parser |
| [archive.org alchemy-kit](https://archive.org/details/alchemy-kit) | Alchemy **5.0** eval — concepts only (`C:\usr\alchemy`) |
| Official SCE 3.0.3 PDFs | **No Alchemy** strings; CDVD/pad/libsd harvest = shared HLE only (`sdk-pdf-quote-harvest-cnk-informed-2026-11-07.md`) |

**Not found:** Alchemy **3.0 PS2 SDK** source. Future goal: rebuild Alchemy 3.0 understanding from ELF knowledge only.

**CNK audio note:** keep **CRI ADX** from `E:\AI Browser Games\ps2_sdks\CRI_SDK_1.10_patch5.zip` — not in Sony SCE tree (`libsd` ≠ CRI).

---

## 7. PS2 SDK 3.0.3 (official install)

| Item | Value |
|------|--------|
| **Path (only)** | `E:\usr\local\sce` |
| **Size** | ~**1659 MB**, **7954** files |
| **Version** | Runtime Library **3.0.3**, **June 2005** (`readme-3.0.3.txt`, `libver.h` `SCE_LIBRARY_VERSION 0x3030`) |
| **Includes** | RTLibs + toolchain, Docs&Training, Extra Libraries, SCEE Tools |
| **R5 markers** | `ee\lib\libcdvd.a`, `common\include\libcdvd.h` (`sceCdSync`, `sceCdDiskReady`), `iop\modules\padman.irx`, `iop\modules\libsd.irx` |
| **Removed** | Entire **`C:\usr`** (silent RTLibs default path) — do **not** recreate |
| **Do not use** | `C:\usr\local\sce`, `E:\PS2_SDK` (empty), `E:\AI games\PS2_SDK` |
| **Rule file** | `.cursor/rules/ps2-sdk-research-path.mdc` |

**PDF extracts:** `verification/recovery/_sdk_pdf_extract/` (14 docs) — see RESUME POINT §B.

---

## 8. Archive `ps2_sdks` torrent folder (cleaned)

**Path:** `E:\AI Browser Games\ps2_sdks` (~832 MB after cleanup; was ~1.64 GB / 44 archives)

**Removed (14 obsolete Sony runtime/toolchain/tlib packs, ~845 MB):**  
DTL-S12000/12010/13010, EB-S8220, Runtime/Toolchain 2.0 fixed 7z, SCE-RT, SCE Tool-Libs 2.4.2, `tlib_250`–`255`.

**Kept (requested):** CRI SDK, CodeWarrior packs, CD/DVD generators + `cdgen150`, `iop281.tgz`, `ee001003_1.tgz`.

**Also left (undecided):** ProDG / NDK / ProView, LibDNAS, Sound Artist, QA, Super Bender, TIM2, archive meta.

**No PS2-dev-wiki archive** in that dump. **No Alchemy** in dump (prior sweep).

---

## 9. Custom PS2 disc dumper toolkit

Build **our own Windows** dumper from patterns — **do not** wrap or require upstream binaries.

README (every update) must:

1. Credit **[superg/redumper](https://github.com/superg/redumper)** (GPL-3.0).  
2. Credit **[N4gtan/mkps2iso](https://github.com/N4gtan/mkps2iso)** (`dumps2iso` / `mkps2iso`).  
3. Document **every** divergence, including **stripped** ideas/code.  
4. Note **GPL-3.0** obligations for redumper-derived logic; respect mkps2iso license if code is derived.  
5. State **Windows** primary target (CyberArcade Windows branch).

Rules: `.cursor/rules/ps2-disc-dumper-toolkit.mdc`, `.cursor/rules/redumper-derivative-readme.mdc`.  
Local tools already at `E:\AI games\mkps2iso-win64\` (reference only — not the product core).  
Scratch refs only: `tools/_refs/` (not product).

### Status (2026-11-07 ~06:30) — **Phase 1–3 VERIFIED (ISO + GOB/IGB + class map)**

| Item | Value |
|------|--------|
| Path | **`tools/ps2-alchemy-dumper/`** (v0.2.0) |
| Docs | `README.md` (credits/GPL/divergences/Windows), `LICENSE` (GPL-3.0), `DESIGN.md`, `docs/SCHEMA.md`, `docs/RESEARCH.md` |
| CLI | `map` / `list-iso` / **`verify`** / `optical` — own disc + ISO9660 + GFC + GOB STBL inflate + ELF class map |
| Schema | `alchemy-map.json` **v1.1** + `disc-toc.tsv` / `gfc-files.tsv` / `igb-samples.tsv` / `class-map.tsv` + optional `igb_heads/*.bin` |
| CNK gate | `verify` on `games/b49f2e…/disc.iso` → **20/20 PASS** (exit 0): GFC 1830/4327; GOB STBL verify; IGB `DA FA` incl. butanim; ELF 595 `ig*` + 47 raw `.igb`; no igFileIO on MODULES |
| Artifact | `tools/ps2-alchemy-dumper/out-cnk/` (also `out/cnk-phase3/`) |
| Optical | **Stub only** (`optical` subcommand) — redumper-inspired SPTI plan; no drive I/O yet |
| Constraints | Own Windows code; **no** upstream binary wrap; **no** `runtime/` / disc-fix / R5 / CNK game-file edits |

**Research summary (adopt / strip):**

- **redumper:** adopt sector/LBA + rip-vs-analyze + Windows drive-letter mindset; **strip** CDDA/scram/C2/refine/split/firmware/OmniDrive and any binary wrap.  
- **mkps2iso/dumps2iso:** adopt ISO-first path+LBA+size tables; **strip** XML rebuild, boot-logo crypto, Master Disc authoring, binary wrap. ISO9660 PVD walk first (UDF FID later if needed).

**Next implementation steps:**

1. Phase 4 — Windows SPTI DVD sector rip → `.iso` (own I/O).  
2. Multi-title `--va-profile` beyond CNK template.  
3. Optional fuller `.igb` extract / deeper IGB structure walk beyond heads.

---

## 10. PS2Dev org (homebrew — not Sony SDK)

Org: [github.com/orgs/ps2dev/repositories](https://github.com/orgs/ps2dev/repositories)

| Use | Repo |
|-----|------|
| CDVD / SIF / sema / kernel reference | **ps2sdk** |
| Graphics Synthesizer | **gsKit** |
| VU tooling | **openvcl**, **ps2toolchain-dvp** |

**No Alchemy** in PS2Dev. Prefer official `E:\usr\local\sce` for Sony contracts now.

---

## 11. Sly Cooper (texture / buildings)

**Reports:** `sly-gs-vu-live-report.md`, `sly-asset-binwalk-report.md`, samples in `sly-asset-samples/`

- Explore already loaded Paris: health ok, ~**12M prims**.  
- Art in hidden encrypted WAL / BRX inside `disc.iso`.  
- **Next:** shared GS **STQ / PATH3 / CLUT** — research complete enough; implementation parked.

---

## 12. BIOS

- Reference-only (`bios-reference-live-report.md`, `bios-zip-hybrid-restart-report.md`).  
- Labels: **70012** / **77001** family.  
- **Do not** execute BIOS; **do not** vendor BIOS blobs into the tree.

---

## 13. 2Captcha / Downloader / logs

### 2Cap

- Key in Settings localStorage: `ps2-twocaptcha-api-key`.  
- **Rotate** old key that appeared in earlier session artifacts.

### Downloader

- RomDL → merge useful bits into main **`downloader/downloader.js`** — not Settings; skip WebDL.  
- Plan: `verification/recovery/romdl-into-downloader-plan.md`.

### Logs

- Prefer dedicated **`logs/`** over scattering under `verification/`.

---

## 14. Cursor Command Center UI (`jarvis-cursor-ui`)

| Item | Detail |
|------|--------|
| Folder | `C:\PS2Recomp\jarvis-cursor-ui\` |
| Authoritative imagery | **`jarvis-cursor-ui/media/reference-command-center.png`** (boot splash **and** full UI target — exact match, no approximation). Cross-check: `reference-command-center-2.png`. `reference-calibrating-splash.png` is **not** the boot screen under current lock. |
| Mechanism | **Injection** (Custom CSS / workbench DOM) **required**. Overlays definitively out. Fail-safes: auto-disable on Cursor update; auto-disable on inject-break detect; caller owns update/fix/rebuild (no official-support concern). |
| Blueprint site | **`https://jarvis.institute/`** (not `jarvis.institution`) — pattern source; local PNG wins for pixel target |
| Branding | Full CORTANA UI (“Talk to CORTANA”, Suit Modes, F.R.I.D.A.Y. chrome); voice channel = **Cursor** coding agent |
| Plan | `jarvis_pro_recreation_a1985356.plan.md` |
| Activate | Reload after install |

Does not modify PS2 recomp runtime sources.

---

## 15. Future goals (logged, not started)

1. **Linux back-compat** with accumulated Windows-branch fixes.  
2. **Full TypeScript rewrite** of appropriate layers; **C++** (with **inline ASM** where justified) for hot paths.  
3. **Alchemy 3.0 rebuild** from ELF / IGB / GFC knowledge — **no source available**.

---

## 16. Self-healing / install-time ELF (proposed)

- Self-healing = priority **2** after disc-fix pair stable.  
- Install-time ELF walking proposed — not current fire drill.

---

## 17. Worker / todo posture

**Coordination:** `verification/recovery/worker-coordination.md`  
**Open follow-ups:** `verification/recovery/open-followups.md`  
**Live snapshot:** see **RESUME POINT §C**.

---

## 18. Hard rules (do not forget)

1. Engine-generic HLE; quarantine CNK Alchemy pulses from Hitman/NFS.  
2. Never blind-wake WaitSema **2**.  
3. Prove-before-swap via matrix board before R1–R5 behavioral patches.  
4. BIOS = reference only.  
4b. **PS2 SDK research:** **`E:\usr\local\sce` only.** Never recreate `C:\usr\local\sce`.  
5. Chrome + Edge only for product browser work.  
6. **No commits** until a stable build — then commit freely (user may pre-approve stable disc-fix commits).  
7. Simple-language status when reporting to the user.  
8. PCSX2 oracle path is dropped.  
9. **Custom PS2 disc dumper:** credit redumper + mkps2iso/dumps2iso; document all changes including stripped; Windows target; own code not wrappers. See `.cursor/rules/ps2-disc-dumper-toolkit.mdc`.  
10. **Periodically update this MASTER-CONTEXT** with completed and in-progress steps (crash / reload resilience).  
11. **Agent decides:** full authority to proceed without asking approval on every action; discuss only when needed; after discussion the agent still makes the final call.

---

## 19. Where to read next

| Need | File |
|------|------|
| **Cold start** | **RESUME POINT** (top of this file) |
| Disc-fix ↔ matrix board | `verification/recovery/discfix-matrix-board.json` |
| R1–R4 stable marker | `verification/recovery/DISCFIX-R1-R4-STABLE.md` |
| SDK PDF text | `verification/recovery/_sdk_pdf_extract/` |
| CNK ELF map | `verification/recovery/cnk-elf-alchemy-full-redo-report.md` |
| Alchemy web sources | `verification/recovery/alchemy-sdk-research-report.md` |
| Null-bind | `verification/recovery/cnk-nullbind-51ACEC-live-report.md` |
| Sly assets / GS | `verification/recovery/sly-asset-binwalk-report.md`, `sly-gs-vu-live-report.md` |
| WaitSema ownership | `verification/recovery/waitsema-createsema-trace-live-report.md` |
| Alchemy 5.0 eval kit (local) | `C:\usr\alchemy\` (44 IA files) |
| ps2tek mirror (local) | `C:\usr\alchemy\ps2tek\` |
| CNK Alchemy A1–A4 + synthesis | `alchemy-rebuild-w*-2026-11-07.md`, `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` |
| CNK-informed PDF harvest | `sdk-pdf-quote-harvest-cnk-informed-2026-11-07.md` |
| Custom Alchemy ISO dumper | `tools/ps2-alchemy-dumper/` (`README.md`, `DESIGN.md`, `docs/SCHEMA.md`) |

---

*End of MASTER-CONTEXT.*
