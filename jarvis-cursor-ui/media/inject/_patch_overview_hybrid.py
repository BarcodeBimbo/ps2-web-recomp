"""Patch hud.css overview block for PNG-face hybrid + refresh data-URI."""
from pathlib import Path
import base64
import re

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject")
CSS = ROOT / "hud.css"
FACE = ROOT / "overview-face.png"
URI_TXT = ROOT / "_overview_face_datauri.txt"

b64 = base64.b64encode(FACE.read_bytes()).decode("ascii")
uri = f'url("data:image/png;base64,{b64}")'
URI_TXT.write_text(uri, encoding="utf-8")

new_block = f"""/* Overview — Workstation Overview (pixel face from reference-command-center-2.png) */
.jcc-overview {{
  --ov-memory: "—";
  --ov-agents: "2";
  --ov-llms: "4";
  --jcc-ov-face: {uri};
  position: relative;
  container-type: inline-size;
  aspect-ratio: 188 / 184;
  min-height: 0;
  padding: 0 !important;
  overflow: hidden;
  background: transparent;
  border-color: transparent;
  box-shadow: none;
  clip-path: none;
  backdrop-filter: none;
}}

.jcc-overview.jcc-panel::before,
.jcc-overview.jcc-panel::after {{
  display: none;
}}

.jcc-ov-face {{
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image: var(--jcc-ov-face);
  background-size: 100% 100%;
  background-repeat: no-repeat;
  background-position: center;
}}

.jcc-overview .jcc-ov-title {{
  position: absolute;
  z-index: 2;
  top: 1.4%;
  left: 6.4%;
  margin: 0;
  padding: 0;
  font-size: clamp(7px, 4.8cqw, 9px);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7ec8e3;
  font-weight: 700;
  text-shadow: 0 0 6px rgba(0, 212, 255, 0.35);
  white-space: nowrap;
  pointer-events: none;
}}

.jcc-ov-title-ico {{
  display: none;
}}

.jcc-ov-row1-lab {{
  position: absolute;
  z-index: 2;
  top: 14.2%;
  left: 22.5%;
  font-size: clamp(9px, 5.8cqw, 12px);
  font-weight: 700;
  color: #e8f7ff;
  letter-spacing: 0.02em;
  line-height: 1.1;
  white-space: nowrap;
  pointer-events: none;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.45);
}}

/* Semantic list for a11y / live counts; visible pixels from PNG face */
.jcc-ov-list {{
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
  list-style: none;
}}

.jcc-ov-num[data-ov-num="memory"]::before {{
  content: var(--ov-memory);
}}

.jcc-ov-num[data-ov-num="agents"]::before {{
  content: var(--ov-agents);
}}

.jcc-ov-num[data-ov-num="llms"]::before {{
  content: var(--ov-llms);
}}
"""

css = CSS.read_text(encoding="utf-8")
pat = re.compile(
    r"/\* Overview(?: — Workstation Overview)?.*?\*/\s*.*?(?=\n/\* Hero globe \*/)",
    re.S,
)
m = pat.search(css)
if not m:
    raise SystemExit("overview block not found")
print("matched", m.start(), m.end(), "len", m.end() - m.start())
CSS.write_text(css[: m.start()] + new_block + css[m.end() :], encoding="utf-8")
print("wrote", CSS, CSS.stat().st_size)
