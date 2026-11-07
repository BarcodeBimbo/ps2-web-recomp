# Harness shot manifest — 20261107T140555Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261107T140555Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261107T140555Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261107T140555Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261107T140555Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261107T140555Z\fps-overlay.jsonl`

## Hitman (`Hitman_BM`)
- ok=False goal=expect=menu booted=True max_prims=864983 end_lum=2.8723563247011366 software=False abort=False
- fps_overlay: `{'samples': 25, 'avg': 56.16, 'min': 23.0, 'max': 65.0, 'maxMs_peak': 340.0, 'graph_trend_avg': -0.007807692307692305, 'graph_trend_last': 0.032}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm\00_goto.png` — canvas_lum=6.17; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm\01_boot.png` — canvas_lum=0.16; overlay_fps=35; overlay_maxMs=219; graph_trend=-0.592; shot_fps_tint=warn_bad graph_ink=0.1951
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm\02_observe_start.png` — canvas_lum=0.23; overlay_fps=23; overlay_maxMs=340; graph_trend=0.156; shot_fps_tint=warn_bad graph_ink=0.295
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm\03_observe_mid.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=17; graph_trend=0; shot_fps_tint=ok graph_ink=0.1806
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T140555Z\hitman_bm\04_observe_end.png` — canvas_lum=0.14; overlay_fps=62; overlay_maxMs=36; graph_trend=0.032; shot_fps_tint=ok graph_ink=0.1853
