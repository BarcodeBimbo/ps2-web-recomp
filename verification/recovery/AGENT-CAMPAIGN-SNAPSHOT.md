# Agent campaign snapshot (context rollover seed)

**Updated:** 2026-11-07 ~19:12 local (campaign-owner permanent overnight resume)  
**Read this + `MASTER-CONTEXT.md` RESUME POINT on every fresh agent start.**  
**Checkbox campaign plan:** `logs/master-campaign-plan-2026-11-07.md`  
**Standing orders:** `logs/call-log-2026-11-07.md` §8 + `logs/campaign-owner-permanent-mode.md`

**Owner OS (permanent until God says stop):** never idle; never wait for permission; never stop on a completed checkbox — next open immediately; test/fix/improve all night; no kill-on-retry; no session-end stalls; platform-wide parallel lanes; **report only on breaks or major greens.**

## Owner resume (watchdog ~19:05 → owner ~19:06+)

- Prior owner pid **DEAD**; watchdog armed; this owner wrote `status=permanent-overnight-running`.
- **Alive:** `logs/campaign-owner-alive.txt` + `logs/campaign-owner-heartbeat.json`
- **Adopted orphan Hitman web-next watch** (cmake/ninja live — no kill). Locks updated to campaign-owner; promote only after build exits.
- **Mode B:** `PS2_GS_NO_TME` **falsified** — present lum still ~0.05–0.10 (`logs/workers/W-HITMAN-modeB-notme-2026-11-07.md`).
- **Store nightly:** orchestrator landed + **6/6** unit tests; master-plan nightly checkbox **flipped**.
- **GoW min60 accept:** **FAIL** hard gate (`pass_all_min60=false`; avg≈60 but dips to 56.8) — `tools/gow-min60-accept.json`; checkbox stays open.
- **CNK:** o20/smoke still **`prims=2`** (`W-CNK-ALCHEMY` 19:11).

## LIVE builds (do not kill)

| Tree | Job |
|------|-----|
| `build/web-a2116…-next` | cmake/ninja -j1 `ps2web` (Hitman) |
| `build/web-60c82f…-next` | cmake/ninja -j1 `ps2web` + `W-NFS-rebuild-web.py` |
| `build/native-a2116…` | W-HITMAN type7-fst cmake/ninja -j4 `ps2run` |
| `build/native-b49f2e…` | CNK native (dual cmake seen earlier; smoke used bin copy) |

## Lanes (7)

| Lane | Status / next |
|------|----------------|
| Hitman | Mode B sprite/tex; NO_TME falsified; type7-fst rebuild; web-next watch |
| NFS | Chrome ≥60; prefetch in `host/web.cpp` (48/24/16); waiting web-next |
| Sly | STQ/PATH3/CLUT parse capture |
| GoW | min60 hard gate FAIL — improve hitch/dips then re-run accept |
| Host | PRESENT_FB self_heal landed; heartbeat may need refresh |
| Store | Nightly script green; next: store→Chrome DoD contract |
| CNK | `prims=2` still; quarantine intact |

## Open priorities (master plan)

- Hitman canvas_lum / Chrome flawless / DISPFB compose (B) after non-empty raster
- NFS Chrome ≥60
- CNK prims=2 → proven_fixes
- GoW min60 re-verify
- Library `autonomous_verify` sweep
- Store pull → Chrome without manual patches

## Immediate commands

```powershell
$env:PATH = "C:\PS2Recomp\runtime-deps;C:\PS2Recomp\tools\msys64\clang64\bin;C:\PS2Recomp\third_party\wgpu-native\lib;" + $env:PATH
# After Hitman web-next exits: promote -next → published, harness Hitman_BM
# After native type7-fst: 180f frames-dir lum compare vs modeB-notme
py -3 -u C:\PS2Recomp\tools\_cyberarcade_live_harness.py 45 Hitman_BM
```
