# W-CHROME60 — Chrome FPS measurement (research only)

**Worker:** W-CHROME60  
**Date:** 2026-11-07  
**Mandate:** Measurement + registry hooks only — **no** V-Sync / uncap / `ps2web_set_fps_limit` product changes.

## `host/web.cpp` `pace()` (research)

- **File:** `c:\PS2Recomp\host\web.cpp` lines 326–362.
- `g_vsync` default **true**; with V-Sync on, `period` is clamped to ≥ ~60 Hz NTSC (`1000/60`) or PAL 20 ms — uncapped EE is explicitly avoided (“hitch trains”).
- `g_frame_period_ms` default `1000/60`; `ps2web_set_fps_limit()` (lines 470+) caps at 60 when V-Sync is on (`fps > 60.5` → 60/50).
- **Deferred for apply:** any change to raise FPS ceiling or turn off V-Sync pacing.

## Harness (`tools/_cyberarcade_live_harness.py`)

- **Present** (29k+ lines Playwright); outputs `summary.json`, `fps-overlay.jsonl`, `console.jsonl`.
- FPS: DOM `#fps-overlay-*`, `#stats` regex `([\d.]+) fps ((\d+) on screen)`, 0.5s observe ticks.
- **canvas_lum:** PIL sample on `#canvas` crops (`CANVAS_BLACK_LUM = 8.0`).
- **New:** `write_metrics()` → `logs/harness-runs/<run>/metrics.json` + alias `logs/cyberarcade-harness-metrics-latest.json`.

### `metrics.json` schema (`ps2recomp.harness.metrics/v1`)

Per game: `game_id`, `canvas_lum_by_tag`, `canvas_lum_end`, `canvas_black_end`, `fps` (stats avg/min/max), `fps_overlay`, `bootmenu` (`BOOTMENU.(ZIP|WHD|WAV);1 -> found` from `console.jsonl`), `max_prims`, `booted`.

### Verified run `20261107T140555Z` (Hitman_BM)

| Signal | Value |
|--------|--------|
| Harness FPS avg / min / max | 58.91 / 23.5 / 64.8 |
| Overlay FPS avg | 56.16 |
| `canvas_lum_end` | 0.138 (black) |
| BOOTMENU ZIP+WHD+WAV | found (5 console hits) |
| max_prims | 864983 |

Paths:

- `c:\PS2Recomp\logs\harness-runs\20261107T140555Z\metrics.json`
- `c:\PS2Recomp\logs\cyberarcade-harness-metrics-latest.json`

## `scripts/autonomous_verify.py`

- **`parse_fps_from_log`:** `[stats] frame N X fps` (Chrome statslog if ever in log); native `[ee] stopped after N frames, C cycles` → `native_vblank_frames`, `ee_cycles_per_vblank` (~4.94M for Hitman 200f smoke).
- **`harness_chrome_metrics(game_id)`:** merges latest `metrics.json` or summary alias into verify result as `chrome_metrics`.
- Verify output fields: `fps_metrics`, `chrome_metrics` on each game result + top-level summary JSON unchanged shape (`results` array).

Native-only smoke test (`a2116d2ac08a7be4db4e8455ad58d2e5-200f` log): `source=native_stopped`, 200 vblank frames — **no wall FPS** in native logs (by design).

## Master plan §5

- Checked **Parse FPS / frame timing in autonomous_verify** and **Harness metrics.json** (2026-11-07).
- Left unchecked: 30 FPS allowlist, library sweep, optimization pass, V-Sync apply.

## Next (not W-CHROME60 apply)

1. Re-run harness after Hitman web rebuild; require `canvas_lum_end ≥ 8` while FPS stays ≥55 sustained.
2. Wire `chrome_metrics.fps_overlay.avg` into `game-fix-registry.json` when registry field is agreed (allowlist lane).
3. God unlock only before any `pace()` / `ps2web_set_fps_limit` tuning beyond locked 60.
