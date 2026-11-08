# Agent campaign snapshot (context rollover seed)

**Updated:** 2026-11-07 ~19:04 local (permanent overnight mode encoded)  
**Read this + `MASTER-CONTEXT.md` RESUME POINT on every fresh agent start.**  
**Checkbox campaign plan:** `logs/master-campaign-plan-2026-11-07.md`  
**Standing orders:** `logs/call-log-2026-11-07.md` §8 permanent overnight mode.

**Owner OS (permanent until God says stop):** never idle; never wait for permission; never stop on a completed checkbox — next open immediately; test/fix/improve all night; no kill-on-retry; no session-end stalls; platform-wide parallel lanes; **report only on breaks or major greens.**

## Owner pivot (2026-11-07 night)

- **Alive:** `logs/campaign-owner-alive.txt` + `logs/campaign-owner-heartbeat.json`
- **Locks:** `logs/locks/web-a2116….lock`, `native-a2116….lock`, `web-a2116…-next.lock` (owner fresh)
- **XYOFFSET:** reverted 11-bit→**16-bit 12.4** (`gs.hpp`); GS manual confirmed. Clears land `0..512×448` on FBP288 but present still ~0.1 lum.
- **Compose research ([W-HITMAN-compose](f858f950-e5e1-410c-9cef-3161ee7cb882)):** recommend **(B)** sprite/tex write path — defer host 288→400 blit until FBP288 non-empty. Report `logs/workers/W-HITMAN-compose-research-2026-11-07.md`.
- **NFS ([W-NFS](d687f486-1771-4f45-8cd9-0605050a2363)):** id `60c82f4a…`; Chrome hitch = web disc `chunk`/`read_ahead` EE stall (not SW GS). Follow-up W-NFS-2 prefetch implementer spawned.
- **Still open:** Hitman mesh fill after correct clear; NFS Chrome ≥60; CNK Alchemy.
- **Workers:** W-CNK, W-NFS-2 prefetch; Hitman web-next rebuild

## Worker merge (2026-11-07)

| Worker | Id | Landed in repo |
|--------|-----|----------------|
| W-HITMAN | `b5fcf52a-e184-46a6-92a7-2c7ce8fe9273` | Layer 3 capture, ELF Phase 0, Layer 1 Ghidra clears |
| W-NFS | `c86fe5bd-c641-41f0-a412-1422aaa9eee4` | 500f pass, `matrix_phase_check` fileio fix, A–H report |
| W-STORE | `9cf97173-9502-488b-827c-3c2ba6db2e20` | `store_pipeline_hooks.py`, strict verify, manifest |
| W-HEAL | `721aeabc-e3b3-4c70-8bc0-6d62431e00a6` | Detectors + poll; coordinator fixed matrix log scope + XYOFFSET stale neg |
| W-CHROME60 | `e933d45d-90f7-4506-95b0-dacaaaf345b5` | Harness `metrics.json`, `autonomous_verify` fps/chrome_metrics |
| W-RES | `49970e90-bc53-4ac8-8e0e-b053b060986a` | Resource probe; binwalk → structural CNK scripts |
| W-CNK | `9e5dc949-0175-4854-bac9-df87926f1c0f` | Loadgate RE observe; `prims=2` still open |

## Current pointer

- **Hitman web:** `ps2web.wasm` **11:09**; `library.json` **ready**; harness `20261107T161255Z` → **845k** prims, **~58 FPS**, **`canvas_lum≈0.14`** (fail).
- **Blocking:** DISPFB **400** present vs FRAME **288** draws (`gs.cpp` `resolve_present_source`).
- **NFS:** native matrix pass; Chrome FPS/lum open per W-NFS report.
- **Verify smoke:** always `--disc games/<id>/disc.iso`.

## Immediate commands

```powershell
$env:PATH = "C:\PS2Recomp\runtime-deps;C:\PS2Recomp\tools\msys64\clang64\bin;C:\PS2Recomp\third_party\wgpu-native\lib;" + $env:PATH
python C:\PS2Recomp\scripts\self_heal.py --game a2116d2ac08a7be4db4e8455ad58d2e5
py -3 -u C:\PS2Recomp\tools\_cyberarcade_live_harness.py 45 Hitman_BM
```
