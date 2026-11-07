# Harness shot manifest — 20261107T161255Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261107T161255Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261107T161255Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261107T161255Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261107T161255Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261107T161255Z\fps-overlay.jsonl`

## Hitman (`Hitman_BM`)
- ok=False goal=expect=menu booted=True max_prims=845147 end_lum=2.9001153718458914 software=False abort=False
- fps_overlay: `{'samples': 25, 'avg': 54.8, 'min': 0.0, 'max': 60.0, 'maxMs_peak': 167.0, 'graph_trend_avg': -0.05226923076923077, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm\00_goto.png` — canvas_lum=6.18; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm\01_boot.png` — canvas_lum=0.12; overlay_fps=0; overlay_maxMs=0; graph_trend=-0.28; shot_fps_tint=warn_bad graph_ink=0.0972; boot=Starting game…
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm\02_observe_start.png` — canvas_lum=0.16; overlay_fps=37; overlay_maxMs=167; graph_trend=-0.564; shot_fps_tint=warn_bad graph_ink=0.1578
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm\03_observe_mid.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=17; graph_trend=0; shot_fps_tint=ok graph_ink=0.1805
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T161255Z\hitman_bm\04_observe_end.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=17; graph_trend=0.002; shot_fps_tint=ok graph_ink=0.1816
