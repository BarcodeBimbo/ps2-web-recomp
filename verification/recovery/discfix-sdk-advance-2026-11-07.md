# Disc-fix SDK advance — R4-D1 DiskReady mode fidelity (2026-11-07)

**Target:** TARGET 1 — Disc-fix → SDK standard  
**Games:** Hitman Blood Money `a2116d2ac08a7be4db4e8455ad58d2e5` · NFS Most Wanted `60c82f4a111da300ac23bbec85272788`  
**SDK root:** `E:\usr\local\sce` only  
**Joint-stable base:** R1–R4 `1e04172`  
**Board cycle:** step 9 · `R4D1_DiskReady_mode_fidelity`  
**Quarantine held:** no CNK Alchemy (`host_signal` 16/54/55, soft-arm, FCE0 force, virt-LBA)

---

## Verdict

**PASS (verified_apply)** — narrow DiskReady HLE now honors SDK mode / return contract. Hitman + NFS 600f smokes green; NFS actively exercises N-cmd `0x0E` (DiskReady). R5 pad/sound remains gated.

---

## SDK alignment

| Source | Contract |
|--------|----------|
| EE Ref Device 3.0.3 `sceCdDiskReady` (2-23) | mode `0` block until rotation stable; mode `1` poll; returns `0x02` `SCECdComplete` or `0x06` `SCECdNotReady` |
| `libcdvd.h` | `#define SCECdComplete 0x02` / `#define SCECdNotReady 0x06` |
| EE `libcdvd.a` (disasm) | `sceCdDiskReady` stores mode, `sceSifCallRpc` → `0x8000059C` (new) / `0x8000059A` (old) with **4-byte send**; `sceCdNcmdDiskReady` uses N-cmd method **`0x0E`** with **no mode word** (status only) |
| Prior flag | Product always returned `2` and ignored mode/args — R4-D1 in `sdk-compliance-r4-cdsync.md` / `SDK-R1-R5-COMPLIANCE-REPORT.md` |

**What we closed:** mode is read; NotReady(6) branch exists; IOP `cdvdman` export 13 can block on mode 0 when `!drive_ready`.  
**What remains intentional:** ISO HLE keeps `drive_ready=true` (disc always mounted) — so Hitman/NFS still see Complete(2). No tray/spin-up model; Stop does not clear ready (would hang mode-0 waiters without a Standby wake). That residual is **correct for mounted-ISO HLE**, not “ignore mode.”

---

## What changed (files)

| File | Change |
|------|--------|
| `runtime/src/iop/cdvd.cpp` | `drive_ready` + `ready_waiters`; `sceCdDiskReady` mode 0/1; Init/Standby call `finish_drive_ready()` |
| `runtime/src/iop/cdvdfsv.cpp` | FSV servers `0x8000059A`/`0x8000059C` read mode from CallRpc send word; N-cmd `0x0E` returns `2`/`6` from `g_fsv_drive_ready` |
| `verification/recovery/discfix-matrix-board.json` | Cycle 9 proposal → matrix pass / verified_apply |
| `verification/recovery/discfix-sdk-advance-2026-11-07.md` | This report |

**Not touched:** CNK Alchemy paths, R5 pad/sound HLE, CdSync wake (R4 already cleared).

---

## Smoke results (PATH=`runtime-deps` + clang64 + wgpu)

| | Hitman BM | NFS MW |
|--|-----------|--------|
| Frames | **600** (frame limit) | **600** (frame limit) |
| Primitives | **146363** | **49750** |
| SIF packets waiting | **0** | **0** |
| Exit | 0 | 0 |
| Alchemy quarantine hits | **0** | **0** |
| CDVD searches (scorer) | **14** | 0 (fileio-heavy; same scorer gap as R5) |
| Matrix phases | **all pass** | boot+menu pass; first_disc_read+ mechanical fail on `searches>=1` — **manual pass** (loads IRX via fileio, draws, SIF 0; DiskReady N `0x0E` proved under `--trace-iop-hle`) |

### Logs

- `logs/discfix-sdk-hitman-600.err.log` (+ `.merged.log`)
- `logs/discfix-sdk-nfs-600.err.log` (+ `.merged.log`)
- `logs/discfix-sdk-nfs-hletrace.err.log` — 300f `--trace-iop-hle`: **60×** `[cdvdfsv] N 0xE` (DiskReady) + **60×** `N 0x1` (Read)

---

## Matrix-style board outcome

- `allow_discfix_apply`: was `true` for this apply; set **`false`** after verified_apply  
- `ranked_rewrite_decision.R4D1_DiskReady`: **`verified_apply`**  
- R5: still **`observe_pass_still_gated`**

---

## Blocked / next

1. **Not blocked** on DiskReady for Hitman/NFS — D1 mode-ignore closed; tray/NotReady media model deferred.  
2. **Next legal options:** R5 `clear_with_evidence` (still no pad/sound HLE), or evidence-named narrow RPC fix; parent joint-stable commit ask when ready.  
3. **Do not** clear `drive_ready` on `sceCdStop` without a Standby/tray wake path.  
4. Optional scorer tweak: accept NFS fileio / N-cmd evidence when SearchFile strings absent (out of this apply).
