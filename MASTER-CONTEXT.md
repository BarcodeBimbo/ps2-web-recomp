# MASTER-CONTEXT — CyberArcade / PS2Recomp handoff

**Updated:** 2026-11-06 (~22:10 local)  
**Repo root:** `C:\PS2Recomp`  
**Branch posture:** `windows` branch — keep it clean. No commits until a stable build; then commit freely.

This file is the single handoff for humans and agents. Detailed evidence lives under `verification/recovery/` and `logs/`. Prefer those reports over re-deriving.

---

## 1. What this project is

**CyberArcade / PS2Recomp** — a PlayStation 2 recompiler / host runtime that runs recompiled EE game code on PC (native builds + web/GPU paths). Engine-generic HLE preferred over game-specific hacks.

**Product browser target:** **Chrome + Edge only.** Firefox, mobile UI, and controls redesign are back-burner.

---

## 2. Priority stack (current)

| Priority | Track | Status |
|----------|--------|--------|
| **Main** | Hitman Blood Money + NFS Most Wanted **disc-fix** (shared CDVD / `cdvdfsv`) | Active; R1–R3 cleared/verified; R4/R5 gated |
| **Patient zero (fps)** | God of War **60 fps** | Keep in mind; not the current disc-fix pair |
| **Main game choice** | NFS **or** CNK as long-term flagship | Undecided; CNK Alchemy research continues in quarantine |
| **Parked** | CNK deep play / Crash Bandicoot / software-renderer ×10 / mobile UI | Do not launch unless unparked |
| **Parked research** | Sly Cooper texture / GS (buildings) | Research done; implementation next is shared GS STQ/PATH3/CLUT |
| **Dropped** | PCSX2-as-oracle workflow | Do not reopen as primary truth source |
| **Reference-only** | BIOS zip (`70012` / `77001` family) | Never execute BIOS; never copy into repo as a ship artifact |
| **P2** | Self-healing runtime | Priority 2 — after disc-fix stability |
| **Proposed** | Install-time ELF walking | Proposed; not landed as product default |

**Standing rule:** Workers stay up until the user says done (no self-dismiss after one step).

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

### Problem model (simple)

- Disc **readers** were not correctly setting **readee length** fields and/or not waking **waiters** the Sony way.
- BIOS / reference reading confirms a **shared CDVD complete** contract (not Alchemy).
- Leftover **WaitSema(2)** is **libcdvd durable parking** — **never** blind `host_signal(2)`.
- Hitman and NFS share the same `cdvdfsv` path: N `0x1` → `read_to_ee` → `complete_call`. Not CNK Alchemy.

### Ranked rewrite gates (prove-before-swap)

| Rank | Item | Status (as of cycle 6) |
|------|------|-------------------------|
| R1 | SIF end | **cleared_with_evidence** (queue drains to 0) |
| R2 | WaitSema fidelity | **cleared_with_evidence** (sema 2 = observe parking; never pulse) |
| R3 | readee lengths / AlignReadBuffer | **verified_apply** in `runtime/src/iop/cdvdfsv.cpp` |
| R4 | sceCdSync / finish_read wake | **cleared_with_evidence** (cycle 7 — no wake code needed) |
| R5 | pad / sound | **still gated** (separate from CDVD) |

### Matrix protocol

1. Disc-fix posts `proposed_change` + evidence on the board.  
2. **Test-matrix** runs **5 phases** (boot → menu → first disc read → streaming → sustained run) with Sony-style pass checks.  
3. Disc-fix applies **only after** `verdict=pass` / `allow_discfix_apply`.  
4. **Prove-before-swap** before any R1–R5 behavioral rewrite. Earlier: matrix blocked R3 until R1 proven; cycle 3 also blocked R3 while R2 gated.

### Board cycles so far

1. FAIL — bundled R3 + R4 while R1/R2 locked  
2. PASS — `R1_clear_with_evidence`  
3. FAIL — `R3_readee_length_harden` while R2 gated  
4. PASS — `R2_clear_with_evidence`  
5. PASS — allow R3 apply  
6. PASS — `R3_post_apply_verify` (Hitman unaligned `dst=0x52C098 head=8 tail=8`; both games 600f green)
7. PASS — `R4_clear_with_evidence` (no CdSync wake code; mode=1 polls ≠ missing wake)

