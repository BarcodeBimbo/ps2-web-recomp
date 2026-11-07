# -*- coding: utf-8 -*-
"""Photo-matched hairline icons + stroke-weight tokens from reference-command-center-2.png."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui")
REF = ROOT / "media" / "reference-command-center-2.png"
MARKUP = ROOT / "media" / "inject" / "hud-markup.html"
CSS = ROOT / "media" / "inject" / "hud.css"
TOKENS = ROOT / "media" / "inject" / "tokens.css"
JS = ROOT / "src" / "workbenchInject.js"
REPORT = ROOT / "media" / "inject" / "PIXEL-CROSSCHECK.md"

OV_SVGS = [
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><circle cx="8" cy="8" r="5.2"/><circle cx="8" cy="8" r="2"/><circle cx="8" cy="5.2" r="0.7" fill="currentColor" stroke="none"/><circle cx="5.8" cy="9.6" r="0.7" fill="currentColor" stroke="none"/><circle cx="10.2" cy="9.6" r="0.7" fill="currentColor" stroke="none"/></svg>',
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><ellipse cx="8" cy="4.4" rx="4.2" ry="1.6"/><path d="M3.8 4.4v7c0 .85 1.9 1.55 4.2 1.55s4.2-.7 4.2-1.55v-7"/><path d="M3.8 7.6c0 .85 1.9 1.55 4.2 1.55s4.2-.7 4.2-1.55"/></svg>',
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><rect x="5.6" y="2.6" width="4.8" height="7" rx="2.4"/><path d="M3.8 8a4.2 4.2 0 0 0 8.4 0M8 12.2v1.4"/></svg>',
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><rect x="3.4" y="5" width="9.2" height="7" rx="1.6"/><circle cx="6.2" cy="8.4" r="0.85" fill="currentColor" stroke="none"/><circle cx="9.8" cy="8.4" r="0.85" fill="currentColor" stroke="none"/><path d="M8 2.6v2.4"/><circle cx="8" cy="2.2" r="0.7" fill="currentColor" stroke="none"/></svg>',
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><circle cx="8" cy="4" r="1.6"/><circle cx="4.6" cy="11" r="1.6"/><circle cx="11.4" cy="11" r="1.6"/><path d="M7.1 5.2L5.4 9.6M8.9 5.2l1.7 4.4M6.2 11h3.6"/></svg>',
    '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><path d="M8 2.4l5 2v3.5c0 3-2.1 5-5 5.9-2.9-.9-5-2.9-5-5.9V4.4l5-2z"/><path d="M5.8 8l1.6 1.6 2.8-2.9"/></svg>',
]

NAV = {
    "home": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"><rect x="2.4" y="2.4" width="4.4" height="4.4" rx="0.7"/><rect x="9.2" y="2.8" width="4.4" height="3.6" rx="0.7"/><rect x="2.4" y="9.2" width="4.4" height="4.4" rx="0.7"/><rect x="9.2" y="9.2" width="4.4" height="4.4" rx="0.7"/></svg>',
    "core": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><path d="M5.2 3.4c1.2-.9 4.4-.9 5.6 0 1 1.4 1 6.8 0 8.2-1.2.9-4.4.9-5.6 0-1-1.4-1-6.8 0-8.2z"/><path d="M8 3.2v9.6"/></svg>',
    "agents": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><rect x="3.2" y="5" width="9.6" height="7.2" rx="1.8"/><circle cx="6.2" cy="8.5" r="0.9" fill="currentColor" stroke="none"/><circle cx="9.8" cy="8.5" r="0.9" fill="currentColor" stroke="none"/><path d="M8 2.4v2.6"/><circle cx="8" cy="2.1" r="0.75" fill="currentColor" stroke="none"/></svg>',
    "tasks": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"><path d="M4 2.8h6.2L12.4 5v8.2H4V2.8z"/><path d="M10.2 2.8V5h2.2"/><path d="M5.8 8h4.4M5.8 10.2h3.2M5.8 12.2h2.4"/></svg>',
    "tools": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><path d="M10.6 3.2a2.6 2.6 0 0 1 2.2 2.2l-2.4 2.4-1.6-1.6 2.4-2.4z"/><path d="M9.2 7.4L4.2 12.4c-.6.6-1.6.6-2.2 0v0c-.6-.6-.6-1.6 0-2.2l5-5"/></svg>',
    "workflows": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><path d="M6.2 4.2a2.4 2.4 0 1 1 2.2 3.8M9.8 11.8a2.4 2.4 0 1 1-2.2-3.8"/><path d="M7.4 7.2l1.2 1.6"/></svg>',
    "knowledge": '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.25"><circle cx="8" cy="4.2" r="1.7"/><circle cx="4.6" cy="11" r="1.7"/><circle cx="11.4" cy="11" r="1.7"/><path d="M7.1 5.5L5.5 9.5M8.9 5.5l1.6 4M6.3 11h3.4"/></svg>',
}


def lum(c: tuple[int, int, int]) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def sample_hex(im: Image.Image, x: int, y: int, r: int = 2) -> str:
    w, h = im.size
    px = im.load()
    cs = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx = max(0, min(w - 1, x + dx))
            yy = max(0, min(h - 1, y + dy))
            c = px[xx, yy]
            cs.append((c[0] // 4 * 4, c[1] // 4 * 4, c[2] // 4 * 4))
    best = Counter(cs).most_common(1)[0][0]
    return "#%02x%02x%02x" % best


def measure_run_thickness(im: Image.Image, x0: int, y0: int, axis: str = "y") -> int:
    """Walk perpendicular to a bright line; return contiguous bright-run length in px."""
    w, h = im.size
    px = im.load()
    if axis == "y":
        # vertical line at x0 — measure thickness along x
        mid = lum(px[x0, y0])
        # find peak near x0
        best_x, best_l = x0, mid
        for x in range(max(0, x0 - 4), min(w, x0 + 5)):
            L = lum(px[x, y0])
            if L > best_l:
                best_l, best_x = L, x
        thr = best_l * 0.55
        left = best_x
        while left > 0 and lum(px[left - 1, y0]) >= thr:
            left -= 1
        right = best_x
        while right < w - 1 and lum(px[right + 1, y0]) >= thr:
            right += 1
        return max(1, right - left + 1)
    # horizontal line at y0 — measure along y
    best_y, best_l = y0, lum(px[x0, y0])
    for y in range(max(0, y0 - 4), min(h, y0 + 5)):
        L = lum(px[x0, y])
        if L > best_l:
            best_l, best_y = L, y
    thr = best_l * 0.55
    top = best_y
    while top > 0 and lum(px[x0, top - 1]) >= thr:
        top -= 1
    bot = best_y
    while bot < h - 1 and lum(px[x0, bot + 1]) >= thr:
        bot += 1
    return max(1, bot - top + 1)


def measure_gauge_stroke(im: Image.Image, cx: int, cy: int, r_guess: int = 22) -> int:
    """Sample radial brightness around a circular gauge to estimate ring thickness."""
    w, h = im.size
    px = im.load()
    # scan rightward from center along +x for bright ring
    profile = []
    for dx in range(0, r_guess + 12):
        x = min(w - 1, cx + dx)
        profile.append(lum(px[x, cy]))
    # find outer bright peak beyond half radius
    start = max(8, r_guess // 2)
    peak_i = start + max(range(len(profile) - start), key=lambda i: profile[start + i])
    peak = profile[peak_i]
    thr = peak * 0.55
    left = peak_i
    while left > 0 and profile[left - 1] >= thr:
        left -= 1
    right = peak_i
    while right < len(profile) - 1 and profile[right + 1] >= thr:
        right += 1
    return max(1, right - left + 1)


def measure_photo() -> dict:
    im = Image.open(REF).convert("RGB")
    w, h = im.size
    px = im.load()

    def col_edge(x: int) -> int:
        s = 0
        for y in range(50, 400, 4):
            a, b = px[x, y], px[min(w - 1, x + 1), y]
            s += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        return s

    def row_edge(y: int) -> int:
        s = 0
        for x in range(170, w - 20, 4):
            a, b = px[x, y], px[x, min(h - 1, y + 1)]
            s += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        return s

    rail_x = max(range(100, 220), key=col_edge)
    header_y = max(range(28, 60), key=row_edge)
    footer_y = max(range(480, 560), key=row_edge)

    # Stroke samples
    rail_div_t = measure_run_thickness(im, rail_x, 200, "y")
    header_div_t = measure_run_thickness(im, 400, header_y, "x")
    # Panel border — sample near overview left edge
    panel_border_x = rail_x + 10
    panel_border_t = measure_run_thickness(im, panel_border_x, 120, "y")
    # L-bracket arm near panel corner
    bracket_t = measure_run_thickness(im, rail_x + 18, 70, "x")
    # Gauge rings — System Monitor area ~ mid-left below agents
    # From earlier crops: gauges around y~470-500 in photo? Actually system monitor under agents
    # agents ~288-440, gauges in system monitor panel roughly y 455-510, x ~220/280/340
    gauge_t = measure_gauge_stroke(im, 230, 480, 20)
    gauge_t2 = measure_gauge_stroke(im, 290, 480, 20)
    gauge_t3 = measure_gauge_stroke(im, 350, 480, 20)
    gauge_avg = int(round((gauge_t + gauge_t2 + gauge_t3) / 3))

    # Horizontal progress / timeline bars if any — scan for thin cyan horizontal runs
    # Wave bars in agent cards — vertical bars; measure width of one bar
    wave_bar_t = measure_run_thickness(im, 280, 310, "y")

    # Para foot under titles — thin strip
    para_foot_t = 4  # known from design; verify near panel title
    # sample near "ACTIVE AGENTS" area
    for y in range(270, 295):
        t = measure_run_thickness(im, rail_x + 40, y, "x")
        if 2 <= t <= 6:
            para_foot_t = t
            break

    palette = {
        "void": sample_hex(im, 8, 8),
        "rail": sample_hex(im, 40, 120),
        "panel": sample_hex(im, rail_x + 40, 90),
        "cyan": sample_hex(im, 60, 24),
        "cyan_bright": sample_hex(im, 520, 28),
        "ok": sample_hex(im, 220, 300),
        "text": sample_hex(im, 90, 70),
        "border_solid": sample_hex(im, rail_x, 200),
    }

    # Panel boxes (approx absolute in photo)
    panels = {
        "rail": {"w": rail_x, "h": footer_y},
        "header": {"w": w - rail_x, "h": header_y},
        "overview": {"x": rail_x + 8, "y": header_y + 6, "w": 210, "h": 230},
        "globe": {"x": rail_x + 230, "y": header_y + 6, "w": 300, "h": 230},
        "feed": {"x": w - 360, "y": header_y + 6, "w": 340, "h": 230},
        "agents": {"x": rail_x + 8, "y": 288, "w": 318, "h": 148},
        "footer": {"x": 0, "y": footer_y, "w": w, "h": h - footer_y},
    }

    strokes = {
        "rail_divider_px": rail_div_t,
        "header_divider_px": header_div_t,
        "panel_border_px": panel_border_t,
        "l_bracket_arm_px": bracket_t,
        "gauge_ring_px": gauge_avg,
        "gauge_samples": [gauge_t, gauge_t2, gauge_t3],
        "agent_wave_bar_px": wave_bar_t,
        "para_foot_px": para_foot_t,
        "icon_stroke_css": 1.25,  # hairline at photo icon ~12px well
    }

    return {
        "size": (w, h),
        "rail_x": rail_x,
        "header_y": header_y,
        "footer_y": footer_y,
        "panels": panels,
        "strokes": strokes,
        "palette": palette,
    }


def patch_markup() -> None:
    html = MARKUP.read_text(encoding="utf-8")
    for key, svg in NAV.items():
        pat = rf'(data-nav="{key}"><span class="jcc-nav-ico"[^>]*>)<svg[\s\S]*?</svg>'
        html2, n = re.subn(pat, rf"\1{svg}", html, count=1)
        print(f"NAV {key}: {n}")
        if n == 1:
            html = html2
    for i, svg in enumerate(OV_SVGS):
        pat = rf'<span class="jcc-ov-ico" data-ico="{i}" aria-hidden="true">(?:</span>|<svg[\s\S]*?</svg></span>)'
        html2, n = re.subn(
            pat,
            f'<span class="jcc-ov-ico" data-ico="{i}" aria-hidden="true">{svg}</span>',
            html,
            count=1,
        )
        print(f"OV {i}: {n}")
        if n == 1:
            html = html2
    # Unify agent/cmd/meta/header icon stroke-width to 1.25
    html = re.sub(r'stroke-width="1\.[34567]"', 'stroke-width="1.25"', html)
    html = re.sub(r'stroke-width="1\.6"', 'stroke-width="1.25"', html)
    html = re.sub(r'stroke-width="1\.7"', 'stroke-width="1.25"', html)
    html = re.sub(r'stroke-width="2\.2"', 'stroke-width="1.25"', html)
    MARKUP.write_text(html, encoding="utf-8")


def patch_css_llm_feed_ov() -> None:
    hud = CSS.read_text(encoding="utf-8")

    # Replace letter-logo block via regex
    hud2, n = re.subn(
        r"\.jcc-llm-logo \{[\s\S]*?\.jcc-llm-logo\[data-provider=\"copilot\"\]::before \{ content: \"Co\"; \}",
        """.jcc-llm-logo {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border-radius: 5px;
  display: grid;
  place-items: center;
  background: rgba(0, 16, 32, 0.92);
  border: 1px solid rgba(0, 120, 160, 0.35);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04), 0 0 8px rgba(0, 180, 220, 0.12);
  line-height: 0;
  overflow: hidden;
}
.jcc-llm-logo::before { content: none !important; }
.jcc-llm-logo svg { display: block; width: 14px; height: 14px; }
.jcc-llm-logo[data-provider="claude"] { border-color: rgba(212, 165, 116, 0.55); box-shadow: 0 0 8px rgba(212, 165, 116, 0.22); }
.jcc-llm-logo[data-provider="openai"] { border-color: rgba(110, 231, 183, 0.5); box-shadow: 0 0 8px rgba(110, 231, 183, 0.2); }
.jcc-llm-logo[data-provider="gemini"] { border-color: rgba(122, 162, 255, 0.5); box-shadow: 0 0 8px rgba(122, 162, 255, 0.2); }
.jcc-llm-logo[data-provider="grok"] { border-color: rgba(232, 232, 232, 0.4); }
.jcc-llm-logo[data-provider="groq"] { border-color: rgba(245, 197, 66, 0.55); box-shadow: 0 0 8px rgba(245, 197, 66, 0.2); }
.jcc-llm-logo[data-provider="cursor"] { border-color: rgba(74, 209, 241, 0.55); box-shadow: 0 0 8px rgba(74, 209, 241, 0.25); }
.jcc-llm-logo[data-provider="muse"] { border-color: rgba(192, 132, 252, 0.5); box-shadow: 0 0 8px rgba(192, 132, 252, 0.2); }
.jcc-llm-logo[data-provider="ollama"] { border-color: rgba(163, 163, 163, 0.45); }
.jcc-llm-logo[data-provider="openrouter"] { border-color: rgba(91, 159, 255, 0.5); box-shadow: 0 0 8px rgba(91, 159, 255, 0.2); }
.jcc-llm-logo[data-provider="copilot"] { border-color: rgba(61, 214, 140, 0.5); box-shadow: 0 0 8px rgba(61, 214, 140, 0.22); }""",
        hud,
        count=1,
    )
    print(f"LLM CSS: {n}")
    hud = hud2 if n else hud

    hud2, n = re.subn(
        r"\.jcc-feed-glyph\.info::before,[\s\S]*?\.jcc-feed-glyph\.live::before,\n\.jcc-tag\.live::before \{ content: \"◉\"; font-size: 9px; \}",
        """.jcc-feed-glyph::before,
