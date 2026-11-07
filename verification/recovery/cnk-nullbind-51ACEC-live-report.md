# CNK null jalr @ ra=0x0051ACEC — live report

Read-only. GID `b49f2e769315347e8bda839feb705744`. No production patches. Quarantined from Hitman/NFS disc-fix. No host_signal Alchemy “fixes.”

Sources: `boot.elf` disasm, `logs/cnk-arm45-20k.log` (forced FCE0 crash), end-of-run RAM snapshots taken this session from `cnk-arm45.ram` / `cnk-softarm-hold.ram` / `cnk-deferred-*.ram` (snapshots were present during analysis; may no longer be on disk), overnight crumbs `verification/host-session-2026-11-06-overnight-cnk-10p.json` + `10s`, prior `cnk-nullbind-51ACEC-restart-report.md`.

## Bottom line

`ra=0x51ACEC` is **not** “a live object whose vt+84 slot is zero.”  
Forced FCE0 reaches helper `0x51AC80`, calls bind-registry **vt+80** (`0x53B940`), gets **`v0 = 0`**, then still does `*(v0->vtable+84)` and `jalr`s **PC 0**. Soft-arm alone never finishes parse (`prims=2`) and does not need a stuffed function pointer.

## Disassembly map (`0x51AC80`–`0x51AD00`)

From `games/.../disc/boot.elf` (load VA `0x00100000`):

| VA | What |
|----|------|
| `0x51AC90` | `lbu` flag at `a0+24`; early-out if 0 |
| `0x51AC98` | `s0 = a0` (stream/attach object) |
| `0x51AC9C` | clear `obj+24` |
| `0x51ACA4`–`ACB4` | `a1 = *(s0+28)`; **jalr `*(vtable+92)`** (prep on inner object) |
| `0x51ACBC`–`ACC0` | `a0 = ee32(0x00725F50)` — **bind registry global** |
| `0x51ACC4`–`ACCC` | **jalr registry `vt+80`** (= `0x53B940` in live dumps) |
| `0x51ACD0` | delay: **`s1 = *(s0+32)`** — key / bind object pointer |
| `0x51ACD4` | `t9 = *v0` (vtable of **lookup result**) |
| `0x51ACD8` | `a2 = s1` (pass key into next call) |
| `0x51ACE0`–`ACE4` | **`t9 = *(vtable+84)`; jalr t9** ← crash when `v0` was 0 |
| `0x51ACE8` | delay: `a1 = v0` |
| `0x51ACEC` | next insn / **ra after the null jalr** (`jal 0x5170A0`…) |

Vtable offsets (bytes): **+80 = 0x50**, **+84 = 0x54**, **+92 = 0x5C**. UI parse’s **vt+108** is on the *loadgate/UI object* (e.g. `0x97E5A8`), not on this registry — and is already live (`0x5032E0`) when soft-arm arms `+45`.

## What the registry returns

### Global `0x00725F50`

- **Written** at `0x520180` (`sw v0, 0x5F50(at)` after factory calls).
- **Cleared** at `0x5202AC` (`sw zero, 0x5F50(at)`).
- Soft-arm end dump: **`ee32(0x725F50) = 0`** (registry not installed / already cleared).
- Forced-FCE0 / arm45 / deferred dumps: **`ee32(0x725F50) = 0x735638`**.

### Registry object `0x735638` (when live)

| Slot | Value | Meaning |
|------|-------|---------|
| vtable | `0x6DF110` | |
| vt+80 | `0x53B940` | lookup / “get context for this thread” |
| vt+84 | `0x53BA50` | follow-on bind op (only safe if vt+80 returned a real object) |
| vt+108 | `0x5111F0` | unrelated to the null jalr |
| +8 | `0x735658` | list object passed into lookup |

Registry’s own vt+80/+84 are **non-null**. Stuffing those slots is the wrong fix.

### vt+80 (`0x53B940`) → helper `0x511070`

`0x53B940` roughly:

1. `GetThreadId` via EE syscall stub `0x43C9D0` (`v1=47` / `0x2F`).
2. Touches priority via `0x43C970` (`v1=41` / ChangeThreadPriority).
3. Calls `0x511070(list=registry+8, type=ee32(0x725C20), key=GetThreadId())`.

`0x511070` walks `list.count` entries at `list.array` and returns the entry whose word at **`entry + *(type+8)`** equals `a2`. In dumps, `*(type+8) = 0x3C` — so it matches **`*(entry+0x3C)` to the current thread id**.

Observed arm45 list (`registry+8` @ `0x735658`, count=2, array `0x735C98`):

| Entry | Ptr | `*(entry+0x3C)` |
|-------|-----|-----------------|
| 0 | `0x735C18` | **1** |
| 1 | `0x1859D28` | **4** |

So the registry returns **the per-thread bind/context object for `GetThreadId()`**, or **NULL** if the running thread id is not in that map.

## Captured values (forced-FCE0 vs soft-arm)

Requested probes, filled from crash regs + RAM (no new instrumentation this pass):

| Probe | Soft-arm baseline (`cnk-softarm-hold`) | Forced FCE0 / arm45 crash |
|-------|----------------------------------------|---------------------------|
| `ee32(0x725F50)` | **0** | **0x735638** |
| `r2` after vt+80 | path not hit / N/A | **0** (crash dump `r2`) |
| key `*(obj+32)` one insn before `0x51ACD4` | N/A (no registry) | **`s1 = 0x01859D28`** (delay slot of vt+80; also `a2` at crash) |
| `a1` at null jalr | — | **0** (= moved from `v0`) |
| `t9` / jalr target | — | **0** |
| UI `vt+108` | live when armed | live (`0x5032E0`) — first virtual parse path OK |

**Correction to earlier wording:** `0x01859D28` is the **stream key / listed bind object** (`obj+32` and table entry for tid 4), **not** the vt+80 return value. Return was **null**.

## Why vt+84 looks “null”

1. `v0 == 0` after registry vt+80.
2. `lw t9, 0(v0)` reads EE address 0.
3. `lw t9, 84(t9)` yields 0 → `jalr` to 0 with `ra=0x51ACEC`.
4. Log line matches: `missing code at 0x00000000 (ra 0x0051ACEC)`, `r25=0`.

Root miss: **thread-id bind lookup failed** (no entry for `GetThreadId()` at call time), not a zeroed method on a good object.

Likely aggravator for **host** FCE0: `kernel::host_call` / `run_guest` keeps `g_current` as-is and uses a kernel stack. If FCE0 is forced while EE is idle (`g_current==0`) or on a thread **without** a `+0x3C` map entry, lookup returns 0 every time. Soft-arm avoids the crash by **not** host-calling FCE0; it also never gets a durable registry install in the hold dump (`0x725F50=0`), so parse stays unfinished (`prims=2`).

## Next safe step (still no blind FP stuffing)

1. **Do not** poke vt+84, invent `0x725F50`, or host_signal Alchemy as a “fix.”
2. On the next diagnostic run only, log at `0x51ACCC`→`0x51ACD4`: `ee32(0x725F50)`, `GetThreadId`/`g_current`, list count, whether any `entry+0x3C` matches, and `r2` after vt+80 — forced FCE0 vs soft-arm (soft-arm may never reach the site).
3. Prefer making parse run on a **thread that already owns a registry entry** (observed tids **1** and **4**), or let the guest create the entry before FCE0 — not forcing FCE0 from idle/`g_current==0`.
4. Keep CNK Alchemy soft-arm/FCE0/+24008 work **quarantined** from Hitman/NFS.

Gate stays red until `prims >> 2` without a null jalr.