**R3 landed (only behavioral CDVD code so far):** set `b1len`/`b2len` when dest1/dest2 fed; unaligned head/tail staging (+16/+80). Did **not** touch CdSync wake, WaitSema, or CNK.

**CDVD ranked path R1–R4 is done.** Joint-stable marker: commit `1e04172` + `verification/recovery/DISCFIX-R1-R4-STABLE.md` (behavioral code already in `cdvdfsv.cpp` from earlier apply). Next: optional **R5 pad/sound**; push when ready.

**Quarantine:** Never apply CNK Alchemy host_signal 16/54/55, soft-arm, FCE0 force, virt-LBA, or +24008 hacks to Hitman/NFS.

---

## 5. Test-matrix worker

- Five phases + board protocol (above).  
- Prove-before-swap for R1–R5.  
- Lives in `verification/recovery/test-matrix-live-report.md`.  
- Stays watching for the next proposal after each verdict.

---

## 6. CNK / Alchemy (quarantined from Hitman/NFS)

**Reports:** `cnk-elf-alchemy-full-redo-report.md`, `alchemy-sdk-research-report.md`, `cnk-nullbind-51ACEC-live-report.md`  
**Overnight crumbs:** `verification/host-session-2026-11-06-overnight-cnk-10p.json` / `10s.json`

### Engine identity

- **Intrinsic Alchemy v3.0 -0909** (Static/Release), Sep 2003 — Vicarious Visions; studio pipeline nicknamed **Velocity**.  
- ~**673** `ig*` class-name strings in ELF.  
- Assets: **IGB** scenes inside **ASSETS.GFC** / **ASSETS.GOB** (STBL / zlib framing — not an Alchemy C++ class named “STBLz”).  
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

- Forced FCE0 / `0x110100` without a live binder → lookup via `*0x725F50` **vt+80** returns null (GetThreadId / map miss) → code still **jalr vt+84** → `missing code @0`, `ra=0x51ACEC`.  
- Soft-arm (+45) without host FCE0: registry often clear; **stuck at prims=2**.  
- **Latest observation:** soft-arm **20K frames**, still **2 prims**.  
- **Next:** dump **live vtable** at `*ee32(0x725F50)` under soft-arm vs forced-FCE0 (slots 20/21/27); log tid vs map — **no pointer stuffing**.

### Web / SDK research

