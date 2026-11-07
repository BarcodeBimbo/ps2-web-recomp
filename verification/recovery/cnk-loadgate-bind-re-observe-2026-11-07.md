# CNK loadgate + bind registry — observe-only EE RE (2026-11-07)

**Mode:** RESEARCH / OBSERVE ONLY. **Quarantine:** no disc-fix, R5, or CNK **runtime** patches; no Hitman/NFS coupling.  
**Game:** Crash Nitro Kart — `b49f2e769315347e8bda839feb705744`  
**Worker:** W-CNK  
**Sources:** `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md`, `cnk-2prims-gate-diagnose-2026-11-07.md`, `logs/ghidra-ps2/cnk-key-vas.json`, Ghidra MCP `:8089` (session reload of `cnk_boot.elf`), `tools/ps2-alchemy-dumper/` verify re-run.

---

## Executive picture

| Layer | Stall role |
|-------|------------|
| **Bind install** `0x520160` | Runs via class-init jump table; stores factory product in `*0x725F50` — **works** in soft-arm (registry non-null, tid **1** in map). |
| **Parent tick** `0x10F560` | Per-frame gate: calls guest **`0x10FCE0` only if** `gate+0x5DC8≠0` **and** `gate+0x5DD0==0`. |
| **Loadgate pump** `0x10FCE0` | Slot walk / finalize `0x110100`; end-of-walk sets **`+0x5DD0=1`**, resets walker, spawns Alchemy worker (`0x23AAE0`, entry **`0x10F9E0`**). |
| **Null-bind** `0x51AC80` | After walk when `*(0x725D48+0x18)≠0`; registry **vt+80** (`0x53B940`) → `0x511070` tid map; miss → **vt+84 on null** → `ra=0x51ACEC`. |

**`prims=2` is not “installer never ran.”** It is **post-install guest gating**: soft-arm smoke shows `*0x725F50` live but `+0x5DD0=1` so `0x10F560` never re-enters `0x10FCE0`.

---

## 1) Loadgate object layout (Ghidra `FUN_0010fce0`, slot stride **0x60** = 96 bytes)

| Gate offset | Hex | Role |
|-------------|-----|------|
| `gate+8` | — | First slot base (passed to slot helpers as `slot+8`) |
| `gate+0x5DC8` | 24008 | **Busy** byte; FCE0 may clear via `FUN_00110da0`; parent requires non-zero to pump |
| `gate+0x5DD0` | 24016 | **Hold** byte; when **1**, parent **skips** `0x10FCE0` |
| `gate+0x5DD4` | 24020 | Walker index (0…`0xF9`) |
| `gate+0x5DD8` | 24024 | Parent wait flag (spun on `FUN_0023af50` while non-zero) |
| `gate+0x5DCC` | — | Thread-spawn handle for `FUN_0023aae0` |

Per-slot (base = `gate + i*0x60`):

| Slot off | Role in pump |
|----------|----------------|
| `+0x50` | State word (e.g. must be `1` with status `1` to call finalize) |
| `+0x54` | Status enum (`1` CD-done path, `2`/`3`/`4` branches in sweep loops) |

Finalize **`0x110100`** receives `(gate, slot+8)`; uses stream side `iRam00725d48` and object **vt+0x6C** parse path.

---

## 2) Per-frame parent — `FUN_0010f560` (new Ghidra decompile, 2026-11-07)

```c
// Pseudocode from Ghidra MCP — cnk_boot.elf
void loadgate_parent_tick(int gate) {
  while (*(char *)(gate + 0x5dd8) != '\0')
    FUN_0023af50(0x10);
  FUN_0023d670(*(gate + 4));
  if (FUN_0023ae60(*(gate + 0x5dcc)) != 0 && *(char *)(gate + 0x5dd0) == '\0')
    FUN_0010fa10(gate);          // worker-side AE60/AE70/AED0 trio
  if (*(char *)(gate + 0x5dc8) != '\0' && *(char *)(gate + 0x5dd0) == '\0') {
    FUN_0010faf0(gate);          // pre-pass: status-2 slots → 3 (250× stride 0x60)
    FUN_0010fce0(gate);          // pump
  }
  if (*(char *)(gate + 0x5dc8) != '\0')
    FUN_0023af50(0x10);
}
```

