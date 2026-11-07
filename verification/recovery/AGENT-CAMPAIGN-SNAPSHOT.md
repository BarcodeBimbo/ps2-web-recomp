# Agent campaign snapshot (context rollover seed)

**Updated:** 2026-11-07 ~11:20 local  
**Read this + `MASTER-CONTEXT.md` RESUME POINT on every fresh agent start.**  
**Checkbox campaign plan:** `logs/master-campaign-plan-2026-11-07.md`  
**Standing orders:** `logs/call-log-2026-11-07.md` — chat-only, no idle.

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
