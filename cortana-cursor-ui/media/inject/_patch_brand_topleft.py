"""Patch hud-markup.html + hud.css for pixel-perfect top-left brand chrome."""
from __future__ import annotations

from pathlib import Path

OUT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject")
MARKUP = OUT / "hud-markup.html"
CSS = OUT / "hud.css"
VAR = OUT / "_probe" / "topleft_var.css"

OLD_BRAND_HTML = """    <div class="jcc-brand">
      <div class="jcc-iris" aria-hidden="true">
        <span class="jcc-iris-ring"></span>
        <span class="jcc-iris-ring r2"></span>
        <span class="jcc-iris-core"></span>
      </div>
      <div class="jcc-brand-text">
        <div class="jcc-brand-title">CORTANA COMMAND CENTER</div>
        <div class="jcc-brand-sub">OPERATOR SUITE</div>
      </div>
    </div>"""

NEW_BRAND_HTML = """    <div class="jcc-brand">
      <!-- Pixel chrome: cortana-topleft.png crop from reference-command-center-2.png -->
      <div class="jcc-brand-chrome" aria-hidden="true"></div>
      <div class="jcc-brand-text">
        <div class="jcc-brand-title">CORTANA</div>
        <div class="jcc-brand-sub">COMMAND CENTER</div>
      </div>
    </div>"""

BRAND_CSS_START = "/* Brand block — distinct header cell with diagonal bottom-right cut (ref split) */"
BRAND_CSS_END = ".jcc-nav {"

NEW_BRAND_CSS = """/* Brand block — pixel chrome from reference-command-center-2.png (cortana-topleft.png) */
/* Hybrid: PNG owns iris + trapezoid chrome; HTML owns CORTANA naming overlay. */
/* Does not restyle titlebar / header-right — rail-local only. */
{var_block}
.jcc-brand {{
  position: relative;
  z-index: 3;
  display: block;
  margin: 0 0 6px;
  padding: 0;
  width: 100%;
  max-width: 100%;
  aspect-ratio: 162 / 48;
  height: auto;
  min-height: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  clip-path: none;
  overflow: hidden;
  pointer-events: none;
}}

.jcc-brand-chrome {{
  position: absolute;
  inset: 0;
  background-image: var(--jcc-photo-topleft);
  background-repeat: no-repeat;
  background-position: left top;
  background-size: 100% 100%;
  pointer-events: none;
  z-index: 0;
}}

/* Hide legacy CSS iris (photo chrome replaces it) */
.jcc-brand .jcc-iris,
.jcc-iris-ring,
.jcc-iris-core {{
  display: none !important;
}}

.jcc-brand-text {{
  position: absolute;
  z-index: 1;
  left: 33.3%;
  top: 50%;
  transform: translateY(-50%);
  right: 12%;
  min-width: 0;
  pointer-events: none;
}}

.jcc-brand-title {{
  font-family: var(--CORTANA-font-display, var(--cortana-font-display, "Segoe UI", sans-serif));
  font-weight: 700;
  letter-spacing: 0.22em;
  color: #d7f7ff;
  text-shadow: 0 0 6px rgba(0, 242, 255, 0.35);
  font-size: clamp(9px, 1.05vw, 12px);
  line-height: 1.05;
  text-transform: uppercase;
  white-space: nowrap;
}}

.jcc-brand-sub {{
  font-size: clamp(6px, 0.62vw, 8px);
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #9ad4e6;
  margin-top: 2px;
  text-transform: uppercase;
  white-space: nowrap;
}}

"""


def main() -> None:
    html = MARKUP.read_text(encoding="utf-8")
    if OLD_BRAND_HTML not in html:
        # tolerate already-patched or slight drift
        if 'class="jcc-brand-chrome"' in html and ">CORTANA</div>" in html:
            print("markup already hybrid")
        else:
            raise SystemExit("brand HTML block not found — abort")
    else:
        MARKUP.write_text(html.replace(OLD_BRAND_HTML, NEW_BRAND_HTML, 1), encoding="utf-8")
        print("patched markup")

    css = CSS.read_text(encoding="utf-8")
    start = css.find(BRAND_CSS_START)
    end = css.find(BRAND_CSS_END, start)
    if start < 0 or end < 0:
        raise SystemExit(f"brand CSS anchors missing start={start} end={end}")

    var_block = VAR.read_text(encoding="utf-8").strip()
    # Avoid double :root nesting noise — keep as-is (tokens already use :root)
    replacement = NEW_BRAND_CSS.format(var_block=var_block)
    CSS.write_text(css[:start] + replacement + css[end:], encoding="utf-8")
    print("patched hud.css brand block", len(replacement), "chars")


if __name__ == "__main__":
    main()