**Call site:** sole unconditional `jal` to FCE0 from `0x0010F5EC` inside this function (matches prior `cnk-key-vas.json` xref).

**Implication:** On every allowed frame, guest runs **`0x10FAF0` then `0x10FCE0`**. The pre-pass duplicates the end-of-walk slot sweep embedded in FCE0 — likely keeps UI slot statuses moving while CD/async work is in flight.

---

## 3) End-of-walk side effects — `FUN_0010fce0` (from locked `cnk-key-vas.json`)

When walker `≥ 0xFA`:

1. Optional `jal 0x51AC80` if `*(iRam00725d48 + 0x18) != 0`.
2. Full slot sweep (status `2` → `3`, same pattern as `0x10FAF0`).
3. `FUN_00110da0` may clear `+0x5DC8`.
4. On success path: `FUN_0042d770` resets slot ring; sets **`+0x5DC8=1`**, **`+0x5DD4=0`**, **`+0x5DD0=1`**; spawns  
   `FUN_0023aae0(*(gate+0x5dcc), 0x10F9E0, 2, 0, 0x4000)`.

That sequence explains observe smoke: **`+0x5DD0=1`** after one pump cycle → parent stops calling FCE0 → parse/graph never reaches drawable UI (**`prims=2`**).

Natural unblock (guest-side, **not** host `host_call(0x10FCE0)`): mapped worker at **`0x10F9E0`** must clear `+0x5DD0` or finish IGB bind on **tid 4** (per `cnk-2prims-gate-diagnose-2026-11-07.md`).

---

## 4) Bind registry — install + lookup (observe)

### Install `FUN_00520160`

```text
factory → wrapper → piRam00725f50 = registry
factory → second object; obj+0x2C = 1; vt+0xD0; registry vt+0x54 register
```

(Jump-table entry `0x4D2740` — not direct `jal` from FCE0.)

### Lookup list walk `FUN_00511070` (Ghidra this session)

```c
int list_find(int *list, long type, int key) {
  for (i = 0; i < list[2]; i++) {          // count @ list+8
    entry = ((int *)list[4])[i];           // array @ list+0x10
    if (entry && key == *(int *)(entry + *(int *)(type + 8)))
      return entry;
  }
  return 0;
}
```

Matches live report: type `0x725C20`, offset **`0x3C`** in each entry vs `GetThreadId()`.

### vt+80 `@ 0x53B940`

- Prologue **`addiu sp,sp,-0x40`** confirmed in raw `boot.elf` @ file offset `0x43B9C0`.
- Prior live + MCP work: syscall stub GetThreadId → `0x511070(registry+8, type@0x725C20, tid)`.
- Ghidra function label created this session (`cnk_bind_registry_vt80_tid_lookup`); decompile intermittently unavailable while headless analysis catches up — treat **`cnk-nullbind-51ACEC-live-report.md`** + `0x511070` decompile as canonical.

---

## 5) Tooling evidence

| Check | Result |
|-------|--------|
| `python -m ps2_alchemy_dumper verify` on CNK `disc.iso` | **28/28 PASS** (2026-11-07 W-CNK re-run) |
| Ghidra MCP `:8089` | Connected `PS2Elves`; **re-loaded** `cnk_boot.elf` (was Hitman-only at session start) |
| Key VA prologue locks | Still **6/6** in `logs/ghidra-ps2/cnk-key-vas-summary.json` |
| Observe smoke | `cnk-2prims-gate-diagnose-2026-11-07.md` — registry live, `+5DD0=1`, **prims=2**, no `0x51ACEC` |

---

## 6) Next observe-only steps (no runtime patch)

1. Ghidra: stable decompile `0x53B940`, `0x10F9E0` worker entry, and **`FUN_0023aae0`** child → who clears `+0x5DD0`.
2. Xref timeline: guest-only breakpoint sites at `0x10F560` branch (`5DC8`/`5DD0`) and `0x51ACD0` (tid vs map) when diagnostic build is explicitly approved.
3. Correlate `0x10F9E0` worker with tid **4** map entry (`0x1859D28` in prior RAM dumps) without host-forced FCE0.

---

## Quarantine checklist

- [x] No edits under `runtime/` for CNK Alchemy pulses  
- [x] No disc-fix / R5 apply on Hitman / NFS  
- [x] Dumper / RE only under `tools/ps2-alchemy-dumper/` and `verification/recovery/`
