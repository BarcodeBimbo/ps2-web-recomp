# R4 — sceCdSync / sceCdDiskReady compliance (research only)

**Track:** A · R4  
**SDK root:** `E:\usr\local\sce`  
**Runtime:** `runtime/src/iop/cdvd.cpp` L108–116 (+ `finish_read` L37–44) — **READ ONLY; no patch**  
**Product status (matrix):** R4 `cleared_with_evidence` — **no new** CdSync wake; Hitman ~mode=1 polls ≠ stuck blocking waiters

---

## MASTER next action — Device Reference deep-read (`sceCdSync` modes)

### EE Device Reference 3.0.3 · `sceCdSync` (2-47)

```
int sceCdSync(int mode);
  0x00: Wait for completion (blocking) → returns 0 when done
  0x01: Check status, return immediately (non-blocking) → 0 completed / 1 not completed
```

- Blocking type **cannot** be called interrupt-disabled.  
- Multithread: non-blocking polls should `DelayThread()` so other threads run.  
- See also: Read / Seek / Stop / Standby / Pause.

**EE PDF does not document 0x10 / 0x11** on the EE library page (those are IOP-oriented).

### IOP Device Reference 3.0.2 · `sceCdSync` (1-39) — fuller mode set

| mode | Behavior | Return |
|------|----------|--------|
| **0x00** | Block until command complete | 0 |
| **0x01** | Poll current state | 0 done / 1 busy |
| **0x10** | Block until complete **including EE-issued commands** | 0 |
| **0x11** | Poll including EE-issued command state | 0 / 1 |

### Public header + sample

- `E:\usr\local\sce\common\include\libcdvd.h` **L279–282**:
  - `int sceCdSync(int mode);`
  - `int sceCdDiskReady(int mode);`
  - (no mode enums in header; modes are PDF/docs)
- `E:\usr\local\sce\ee\sample\cdvd\smp_ee\main.c`:
  - Read path: **`sceCdSync(1)` poll loop** + `DelayThread` + `sceCdGetReadPos` (L272–277)
  - Standby/Pause/Stop tests: **`sceCdSync(0)`** blocking (L296–314)
  - Ready gate: repeated **`sceCdDiskReady(0)`** before commands (L119, 141, 181, 229, 264, …)

### `sceCdDiskReady` (EE Device 2-23 / IOP 1-20)

| mode | Behavior |
|------|----------|
| 0 | Blocking — wait until drive rotation stable |
| 1 | Non-blocking — return status immediately |

| Return | Macro | Meaning |
|--------|-------|---------|
| **0x02** | `SCECdComplete` | Drive can accept commands |
| **0x06** | `SCECdNotReady` | Drive cannot accept commands |

Defined in `libcdvd.h` L123 / L127.

---

## Product status (`cdvd.cpp`)

```108:116:runtime/src/iop/cdvd.cpp
    def("cdvdman", 11, "sceCdSync", [](Cpu &c) {
        if (arg(c, 0) == 1 || arg(c, 0) == 17) { c.r[2] = g_cd.busy ? 1u : 0u; return; }
        c.r[2] = 0;
        if (!g_cd.busy || !current()) return;
        g_cd.sync_waiters.push_back(current()->id);
        block(c, kWaitHle, 0);
    });
    def("cdvdman", 12, "sceCdGetDiskType", [](Cpu &c) { c.r[2] = 0x14; });
    def("cdvdman", 13, "sceCdDiskReady", [](Cpu &c) { c.r[2] = 2; });
```

| Mode arg | Product | SDK |
|----------|---------|-----|
| 1 (`0x01`) | Poll busy → 0/1 | **MATCH** EE+IOP |
| 17 (`0x11`) | Poll busy → 0/1 | **MATCH** IOP (EE-issued inclusive poll approximated as local busy) |
| 0 / 16 (`0x10`) / other | If busy: park in `sync_waiters`; else return 0 | **MATCH** blocking 0x00 / 0x10 shape |
| Wake | `finish_read()` clears busy, wakes `sync_waiters`, optional callback | Present — R4 clear = no *extra* wake patch needed |

Matrix evidence: Hitman ~1854× `sceCdSync(1)` vs ~10× mode 0 — sample-like poll pattern; not a missing-wake hang.

---

## Match flags

| # | Item | Verdict |
|---|------|---------|
| M1 | mode 0x01 / 0x11 non-blocking poll returns 0/1 | **MATCH** |
| M2 | mode 0 / 0x10 block via waiter list when busy | **MATCH** IOP blocking modes |
| M3 | Completion path wakes sync waiters (`finish_read`) | **MATCH** (already present; R4 did not need new wake) |
| M4 | Sample uses Sync(1) poll during read + Sync(0) for simple cmds | **MATCH** observed Hitman poll-heavy pattern |
| M5 | DiskReady success value **2** = `SCECdComplete` | **MATCH** constant |

---

## Deviation flags (observe-only)

| # | Item | Severity | Notes |
|---|------|----------|-------|
| **D1** | **`sceCdDiskReady` always returns 2**, ignores `mode` | **FLAG** | Never returns `SCECdNotReady` (6); never blocks on mode 0. Wrong if a title depends on NotReady during spin-up / tray / media detect. OK only while HLE assumes disc always spun-up and present (Hitman/NFS joint-stable assumption). |
| D2 | mode 0x10/0x11 do not separately track “EE-issued vs IOP-local” cmd queues | low | Single `g_cd.busy` bit approximates both; fine until dual-queue titles diverge. |
| D3 | Blocking Sync when `!current()` returns 0 without waiting | edge | No IOP thread context → treat complete; rare in normal cdvdman calls. |
| D4 | `sceCdStatus` HLE uses 0x06 busy / 0x0A idle (L138) | separate | Not Sync; note if Status vs DiskReady macros confuse triage. |

### DiskReady always-2 — when wrong

Per Device PDF, mode 0 must **wait until ready**; mode 1 may return NotReady. Constant `2` means:

- Apps that only check `== SCECdComplete` before issue → appear OK.  
- Apps that spin on NotReady / expect blocking settle → **incorrect HLE** (infinite instant-ready).  
- Tray open / no disc / detect sequences in `smp_ee` use DiskReady(0) after tray events — product never models NotReady.

**Do not “fix” by returning random NotReady without a drive-state model** — research flag only under this track.

---

## Evidence paths

- Runtime: `runtime/src/iop/cdvd.cpp` L37–44 (`finish_read`), L108–116 (`sceCdSync` / `sceCdDiskReady`)  
- Header: `E:\usr\local\sce\common\include\libcdvd.h` L123–127, L279–282  
- Sample: `E:\usr\local\sce\ee\sample\cdvd\smp_ee\main.c` (Sync 0/1, DiskReady 0)  
- Extracts:  
  - `PS2_EE-Reference-Device-3.0.3.pdf.txt` (`sceCdSync` 2-47, `sceCdDiskReady` 2-23)  
  - `PS2_IOP-Reference-Device-3.0.2.pdf.txt` (`sceCdSync` 1-39 with 0x10/0x11)  
- Board: `DISCFIX-R1-R4-STABLE.md`, `test-matrix-live-report.md` (R4_clear_with_evidence PASS)

---

## No-patch

Research audit only. **Do not** add CdSync waiter wake patches, **do not** change DiskReady HLE, **do not** modify runtime sources under this track.
