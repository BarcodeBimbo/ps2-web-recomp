# W-CNK worker report — CNK Alchemy loadgate/bind RE (2026-11-07)

**Worker:** W-CNK  
**Game:** Crash Nitro Kart (`b49f2e769315347e8bda839feb705744`)  
**Plan:** `logs/master-campaign-plan-2026-11-07.md` §2c  
**Quarantine:** no disc-fix / R5 / CNK **host** patches on Hitman or NFS.

---

## Mission summary

| Step | Result | Evidence |
|------|--------|----------|
| Read A1–A4 synthesis + MASTER §G | done | `alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` |
| Alchemy dumper verify (CNK) | **28/28 PASS** | re-run this session, exit 0 |
| Ghidra MCP `:8089` | **up**; CNK ELF **re-loaded** | was `hitman_boot.elf` only → `load_program(cnk_boot.elf)` |
| Loadgate/bind RE advance | **documented** | `verification/recovery/cnk-loadgate-bind-re-observe-2026-11-07.md` |
| CNK `prims=2` fix | **not claimed** | prior observe smoke unchanged |

### Master plan §2c

| Checkbox | Action |
|----------|--------|
| [x] Dumper 28/28 | unchanged (re-verified) |
| [x] Quarantine hard bans | honored |
| [ ] `prims=2` / loadgate / bind EE RE | **open** — RE advanced (parent `0x10F560` decompile + gate map); playable still blocked on `+0x5DD0` / worker `0x10F9E0` |
| [ ] `game-fix-registry.json` proven fixes | no new proven runtime fix |
| [ ] CNK Chrome playable | open |

---

## 1) Alchemy dumper

```text
cd tools\ps2-alchemy-dumper
python -m ps2_alchemy_dumper verify c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso
# verify 28/28 — prologue locks, GFC/GOB/IGB, 595 ig*, absent igFileIO on MODULES
```

Artifacts refreshed under `tools/ps2-alchemy-dumper/out/`.

---

## 2) Ghidra MCP (observe RE)

| Item | Detail |
|------|--------|
| Transport | `http://127.0.0.1:8089`, project `PS2Elves` |
| Session fix | Imported `C:\Users\joshy\ghidra_exports\ps2-elves\cnk_boot.elf` (6 234 672 B) |
| Prior locks | `logs/ghidra-ps2/cnk-key-vas.json` — FCE0, finalize, null_bind, install, factory **6/6** |
| New this session | Decompile **`FUN_0010f560`** parent tick; **`FUN_0010faf0`** pre-sweep; **`FUN_00511070`** list walk |
| vt+80 `0x53B940` | Function create acknowledged; decompile pending analysis — raw prologue + prior null-bind report |

**Parent gate (verified decompile):** guest `0x10FCE0` runs only when `*(gate+0x5DC8)≠0` **and** `*(gate+0x5DD0)==0`, after optional `0x10FAF0` slot sweep — aligns with `cnk-2prims-gate-diagnose-2026-11-07.md` (`+5DD0=1` stall).

---

## 3) Root cause (unchanged, cross-checked)

Soft-arm installs bind registry (`*0x725F50` live, tid **1**). One loadgate walk sets **`gate+0x5DD0=1`**, so **`0x10F560` stops calling guest FCE0** before IGB/UI graph produces drawables → **`prims=2`**. Host-forced FCE0 on unmapped tid still routes to **`ra=0x51ACEC`** — remain forbidden per quarantine.

**Approved observe next:** trace **`0x10F9E0`** worker + what clears `+0x5DD0` on retail schedule (no `host_call` FCE0).

---

## 4) Deliverables

| Artifact | Path |
|----------|------|
| Loadgate/bind RE note | `verification/recovery/cnk-loadgate-bind-re-observe-2026-11-07.md` |
| This report | `logs/workers/W-CNK-report-2026-11-07.md` |
| Synthesis (input) | `verification/recovery/alchemy-rebuild-synthesis-a1-a4-2026-11-07.md` |

---

## 5) Continuous loop — next iteration

1. Ghidra: complete decompile/xref for `0x53B940`, `0x10F9E0`, `FUN_0023aae0` spawn chain.  
2. RAM timeline: compare `+0x5DD0` / tid map across existing `logs/ram/cnk-*.ram` (offline, no patch).  
3. When explicitly approved for diagnostic build only: guest-side log at `0x10F560` / `0x51ACD0` — still **no** Hitman/NFS / disc-fix coupling.
