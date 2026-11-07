# Logs relocation report

Simple map of where logs lived, where they live now, and what still writes outside the tree.

Dedicated root: `c:\PS2Recomp\logs`  
Override: set env `PS2_LOGS` (absolute or repo-relative).  
Helper: `scripts/log_paths.py`

## Before → after

| Before | After |
| --- | --- |
| `games/<gid>/*.log` (build, explore, smoke, repair, …) | `logs/games/<gid>/` |
| `games/<gid>/trace_*.txt` | `logs/games/<gid>/` |
| `games/<gid>/shots/` (explore frames) | `logs/games/<gid>/shots/` (new runs) |
| `tools/*.log` (setup + GoW/min60 run logs) | `logs/tools/` |
| `logs/*.ram` (flat) | `logs/ram/` |
| `logs/*-frames*`, `logs/sly-*`, `logs/shot_preview` | `logs/frames/<name>/` |
| `logs/*.log` / `*.out` (run transcripts) | stayed at `logs/` (already under root) |

Game assets (`disc.iso`, `boot.elf`, `entries.txt`, `misses.txt`, `health.json`, VU bins, etc.) were **not** moved.

## What moved (this run)

- **56** per-game log/trace files → `logs/games/<gid>/` (15 game folders). Zero `*.log` / `trace_*.txt` left under `games/`.
- **33** tools run logs → `logs/tools/` (includes `setup.log`). Zero `*.log` left under `tools/`.
- **59** RAM dumps → `logs/ram/` (moved, not copied).
- **72** frame dump directories → `logs/frames/`.

### Stuck / partial

- `logs/sly-live-vu-exact/run.log` was open by another process. Most of that run’s frames are in `logs/frames/sly-live-vu-exact/`. Source stub still has the locked `run.log` plus `MOVED.txt`. Re-run a move after that process exits.

## Writers updated (new runs)

| Writer | Change |
| --- | --- |
| `scripts/log_paths.py` | New path constants + `PS2_LOGS` |
| `scripts/panel.py` | `build.log` write + log API read via helper (legacy fallback) |
| `scripts/windows_port.py` | `explore.log` + explore `--frames-dir` under `logs/games/<gid>/` |
| `scripts/install_health.py` | Reads smoke/explore from `logs/games/<gid>/`, falls back to `games/<gid>/` |
| `scripts/port.sh` | Same explore log/shots layout; respects `PS2_LOGS` |
| `PS2WebRecomp/scripts/port.sh` | Same |
| `scripts/setup_progress.py` | Setup transcript → `logs/tools/setup.log` |
| `scripts/windows_setup.py` | Message points at new setup log path |

Preferred helpers for ad-hoc runs:

- frames: `logs/frames/<name>/` (`log_paths.frames_dir`)
- RAM: `logs/ram/<name>.ram` (`log_paths.ram_path`)
- Example: `--frames-dir logs/frames/cnk-NAME` and `$env:PS2_DUMP='logs/ram/cnk-NAME.ram'`

## What still writes elsewhere (on purpose or leftover)

| Location | Why |
| --- | --- |
| `games/<gid>/explore_ram.bin` | Build-pipeline RAM used by overlay capture; not a archived dump |
| `games/<gid>/shots/` | Old explore shots if any remain; new explores use `logs/games/<gid>/shots/` |
| `build/**/ninja.log` | Local build tool log next to ninja output |
| stderr traces (`--trace-*`) | Console only unless redirected by the caller |
| One-off scripts under `logs/_*.py` | Still hardcode old flat paths like `logs/cnk-….ram` → now under `logs/ram/` |
| Historical notes / JSON under `verification/` | Still cite old flat `logs/cnk-….log` paths (files themselves stayed at `logs/*.log`) |
| `logs/sly-live-vu-exact/` stub | Locked `run.log` until the holder exits |

`cdvdfsv` was not edited.

## Follow-ups

1. After the holder releases it, finish moving `logs/sly-live-vu-exact/`.
2. Optionally retarget one-off `logs/_*.py` RAM paths to `logs/ram/…`.
3. Optionally refresh old command snippets in big recovery notes to use `logs/frames/` and `logs/ram/`.
4. **Open — user cut off:** the user started to say they were fixing something else and got cut off. Leave this open until they say what it was.
