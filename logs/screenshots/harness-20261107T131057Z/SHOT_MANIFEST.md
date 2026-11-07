# Harness shot manifest — 20261107T131057Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261107T131057Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261107T131057Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261107T131057Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261107T131057Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261107T131057Z\fps-overlay.jsonl`

## Hitman (`Hitman_BM`)
- ok=False goal=expect=menu booted=True max_prims=787727 end_lum=2.875126162018534 software=False abort=False
- fps_overlay: `{'samples': 23, 'avg': 54.608695652173914, 'min': 16.0, 'max': 60.0, 'maxMs_peak': 683.0, 'graph_trend_avg': -0.03321739130434783, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\hitman_bm`
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\hitman_bm\01_boot.png` — canvas_lum=0.18; overlay_fps=16; overlay_maxMs=683; graph_trend=-0.617; shot_fps_tint=warn_bad graph_ink=0.14
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\hitman_bm\02_observe_start.png` — canvas_lum=0.23; overlay_fps=20; overlay_maxMs=354; graph_trend=-0.053; shot_fps_tint=warn_bad graph_ink=0.317
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\hitman_bm\03_observe_mid.png` — canvas_lum=0.13; overlay_fps=60; overlay_maxMs=18; graph_trend=0; shot_fps_tint=ok graph_ink=0.1818
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\hitman_bm\04_observe_end.png` — canvas_lum=0.14; overlay_fps=60; overlay_maxMs=18; graph_trend=0.002; shot_fps_tint=ok graph_ink=0.1816

## NFS (`NFS_MW`)
- ok=True goal=expect=gpu_boot booted=True max_prims=52308 end_lum=7.998044488712303 software=False abort=False
- fps_overlay: `{'samples': 23, 'avg': 20.47826086956522, 'min': 9.0, 'max': 53.0, 'maxMs_peak': 1110.0, 'graph_trend_avg': -0.026521739130434784, 'graph_trend_last': 0.039}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\nfs_mw`
  - **01_boot** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\nfs_mw\01_boot.png` — canvas_lum=20.39; overlay_fps=26; overlay_maxMs=372; graph_trend=-0.657; shot_fps_tint=warn_bad graph_ink=0.1507
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\nfs_mw\02_observe_start.png` — canvas_lum=20.45; overlay_fps=44; overlay_maxMs=155; graph_trend=-0.02; shot_fps_tint=warn_bad graph_ink=0.2552
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\nfs_mw\03_observe_mid.png` — canvas_lum=1.00; overlay_fps=11; overlay_maxMs=671; graph_trend=0.207; shot_fps_tint=warn_bad graph_ink=0.2432
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\nfs_mw\04_observe_end.png` — canvas_lum=7.43; overlay_fps=13; overlay_maxMs=520; graph_trend=0.039; shot_fps_tint=warn_bad graph_ink=0.2609

## GoW (`GoW_USA`)
- ok=False goal=expect=fps60 booted=True max_prims=27746217 end_lum=36.18280677290761 software=False abort=False
- fps_overlay: `{'samples': 23, 'avg': 52.34782608695652, 'min': 1.0, 'max': 61.0, 'maxMs_peak': 53.0, 'graph_trend_avg': -0.02421739130434783, 'graph_trend_last': -0.014}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\gow_usa`
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\gow_usa\01_boot.png` — canvas_lum=6.16; overlay_fps=1; overlay_maxMs=0; graph_trend=-0.231; shot_fps_tint=warn_bad graph_ink=0.0944
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\gow_usa\02_observe_start.png` — canvas_lum=6.16; overlay_fps=1; overlay_maxMs=0; graph_trend=-0.247; shot_fps_tint=warn_bad graph_ink=0.1555
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\gow_usa\03_observe_mid.png` — canvas_lum=46.96; overlay_fps=60; overlay_maxMs=18; graph_trend=-0.0; shot_fps_tint=warn_bad graph_ink=0.2955
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\gow_usa\04_observe_end.png` — canvas_lum=47.54; overlay_fps=60; overlay_maxMs=29; graph_trend=-0.014; shot_fps_tint=warn_bad graph_ink=0.2982

## Crash (`CNK`)
- ok=False goal=expect=prims_break booted=True max_prims=2 end_lum=3.1194198207170682 software=False abort=False
- fps_overlay: `{'samples': 23, 'avg': 44.26086956521739, 'min': 21.0, 'max': 61.0, 'maxMs_peak': 131.0, 'graph_trend_avg': -0.08773913043478265, 'graph_trend_last': 0.026}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\cnk`
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\cnk\01_boot.png` — canvas_lum=6.24; overlay_fps=21; overlay_maxMs=131; graph_trend=-0.698; shot_fps_tint=warn_bad graph_ink=0.1711; boot=Starting game…
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\cnk\02_observe_start.png` — canvas_lum=6.21; overlay_fps=21; overlay_maxMs=131; graph_trend=-0.643; shot_fps_tint=warn_bad graph_ink=0.2354; boot=Starting game…
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\cnk\03_observe_mid.png` — canvas_lum=6.20; overlay_fps=36; overlay_maxMs=56; graph_trend=-0.0; shot_fps_tint=warn_bad graph_ink=0.2756; boot=Starting game…
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\cnk\04_observe_end.png` — canvas_lum=0.18; overlay_fps=38; overlay_maxMs=71; graph_trend=0.026; shot_fps_tint=warn_bad graph_ink=0.3061

## Sly (`Sly1`)
- ok=True goal=expect=draw booted=True max_prims=383240 end_lum=12.992630229084018 software=False abort=False
- fps_overlay: `{'samples': 23, 'avg': 50.65217391304348, 'min': 31.0, 'max': 60.0, 'maxMs_peak': 239.0, 'graph_trend_avg': -0.0027391304347826107, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\sly1`
  - **01_boot** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\sly1\01_boot.png` — canvas_lum=8.87; overlay_fps=31; overlay_maxMs=239; graph_trend=-0.602; shot_fps_tint=warn_bad graph_ink=0.1496
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\sly1\02_observe_start.png` — canvas_lum=14.57; overlay_fps=31; overlay_maxMs=239; graph_trend=0.071; shot_fps_tint=warn_bad graph_ink=0.1999
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\sly1\03_observe_mid.png` — canvas_lum=14.70; overlay_fps=60; overlay_maxMs=17; graph_trend=0; shot_fps_tint=ok graph_ink=0.1806
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261107T131057Z\sly1\04_observe_end.png` — canvas_lum=14.64; overlay_fps=39; overlay_maxMs=77; graph_trend=0.002; shot_fps_tint=warn_bad graph_ink=0.2992
