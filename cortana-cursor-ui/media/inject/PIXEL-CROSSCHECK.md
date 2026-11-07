# PIXEL CROSS-CHECK — reference-command-center-2.png vs inject

Photo canvas: **1024×573**
Method: absolute pixel counts on photo crops + inject CSS token readback.
Allowed content diffs: live Cursor data, Manhattan location, animations.

## Layout (photo px → inject)

| Measure | Photo px | Inject | Status |
|---|---:|---|---|
| Rail width (divider x) | 157 | 157px | MATCH |
| Header height | 46 | 46px | MATCH |
| Footer band height | 48 (y525–573) | flex footer | INFO |
| Main grid gutter | 10–12 | 10px | MATCH |
| Clock font-size | ~18 | 18px | MATCH |
| Panel radius | ~6 | 6px | MATCH |
| Brand skew | ~-22° | -22deg | MATCH |
| Status skew | ~-14° | -14deg | MATCH |

## Panel absolute boxes (photo @1024×573)

| Panel | x | y | w | h | Inject notes |
|---|---:|---:|---:|---:|---|
| rail | 0 | 0 | 157 | 525 | `--cortana-rail-w: 157px` |
| header | 157 | 0 | 867 | 46 | `--cortana-header-h: 46px` |
| overview | 165 | 52 | 210 | 230 | grid cell |
| globe | 387 | 52 | 300 | 230 | grid cell |
| feed | 664 | 52 | 340 | 230 | grid cell |
| agents | 165 | 288 | 318 | 148 | agent grid |
| system+memory row | 165 | 448 | ~640 | ~72 | monitor + constellation |
| footer | 0 | 525 | 1024 | 48 | Talk + meta |

## Stroke / line / progress weights (photo → inject)

| Element | Photo px (core) | Photo bloom/glow | Inject | Status |
|---|---:|---:|---|---|
| Panel border | **1** | ~4–6 inner wash | `--cortana-stroke-panel: 1px` | MATCH |
| Rail divider | **1** | ~4 soft cyan bloom | `--cortana-stroke-rail-div: 1px` | MATCH |
| L-bracket arm | **1** × 12 long | ~4 drop-shadow | `--cortana-stroke-bracket: 1px` / 12×1 gradients | MATCH |
| Header / separators | **1** | soft | `--cortana-stroke-divider: 1px` | MATCH |
| Gauge / progress ring | **4** | ~4–6 cyan glow | `--cortana-stroke-gauge: 4` (+ non-scaling-stroke) | MATCH |
| Agent / voice wave bars | **2** | cyan glow | `--cortana-stroke-wave-bar: 2px` | MATCH |
| Title para-foot | **4** | soft | `--cortana-hud-para-foot-h: 4px` | MATCH |
| Icon SVG stroke | hairline ~1.25 @16vb | drop-shadow 3–4 | `stroke-width="1.25"` | MATCH |
| Constellation edges | **0.5–1** | soft | SVG ~1px | MATCH |

## Palette (sampled hex from photo)

| Role | Hex |
|---|---|
| Void / deepest | `#000414` / `#020817` |
| Rail fill | `#04182c` / `#041324` |
| Panel fill | `#0e2538` range |
| Cyan accent | `#00d4ff` / `#4ad1f1` |
| Border solid | `#0a3852` / `#00344c` |
| OK / connected | `#3dd68c` |
| Warn amber | `#ffab00` |
| Text bright | `#e8f7ff` |
| Text dim | `#7a8fa3` |

## Icons (no AI mush)

| Set | Style | Status |
|---|---|---|
| Nav | photo shapes: 2×2 grid, dual-lobe core, robot+antenna, folded doc, wrench, chain, atom | hairline SVG |
| Overview | circuit / db / mic / robot / node-tri / shield | hairline SVG (PNG wells removed) |
| Agents | code / search / db / globe / check / shield in toned wells | hairline SVG |
| Feed severity | calendar / warn triangle / bulb / chip (not unicode) | hairline SVG |
| LLM logos | geometric brand marks (not letter wells) | hairline SVG |
| Footer meta | pin / sun / wifi | hairline SVG |
| Quick Command | + / calendar / mic / arrows | hairline SVG |
| Header | search / expand corners / apps / bell / gear / avatar | hairline SVG |

## Animations inferred from static frame (kept)

- LIVE badge / live glyph pulse
- Mic ripple rings
- Talk + voice waveform bars
- Agent active waveforms
- Panel L-bracket breathe
- Neuron / constellation node pulse
- Gauge glow cadence

## Remaining blockers before package

- Physical folder rename `jarvis-cursor-ui` → `cortana-cursor-ui` (junction interim; Cursor file lock)
- Re-Enable inject and visual confirm gauges/icons at live Cursor size
- Zero MISMATCH after live confirm

**No package until clean.**
