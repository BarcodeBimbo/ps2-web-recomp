# Harness shot manifest — 20261107T131504Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261107T131504Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261107T131504Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261107T131504Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261107T131504Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261107T131504Z\fps-overlay.jsonl`

## Hitman (`Hitman_BM`)
- ok=False goal=expect=menu booted=True max_prims=675671 end_lum=2.8778535856573115 software=False abort=False
- fps_overlay: `{'samples': 21, 'avg': 54.42857142857143, 'min': 15.0, 'max': 60.0, 'maxMs_peak': 674.0, 'graph_trend_avg': -0.046000000000000006, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z\hitman_bm`
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z\hitman_bm\01_boot.png` — canvas_lum=0.16; overlay_fps=15; overlay_maxMs=674; graph_trend=-0.856; shot_fps_tint=warn_bad graph_ink=0.1437
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z\hitman_bm\02_observe_start.png` — canvas_lum=0.22; overlay_fps=25; overlay_maxMs=314; graph_trend=-0.051; shot_fps_tint=warn_bad graph_ink=0.3133
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z\hitman_bm\03_observe_mid.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=18; graph_trend=0; shot_fps_tint=ok graph_ink=0.1819
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131504Z\hitman_bm\04_observe_end.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=17; graph_trend=0.002; shot_fps_tint=ok graph_ink=0.1817
