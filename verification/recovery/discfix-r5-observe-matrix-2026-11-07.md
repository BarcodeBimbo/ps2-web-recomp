# Disc-fix cycle 8 — R5 pad/sound OBSERVE matrix (2026-11-07)

**Gate:** `R5_pad_sound_observe` (`code_change: false`)  
**Games:** Hitman Blood Money `a2116d2ac08a7be4db4e8455ad58d2e5` · NFS Most Wanted `60c82f4a111da300ac23bbec85272788`  
**Hard bans held:** no edits to `cdvdfsv.cpp` / `cdvd.cpp` / `sif.cpp`; no R5 pad/sound HLE apply; no CNK Alchemy pulses; `allow_discfix_apply=false`  
**Board:** `verification/recovery/discfix-matrix-board.json`  
**Matrix verdict (OBSERVE gate only):** **pass**

---

## Launch / PATH

- Product entry: `PS2Recomp.cmd` → `runtime-deps` + clang64 + wgpu on PATH.
- Native smokes used DLLs beside `build/native-<gid>/` (also mirrored in `runtime-deps/` and repo root).
- `ps2run` loads (bad-args exit on `--help`, not `STATUS_DLL_NOT_FOUND`).
- No disc-fix source changes — PATH / deps only.

Env for observe smokes: `PS2_TRACE_SEMA=1`, `PS2_TRACE_PAD=1`, `PS2_TRACE_SPU2=1`, `PS2_SPU2_COUNT=1`.

---

## Evidence paths

| Artifact | Path |
|----------|------|
| Hitman stderr (primary) | `logs/discfix-r5-observe-hitman-400.err.log` |
| NFS stderr (primary) | `logs/discfix-r5-observe-nfs-400.err.log` |
| Hitman merged (copy of err) | `logs/discfix-r5-observe-hitman-400.merged.log` |
| NFS merged (copy of err) | `logs/discfix-r5-observe-nfs-400.merged.log` |
| Prior pad/sound 400f (2026-11-06) | `logs/r5-hitman-pad-sound-400.log`, `logs/r5-nfs-pad-sound-400.log` |
| WaitSema ownership map | `verification/recovery/waitsema-createsema-trace-live-report.md` |
| R5 SDK inventory | `verification/recovery/sdk-compliance-r5-pad-sound-inventory.md` |
| R1–R4 stable marker | `verification/recovery/DISCFIX-R1-R4-STABLE.md` (`1e04172`) |
| Phase scorer (CDVD-oriented) | `verification/recovery/matrix_phase_check.py` |

Tooling: no dedicated matrix runner beyond `matrix_phase_check.py` (score-only). Smokes run manually via `build/native-<gid>/ps2run.exe`.

---

## Smoke results (short regression + observe)

| | Hitman BM | NFS MW |
|--|-----------|--------|
| Frames | **400** (frame limit) | **400** (frame limit) |
| Primitives | **78933** | **73253** |
| SIF packets waiting | **0** | **0** |
| Real Alchemy / host_signal / soft-arm / virt-LBA | **none** | **none** |
| Leftover WaitSema | **2**, **7** | **2**, **17**, **23**, **29**, **30**, **32** |
| create_ra (leftovers) | 2→`0x001038CC`; 7→`0x001008FC` | 2→`0x00495EA8`; 17/23/32→`0x00490224`; 29→`0x0046A208`; 30→`0x0046B748` |

### Module load (guest IRX — not host padman/libsd HLE)

**Hitman:** `SIO2MAN` → `PADMAN` → `MCMAN` → `MCSERV` → `LIBSD` → `SCRTCHPD` → `SYNTHCD`  
**NFS:** `sio2man` → `padman` → `mcman` → `mcserv` → `Sound_Device_Library` → `sdr_driver` → `SND_Library_EE_Driver` (+ USB / LgDev)

### Pad / SPU2 activity

| | Hitman | NFS |
|--|--------|-----|
| `[pad]` lines | 395 | 440 |
| `[spu2]` lines | 128 | 2237 |

Pad path exercises DualShock config / read (cmd `0x42`/`0x43`/mode setup). SPU2 MMIO writes active after LIBSD / Sound_Device_Library load.

### CDVD / R1–R4 short check

- Hitman: **14** `cdvdfsv] search … -> found` (BOOTMENU / ERRORMES / HM3GPAD etc.) — shared CDVD path still live.
- NFS: short observe log under heavy pad/SPU2 trace has no `cdvdfsv] search` strings (same shape as prior `r5-nfs-pad-sound-400`); still draws, loads IRX via fileio, SIF drains. Prior R3 600f logs remain the CDVD prove (`logs/discfix-r3-nfs-600.log`).

---

## Mechanical scorer note (not a real fail)

`matrix_phase_check.py` marks Hitman `alchemy_contamination=true` because createsema `attr=0x1FFFCE0` matches the `FCE0` substring in `ALCHEMY_PULSE`. **Not** a host Alchemy pulse. NFS scorer also under-reports CDVD searches on this observe log.  
**OBSERVE gate scored manually against proposal success_bar** (evidence gathered + short smokes green + no apply).

---

## Verdict

| Item | Result |
|------|--------|
| Observe gate | **PASS** |
| R5 apply | **NOT applied** (still gated) |
| `allow_discfix_apply` | **false** |
| Quarantine | held |

### Next legal proposals (parent / disc-fix — do not auto-apply)

1. **`R5_pad_sound` `clear_with_evidence`** — close observe with no HLE rewrite if leftovers stay classify-only.  
2. **Evidence-named narrow RPC fix** — only after naming a concrete SIF/pad/sound RPC failure from create_ra / pad / SPU2 traces (still prove-before-swap; needs new proposal + matrix + explicit unlock).

Do **not** blind `host_signal` Hitman **7** or NFS **17/23/29/30/32**. Sema **2** remains libcdvd durable parking (R2).
