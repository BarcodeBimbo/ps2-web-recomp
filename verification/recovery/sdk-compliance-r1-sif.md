# R1 — SIF end / orphan RPC compliance (research only)

**Track:** A · R1  
**SDK root:** `E:\usr\local\sce` (`SCE_LIBRARY_VERSION 0x3030`, `readme-3.0.3`)  
**Runtime:** `runtime/src/iop/sif.cpp` — **READ ONLY; no patch**  
**Product status (matrix):** R1 `cleared_with_evidence` (SIF outgoing queue drains to 0 after soft reset)

---

## Sony / ps2sdk-style contract

| Source | Contract |
|--------|----------|
| EE SIF Overview 3.0 | Client `sceSifCallRpc` / Bind wait on **semaphore or event flag** until server response (WAIT). Completion reported via **SIF CMD**. |
| IOP/EE SIF Reference 3.0.2 `sceSifCallRpc` | Thread sleeps (IOP) / **internally reserved semaphore** (EE ≥1.4) until reply; `end_func` runs interrupt-disabled on completion. |
| EE SIF Reference reboot notes | After IOP reset, RPC bind / in-flight state is invalidated; EE must re-bind; reboot notify handlers exist for cleanup. |
| Overview SIF | Re-entry on same `ClientData` before completion hangs; WAIT path parks on sema. |

**ps2sdk-style end packet:** retail/ps2sdk use SIF CMD **`0x80000008` (REND)** carrying the completed RPC command id (`0x8000000A` Call / `0x80000009` Bind) so the EE CMD handler clears client status and **SignalSema**s the CallRpc waiter. Without that end packet, EE WaitSema parks forever.

---

## Product status (`sif.cpp`)

| Mechanism | Location | Behavior |
|-----------|----------|----------|
| REND constant | `kCmdRend = 0x80000008u` (~L35) | Matches SIF CMD REND id |
| `reply_call` | ~L155–158 | Emits REND with `command = 0x8000000A` (CallRpc end) |
| `complete_orphaned_rpc` | ~L379–405 | On IOP reset: reply all `g_held_calls` + queued requests; clear HLE replies; credit/wake SleepThread RPC workers |
| `reboot` | ~L407–438 | Clears `g_outgoing`, then `complete_orphaned_rpc()` so **only end packets** remain for EE WaitSema waiters |
| Soft `SifIopReset("")` | empty path | Republishes BOOTEND/SIFINIT/CMDINIT; reuses last IOPRP image |

---

## Match flags

| # | Item | Verdict |
|---|------|---------|
| M1 | Completion uses SIF CMD REND `0x80000008` | **MATCH** |
| M2 | Orphaned CallRpc gets an end packet on IOP reboot/soft reset | **MATCH** (Sony: reset invalidates in-flight RPC; product completes orphans instead of silent drop) |
| M3 | EE WAIT CallRpc depends on end packet → semaphore wake | **MATCH** intent with Overview/Reference |
| M4 | Soft reset drains prior SIF0 spam before end packets | **MATCH** analogue of stop-DMA then settle |

---

## Deviation flags (observe-only)

| # | Item | Severity | Notes |
|---|------|----------|-------|
| D1 | Orphan completion synthesizes **success** end packets without full IOP module teardown | low | Hardware reboot kills servers; product replies held calls so EE does not WaitSema forever. Acceptable HLE if reply payload zeros / prior recv state are sufficient. |
| D2 | Soft-reset BOOTEND republish loop (`g_soft_bootend_reps`) | low | HLE stand-in for EESYNC/sifman republish; not in PDFs as numeric policy. |
| D3 | No `sceSifAddRebootNotifyHandler` surface | n/a for Hitman/NFS | EE titles that register reboot notify may see different cleanup; not exercised on R1 pair. |

**No R1 blocking deviation for Hitman/NFS** given matrix SIF queue → 0.

---

## Evidence paths

- Runtime: `runtime/src/iop/sif.cpp` (`complete_orphaned_rpc`, `reply_call`, `reboot`, `kCmdRend`)
- SDK extracts:  
  - `verification/recovery/_sdk_pdf_extract/PS2_EE-Overview-Sif-3.0.pdf.txt` (WAIT / SIF CMD completion)  
  - `verification/recovery/_sdk_pdf_extract/PS2_IOP-Reference-Sif-3.0.2.pdf.txt` (`sceSifCallRpc` ~p.4-13)  
  - `verification/recovery/_sdk_pdf_extract/PS2_EE-Reference-Sif-3.0.2.pdf.txt` (EndFunc, reboot APIs)
- Prior product evidence: `verification/recovery/DISCFIX-R1-R4-STABLE.md`, `discfix-hitman-nfs-live-report.md`

---

## No-patch

Research audit only. **Do not modify** `runtime/src/iop/sif.cpp` or other runtime sources under this track.
