# SDK R1–R5 compliance report

**Date:** 2026-11-07  
**Track:** E (formal compliance roll-up)  
**Mode:** Research / report only — **no runtime patches**  
**SDK root:** `E:\usr\local\sce` only (Runtime Library 3.0.3; `SCE_LIBRARY_VERSION 0x3030`)  
**Product pair:** Hitman Blood Money + NFS Most Wanted disc-fix (joint-stable `1e04172`)  
**Stable marker:** `verification/recovery/DISCFIX-R1-R4-STABLE.md`

---

## Executive summary

R1–R4 are **product-cleared** on the Hitman/NFS matrix. This formal SDK audit finds **no blocking compliance gap** that would reopen R1–R4 for those titles. The only behavioral CDVD change remains R3 (`cdvdfsv.cpp` readee lengths / unaligned staging). R4’s “no wake code” stance matches Sony poll vs block modes; **`sceCdDiskReady` always returning `2` (`SCECdComplete`) is the highest-priority observe-only deviation**. R5 pad/sound remains **gated** — inventory complete, no HLE apply.

| Rank | Product status | SDK audit status | Patch under this track? |
|------|----------------|------------------|-------------------------|
| **R1** SIF end | `cleared_with_evidence` | **Compliant (low HLE deltas)** | No |
| **R2** WaitSema fidelity | `cleared_with_evidence` | **Compliant; reinforce never `host_signal(2)`** | No |
| **R3** readee / AlignReadBuffer | `verified_apply` | **Behavior MATCH; layout is private/RE** | No further |
| **R4** sceCdSync / finish_read | `cleared_with_evidence` | **Sync MATCH; DiskReady always-2 FLAGGED** | No |
| **R5** pad / sound | **still gated** | **Inventory only (gated)** | No |

---

## Per-R product vs SDK audit

### R1 — SIF end / orphan RPC

| | |
|--|--|
| **Product** | Soft IOP reset drains SIF0 outbound, then `complete_orphaned_rpc()` emits REND end packets so EE CallRpc WaitSema waiters unblock. Matrix: outgoing queue → 0. |
| **SDK** | EE/IOP SIF docs: CallRpc WAIT parks until SIF CMD completion; reboot invalidates in-flight RPC; retail/ps2sdk-style REND = `0x80000008`. |
| **Audit** | **MATCH** on REND id, orphan end-packet, soft-reset drain-then-settle. |
| **Deviations (observe)** | D1 synthesize success end packets without full module teardown (low); D2 soft BOOTEND republish loop (low HLE); D3 no reboot-notify handler surface (n/a Hitman/NFS). |
| **Detail** | `sdk-compliance-r1-sif.md` |

### R2 — WaitSema / CreateSema fidelity

| | |
|--|--|
| **Product** | Sema **2** = durable libcdvd-class parking (init=0, max=255, never deleted); **never `host_signal(2)`** on Hitman/NFS. |
| **SDK** | Kernel Overview: Wait parks at count 0; Signal wakes. Counting init-0 = “await producer.” |
| **Audit** | **MATCH** Wait/Signal mechanics + live create shape. Same numeric id across titles is **coincidence** (different create_ra). |
| **Deviations (observe)** | D1 CNK `host_signal_sema(2)` in `igfileio.cpp` — **quarantine**, must not land on disc-fix pair; D2 virt UI pulses 16/54/55 — CNK-scoped; D3 IOP Kernel *Reference* WaitSema page not in extract set (Overview + headers sufficient). |
| **Hard rule** | Blind wake of id 2 fakes CD completion — **forbidden** on joint-stable path. |
| **Detail** | `sdk-compliance-r2-waitsema.md`, `waitsema-createsema-trace-live-report.md` |

### R3 — readee / AlignReadBuffer

