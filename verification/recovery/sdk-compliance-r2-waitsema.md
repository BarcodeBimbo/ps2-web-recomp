# R2 — WaitSema / CreateSema fidelity compliance (research only)

**Track:** A · R2  
**SDK root:** `E:\usr\local\sce`  
**Runtime:** EE `runtime/src/kernel.cpp`, IOP `runtime/src/iop/libs.cpp` (thsemap) — **READ ONLY; no patch**  
**Product status (matrix):** R2 `cleared_with_evidence` — sema **2** = durable libcdvd-class parking; **never `host_signal(2)`**

---

## Sony contract (Kernel Overview + headers)

| Source | Contract |
|--------|----------|
| EE Overview Kernel 3.0.2 · Semaphores | `WaitSema` acquires a resource; if none available → **WAIT** queue. `SignalSema` returns resource to head waiter → READY. |
| Counting use | `CreateSema` sets resource count; producer `SignalSema`, consumer `WaitSema` — init **0** means “park until signaled.” |
| IOP Overview Kernel 3.0 · Semaphores | Same Wait/Signal exclusion and buffer-count patterns. |
| `ee/include/eekernel.h` | `SemaParam { currentCount, maxCount, initCount, … }`; `CreateSema` / `WaitSema` / `SignalSema` / `iSignalSema`. |
| Live ownership report | Classic libcdvd cmd-queue shape: **init=0, max=255**, created once, never deleted. |

**Hard rule for this product:** leftover EE sema **id 2** on Hitman BM / NFS MW is durable CD-library parking. Blind `host_signal(2)` / CNK-style pulse **fakes CD command completion** and is forbidden for the Hitman/NFS disc path.

---

## Product status vs live trace

Evidence: `verification/recovery/waitsema-createsema-trace-live-report.md` (+ `logs/waitsema-createsema-{hitman,nfs}-2k.log`).

| Observation | Hitman BM | NFS MW | SDK reading |
|-------------|-----------|--------|-------------|
| Sema **2** create | once, never delete | once, never delete | Durable gate, not temp RPC |
| init / max | **0 / 255** | **0 / 255** | Counting queue / “empty until Signal” |
| create_ra | `0x001038CC` | `0x00495EA8` | **Different** RAs → ID coincidence, not one shared object |
| Wait park | thr 2 @ `0x001037F8` | thr 2 @ `0x00495DE8` | Wait site ~0xC0 from create in same module |
| Private leftovers | id **7** | ids **17,23,29,30,32** | Per-title; not libcdvd-2 |

EE kernel WaitSema path (`kernel.cpp`): count>0 → decrement; else block `kWaitSema`. IOP thsemap mirrors Overview contract (`libs.cpp` Create/Wait/Signal).

---

## Match flags

| # | Item | Verdict |
|---|------|---------|
| M1 | WaitSema parks when count==0 | **MATCH** Overview + header |
| M2 | SignalSema wakes waiter / increments count | **MATCH** |
| M3 | Sema 2 shape (0/255, durable) matches libcdvd-class parking | **MATCH** live evidence |
| M4 | Policy: never blind-wake id 2 on Hitman/NFS | **MATCH** SDK intent (only real Signal/iSignal or CD completion path) |

---

## Deviation flags (observe-only)

| # | Item | Severity | Notes |
|---|------|----------|-------|
| D1 | CNK / Alchemy paths call `host_signal_sema(2)` (`igfileio.cpp`) | **quarantine** | Allowed only under CNK Alchemy quarantine — **must not** be applied to Hitman/NFS disc-fix. Reinforces R2 ban. |
| D2 | `cdvdfsv.cpp` host pulses 16/54/55 on virt UI paths | quarantine | Not sema 2; still CNK-scoped. |
| D3 | IOP Kernel *Reference* WaitSema page not in `_sdk_pdf_extract` | doc gap | Overview + `eekernel.h` + live create params are sufficient for R2 clear; optional later PDF extract if Reference Kernel is located under Docs&Training. |

---

## Reinforce: never `host_signal(2)`

1. Sema 2 init=0 → WaitSema is legitimate “await CD/lib activity.”  
2. `host_signal(2)` is a host-side `SignalSema` that **does not** prove IOP CD cmd / SIF RPC completion.  
3. Same numeric id across titles is **coincidence** (different create_ra).  
4. Matrix / DISCFIX / WaitSema reports: **never** blind `host_signal(2)` on the Hitman+NFS joint-stable path.

---

## Evidence paths

- Live: `verification/recovery/waitsema-createsema-trace-live-report.md`  
- Runtime (read-only): `runtime/src/kernel.cpp` (EE WaitSema / `host_signal_sema`), `runtime/src/iop/libs.cpp` (thsemap)  
- SDK: `E:\usr\local\sce\ee\include\eekernel.h` (SemaParam, WaitSema)  
- Extracts: `PS2_EE-Overview-Kernel-3.0.2.pdf.txt` (Semaphores ~1-6..1-8), `PS2_IOP-Overview-Kernel-3.0.pdf.txt` (Semaphores)  
- Board: `DISCFIX-R1-R4-STABLE.md`, `test-matrix-live-report.md`

---

## No-patch

Research audit only. **Do not** wake/patch WaitSema, **do not** add `host_signal(2)`, **do not** modify runtime sources under this track.