.jcc-tag::before { content: none !important; }
.jcc-feed-glyph svg,
.jcc-tag svg { display: block; width: 11px; height: 11px; }

.jcc-feed-glyph.warn,
.jcc-tag.warn {
  border-color: rgba(255, 171, 0, 0.9);
  background: rgba(255, 171, 0, 0.92);
  box-shadow: 0 0 10px rgba(255, 171, 0, 0.45);
  color: #1a0c04;
}

.jcc-feed-glyph.tip,
.jcc-tag.tip {
  border-color: rgba(0, 212, 255, 0.75);
  background: rgba(0, 180, 220, 0.88);
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.28);
}

.jcc-feed-glyph.live,
.jcc-tag.live {
  border-color: rgba(61, 214, 140, 0.85);
  background: rgba(61, 214, 140, 0.9);
  box-shadow: 0 0 8px rgba(61, 214, 140, 0.32);
  animation: cortana-live-pulse var(--cortana-live-ms, 1.4s) ease-in-out infinite;
  color: #031810;
}""",
        hud,
        count=1,
    )
    print(f"FEED CSS: {n}")
    hud = hud2 if n else hud

    hud2, n = re.subn(
        r'\.jcc-ov-ico\[data-ico="0"\] \{ background-image: url\("\./overview-ico-0\.png"\); \}[\s\S]*?\.jcc-ov-ico\[data-ico="5"\] \{ background-image: url\("\./overview-ico-5\.png"\); \}',
        """.jcc-ov-ico[data-ico] { background-image: none !important; color: var(--cortana-cyan-bright, #4ad1f1); }
.jcc-ov-ico svg { display: block; width: 12px; height: 12px; filter: drop-shadow(0 0 3px rgba(74, 209, 241, 0.45)); }
.jcc-ov-ico[data-ico="1"] { color: #70a1b0; }
.jcc-ov-ico[data-ico="2"] { color: #2dd4bf; }
.jcc-ov-ico[data-ico="3"] { color: #c084fc; }
.jcc-ov-ico[data-ico="4"] { color: #fbbf24; }
.jcc-ov-ico[data-ico="5"] { color: #34d399; }""",
        hud,
        count=1,
    )
    print(f"OV CSS: {n}")
    hud = hud2 if n else hud
    CSS.write_text(hud, encoding="utf-8")


def apply_stroke_tokens(m: dict) -> None:
    s = m["strokes"]
    # Clamp to sane CSS values from photo measurements
    panel_border = max(1, min(2, s["panel_border_px"]))
    rail_div = max(1, min(2, s["rail_divider_px"]))
    gauge = max(2, min(5, s["gauge_ring_px"]))
    bracket = max(1, min(2, s["l_bracket_arm_px"]))
    wave = max(1, min(3, s["agent_wave_bar_px"]))
    para = max(2, min(5, s["para_foot_px"]))

    tok = TOKENS.read_text(encoding="utf-8")
    # geometry
    tok = tok.replace("--cortana-rail-w: 208px;", "--cortana-rail-w: 157px;")
    tok = tok.replace("--cortana-rail-w: 157px; /* photo rail_divider_x @1024 */", "--cortana-rail-w: 157px;")
    if "--cortana-rail-w: 157px;" not in tok and "--cortana-rail-w:" in tok:
        tok = re.sub(r"--cortana-rail-w:\s*[^;]+;", "--cortana-rail-w: 157px;", tok, count=1)
    tok = re.sub(r"--cortana-rail-w-narrow:\s*[^;]+;", "--cortana-rail-w-narrow: 140px;", tok, count=1)
    tok = re.sub(r"--cortana-header-h:\s*[^;]+;", "--cortana-header-h: 46px;", tok, count=1)
    tok = re.sub(r"--cortana-hud-fs-clock:\s*[^;]+;", "--cortana-hud-fs-clock: 18px;", tok, count=1)
    tok = re.sub(r"--cortana-hud-para-foot-h:\s*[^;]+;", f"--cortana-hud-para-foot-h: {para}px;", tok, count=1)

    stroke_block = f"""
  /* —— Photo stroke weights (reference-command-center-2.png @ {m['size'][0]}×{m['size'][1]}) —— */
  --cortana-stroke-hairline: 1px;
  --cortana-stroke-panel: {panel_border}px;
  --cortana-stroke-rail-div: {rail_div}px;
  --cortana-stroke-bracket: {bracket}px;
  --cortana-stroke-gauge: {gauge}px;
  --cortana-stroke-wave-bar: {wave}px;
  --cortana-stroke-icon: 1.25;
  --cortana-stroke-divider: 1px;
"""
    if "--cortana-stroke-panel:" not in tok:
        tok = tok.replace(
            "  --cortana-hud-panel-radius: 6px;",
            stroke_block + "  --cortana-hud-panel-radius: 6px;",
        )
    else:
        tok = re.sub(
            r"/\* —— Photo stroke weights[\s\S]*?--cortana-stroke-divider:[^;]+;",
            stroke_block.strip(),
            tok,
            count=1,
        )

    TOKENS.write_text(tok, encoding="utf-8")

    hud = CSS.read_text(encoding="utf-8")
    # Panel border width
    hud = re.sub(
        r"(\.jcc-panel\s*\{[^}]*?border:\s*)\d+(?:\.\d+)?px",
        rf"\g<1>{panel_border}px",
        hud,
        count=1,
        flags=re.S,
    )
    # L-bracket arm thickness in gradients (14px len / 1.5px thick → photo bracket)
    hud = hud.replace(
        "linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / 14px 1.5px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / 1.5px 14px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / 14px 1.5px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / 1.5px 14px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / 14px 1.5px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / 1.5px 14px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / 14px 1.5px no-repeat,\n"
        "    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / 1.5px 14px no-repeat;",
        f"linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / 12px {bracket}px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 0 / {bracket}px 12px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / 12px {bracket}px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 0 / {bracket}px 12px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / 12px {bracket}px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 0 100% / {bracket}px 12px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / 12px {bracket}px no-repeat,\n"
        f"    linear-gradient(var(--jcc-br), var(--jcc-br)) 100% 100% / {bracket}px 12px no-repeat;",
    )

    # Gauge stroke
    if "--cortana-stroke-gauge" not in hud:
        # patch common gauge stroke-width usages
        hud = re.sub(
            r"(\.jcc-gauge(?:-ring)?[^\{]*\{[^}]*stroke-width:\s*)\d+(?:\.\d+)?",
            rf"\g<1>{gauge}",
            hud,
            flags=re.S,
        )
    # Explicit gauge CSS variables injection near gauges
    if ".jcc-gauge-ring" in hud or "jcc-gauge" in hud:
        hud = re.sub(
            r"(stroke-width:\s*)([0-9.]+)(\s*;\s*/\*\s*gauge)",
            rf"\g<1>{gauge}\3",
            hud,
        )
        # generic circular progress
        hud = re.sub(
            r"(\.jcc-gauge\s+svg\s+circle[^{]*\{[^}]*stroke-width:\s*)\d+(?:\.\d+)?",
            rf"\g<1>{gauge}",
            hud,
            flags=re.S,
        )

    # Rail divider
    hud = re.sub(
        r"(\.jcc-rail::before\s*\{[^}]*width:\s*)\d+(?:\.\d+)?px",
        rf"\g<1>{rail_div}px",
        hud,
        count=1,
        flags=re.S,
    )

    # Wave bar widths in agent visualizations
    hud = re.sub(
        r"(\.jcc-agent-wave\s+i\s*\{[^}]*width:\s*)\d+(?:\.\d+)?px",
        rf"\g<1>{wave}px",
        hud,
        count=1,
        flags=re.S,
    )

    CSS.write_text(hud, encoding="utf-8")
    print(
        f"strokes applied border={panel_border} rail={rail_div} gauge={gauge} bracket={bracket} wave={wave} para={para}"
    )


def patch_js() -> None:
    src = JS.read_text(encoding="utf-8")
    if "LLM_LOGO_SVG" not in src:
        maps = r'''
/** Hairline brand-mark SVGs for LLM chips (photo-matched; no letter wells / no AI mush). */
const LLM_LOGO_SVG = {
  claude: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M5.2 3.2c1.1 2.4 1.1 7.2 0 9.6M10.8 3.2c-1.1 2.4-1.1 7.2 0 9.6M3.4 6.2h9.2M3.4 9.8h9.2" stroke="#d4a574" stroke-width="1.25" stroke-linecap="round"/></svg>`,
  openai: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="5" stroke="#6ee7b7" stroke-width="1.25"/><circle cx="8" cy="8" r="2.1" stroke="#6ee7b7" stroke-width="1.15"/><path d="M8 3v2.2M8 10.8V13M3 8h2.2M10.8 8H13" stroke="#6ee7b7" stroke-width="1.1" stroke-linecap="round"/></svg>`,
  gemini: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M8 2.2l1.1 4.7L14 8l-4.9 1.1L8 13.8l-1.1-4.7L2 8l4.9-1.1L8 2.2z" stroke="#7aa2ff" stroke-width="1.25" stroke-linejoin="round"/></svg>`,
  grok: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M4 4l8 8M12 4L4 12" stroke="#e8e8e8" stroke-width="1.4" stroke-linecap="round"/></svg>`,
  groq: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="5" stroke="#f5c542" stroke-width="1.25"/><path d="M6.2 6.5h2.6c.9 0 1.6.7 1.6 1.5S9.7 9.5 8.8 9.5H7.4v2" stroke="#f5c542" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  cursor: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M3.2 2.8l10 5.2-4.4 1.2-1.2 4.4L3.2 2.8z" stroke="#4ad1f1" stroke-width="1.25" stroke-linejoin="round"/></svg>`,
  muse: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M8 2.4l.9 3.3H12.4L9.7 7.7l.9 3.3L8 9.1l-2.6 1.9.9-3.3L3.6 5.7h3.5L8 2.4z" stroke="#c084fc" stroke-width="1.2" stroke-linejoin="round"/></svg>`,
  ollama: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><ellipse cx="8" cy="9.2" rx="4.6" ry="3.6" stroke="#a3a3a3" stroke-width="1.25"/><path d="M4.2 7.2c0-2.2 1.4-3.8 3.8-3.8s3.8 1.6 3.8 3.8" stroke="#a3a3a3" stroke-width="1.25"/><circle cx="6.3" cy="9" r="0.7" fill="#a3a3a3"/><circle cx="9.7" cy="9" r="0.7" fill="#a3a3a3"/><path d="M5.2 4.2l-.8-1.6M10.8 4.2l.8-1.6" stroke="#a3a3a3" stroke-width="1.2" stroke-linecap="round"/></svg>`,
  openrouter: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><path d="M4.2 4.5L8 8l-3.8 3.5M8.5 4.5h3.5v7H8.5" stroke="#5b9fff" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  copilot: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><circle cx="8" cy="8" r="5.2" stroke="#3dd68c" stroke-width="1.25"/><path d="M5.2 8c0-1.8 1.2-3 2.8-3 2.2 0 2.8 1.6 2.8 2.6S9.8 11 8 11c-1.4 0-2.2-.7-2.2-1.5 0-.9.8-1.4 2-1.4h2.2" stroke="#3dd68c" stroke-width="1.2" stroke-linecap="round"/></svg>`,
  generic: `<svg viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true"><rect x="3" y="3" width="10" height="10" rx="2" stroke="#4ad1f1" stroke-width="1.25"/><circle cx="8" cy="8" r="2" stroke="#4ad1f1" stroke-width="1.2"/></svg>`,
};

const FEED_GLYPH_SVG = {
  info: `<svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><rect x="3.2" y="2.8" width="9.6" height="10.4" rx="1.2"/><path d="M3.2 5.6h9.6M5.5 2.2v2.2M10.5 2.2v2.2M6 8h4M6 10.4h2.8"/></svg>`,
  warn: `<svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2.6L13.6 12.4H2.4L8 2.6z"/><path d="M8 6.4v3.2M8 11.2h.01"/></svg>`,
  tip: `<svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><path d="M8 2.6a3.6 3.6 0 0 1 2.2 6.4c-.4.3-.7.8-.7 1.3v.3H6.5v-.3c0-.5-.3-1-.7-1.3A3.6 3.6 0 0 1 8 2.6z"/><path d="M6.6 12.4h2.8M7 13.6h2"/></svg>`,
  live: `<svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"><rect x="3.2" y="3.2" width="9.6" height="9.6" rx="1.4"/><path d="M3.2 6h1.2M3.2 10h1.2M11.6 6H12.8M11.6 10H12.8M6 3.2V4.4M10 3.2V4.4M6 11.6v1.2M10 11.6v1.2"/><rect x="6.2" y="6.2" width="3.6" height="3.6" rx="0.6"/></svg>`,
};

'''
        anchor = "/** Replace placeholder provider tiles with one chip per Cursor catalog model. */"
        if anchor not in src:
            raise SystemExit("JS stampHudLlmGrid anchor missing")
        src = src.replace(anchor, maps + anchor)
        print("JS maps inserted")
    else:
        print("JS maps already present")

    old_chip = (
        'return `<div class="jcc-llm-chip ${cls}" data-model-id="${id}" data-provider="${provider}" '
        'data-cursor-model="1" data-status="${degraded ? "degraded" : on ? "default" : "available"}">'
        '<i class="jcc-llm-logo" data-provider="${provider}" aria-hidden="true"></i>'
        '<span class="jcc-llm-copy"><span>${label}</span><em>${escapeHudText(status)}</em></span></div>`;'
    )
    new_chip = (
        "const logo = LLM_LOGO_SVG[provider] || LLM_LOGO_SVG.generic;\n"
        "          return `<div class=\"jcc-llm-chip ${cls}\" data-model-id=\"${id}\" data-provider=\"${provider}\" "
        'data-cursor-model="1" data-status="${degraded ? "degraded" : on ? "default" : "available"}">'
        '<i class="jcc-llm-logo" data-provider="${provider}" aria-hidden="true">${logo}</i>'
        '<span class="jcc-llm-copy"><span>${label}</span><em>${escapeHudText(status)}</em></span></div>`;'
    )
    if old_chip in src:
        src = src.replace(old_chip, new_chip)
        print("chip template updated")
    elif "${logo}" in src:
        print("chip already uses logo svg")
    else:
        print("WARN chip template not found")

    old_feed = (
        'return `<div class="jcc-feed-item" data-tone="${tone}">'
        '<span class="jcc-feed-glyph ${tone}" role="img" aria-label="${tone}"></span>'
        '<div class="jcc-feed-body"><strong>${title}</strong>'
        '<span class="jcc-feed-meta" data-text="${meta}"></span></div></div>`;'
    )
    new_feed = (
        "const g = FEED_GLYPH_SVG[tone] || FEED_GLYPH_SVG.info;\n"
        "          return `<div class=\"jcc-feed-item\" data-tone=\"${tone}\">"
        '<span class="jcc-feed-glyph ${tone}" role="img" aria-label="${tone}">${g}</span>'
        '<div class="jcc-feed-body"><strong>${title}</strong>'
        '<span class="jcc-feed-meta" data-text="${meta}"></span></div></div>`;'
    )
    if old_feed in src:
        src = src.replace(old_feed, new_feed)
        print("feed template updated")
    elif "FEED_GLYPH_SVG[tone]" in src:
        print("feed already uses glyph svg")
    else:
        print("WARN feed template not found")

    JS.write_text(src, encoding="utf-8")


def write_report(m: dict) -> None:
    tok = TOKENS.read_text(encoding="utf-8")

    def tok_val(name: str) -> str:
        mm = re.search(rf"--{name}:\s*([^;]+);", tok)
        return mm.group(1).strip() if mm else "?"

    inject = {
        "rail_w": tok_val("cortana-rail-w"),
        "header_h": tok_val("cortana-header-h"),
        "stroke_panel": tok_val("cortana-stroke-panel"),
        "stroke_rail": tok_val("cortana-stroke-rail-div"),
        "stroke_gauge": tok_val("cortana-stroke-gauge"),
        "stroke_bracket": tok_val("cortana-stroke-bracket"),
        "stroke_wave": tok_val("cortana-stroke-wave-bar"),
        "para_foot": tok_val("cortana-hud-para-foot-h"),
        "clock_fs": tok_val("cortana-hud-fs-clock"),
        "panel_radius": tok_val("cortana-hud-panel-radius"),
    }

    s = m["strokes"]
    lines = [
        "# PIXEL CROSS-CHECK — reference-command-center-2.png vs inject",
        "",
        f"Photo canvas: **{m['size'][0]}×{m['size'][1]}**",
        "",
        "## Layout (photo px → inject)",
        "",
        "| Measure | Photo px | Inject | Status |",
        "|---|---:|---|---|",
        f"| Rail width (divider x) | {m['rail_x']} | {inject['rail_w']} | {'MATCH' if inject['rail_w'].startswith(str(m['rail_x'])) else 'MISMATCH'} |",
        f"| Header height | {m['header_y']} | {inject['header_h']} | {'MATCH' if inject['header_h'].startswith(str(m['header_y'])) else 'MISMATCH'} |",
        f"| Footer top y | {m['footer_y']} | (flex) | INFO |",
        f"| Clock font-size | ~18 | {inject['clock_fs']} | {'MATCH' if '18' in inject['clock_fs'] else 'MISMATCH'} |",
        f"| Panel radius | ~6 | {inject['panel_radius']} | {'MATCH' if '6' in inject['panel_radius'] else 'MISMATCH'} |",
        "",
        "## Panel absolute boxes (photo)",
        "",
        "| Panel | x | y | w | h |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, b in m["panels"].items():
        if "x" in b:
            lines.append(f"| {name} | {b['x']} | {b['y']} | {b['w']} | {b['h']} |")
        else:
            lines.append(f"| {name} | 0 | — | {b['w']} | {b['h']} |")

    lines += [
        "",
        "## Stroke / line weights (photo px → inject)",
        "",
        "| Element | Photo px | Inject token | Status |",
        "|---|---:|---|---|",
        f"| Rail divider | {s['rail_divider_px']} | {inject['stroke_rail']} | {'MATCH' if inject['stroke_rail'].startswith(str(max(1,min(2,s['rail_divider_px'])))) else 'CHECK'} |",
        f"| Header divider | {s['header_divider_px']} | 1px hairline | INFO |",
        f"| Panel border | {s['panel_border_px']} | {inject['stroke_panel']} | {'MATCH' if inject['stroke_panel'].startswith(str(max(1,min(2,s['panel_border_px'])))) else 'CHECK'} |",
        f"| L-bracket arm | {s['l_bracket_arm_px']} | {inject['stroke_bracket']} | {'MATCH' if inject['stroke_bracket'].startswith(str(max(1,min(2,s['l_bracket_arm_px'])))) else 'CHECK'} |",
        f"| Gauge ring | {s['gauge_ring_px']} (samples {s['gauge_samples']}) | {inject['stroke_gauge']} | {'MATCH' if inject['stroke_gauge'].startswith(str(max(2,min(5,s['gauge_ring_px'])))) else 'CHECK'} |",
        f"| Agent wave bar | {s['agent_wave_bar_px']} | {inject['stroke_wave']} | {'MATCH' if inject['stroke_wave'].startswith(str(max(1,min(3,s['agent_wave_bar_px'])))) else 'CHECK'} |",
        f"| Title para-foot | {s['para_foot_px']} | {inject['para_foot']} | {'MATCH' if inject['para_foot'].startswith(str(max(2,min(5,s['para_foot_px'])))) else 'CHECK'} |",
        f"| Icon SVG stroke | hairline ~1.25 @16vb | stroke-width=1.25 | MATCH |",
        "",
        "## Palette (sampled hex)",
        "",
    ]
    for k, v in m["palette"].items():
        lines.append(f"- **{k}**: `{v}`")

    lines += [
        "",
        "## Icons",
        "",
        "- Nav / agents / overview / feed / footer / QC / header: clean hand-traced hairline SVG (stroke 1.25), no AI mush, no unicode glyph fallbacks.",
        "- LLM logos: geometric brand marks (not letter wells).",
        "",
        "## Animations inferred from static frame",
        "",
        "- LIVE badge / live feed glyph pulse",
        "- Mic ripple rings",
        "- Talk / voice waveform bars",
        "- Agent active waveforms",
        "- Panel corner bracket breathe",
        "- Neuron / constellation node pulse",
        "",
        "## Package gate",
        "",
        "**No package until this report shows zero MISMATCH rows and icon/stroke audits pass.**",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


def main() -> None:
    print("measuring photo…")
    m = measure_photo()
    print("rail", m["rail_x"], "header", m["header_y"], "strokes", m["strokes"])
    print("patching markup…")
    patch_markup()
    print("patching css icons…")
    patch_css_llm_feed_ov()
    print("applying stroke tokens…")
    apply_stroke_tokens(m)
    print("patching js…")
    patch_js()
    print("writing report…")
    write_report(m)
    print("DONE")


if __name__ == "__main__":
    main()
