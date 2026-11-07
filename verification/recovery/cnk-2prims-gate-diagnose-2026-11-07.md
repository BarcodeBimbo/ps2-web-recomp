# CNK 2-prims gate — diagnose (2026-11-07 ~07:30)

**GID:** `b49f2e769315347e8bda839feb705744`  
**Mode:** OBSERVE ONLY — no new host_signal / soft-arm / FCE0-force / virt-LBA / +24008 patches.

## Bottom line

Gate stays **red at `prims=2`**. Soft-arm arms `obj+45` and opens the UI parse window **without** host-calling `0x10FCE0`. Guest never finishes IGB parse. Forced FCE0 reaches null-bind `ra=0x51ACEC` because registry **vt+80** tid lookup misses (`GetThreadId` ∉ {1,4} or `g_current==0` on `host_call`).

## Evidence chain (prior + this morning)

| Path | Result |
|------|--------|
| Soft-arm hold (`logs/cnk-softarm-hold-20k.log`) | `armed=1`, `UI parse window open`, **`[gs] 2 primitives`**, no `51ACEC` |
| Soft-arm arm45soft RAM | `*0x725F50=0x735638`, list count **1** (tid **1** only); still prims=2 |
| Forced FCE0 (`logs/cnk-arm45-20k.log`) | Registry count **2** (tids 1+4); crash `r2=0`, `ra=0x51ACEC` |
| Bad disc path (this AM, folder not ISO) | `cannot open disc image …\disc` → **0 prims**, STBL cold — not the overnight gate |

## Root-cause one-liner

**Parse completion requires guest FCE0/finalize on a thread that already owns a bind-registry map entry; soft-arm wakes +45 but never drives that call, and host-forced FCE0 runs on the wrong thread context → null vt+80 → PC0 @ `0x51ACEC`.**

## What would unblock `prims >> 2` (still quarantined — NOT applied)

1. **Guest-owned FCE0** after bind install on tid **1** or **4** (preferred; no host_call).
2. Future **approved diagnostic-only** mid-site log at `0x51ACCC→0x51ACD4` (tid / `v0` / list) — not an Alchemy production patch.
3. Do **not**: stuff vt+84, invent `*0x725F50`, host_signal 16/54/55 beyond existing tree behavior, or force FCE0 from idle.

## Next observe step

1. Reconfirm soft-arm **20k / disc.iso** still ends `prims=2` with DLL PATH restored (`logs/cnk-2prims-observe-2026-11-07/`).
2. When Ghidra MCP is back: dump writers of `0x725F50` (`0x520180` / `0x5202AC`) vs loadgate `0x10FCE0` call graph (observe).
3. Keep Alchemy dumper at verify **28/28**; ISO parse is not the blocker.

## Blocked on

Hard ban: no CNK Alchemy host patches this stage. Gate cannot turn green without either guest-path success or an explicit ban lift for a diagnostic probe / approved fix.
