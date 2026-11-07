# MASTER-CONTEXT — CyberArcade / PS2Recomp handoff

**Updated:** 2026-11-06 (~23:49 local)  
**Repo root:** `C:\PS2Recomp`  
**Branch posture:** `windows` branch — keep it clean. No commits until a stable build; then commit freely.

This file is the single handoff for humans and agents. Detailed evidence lives under `verification/recovery/` and `logs/`. Prefer those reports over re-deriving.

**Stasis:** After this update, leave work in place until the user returns. Do not start new tracks unless they ask.

---

## RESUME POINT — pick up here (do not ask the user to re-explain)

**Session cut-off:** 2026-11-06 ~23:49 local. User asked for MASTER-CONTEXT + this resume block only — **no new work**.

### A) R1–R5 official SDK audit (research only)

| Item | Product status | SDK audit status | Where left off |
|------|----------------|------------------|----------------|
| **R1** SIF end | `cleared_with_evidence` (joint-stable `1e04172`) | **Pending formal compliance write-up** | Compared informally to EE/IOP SIF PDFs + `sif.cpp` orphan/end-packet path; no signed compliance report filed yet |
| **R2** WaitSema fidelity | `cleared_with_evidence` (never `host_signal(2)`) | **Pending** | Ownership already in `waitsema-createsema-trace-live-report.md`; not yet line-audited vs IOP Kernel PDF WaitSema sections |
| **R3** readee / AlignReadBuffer | **`verified_apply`** in `runtime/src/iop/cdvdfsv.cpp` | **In progress / partial** | Code + comments claim Sony b1len/b2len + unaligned +16/+80; public `libcdvd.h` has no AlignReadBuffer (internal EE). Need Device PDF + samples vs `read_to_ee` (~L49–236) |
| **R4** sceCdSync / finish_read | `cleared_with_evidence` (no wake code) | **Partial** | IOP HLE in `runtime/src/iop/cdvd.cpp` L108–116 (`mode==1\|\|17` poll busy; else block). SDK: `sceCdSync` / `sceCdDiskReady` in `E:\usr\local\sce\common\include\libcdvd.h` L279–282; sample poll in `ee\sample\cdvd\smp_ee\main.c`. DiskReady HLE always returns `2` — flag if audit finds wrong constant |
| **R5** pad / sound | **still gated** (no disc-fix apply) | **Not started as HLE audit** | SDK assets present: `padman.irx`, `libpad.h`, `libsd.irx`, `libsd.h`, `libsdr.h`. Runtime has SIO2/pad trace env, **no** padman/libsd HLE module set comparable to CDVD. PDF sound/device extracts ready for when R5 opens |

**Audit rules:** research only; **flag deviations, do not patch** unless user asks. Official tree: **`E:\usr\local\sce` only**.

**Next resume action for audit:** finish Device Reference text hunt for `sceCdSync` mode meanings + AlignReadBuffer / readee layout; write per-R compliance notes; then R5 API surface inventory only (still gated).

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

**Hunt status:** extractor keyword pass done. **No Alchemy / Intrinsic hits** in those extracts. **Deep read / quote harvest for CDVD AlignReadBuffer, sceCdSync modes, padman, libsd stack not finished** — interrupted by cleanup / UI / MASTER-CONTEXT.

