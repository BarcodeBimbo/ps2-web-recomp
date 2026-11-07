# Disc-fix cycle 10 — R5 pad/sound CLEAR_WITH_EVIDENCE (2026-11-07)

**Gate:** `R5_pad_sound_clear_with_evidence` (`code_change: false`)  
**Games:** Hitman Blood Money `a2116d2ac08a7be4db4e8455ad58d2e5` · NFS Most Wanted `60c82f4a111da300ac23bbec85272788`  
**Hard bans held:** no padman/libsd/sdrdrv HLE rewrite; no `host_signal` of leftover WaitSema; no CNK Alchemy; `allow_discfix_apply=false` for HLE rewrite  
**Board:** `verification/recovery/discfix-matrix-board.json`  
**Matrix verdict:** **pass** — observe gate **cleared_with_evidence** (still **not** an R5 HLE apply)

---

## Why clear (not rewrite)

R5 asked whether leftover WaitSema parks on Hitman/NFS meant missing padman/libsd HLE. Evidence says **no**:

1. **Guest IRX already loads** pad/sound stacks (not host module HLE).
2. **SIO2 + SPU2 MMIO** already exercise DualShock config/read and SPU2 writes under guest servers.
3. **Leftover WaitSema IDs are owned/classified** durable parks (create_ra + init/max), not orphan RPC gates needing blind wake.
4. **Zero** `host_signal` / Alchemy / soft-arm / virt-LBA on this pair in clear smokes.
5. Inventory confirms **no** padman/libsd `register_hle_*` twin exists — and none is required to keep short smokes green.

Therefore: **close the observe gate with evidence**. Do **not** land a padman/libsd HLE rewrite. `allow_discfix_apply` stays **false** for that class of change.

---

## Leftover WaitSema — owned / classified

Source ownership: `verification/recovery/waitsema-createsema-trace-live-report.md`  
Reconfirmed end-dump on clear 500f smokes (below).

| Game | ID | Class | create_ra | init/max | Clear rule |
|------|-----|-------|-----------|----------|------------|
| Both | **2** | **libcdvd durable parking** (R2) | Hitman `0x001038CC` · NFS `0x00495EA8` | 0 / 255 | Never `host_signal(2)` |
| Hitman | **7** | Title-private durable gate (final owner) | `0x001008FC` | 0 / 1 | Classify-only; **no** wake |
| NFS | **17, 23, 32** | Same EE factory (pad-class RA cluster) | `0x00490224` | 0 / 1 | Classify-only; **no** wake |
| NFS | **29** | Small counting gate | `0x0046A208` | 0 / 3 | Classify-only; **no** wake |
| NFS | **30** | Durable sound-class gate (after early max=1 churn) | `0x0046B748` | 0 / **253** | Classify-only; **no** wake |

**Not** temp RPC ID reuse for these leftovers (contrast Hitman id 13 churn). Parks are owned by guest create sites; clearing them with host pulses would fake completion.

---

## Guest IRX load (not host padman/libsd HLE)

**Hitman:** `SIO2MAN` → `PADMAN` → `MCMAN` → `MCSERV` → `LIBSD` → `SCRTCHPD` → `SYNTHCD`  
**NFS:** `sio2man` → `padman` → `mcman` → `mcserv` → `Sound_Device_Library` → `sdr_driver` → `SND_Library_EE_Driver` (+ USB / LgDev)

Pad/SPU2 activity under those modules (clear 500f):

| | Hitman | NFS |
|--|--------|-----|
| `[pad]` lines | 495 | 640 |
| `[spu2]` lines | 121 | 2237 |

---

## Smoke results (re-smoke after R4-D1)

Env: `PS2_TRACE_SEMA=1`, `PS2_TRACE_PAD=1`, `PS2_TRACE_SPU2=1`, `PS2_SPU2_COUNT=1`  
PATH: `runtime-deps` + clang64. No disc-fix source edits this cycle.

| | Hitman BM | NFS MW |
|--|-----------|--------|
| Frames | **500** (frame limit) | **500** (frame limit) |
| Primitives | **118413** | **140753** |
| SIF packets waiting | **0** | **0** |
| Exit | 0 | 0 |
| Real Alchemy / host_signal / soft-arm / virt-LBA | **none** | **none** |
| Leftover WaitSema | **2**, **7** | **2**, **17**, **23**, **29**, **30**, **32** |
| CDVD searches (scorer strings) | **14** | 0 (fileio; same known gap) |

### Logs

- `logs/discfix-r5-clear-hitman-500.err.log` (+ `.merged.log`)
- `logs/discfix-r5-clear-nfs-500.err.log` (+ `.merged.log`)

Prior observe: `logs/discfix-r5-observe-*-400.*` · report `discfix-r5-observe-matrix-2026-11-07.md`

---

## R5 apply status

| Item | Result |
|------|--------|
| Observe / clear gate | **PASS** → `cleared_with_evidence` |
| padman / libsd / sdrdrv HLE rewrite | **NOT applied** |
| `host_signal` leftovers | **NOT used** (and forbidden) |
| `allow_discfix_apply` | **false** (HLE rewrite still locked) |
| Quarantine (CNK Alchemy) | **held** |

---

## Next legal options (do not auto-apply)

1. Parent joint-stable commit ask for **R3 + R4D1** code (R5 was docs/evidence only).  
2. Evidence-named **narrow** SIF/pad/sound RPC fix **only** if a concrete failing RPC is named from create_ra / pad / SPU2 traces — new proposal + matrix + explicit unlock.  
3. Do **not** reopen R5 as a blind module HLE port without that named failure.
