# BIOS zip live reference (ROM0 → HLE)

**Track:** BIOS zip (#7) — reference only.  
**Date:** 2026-11-06  
**Source zip:** `e:\AI Browser Games\ps2-bios-usa.zip` (still present).  
**Prior:** `verification/recovery/bios-zip-hybrid-restart-report.md`

## Hard rules (honored)

- REFERENCE ONLY — BIOS was string/ROMDIR-scanned offline; **not** loaded into browser, ps2run, or runtime.
- Temp extracts deleted after scan; **no BIOS binaries** left in the repo.
- Does **not** block disc-fix. Facts below feed R3/R1/R2/R4 audit targets.

## Preferred ROM sets

| Set | Image | ROMVER | VERSTR | Use |
|---|---|---|---|---|
| **SCPH-70012** | `.BIN` 4 MiB | `0200AC20040614` | System ROM 5.0 06/14/04 A | **Best default** for mid-gen CDVD/SIF contracts |
| **SCPH-77001** | `.ROM0` (+`.ROM1`) | `0220AC20060210` | System ROM 5.0 02/10/06 A | Matches stub era (`runtime` stubs `0220EC20060210`) |
| SCPH-39001 | `.BIN` | (older 1.60) | — | Early fat diffs only |
| SCPH-90001 | `.ROM0` | late 2.30 | — | Late / NVM; not primary |

**Ignore:** `__MACOSX/` noise; **`.DIFF`** files (~0.06% nonzero — packaging junk, not a real ROM plane).

**Contract note:** Retail **CDVDFSV** blobs in 70012 and 77001 are **byte-identical** (33717 B). Base FSV contracts do not diverge between these two. **XCDVDFSV** differs slightly (58197 vs 58413) — only matters if a game loads the X- variant; Hitman/NFS disc-fix should assume classic `CDVDFSV`.

## ROM0 modules that matter for HLE

From `IOPBTCONF` (identical on 70012 & 77001 boot path):

```
… → SIFMAN → SIFCMD → REBOOT → LOADFILE → CDVDMAN → CDVDFSV → SIFINIT → FILEIO → … → EESYNC
```

| ROM0 name | Role | HLE home | Disc-fix relevance |
|---|---|---|---|
| **CDVDFSV** | EE↔IOP CD N/S RPC server | `runtime/src/iop/cdvdfsv.cpp` | **Primary** — readee / curReadPos / complete |
| **CDVDMAN** | IOP-side disc driver API | `runtime/src/iop/cdvd.cpp` | sceCdSync / busy / DiskReady |
| **XCDVDFSV** / **XCDVDMAN** | Extended variants | same HLE if bound | Secondary; ignore unless guest loads X- |
| **SIFCMD** / **SIFMAN** | RPC bind / DMA / end packets | `runtime/src/iop/sif.cpp` | R1 — `complete_call` must reply |
| **THREADMAN** | WaitSema / iSignalSema | `runtime/src/iop/libs.cpp` | R2 — fidelity, not blind host_signal |
| **FILEIO** | EE file RPC | sif FILEIO HLE | Separate from CDVD path |
| **KERNEL** / **LOADCORE** / **EESYNC** | Boot / EE sync | kernel path | Boot contracts only |

## Concrete HLE audit targets (for disc-fix)

Ranked rewrites on the matrix board: `R1_SIF_end`, `R2_WaitSema_fidelity`, `R3_readee`, `R4_CdSync`.

### R3 — cdvdfsv read completion (highest leverage for Hitman + NFS)

Retail shape that HLE must match on **every** normal EE read (`kJobFsvRead`):

1. Copy sector payload → EE `dst` (args+8).
2. **readee** → `eeaddr1` (args+16): interrupt/align block for `_CdAlignReadBuffer`  
   - Preserve dest pointers EE already staged at +8/+12.  
   - Do not wipe a live 144 B block blindly.
3. **curReadPos** → `eeaddr2` (args+20): write **byte count** (`count * 2048`).  
   - Without this, `sceCdGetReadPos` stays 0 and guests stall even if SIF end fires.
4. Then **`sif::complete_call(0x80000595)`** (N-command RPC end).

**Args layout (N read / stream read):**

| Offset | Field |
|---|---|
| +0 | sector (LSN) |
| +4 | count (sectors) |
| +8 | dst (EE buffer) |
| +16 | eeaddr1 (readee / `_rd_intr_data`) |
| +20 | eeaddr2 (curReadPos) |

**RPC ids to keep honest:**

| Id | Role in HLE today |
|---|---|
| `0x80000595` | N-commands (read method `0x01`, stream `0x09`, IOP read `0x0D`, …) — **must hold then complete** |
| `0x80000593` | S-commands (status/clock/disk type) |
| `0x80000597` | SearchFile |
| `0x8000059A` / `0x8000059C` | DiskReady → return **2** |

**Audit checks for disc-fix (generic, both games):**

- [ ] `g_read_eeaddr1` / `g_read_eeaddr2` stashed on schedule and still valid at job fire  
- [ ] Every `kJobFsvRead` writes curReadPos **before** `complete_call`  
- [ ] `kJobFsvIopRead` path also ends with `complete_call(0x80000595)`  
- [ ] No CNK-only virt-LBA / host_signal(16/54/55) / +24008 logic applied to Hitman/NFS  

### R1 — SIF RPC end

- Held calls for `0x80000595` must leave via `sif::complete_call` → `reply_call`.  
- Missing end ⇒ EE WaitSema on RPC forever (seen historically on NFS when descriptors never issued).  
- Assert under load: outgoing end packets drain; no stuck `g_held_calls` for cdvdfsv after read jobs finish.

### R2 — WaitSema / iSignalSema

- ROM0 THREADMAN exports WaitSema / SignalSema / iSignalSema; HLE is `thsemap` in `libs.cpp`.  
- Retail: count>0 → decrement; else park waiter; Signal wakes one.  
- Disc-fix leftovers on Hitman/NFS (sema **2**, plus per-game ids) are **ownership / CreateSema init** issues — observe first.  
- **Do not** copy CNK Alchemy `host_signal(16/54/55)` into the hybrid path.

### R4 — CdSync / busy wake (`cdvd.cpp`)

- `sceCdSync` must wake `g_cd.sync_waiters` when IOP-side read finishes (`finish_read`).  
- `sceCdDiskReady` → **2** (ready).  
- `sceCdStatus` busy vs idle (`0x06` / `0x0A`) must stay consistent with FSV completion.  
- FSV path and cdvdman path can both touch “busy”; hybrid titles often wait on **EE libcdvd + SIF**, so R3+R1 usually unstick before raw cdvdman Sync.

## Boot contract (stub vs ROM0)

| Item | Stub / HLE | 77001 ROM0 |
|---|---|---|
| ROMVER | `0220EC20060210` | `0220AC20060210` |
| Meaning | Version 2.20, region letter differs (E vs A) | Same date stamp 060210 |

Close enough for module-era assumptions. Prefer **70012** when comparing CDVDFSV behavior; prefer **77001** when checking stub ROMVER-era consistency.

## What this does *not* claim

- Does not unpark CNK Alchemy / IGFILEIO by itself.  
- Does not authorize executing BIOS in-browser.  
- DIFF files are not a second BIOS — ignore for contracts.

## Handoff to disc-fix / matrix

1. Prove-before-swap: log Hitman + NFS last LBA, `eeaddr1/2`, curReadPos value at complete, and whether `0x80000595` was released.  
2. Patch only the **generic** complete path in `cdvdfsv.cpp` (+ SIF end assert if needed).  
3. Matrix phases: boot → menu → first_disc_read → streaming → sustained_run.  
4. WaitSema CreateSema trace stays observe-only until R3/R1 are green.

## Key HLE correction targets (return list)

1. **`cdvdfsv` `read_to_ee`:** payload → dst; preserve readee dests; **nbytes → curReadPos**; then complete.  
2. **`sif::complete_call(0x80000595)`:** every deferred N-read / stream-read / IOP-read / sync-complete job.  
3. **`cdvd` `sceCdSync` / DiskReady / Status:** wake waiters; ready=2; busy bit coherent with FSV.  
4. **`thsemap` WaitSema/iSignalSema:** correct count/waiter semantics; no CNK host_signal bleed.  
5. **Quarantine:** CNK virt-plant / sema 16/54/55 / +24008 stays out of Hitman+NFS disc-fix.