| | |
|--|--|
| **Product** | `read_to_ee`: preserve dest1/dest2; set **b1len/b2len** when dests fed; unaligned head/tail at **+16/+80**; curReadPos via eeaddr2. Smoke: Hitman `dst=0x52C098 head=8 tail=8`. |
| **SDK** | Public PDFs + `libcdvd.h`: **no** `AlignReadBuffer` symbol. Normative text = 64-byte alignment **compensation** + `sceCdGetReadPos` progress / edge caveat. Closest official EE symbols: `_sceCd_rd_intr_data`, `_sceCd_Read_cur_pos` (`libcdvd.a`). |
| **Audit** | **MATCH** on alignment-compensation *behavior* and GetReadPos intent. Layout (+0/+4/+8/+12/+16/+80/~144B) is **implementation evidence** (retail naming / RE), not public PDF prose. |
| **Deviations (observe)** | D1 virt-LBA / Alchemy stream plant — **CNK quarantine**; D2 host may pre-copy into staged dest (medium/research); D3 exact layout absent from PDFs (doc gap); D4 GetReadPos “16-sector units” wording vs byte return (SDK ambiguity). |
| **Detail** | `sdk-compliance-r3-readee.md` |

### R4 — sceCdSync / finish_read / DiskReady

| | |
|--|--|
| **Product** | `sceCdSync`: mode `1` or `17` (`0x01`/`0x11`) poll busy→0/1; else block via `sync_waiters`. `finish_read` already wakes waiters. Hitman poll-heavy (`~sceCdSync(1)`) matches sample. **No extra wake patch.** DiskReady HLE: **always `2`**. |
| **SDK** | EE Ref: modes `0x00` block / `0x01` poll. IOP Ref adds `0x10`/`0x11` (include EE-issued cmds). DiskReady returns **`0x02` SCECdComplete** / **`0x06` SCECdNotReady**; mode 0 blocks until ready. Sample: Sync(1) poll + Sync(0) block + DiskReady(0) gates. |
| **Audit** | Sync modes **MATCH**. DiskReady constant **2** matches Complete **value**, but **ignores mode and never NotReady** → **FLAG**. |
| **Deviations (observe)** | **D1 (priority):** DiskReady always-2 / never blocks — wrong if title needs NotReady during spin-up, tray, or media detect. D2 single busy bit approx for 0x10/0x11 dual-queue (low). D3 Sync block without IOP thread returns 0 (edge). |
| **Detail** | `sdk-compliance-r4-cdsync.md` |

### R5 — pad / sound (**GATED**)

| | |
|--|--|
| **Product** | SIO2 + SPU2 **MMIO** HLE + pad/SPU2 trace env. **No** padman / libsd / sdrdrv HLE module set comparable to CDVD. Guest titles load real IRX. Leftover WaitSema (Hitman 7; NFS 17/23/29/30/32) **unclassified**. |
| **SDK** | Assets present: `padman.irx`, `libsd.irx`, `sio2man.irx`, `sdrdrv.irx`; `libpad.h`, `libsd.h`, `libsdr.h`, `sdrcmd.h`. Stack: libpad↔padman↔sio2man; libsdr(`rSd*`)↔sdrdrv↔libsd↔SPU2. |
| **Audit** | **Inventory complete; HLE audit not opened.** Gate holds. |
| **Apply** | **Forbidden** until matrix / user unlocks R5 beyond observe. Do not blind-wake leftover semas. |
| **Detail** | `sdk-compliance-r5-pad-sound-inventory.md` |

---

## Deviation register (observe-only — do not patch from this report)

| ID | Rank | Severity | Flag |
|----|------|----------|------|
| R1-D1 | R1 | low | Orphan RPC end packets synthesize success without full IOP teardown |
| R1-D2 | R1 | low | Soft-reset BOOTEND republish loop is HLE policy, not PDF numeric |
| R2-D1 | R2 | quarantine | CNK `host_signal(2)` must stay off Hitman/NFS |
| R3-D1 | R3 | quarantine | Virt LBA / stream-sector host assemble = CNK only |
| R3-D2 | R3 | medium | Host may pre-fill AlignReadBuffer dests before EE callback |
| R3-D3 | R3 | doc gap | +16/+80/144B layout not in public PDFs |
| R3-D4 | R3 | ambiguity | GetReadPos quantum wording vs byte return |
| **R4-D1** | **R4** | **FLAG** | **`sceCdDiskReady` always returns 2; ignores mode; never `SCECdNotReady`** |
| R4-D2 | R4 | low | 0x10/0x11 share one busy bit |
| R5-* | R5 | gated | No padman/libsd HLE; leftover semas unclassified — observe only |

