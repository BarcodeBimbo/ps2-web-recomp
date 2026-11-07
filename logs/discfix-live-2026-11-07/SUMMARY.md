# Disc-fix live execution — Hitman + NFS (2026-11-07 ~07:43)

Rebuilt `ps2run` for both titles with DiskReady R4-D1 + latest `cdvdfsv.cpp`, then **real** 900f native runs + Chrome panel play tabs opened.

**Rebuild:** `cmake --build build/native-<gid> --target ps2run` (exit 0)  
**PATH:** `runtime-deps` + clang64 + wgpu  
**Panel:** `http://127.0.0.1:8620/` (connection tool) — play tabs launched for both games

## Per-game outcomes

| | Hitman Blood Money | NFS Most Wanted |
|--|--------------------|-----------------|
| GID | `a2116d2ac08a7be4db4e8455ad58d2e5` | `60c82f4a111da300ac23bbec85272788` |
| Disc mount | **YES** — `disc.iso` 310 files / 1,540,176 sectors | **YES** (ISO path; IRX load + draws) |
| Boot | **YES** (frame limit, exit 0) | **YES** (frame limit, exit 0) |
| Past loader | **YES** — IOPRP310, SIO2MAN→PADMAN→LIBSD, BOOTMENU searches | **YES** — sio2man→padman→Sound_Device_Library→sdr_driver |
| CDVD searches | **14** found (SYSTEM.CNF, ERRORMES, BOOTMENU, …) | IRX/fileio path live (900f draw load) |
| Prims | **261,534** | **408,728** |
| SIF wait | **0** | **0** |
| Crash / missing code | **none** | **none** |
| Host pace | ~241 f/s wall | (900f completed) |
| Chrome play URL | `/play/a2116d2a…/` opened | `/play/60c82f4a…/` opened |

## R5 next

R5 observe already PASS (cycle 8). Worker posting **`clear_with_evidence`** — no padman/libsd HLE rewrite; classify leftover WaitSemas (Hitman 2+7; NFS 2+17/23/29/30/32).

## Logs

- `Hitman_BM-900.log`, `NFS_MW-900.log`
- `native-live-results.json` / `.txt`
