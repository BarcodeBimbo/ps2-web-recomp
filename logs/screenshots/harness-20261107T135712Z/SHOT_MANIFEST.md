# Harness shot manifest — 20261107T135712Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261107T135712Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261107T135712Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261107T135712Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261107T135712Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261107T135712Z\fps-overlay.jsonl`

## Hitman (`Hitman_BM`)
- ok=False goal=expect=menu booted=False max_prims=0 end_lum=9.189174551794766 software=False abort=True
- fps_overlay: `{'samples': 0, 'avg': None, 'min': None, 'max': None, 'maxMs_peak': None, 'graph_trend_avg': 0.0, 'graph_trend_last': 0.0}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm`
  - **00_goto** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm\00_goto.png` — canvas_lum=8.39; graph_trend=0; boot=Preparing game…
  - **00_halt** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm\00_halt.png` — canvas_lum=8.39; graph_trend=0; boot=Game stopped — crash log saved; help=The browser engine script could not load. Rebuild this game or check the server. A crash log was saved aut
  - **01_boot** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm\01_boot.png` — canvas_lum=8.39; graph_trend=0; boot=Game stopped — crash log saved; help=The browser engine script could not load. Rebuild this game or check the server. A crash log was saved aut
  - **issue_halt_0** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm\issue_halt_0.png` — canvas_lum=8.39; graph_trend=0; boot=Game stopped — crash log saved; help=The browser engine script could not load. Rebuild this game or check the server. A crash log was saved aut
  - **04_observe_end** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261107T135712Z\hitman_bm\04_observe_end.png` — canvas_lum=8.39; graph_trend=0; boot=Game stopped — crash log saved; help=The browser engine script could not load. Rebuild this game or check the server. A crash log was saved aut
