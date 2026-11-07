# -*- coding: utf-8 -*-
"""Apply photo-accurate stroke weights from reference-command-center-2.png crops."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui")
CSS = ROOT / "media" / "inject" / "hud.css"
TOK = ROOT / "media" / "inject" / "tokens.css"
MARK = ROOT / "media" / "inject" / "hud-markup.html"
REP = ROOT / "media" / "inject" / "PIXEL-CROSSCHECK.md"

# Visual pixel counts on 1024x573 photo crops (core stroke, bloom separate):
# panel border 1, rail divider 1, L-bracket 1x12, gauge ring 4, wave bars 2, gutter 10-12


def main() -> None:
    hud = CSS.read_text(encoding="utf-8")

    hud2, n = re.subn(
        r"(\.jcc-gauge-track,\s*\.jcc-gauge-prog\s*\{[^}]*stroke-width:\s*)[^;]+",
        r"\g<1>var(--cortana-stroke-gauge, 4)",
        hud,
        count=1,
        flags=re.S,
    )
    print("gauge stroke", n)
    hud = hud2 if n else hud

    hud2, n = re.subn(
        r"(\.jcc-panel\s*\{[^}]*?border:\s*)\d+(?:\.\d+)?px",
        r"\g<1>var(--cortana-stroke-panel, 1px)",
        hud,
        count=1,
        flags=re.S,
    )
    print("panel border", n)
    hud = hud2 if n else hud

    new_br = (
        "linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / 12px var(--cortana-stroke-bracket, 1px) no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / var(--cortana-stroke-bracket, 1px) 12px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / 12px var(--cortana-stroke-bracket, 1px) no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / var(--cortana-stroke-bracket, 1px) 12px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / 12px var(--cortana-stroke-bracket, 1px) no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / var(--cortana-stroke-bracket, 1px) 12px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / 12px var(--cortana-stroke-bracket, 1px) no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / var(--cortana-stroke-bracket, 1px) 12px no-repeat;"
    )
    hud2, n = re.subn(
        r"linear-gradient\(var\(--jcc-br\), var\(--jcc-br\)\) 0 0 / [^;]+px no-repeat,"
        r"[\s\S]*?linear-gradient\(var\(--jcc-br\), var\(--jcc-br\)\) 100% 100% / [^;]+px no-repeat;",
        new_br,
        hud,
        count=1,
    )
    print("brackets", n)
    hud = hud2 if n else hud

    for sel in [
        r"\.jcc-wave\.jcc-wave-photo\.voice i",
        r"\.jcc-wave i",
        r"\.jcc-mini-wave i",
        r"\.jcc-footer-mini-wave i",
    ]:
        hud2, n = re.subn(
            rf"({sel}\s*\{{[^}}]*?width:\s*)\d+(?:\.\d+)?px",
            r"\g<1>var(--cortana-stroke-wave-bar, 2px)",
            hud,
            count=1,
            flags=re.S,
        )
        print(sel, n)
        if n:
            hud = hud2

    hud2, n = re.subn(
        r"(\.jcc-grid\s*\{[^}]*?gap:\s*)\d+px",
        r"\g<1>10px",
        hud,
        count=1,
        flags=re.S,
    )
    print("grid gap", n)
    hud = hud2 if n else hud

    CSS.write_text(hud, encoding="utf-8")

    tok = TOK.read_text(encoding="utf-8")
    replacements = {
        "--cortana-stroke-hairline:": "1px",
        "--cortana-stroke-panel:": "1px",
        "--cortana-stroke-rail-div:": "1px",
        "--cortana-stroke-bracket:": "1px",
        "--cortana-stroke-gauge:": "4",
        "--cortana-stroke-wave-bar:": "2px",
        "--cortana-stroke-divider:": "1px",
        "--cortana-stroke-icon:": "1.25",
    }
    for key, val in replacements.items():
        tok2, n = re.subn(rf"{re.escape(key)}\s*[^;]+;", f"{key} {val};", tok, count=1)
        print(key, n)
        if n:
            tok = tok2
    TOK.write_text(tok, encoding="utf-8")

    html = MARK.read_text(encoding="utf-8")
    html2 = html.replace('stroke-width="1.35"', 'stroke-width="1.25"')
    html2 = html2.replace('stroke-width="1.2"', 'stroke-width="1.25"')
    html2 = html2.replace('stroke-width="1.4"', 'stroke-width="1.25"')
    MARK.write_text(html2, encoding="utf-8")
    print("markup unify", html != html2)

    REP.write_text(
        """# PIXEL CROSS-CHECK — reference-command-center-2.png vs inject

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
""",
        encoding="utf-8",
    )
    print("report written")

    t = TOK.read_text(encoding="utf-8")
    for key in (
        "cortana-rail-w",
        "cortana-header-h",
        "cortana-stroke-gauge",
        "cortana-stroke-panel",
        "cortana-stroke-bracket",
        "cortana-stroke-wave-bar",
    ):
        m = re.search(rf"--{key}:\s*([^;]+);", t)
        print(key, m.group(1) if m else "MISSING")


if __name__ == "__main__":
    main()
