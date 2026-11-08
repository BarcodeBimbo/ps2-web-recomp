# Harness shot manifest — 20261108T001208Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261108T001208Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261108T001208Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261108T001208Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261108T001208Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261108T001208Z\fps-overlay.jsonl`

## NFS (`NFS_MW`)
- ok=False goal=expect=gpu_boot booted=True max_prims=29164 end_lum=9.579089060427014 software=False abort=True
- fps_overlay: `{'samples': 10, 'avg': 42.4, 'min': 20.0, 'max': 60.0, 'maxMs_peak': 553.0, 'graph_trend_avg': -0.10136363636363636, 'graph_trend_last': -0.097}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\00_goto.png` — canvas_lum=6.24; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\01_boot.png` — canvas_lum=20.44; overlay_fps=20; overlay_maxMs=553; graph_trend=-0.533; shot_fps_tint=warn_bad graph_ink=0.2806
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\02_observe_start.png` — canvas_lum=20.43; overlay_fps=25; overlay_maxMs=132; graph_trend=-0.051; shot_fps_tint=warn_bad graph_ink=0.3234
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\03_observe_mid.png` — canvas_lum=0.16; overlay_fps=60; overlay_maxMs=124; graph_trend=-0.091; shot_fps_tint=warn_bad graph_ink=0.1974
  - **issue_halt_18** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\issue_halt_18.png` — canvas_lum=8.36; overlay_fps=59; overlay_maxMs=71; graph_trend=-0.097; shot_fps_tint=warn_bad graph_ink=0.1996; boot=Game stopped — crash log saved; help=missing code at 0x01A5C000
  - **04_observe_end** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001208Z\nfs_mw\04_observe_end.png` — canvas_lum=8.36; overlay_fps=59; overlay_maxMs=71; graph_trend=-0.097; shot_fps_tint=warn_bad graph_ink=0.1996; boot=Game stopped — crash log saved; help=missing code at 0x01A5C000