**No R1–R3 blocking deviation for the Hitman/NFS joint-stable path.**  
**R4-D1 is the primary compliance flag for future drive-state work — research only until asked.**

---

## R5 inventory (gated) — short form

- **Gate:** `still gated` / `inventory_only` / no `allow_discfix_apply`.  
- **SDK:** padman + libsd (+ sio2man, sdrdrv) IRX and headers confirmed under `E:\usr\local\sce`.  
- **Runtime gap:** MMIO SIO2/SPU2 yes; CDVD-style padman/libsd `register_hle_*` **no**.  
- **Next when unlocked:** classify leftover WaitSema with `PS2_TRACE_PAD` / `PS2_TRACE_SPU2` / SIF tags — never blind `host_signal`.

Full inventory: `sdk-compliance-r5-pad-sound-inventory.md`.

---

## Pointers (siblings + sources)

### Per-R compliance notes (siblings — merged)

| File | Role |
|------|------|
| `verification/recovery/sdk-compliance-r1-sif.md` | R1 SIF end / orphan RPC |
| `verification/recovery/sdk-compliance-r2-waitsema.md` | R2 WaitSema fidelity |
| `verification/recovery/sdk-compliance-r3-readee.md` | R3 AlignReadBuffer / readee |
| `verification/recovery/sdk-compliance-r4-cdsync.md` | R4 CdSync / DiskReady |
| `verification/recovery/sdk-compliance-r5-pad-sound-inventory.md` | R5 gated inventory |

### Quote harvest (Track B)

| File | Role |
|------|------|
| `verification/recovery/sdk-pdf-quote-harvest-r1r5.md` | Verbatim PDF quotes: alignment/GetReadPos, CdSync/DiskReady modes, padman/libpad, libsd/libsdr |

### Product evidence

| File | Role |
|------|------|
| `verification/recovery/DISCFIX-R1-R4-STABLE.md` | Joint-stable R1–R4 marker |
| `verification/recovery/discfix-matrix-board.json` | Matrix board through R4; R5 observe gated |
| `verification/recovery/waitsema-createsema-trace-live-report.md` | Sema ownership |
| `verification/recovery/_sdk_pdf_extract/*.pdf.txt` | 14 official PDF text extracts |
| `MASTER-CONTEXT.md` §A / §B | Resume point for this audit |

### Runtime (read-only under this track)

- `runtime/src/iop/sif.cpp` — R1  
- `runtime/src/kernel.cpp`, `runtime/src/iop/libs.cpp` — R2  
- `runtime/src/iop/cdvdfsv.cpp` (`read_to_ee`) — R3  
- `runtime/src/iop/cdvd.cpp` (`sceCdSync` / `sceCdDiskReady` / `finish_read`) — R4  
- `runtime/src/iop/sio2.cpp`, `runtime/src/iop/spu2.cpp` — R5 MMIO only  

---

## Next actions for the user

1. **Accept R1–R4 compliance posture** — no disc-fix reopen required for Hitman/NFS; keep prove-before-swap.  
2. **Decide whether to chase R4-D1** (DiskReady always-2) as a *future* research/design item — still **no patch** until you ask; needs a drive-state model before any NotReady returns.  
3. **Keep R5 gated** until you want leftover WaitSema classification (pad vs sound) with traces — inventory is ready.  
4. **Optional doc follow-ups:** IOP Kernel Reference WaitSema extract; deepen Sound PDF interrupt/transfer tables if R5 opens; resolve GetReadPos quantum ambiguity if a title mis-reads progress.  
5. **Do not** apply CNK quarantine pulses, `host_signal(2)`, CdSync wake hacks, or padman/libsd HLE from this report.  
6. Reload Cursor if Command Center UI is missing (unrelated to this track; see MASTER-CONTEXT §D).

---

## Merge / completeness

| Sibling | Merged? |
|---------|---------|
| `sdk-pdf-quote-harvest-r1r5.md` | Yes |
| `sdk-compliance-r1-sif.md` … `r4-cdsync.md` | Yes |
| `sdk-compliance-r5-pad-sound-inventory.md` | Yes |

**Track E status:** `complete` — roll-up filed; research only; no runtime edits.
