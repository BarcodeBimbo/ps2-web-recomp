# CNK two-primitives gate — deep diagnose (2026-11-07)

**Mode:** OBSERVE ONLY. GID `b49f2e769315347e8bda839feb705744`.  
**Hard ban honored:** no disc-fix / R5 / CNK patches; no new soft-arm / FCE0-force / virt-LBA / +24008 / host_signal 16/54/55 code; Alchemy dumper ISO parse not re-litigated (28/28 already PASS).

**Sources:** MASTER-CONTEXT §6; `cnk-nullbind-51ACEC-live-report.md`; `worker-resume-cnk-nullbind-w3-2026-11-07.md`; `cnk-elf-alchemy-full-redo-report.md`; Ghidra HTTP `:8089` (`switch_program` → `cnk_boot.elf`); offline `logs/ram/cnk-*.ram`; new observe smoke `logs/cnk-2prims-obs-2k.log` + `logs/ram/cnk-2prims-obs-2026-11-07.ram`.  
`C:\Users\joshy\ghidra_exports\ps2-elves\cnk-key-vas-summary.json` — **absent**; equivalent: `logs/ghidra-ps2/cnk-key-vas.json` + `logs/ghidra-ps2/cnk-vas/*`.

---

## Root-cause hypothesis (one liner)

Soft-arm reaches bind install (`*0x725F50` live, tid **1** only) but loadgate **`+0x5DD0=1` gates guest `0x10FCE0` off** after one cycle, so parse never finishes (`prims=2`); host-forced FCE0 bypasses that gate on the wrong EE thread → tid-map miss → `ra=0x51ACEC`.

---

## Evidence

### 1) Call graph: writers of `*0x725F50` vs loadgate / finalize

| VA | Role | Relative order |
|----|------|----------------|
| `0x00520160` | **Install** — factory → `sw v0 → 0x725F50` @ `0x520180` → second alloc → vt+208 → registry **vt+84** register | Alchemy class-init jump table (`j 0x520160` word @ `0x4D2740`), driven via `FUN_00510A20` / ctor table — **not** called from FCE0 |
| `0x00520210` | **Clear** — vt+80/vt+88 release then `piRam00725f50 = 0` (`sw zero` @ `0x5202AC`) | Sibling jump-table slot `0x4D2750` |
| `0x0010F560` | Per-frame loadgate tick (from `0x109F80`) | Calls `0x10FCE0` **only if** `gate+0x5DC8≠0` **and** `gate+0x5DD0==0` |
| `0x0010FCE0` | Loadgate pump | Calls finalize `0x110100` when slot state/status match; at walker `≥0xFA` may `jal 0x51AC80` if `*(0x725D48+0x18)≠0`; then can set **`+0x5DD0=1`**, reset walker, spawn `FUN_0023AAE0(..., entry=0x10F9E0, …)` |
| `0x00110100` | Slot finalize / parse kick | Uses `0x725D48` stream side — **does not write `0x725F50`** |
| `0x0051AC80` | Null-bind helper (`ra=0x51ACEC` crash site) | Needs live registry; **vt+80** = tid lookup |

**Soft-arm stall is not “installer never runs.”** End-RAM + live smoke both show `ee32(0x725F50)=0x735638`. What stalls **after** install is guest FCE0 re-entry: parent tick sees `+0x5DD0=1` and skips `0x10FCE0`.

Exception: `cnk-softarm-hold.ram` still has `0x725F50=0` (teardown / never-installed hold path) — that variant never even has a binder.

### 2) Thread ownership of bind map (tid 1 vs 4)

Registry list object @ `registry+8` (`0x735658`): **count @ +0x08**, **pointer array @ +0x10** (`0x735C98`). Lookup `0x53B940` → `GetThreadId` (syscall `0x2F`) → `0x511070(list, type, tid)` matching `*(entry + *(type+8))` with `*(type+8)=0x3C`.

| Snap / run | `*0x725F50` | count | tids | loadgate `+5DC8/+5DD0/walker` |
|------------|-------------|-------|------|-------------------------------|
| softarm-hold | **0** | — | — | lg ptr junk / cleared |
| arm45soft / stable / simple | `0x735638` | **1** | **1** only (`0x735C18`); slot1 ptr `0x1859D28` present but tid=`-1` / dead | `1 / 1 / 0` |
| arm45 forced FCE0 (crash) | `0x735638` | **2** | **1** + **4** (`0x1859D28`) | `1 / 0 / 0xFA` |
| **obs smoke 2026-11-07** (2k frames) | `0x735638` | **1** | **1** | `1 / 1 / 0` |

