# Harness shot manifest — 20261108T001703Z

Agents: **Read** each PNG path below as an image to verify black screens, abort UI, menus, GPU draw,
and the **live FPS overlay + graph** (top-left). FPS numbers/trends also in `fps-overlay.jsonl`.
Logs: console/pageerror/dom/fps-overlay jsonl under the harness-runs folder.

- Run dir: `C:\PS2Recomp\logs\harness-runs\20261108T001703Z`
- Shots root: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z`
- Console: `C:\PS2Recomp\logs\harness-runs\20261108T001703Z\console.jsonl`
- Page errors: `C:\PS2Recomp\logs\harness-runs\20261108T001703Z\pageerror.jsonl`
- DOM status: `C:\PS2Recomp\logs\harness-runs\20261108T001703Z\dom-status.jsonl`
- FPS overlay: `C:\PS2Recomp\logs\harness-runs\20261108T001703Z\fps-overlay.jsonl`

## NFS (`NFS_MW`)
- ok=False goal=expect=gpu_boot booted=True max_prims=57277 end_lum=9.514845451529272 software=False abort=True
- fps_overlay: `{'samples': 11, 'avg': 39.09090909090909, 'min': 13.0, 'max': 61.0, 'maxMs_peak': 602.0, 'graph_trend_avg': -0.08008333333333333, 'graph_trend_last': -0.053}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\00_goto.png` — canvas_lum=6.25; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\00b_loading.png` — canvas_lum=19.30; overlay_fps=13; overlay_maxMs=602; graph_trend=-0.602; shot_fps_tint=warn_bad graph_ink=0.1268; boot=Starting game…
  - **01_boot** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\01_boot.png` — canvas_lum=20.44; overlay_fps=13; overlay_maxMs=602; graph_trend=-0.602; shot_fps_tint=warn_bad graph_ink=0.2666; boot=Starting game…
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\02_observe_start.png` — canvas_lum=20.47; overlay_fps=25; overlay_maxMs=113; graph_trend=0.173; shot_fps_tint=warn_bad graph_ink=0.3021
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\03_observe_mid.png` — canvas_lum=0.14; overlay_fps=61; overlay_maxMs=84; graph_trend=0.008; shot_fps_tint=warn_bad graph_ink=0.2186
  - **issue_halt_18** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\issue_halt_18.png` — canvas_lum=8.38; overlay_fps=59; overlay_maxMs=60; graph_trend=-0.053; shot_fps_tint=warn_bad graph_ink=0.1916; boot=Game stopped — crash log saved; help=missing code at 0x01A5C000
  - **04_observe_end** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfs_mw\04_observe_end.png` — canvas_lum=8.38; overlay_fps=59; overlay_maxMs=60; graph_trend=-0.053; shot_fps_tint=warn_bad graph_ink=0.1916; boot=Game stopped — crash log saved; help=missing code at 0x01A5C000

## Sly (`Sly1`)
- ok=True goal=expect=draw booted=True max_prims=314210 end_lum=12.806539259628492 software=False abort=False
- fps_overlay: `{'samples': 18, 'avg': 55.94444444444444, 'min': 1.0, 'max': 60.0, 'maxMs_peak': 1892.0, 'graph_trend_avg': -0.012210526315789475, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1\00_goto.png` — canvas_lum=6.32; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1\01_boot.png` — canvas_lum=0.11; overlay_fps=1; overlay_maxMs=1892; graph_trend=-0.318; shot_fps_tint=warn_bad graph_ink=0.0969
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1\02_observe_start.png` — canvas_lum=11.90; overlay_fps=53; overlay_maxMs=107; graph_trend=0.053; shot_fps_tint=warn_bad graph_ink=0.2249
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1\03_observe_mid.png` — canvas_lum=14.71; overlay_fps=60; overlay_maxMs=20; graph_trend=-0.008; shot_fps_tint=ok graph_ink=0.1826
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\sly1\04_observe_end.png` — canvas_lum=14.74; overlay_fps=60; overlay_maxMs=18; graph_trend=0.002; shot_fps_tint=ok graph_ink=0.1815

## GoW2 (`GoW2`)
- ok=True goal=expect=draw booted=True max_prims=5443056 end_lum=30.973276311419905 software=False abort=False
- fps_overlay: `{'samples': 17, 'avg': 51.0, 'min': 0.0, 'max': 68.0, 'maxMs_peak': 269.0, 'graph_trend_avg': 0.00027777777777777957, 'graph_trend_last': -0.069}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2\00_goto.png` — canvas_lum=6.14; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2\01_boot.png` — canvas_lum=6.19; overlay_fps=0; overlay_maxMs=0; graph_trend=-0.28; shot_fps_tint=warn_bad graph_ink=0.1169; boot=Starting game…
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2\02_observe_start.png` — canvas_lum=7.12; overlay_fps=45; overlay_maxMs=269; graph_trend=0.004; shot_fps_tint=warn_bad graph_ink=0.1938
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2\03_observe_mid.png` — canvas_lum=40.51; overlay_fps=68; overlay_maxMs=96; graph_trend=0.008; shot_fps_tint=warn_bad graph_ink=0.3241
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gow2\04_observe_end.png` — canvas_lum=40.27; overlay_fps=59; overlay_maxMs=35; graph_trend=-0.069; shot_fps_tint=warn_bad graph_ink=0.3078

## Ratchet2 (`Ratchet2`)
- ok=False goal=expect=draw booted=True max_prims=6386 end_lum=3.2054171646745577 software=False abort=False
- fps_overlay: `{'samples': 18, 'avg': 32.388888888888886, 'min': 1.0, 'max': 45.0, 'maxMs_peak': 19731.0, 'graph_trend_avg': 0.024684210526315777, 'graph_trend_last': 0.114}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2\00_goto.png` — canvas_lum=6.25; graph_trend=0; boot=Preparing game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2\01_boot.png` — canvas_lum=0.31; overlay_fps=35; overlay_maxMs=136; graph_trend=-0.702; shot_fps_tint=warn_bad graph_ink=0.1626; boot=Starting game…
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2\02_observe_start.png` — canvas_lum=1.00; overlay_fps=35; overlay_maxMs=136; graph_trend=-0.191; shot_fps_tint=warn_bad graph_ink=0.2457
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2\03_observe_mid.png` — canvas_lum=0.15; overlay_fps=38; overlay_maxMs=50; graph_trend=0.107; shot_fps_tint=warn_bad graph_ink=0.277
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\ratchet2\04_observe_end.png` — canvas_lum=0.15; overlay_fps=5; overlay_maxMs=1890; graph_trend=0.114; shot_fps_tint=warn_bad graph_ink=0.3168

## DefJam (`DefJam`)
- ok=False goal=expect=draw booted=True max_prims=15133 end_lum=9.580715803454922 software=False abort=True
- fps_overlay: `{'samples': 14, 'avg': 45.714285714285715, 'min': 0.0, 'max': 62.0, 'maxMs_peak': 253.0, 'graph_trend_avg': -0.022266666666666664, 'graph_trend_last': -0.118}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\00_goto.png` — canvas_lum=6.25; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\00b_loading.png` — canvas_lum=6.22; overlay_fps=0; overlay_maxMs=0; graph_trend=0; shot_fps_tint=warn_bad graph_ink=0.039; boot=Starting game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\01_boot.png` — canvas_lum=2.10; overlay_fps=36; overlay_maxMs=253; graph_trend=0.006; shot_fps_tint=warn_bad graph_ink=0.2177
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\02_observe_start.png` — canvas_lum=1.32; overlay_fps=59; overlay_maxMs=82; graph_trend=-0.061; shot_fps_tint=warn_bad graph_ink=0.1891
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\03_observe_mid.png` — canvas_lum=2.05; overlay_fps=60; overlay_maxMs=20; graph_trend=-0.004; shot_fps_tint=ok graph_ink=0.1827
  - **issue_halt_29** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\issue_halt_29.png` — canvas_lum=8.35; overlay_fps=40; overlay_maxMs=96; graph_trend=-0.118; shot_fps_tint=warn_bad graph_ink=0.2559; boot=Game stopped — crash log saved; help=missing code at 0x002A9E20
  - **04_observe_end** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\defjam\04_observe_end.png` — canvas_lum=8.35; overlay_fps=40; overlay_maxMs=96; graph_trend=-0.118; shot_fps_tint=warn_bad graph_ink=0.2559; boot=Game stopped — crash log saved; help=missing code at 0x002A9E20

## GT4 (`GT4`)
- ok=True goal=expect=draw booted=True max_prims=591176 end_lum=100.22695310424581 software=False abort=False
- fps_overlay: `{'samples': 17, 'avg': 53.23529411764706, 'min': 29.0, 'max': 61.0, 'maxMs_peak': 137.0, 'graph_trend_avg': -0.007947368421052632, 'graph_trend_last': 0.0}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\00_goto.png` — canvas_lum=6.26; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\00b_loading.png` — canvas_lum=6.21; graph_trend=0; shot_fps_tint=warn_bad graph_ink=0.0341; boot=Starting game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\01_boot.png` — canvas_lum=2.65; overlay_fps=51; overlay_maxMs=73; graph_trend=0.087; shot_fps_tint=warn_bad graph_ink=0.2056
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\02_observe_start.png` — canvas_lum=3.95; overlay_fps=29; overlay_maxMs=137; graph_trend=0.087; shot_fps_tint=warn_bad graph_ink=0.2583
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\03_observe_mid.png` — canvas_lum=145.32; overlay_fps=59; overlay_maxMs=63; graph_trend=-0.063; shot_fps_tint=warn_bad graph_ink=0.3038
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\gt4\04_observe_end.png` — canvas_lum=145.21; overlay_fps=60; overlay_maxMs=17; graph_trend=0; shot_fps_tint=ok graph_ink=0.295

## NFSU2 (`NFSU2`)
- ok=True goal=expect=draw booted=True max_prims=45293 end_lum=10.311139608234116 software=False abort=False
- fps_overlay: `{'samples': 17, 'avg': 16.0, 'min': 2.0, 'max': 62.0, 'maxMs_peak': 1599.0, 'graph_trend_avg': 0.082, 'graph_trend_last': 0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\00_goto.png` — canvas_lum=6.28; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\00b_loading.png` — canvas_lum=6.20; graph_trend=0; shot_fps_tint=warn_bad graph_ink=0.0449; boot=Starting game…
  - **01_boot** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\01_boot.png` — canvas_lum=14.56; overlay_fps=23; overlay_maxMs=88; graph_trend=0.089; shot_fps_tint=warn_bad graph_ink=0.3475
  - **02_observe_start** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\02_observe_start.png` — canvas_lum=14.69; overlay_fps=33; overlay_maxMs=105; graph_trend=-0.103; shot_fps_tint=warn_bad graph_ink=0.3049
  - **03_observe_mid** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\03_observe_mid.png` — canvas_lum=79.89; overlay_fps=4; overlay_maxMs=1599; graph_trend=-0.004; shot_fps_tint=warn_bad graph_ink=0.269
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\nfsu2\04_observe_end.png` — canvas_lum=10.89; overlay_fps=4; overlay_maxMs=935; graph_trend=0.002; shot_fps_tint=warn_bad graph_ink=0.4045

## Hitman2 (`Hitman2`)
- ok=False goal=expect=draw booted=False max_prims=0 end_lum=9.265529631476115 software=False abort=True
- fps_overlay: `{'samples': 0, 'avg': None, 'min': None, 'max': None, 'maxMs_peak': None, 'graph_trend_avg': 0.0, 'graph_trend_last': 0.0}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2\00_goto.png` — canvas_lum=6.25; graph_trend=0; boot=Preparing game…
  - **00_halt** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2\00_halt.png` — canvas_lum=8.34; graph_trend=0; boot=Game stopped — crash log saved; help=program asked to run another executable A crash log was saved automatically. The runtime cannot safely res
  - **01_boot** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2\01_boot.png` — canvas_lum=8.34; graph_trend=0; boot=Game stopped — crash log saved; help=program asked to run another executable A crash log was saved automatically. The runtime cannot safely res
  - **issue_halt_0** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2\issue_halt_0.png` — canvas_lum=8.34; graph_trend=0; boot=Game stopped — crash log saved; help=program asked to run another executable A crash log was saved automatically. The runtime cannot safely res
  - **04_observe_end** verdict=`abort_ui` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hitman2\04_observe_end.png` — canvas_lum=8.34; graph_trend=0; boot=Game stopped — crash log saved; help=program asked to run another executable A crash log was saved automatically. The runtime cannot safely res

## HSG3 (`HSG3`)
- ok=True goal=expect=draw booted=True max_prims=66306283 end_lum=18.52911487383811 software=False abort=False
- fps_overlay: `{'samples': 18, 'avg': 27.72222222222222, 'min': 0.0, 'max': 57.0, 'maxMs_peak': 152.0, 'graph_trend_avg': 0.021473684210526315, 'graph_trend_last': -0.008}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\00_goto.png` — canvas_lum=6.25; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\00b_loading.png` — canvas_lum=0.11; overlay_fps=0; overlay_maxMs=0; graph_trend=0; shot_fps_tint=warn_bad graph_ink=0.0366; boot=Starting game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\01_boot.png` — canvas_lum=0.14; overlay_fps=57; overlay_maxMs=67; graph_trend=-0.166; shot_fps_tint=warn_bad graph_ink=0.1948
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\02_observe_start.png` — canvas_lum=0.14; overlay_fps=38; overlay_maxMs=81; graph_trend=0.154; shot_fps_tint=warn_bad graph_ink=0.2452
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\03_observe_mid.png` — canvas_lum=0.16; overlay_fps=40; overlay_maxMs=60; graph_trend=-0.063; shot_fps_tint=warn_bad graph_ink=0.2613
  - **04_observe_end** verdict=`ok` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\hsg3\04_observe_end.png` — canvas_lum=22.94; overlay_fps=21; overlay_maxMs=67; graph_trend=-0.008; shot_fps_tint=warn_bad graph_ink=0.4149

## RE4 (`RE4`)
- ok=False goal=expect=draw booted=True max_prims=128305 end_lum=4.83633183930936 software=False abort=False
- fps_overlay: `{'samples': 17, 'avg': 59.76470588235294, 'min': 57.0, 'max': 61.0, 'maxMs_peak': 71.0, 'graph_trend_avg': -0.016526315789473684, 'graph_trend_last': -0.002}`
- shots_dir: `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4`
  - **00_goto** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\00_goto.png` — canvas_lum=6.24; graph_trend=0; boot=Preparing game…
  - **00b_loading** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\00b_loading.png` — canvas_lum=0.11; graph_trend=0; shot_fps_tint=warn_bad graph_ink=0.0492; boot=Starting game…
  - **01_boot** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\01_boot.png` — canvas_lum=0.14; overlay_fps=61; overlay_maxMs=57; graph_trend=-0.109; shot_fps_tint=warn_bad graph_ink=0.2106
  - **02_observe_start** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\02_observe_start.png` — canvas_lum=0.14; overlay_fps=59; overlay_maxMs=71; graph_trend=-0.051; shot_fps_tint=warn_bad graph_ink=0.1874
  - **03_observe_mid** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\03_observe_mid.png` — canvas_lum=2.93; overlay_fps=60; overlay_maxMs=17; graph_trend=-0.002; shot_fps_tint=ok graph_ink=0.1806
  - **04_observe_end** verdict=`black_screen` → `C:\PS2Recomp\logs\screenshots\harness-20261108T001703Z\re4\04_observe_end.png` — canvas_lum=2.93; overlay_fps=60; overlay_maxMs=18; graph_trend=-0.002; shot_fps_tint=ok graph_ink=0.1817