**Not extracted yet (optional later):** graphics/movie/network EE+IOP overviews/refs, Docs&Training PDFs under `E:\usr\local\sce\Docs&Training\`, tips beyond `cdvdtips`.

**Helper script:** `verification/recovery/_extract_sdk_pdfs.py` (needs Python 3.10 + `pypdf`).

**Next resume action:** grep/read Device Reference + Sound extracts; produce the deferred R1–R5 compliance report.

### C) Active workers — last known state (stasis)

| ID | Track | Last known |
|----|--------|------------|
| w1 | Disc-fix Hitman/NFS | R1–R4 done; R5 gated; joint-stable `1e04172` + `DISCFIX-R1-R4-STABLE.md` |
| w2 | Test-matrix | Idle after R4 clear PASS; watching board; no soak |
| w3 | CNK null-bind `51ACEC` | Read-only observe; soft-arm still 2 prims; next live vtable dump |
| w4 | Sly GS/VU | **Completed** research; next STQ/PATH3/CLUT when prioritized |
| w4b | Sly asset bin-walk | **Done** |
| w5 | WaitSema / CreateSema | Ownership report done; observe-only |
| w6 | BIOS zip reference | Reference-only; never execute |
| w7 | CNK ELF Alchemy redo | Reports exist; Alchemy 3.0 source still not found |

Standing rule: workers persist until user says done — currently **stasis / no new launches**.

### D) jarvis-cursor-ui

| Item | Value |
|------|--------|
| Folder | `C:\PS2Recomp\jarvis-cursor-ui\` |
| VSIX | `C:\PS2Recomp\jarvis-cursor-ui\jarvis-cursor-ui-0.2.0.vsix` |
| Install | **Succeeded** via `cursor --install-extension` on the VSIX (folder path install **fails** — CLI wants ID or `.vsix`) |
| Design | Command Center look (dark navy, cyan) from jarvis.institute layout patterns |
| Voice | **Cursor coding-agent voice** — not JARVIS persona |
| Activate | **Reload Cursor window**, then activity bar **Command Center** + theme **JARVIS Command** |

### E) In-flight terminals / installs

| Item | State |
|------|--------|
| `C:\usr` delete | **Done** (removed); do not recreate |
| `E:\PS2_SDK` poll | Finished **empty** — obsolete target |
| PDF extract job | **Succeeded** (14 docs) |
| cursor.cmd locate | Found: `C:\Program Files\cursor\resources\app\bin\cursor.cmd` |
| VSIX install | **Succeeded** exit 0 |
| R1–R5 compliance report | **Not written** (audit incomplete) |
| No other intentional long-running installs | — |

### F) One-liner for next agent

1. Read this **RESUME POINT**.  
2. Continue **SDK PDF deep-read → R1–R5 compliance flags** (research only) using `E:\usr\local\sce` + `_sdk_pdf_extract/`.  
3. Remind user to **reload** if Command Center UI missing.  
4. Do **not** patch disc-fix/R5 or touch CNK quarantine unless asked.

---

## 1. What this project is

**CyberArcade / PS2Recomp** — a PlayStation 2 recompiler / host runtime that runs recompiled EE game code on PC (native builds + web/GPU paths). Engine-generic HLE preferred over game-specific hacks.

**Product browser target:** **Chrome + Edge only.** Firefox, mobile UI, and controls redesign are back-burner.

---

## 2. Priority stack (current)

| Priority | Track | Status |
|----------|--------|--------|
| **Main** | Hitman Blood Money + NFS Most Wanted **disc-fix** (shared CDVD / `cdvdfsv`) | R1–R4 joint-stable; R5 gated; SDK compliance audit in progress |
| **Patient zero (fps)** | God of War **60 fps** | Keep in mind; not the current disc-fix pair |
| **Main game choice** | NFS **or** CNK as long-term flagship | Undecided; CNK Alchemy research continues in quarantine |
| **Parked** | CNK deep play / Crash Bandicoot / software-renderer ×10 / mobile UI | Do not launch unless unparked |
| **Parked research** | Sly Cooper texture / GS (buildings) | Research done; implementation next is shared GS STQ/PATH3/CLUT |
| **Dropped** | PCSX2-as-oracle workflow | Do not reopen as primary truth source |
| **Reference-only** | BIOS zip (`70012` / `77001` family) | Never execute BIOS; never copy into repo as a ship artifact |
| **P2** | Self-healing runtime | Priority 2 — after disc-fix stability |
| **Proposed** | Install-time ELF walking | Proposed; not landed as product default |
| **Future** | Linux back-compat with fixes | Logged — not started |
| **Future** | Full TypeScript rewrite; C++ (+ inline ASM) for hot paths | Logged — not started |
| **Future** | Alchemy 3.0 rebuild from ELF knowledge (no source available) | Logged — research only until source appears |

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

**Reports:** `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `cnk-nullbind-51ACEC-live-report.md`  
**Overnight crumbs:** `verification/host-session-2026-11-06-overnight-cnk-10p.json` / `10s.json`

### Engine identity

- **Intrinsic Alchemy v3.0 -0909** (Static/Release), Sep 2003 — Vicarious Visions; studio pipeline nicknamed **Velocity**.  
- ~**673** `ig*` class-name strings in ELF.  
- Assets: **IGB** scenes inside **ASSETS.GFC** / **ASSETS.GOB** (STBL / zlib framing).  
- IOP helper name: `igFileIO.irx` (host often cannot load as ELF IRX; HLE around it).

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
- **Next:** dump **live vtable** at `*ee32(0x725F50)` under soft-arm vs forced-FCE0 — **no pointer stuffing**.

### Web / SDK research

| Source | Use |
|--------|-----|
| [YacaloX-Studios/cnk-decomp](https://github.com/YacaloX-Studios/cnk-decomp) | Best public CNK RE |
| TCRF CNK page | Exact Alchemy version strings |
| [mateon1 IGB gist](https://gist.github.com/mateon1/b123a53d824305767989ebc2ba3e5814) | Alchemy **3.2** IGB parser |
| [archive.org alchemy-kit](https://archive.org/details/alchemy-kit) | Alchemy **5.0** eval — concepts only |
| Official SCE 3.0.3 PDFs | **No Alchemy** strings in extracted device/sound/SIF set |

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
| VSIX | `C:\PS2Recomp\jarvis-cursor-ui\jarvis-cursor-ui-0.2.0.vsix` (**installed**) |
| Blueprint site | **`https://jarvis.institute/`** (not `jarvis.institution` — that host fails) |
| Look | Dark navy + cyan Command Center panels; large File Map webview |
| Voice | **Cursor coding agent** — not JARVIS persona / “Talk to Jarvis” |
| Activate | **Reload Cursor window** |

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
| Command Center UI | `jarvis-cursor-ui/README.md` |

---

*End of MASTER-CONTEXT.*