**Correct guest sequence (no host FCE0):**

1. Class init runs installer `0x520160` → `*0x725F50` live (tid **1** context registered on main EE thread).
2. Per-frame `0x10F560` with `+5DC8=1` and **`+5DD0=0`** calls guest `0x10FCE0` on a thread that **already owns a map entry** (observed owners: **1**, later **4**).
3. Slots reach CD-done / finalize via `0x110100` while still on that thread.
4. When walker completes (`≥250`), if attach flag `*(0x725D48+0x18)` is set, `0x51AC80` runs **on the same mapped tid** so vt+80 returns non-null → vt+84 safe.
5. End-of-walk may spawn Alchemy worker via `0x23AAE0` / entry `0x10F9E0` — that is the natural path for **tid 4** to appear in the map; that worker (not idle/`g_current==0`) is what should keep pumping parse after the parent sets `+5DD0`.

**Forbidden path (already proven lethal):** `kernel::host_call(0x10FCE0)` while `g_current` is idle/unmapped → vt+80 returns 0 → `jalr` PC0, `ra=0x51ACEC` (key often the tid-4 object `0x1859D28`, but lookup tid ≠ 1/4).

### 3) Observe-only smoke (ran once)

```
PATH=runtime-deps;…  (DLL restore)
PS2_DUMP=logs/ram/cnk-2prims-obs-2026-11-07.ram
PS2_PEEK=725F50,10;6F2540,4
PS2_ALCHEMY_NO_CDVD_GFC=1   # avoid host_signal 16/54/55 this run
PS2_ALCHEMY_NO_BIND=1
ps2run games/…/boot.elf --disc …/disc.iso --frames 2000
```

| Probe | Result |
|-------|--------|
| Prims | **2** (`[gs] 2 primitives drawn`) |
| `ee32(0x725F50)` | **`0x735638`** (peek + dump) |
| Nullbind `51ACEC` | **not hit** |
| Tid map | count=1, tid **1** only |
| Gate flags | `+5DC8=1`, **`+5DD0=1`**, walker=0 |

Confirms soft-arm-class stall: registry installed, guest FCE0 gated off, prims stuck at 2, no null jalr.

---

## What would unblock `prims >> 2` **without** quarantine violations

These are **not** patches applied here — directions that stay outside host FCE0 / soft-arm / host_signal Alchemy hacks:

1. **Guest-side:** keep `gate+0x5DD0` clear (or never set early) until UI IGB parse actually produces drawables; let `0x10F560` keep calling guest `0x10FCE0` on **tid 1** (or the mapped worker) until slots finish.
2. **Guest-side:** ensure the `0x23AAE0` / `0x10F9E0` worker that owns **tid 4** is created and its bind entry stays live **before** any path reaches `0x51AC80` with attach flag set.
3. **Future approved diagnostic only:** mid-site log at `0x51ACD0` (GetThreadId / `g_current` / list tids / `v0`) — observe, no pointer stuffing.
4. **Do not:** host_force FCE0/`0x110100`, stuff vt+84, invent `0x725F50`, host_signal 16/54/55, virt-LBA, +24008 clears — those are the quarantined failures already on disk.

---

## Next observe step

1. Offline (no patch): dump `gate+0x5DD0` timeline across existing `logs/ram/cnk-*.ram` vs smoke — already shows soft path `5DD0=1` / forced path `5DD0=0`+walker=`0xFA`.
2. When a **diagnostic-only** build is explicitly allowed: one-shot log at `0x10F560` branch (`5DC8/5DD0`) and at `0x51ACD0` (tid vs map) on guest-driven FCE0 only.
3. Optional short smoke with `PS2_PEEK` extended to `gate+0x5DC8..5DD8` after N frames (env-only) — still no CNK code edits.

---

## Return blob

```
prims: 2 (stuck)
registry: ee32(0x725F50)=0x735638 (live; tid map = {1} only)
nullbind: not hit on soft/obs path; forced FCE0 → ra=0x51ACEC tid miss
root_cause: post-install loadgate +0x5DD0 gates guest FCE0; host FCE0 hits wrong tid
file: verification/recovery/cnk-2prims-gate-diagnose-2026-11-07.md
blocked_or_next: gate red; next=approved mid-site tid/5DD0 diagnostic OR guest-side keep FCE0 on mapped tid — no host force
```