| Source | Use |
|--------|-----|
| [YacaloX-Studios/cnk-decomp](https://github.com/YacaloX-Studios/cnk-decomp) | Best public CNK RE — GFC/GOB/IGB docs, same ELF entry |
| TCRF CNK page | Exact Alchemy version strings |
| ZenHAX GOB/STBL threads | Archive framing |
| [mateon1 IGB gist](https://gist.github.com/mateon1/b123a53d824305767989ebc2ba3e5814) | Alchemy **3.2** IGB parser (format v6) — **near** CNK era, not identical |
| [archive.org alchemy-kit](https://archive.org/details/alchemy-kit) | Alchemy **5.0** eval + docs — **concepts only** |
| Private Reddit / Alchemy 3.0 RE repo | **Pending approval** — user also searching Internet Archive |

**Not found publicly:** Alchemy **3.0 PS2 SDK** source. Ignore blockchain “Alchemy” GitHub noise.

---

## 7. PS2Dev org (homebrew — not Sony SDK)

Org: [github.com/orgs/ps2dev/repositories](https://github.com/orgs/ps2dev/repositories)

| Use | Repo |
|-----|------|
| CDVD / SIF / sema / kernel reference | **ps2sdk** |
| Graphics Synthesizer | **gsKit** |
| VU tooling | **openvcl**, **ps2toolchain-dvp** |
| Packed ELF notes | **ps2-packer** |
| Skip for day-to-day recomp | Full toolchain mirrors, docker, lua/lwip/fluidsynth, mymc, etc. |

**No Alchemy** in PS2Dev. Use for HLE behavior reference, not CNK bind/FCE0.

---

## 8. Sly Cooper (texture / buildings)

**Reports:** `sly-gs-vu-live-report.md`, `sly-asset-binwalk-report.md`, samples in `sly-asset-samples/`

- Explore already loaded Paris: health ok, ~**12M prims** (e.g. 11.8M / 3600f).  
- Art lives in a **hidden encrypted WAL** of **BRX** levels inside `disc.iso` (ISO directory only shows boot + IOP).  
- Strict VU did **not** restore buildings. Soft vs WebGPU ~**28%** diverge late, but buildings missing in **both** → not “soft-only.”  
- **Next:** shared GS **STQ / PATH3 / CLUT** texturing — not “assets never loaded.”  
- Implementation parked until prioritized; research is complete enough to aim there.

---

## 9. BIOS

- Reference-only research on zip / hybrid notes (`bios-reference-live-report.md`, `bios-zip-hybrid-restart-report.md`).  
- Labels of interest: **70012** / **77001** family.  
- **Do not** execute BIOS; **do not** vendor BIOS blobs into the tree.

---

## 10. 2Captcha / Downloader / logs

### 2Cap

- Key lives in **Settings localStorage**: `ps2-twocaptcha-api-key` (also job JSON to worker).  
- **Not** `process.env` / `TWOCAPTCHA_API_KEY`.  
- Scrub report: tree clean of leftover env wiring (`twocaptcha-key-scrub-report.md`).  
- **Rotate** the old key that appeared in earlier session artifacts.

### Downloader

- **RomDL** is third-party tooling under `RomDL/` (phantomwright fixed for local tsc).  
- Plan: merge useful bits into main **`downloader/downloader.js`** (and related scripts) — **not** Settings UI; **skip WebDL**.  
- Plan note: `verification/recovery/romdl-into-downloader-plan.md`.

### Logs

- Runtime / worker logs live under dedicated **`logs/`** (see `logs-relocation-report.md`).  
- Prefer `PS2_LOGS` / that folder over scattering under `verification/`.

---

## 11. Self-healing / install-time ELF (proposed)

- **Self-healing runtime** = priority **2** (after disc-fix pair is stable).  
- **Install-time ELF walking** proposed as a way to map structures earlier — not the current fire drill.

---

## 12. Worker / todo posture

**Coordination:** `verification/recovery/worker-coordination.md`  
**Open follow-ups:** `verification/recovery/open-followups.md`

Classic seven tracks (plus extras that spun up):

1. Disc-fix (Hitman/NFS)  
2. Test-matrix  
3. CNK null-bind (model solved; observe next)  
4. Sly GS/VU (+ asset bin-walk **done**)  
5. WaitSema / CreateSema  
6. BIOS reference  
7. CNK ELF Alchemy full redo (+ Alchemy SDK web research)

**Todos snapshot from evening session:** **2 / 8** marked done (Sly GS/VU + Sly asset bin-walk); disc-fix/matrix and others still in progress or parked as above.

**Workers stay up until the user says done.**

---

## 13. Hard rules (do not forget)

1. Engine-generic HLE; quarantine CNK Alchemy pulses from Hitman/NFS.  
2. Never blind-wake WaitSema **2**.  
3. Prove-before-swap via matrix board before R1–R5 behavioral patches.  
4. BIOS = reference only.  
5. Chrome + Edge only for product browser work.  
6. **No commits** until a stable build — then commit freely (user may pre-approve stable disc-fix commits).  
7. Simple-language status when reporting to the user.  
8. PCSX2 oracle path is dropped.  
9. **Custom PS2 disc dumper toolkit:** Build **our own Windows** dumper from patterns (do **not** wrap upstream binaries). README (every update) must credit both [superg/redumper](https://github.com/superg/redumper) and [N4gtan/mkps2iso](https://github.com/N4gtan/mkps2iso) (`dumps2iso`/`mkps2iso`), document every divergence including stripped ideas, and note GPL-3.0 implications from redumper-derived logic. Both upstreams ship Windows builds (not Linux-only). See `.cursor/rules/ps2-disc-dumper-toolkit.mdc`.

---

## 14. Where to read next

| Need | File |
|------|------|
| Disc-fix ↔ matrix board | `verification/recovery/discfix-matrix-board.json` |
| CNK ELF map | `verification/recovery/cnk-elf-alchemy-full-redo-report.md` |
| Alchemy web sources | `verification/recovery/alchemy-sdk-research-report.md` |
| Null-bind | `verification/recovery/cnk-nullbind-51ACEC-live-report.md` |
| Sly assets | `verification/recovery/sly-asset-binwalk-report.md` |
| Sly GS/VU | `verification/recovery/sly-gs-vu-live-report.md` |
| WaitSema ownership | `verification/recovery/waitsema-createsema-trace-live-report.md` |
| Overnight CNK | `verification/host-session-2026-11-06-overnight-cnk-10p.json` |

---

*End of MASTER-CONTEXT.*
