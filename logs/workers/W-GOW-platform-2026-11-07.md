# W-GOW platform rebalance — 2026-11-07

**Lane:** God of War (USA) `695b874b308a4e5353767bb6df8ba697`  
**Task:** browser min60 re-verify (Chrome / `_gow_min60_accept.py`)  
**Hard ban observed:** no disc-fix / R5 / CNK Alchemy patches

## Readiness

| Check | Result |
|---|---|
| Panel `:8620` | UP (`HTTP 200`) |
| `/api/games` GoW status | `ready` |
| `/play/695b…/?statslog=1&fps=1` | `HTTP 200` |
| Native patient-zero smoke | PASS prior — 3600f, **19,189,130** prims (`logs/gow-patientzero-smoke/run.log`) |
| Health | `ok`, `reached_frame_limit`, prims 28,463,922 (explore) |

## Browser min60 verify

| Field | Value |
|---|---|
| **Verdict** | **FAIL** |
| Harness | `python tools/_gow_min60_accept.py 90 200 70` |
| Pipeline log | `logs/autonomous-pipeline/gow-min60-W-GOW-platform-20261107T190534.log` |
| Accept JSON | `tools/gow-min60-accept.json` (overwritten this run) |
| Gate | `min_fps_gate=59.5`, `pass_all_min60=false`, `pass_active_min60=false` |
| Exit | `1` |

### FPS (stable window t≥70s, hold 200s)

| Metric | all / active |
|---|---|
| n | 242 |
| avg | **60.00** |
| min | **56.8** |
| max | 64.2 |
| below60 (&lt;59.5) | **15** |
| below45 | 0 |
| on-screen min | **43** (below60 on-screen: 30) |

Not sustained ≥60: 15 samples dipped under the 59.5 gate (worst 56.8 fps / 43 on-screen at t≈72s, hitch 197.8 ms).

### Contrast vs prior PASS (2026-11-06)

Prior `logs/gow-min60-PASS.txt`: avg 60.0, min 59.8, below60=0, `pass_all_min60=true`.  
This run: audio queue ~241–330 ms (prior PASS ~70–90 ms); Hitman Blood Money was **`building`** on the same panel during the hold.

## Plan checkbox

- [ ] GoW USA min60 browser re-verify (`695b874b…`) — **NOT flipped** (fail; sustained ≥60 not verified)

## Heartbeat

`logs/workers/W-GOW-platform-heartbeat.log`
