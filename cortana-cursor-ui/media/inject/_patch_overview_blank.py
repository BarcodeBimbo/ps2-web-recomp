"""Clear dummy Workstation Overview values — real or blank only."""
from pathlib import Path
import re

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject")
MARKUP = ROOT / "hud-markup.html"
CSS = ROOT / "hud.css"

NEW_SECTION = r'''      <section
        class="jcc-panel jcc-overview"
        data-memory-count=""
        data-agent-count=""
        data-llm-count=""
      >
        <h2 class="jcc-panel-title jcc-ov-title">
          <span class="jcc-ov-title-ico" aria-hidden="true">
            <svg viewBox="0 0 12 12" width="10" height="10" fill="currentColor"><rect x="0" y="0" width="4" height="4" rx="0.6"/><rect x="8" y="0" width="4" height="4" rx="0.6"/><rect x="0" y="8" width="4" height="4" rx="0.6"/><rect x="8" y="8" width="4" height="4" rx="0.6"/></svg>
          </span>
          Workstation Overview
        </h2>
        <ul class="jcc-ov-list">
          <li class="jcc-ov-row" data-row="workstation">
            <span class="jcc-ov-ico" data-tone="cyan" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="4" y="4" width="12" height="12" rx="2"/><rect x="7.5" y="7.5" width="5" height="5" rx="1"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2"/></svg>
            </span>
            <span class="jcc-ov-k">Workstation</span>
            <span class="jcc-ov-v" data-ov-live="workstation"></span>
          </li>
          <li class="jcc-ov-row" data-row="memory">
            <span class="jcc-ov-ico" data-tone="cyan" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4"><ellipse cx="10" cy="5.5" rx="5.5" ry="2.2"/><path d="M4.5 5.5v3.2c0 1.2 2.5 2.2 5.5 2.2s5.5-1 5.5-2.2V5.5"/><path d="M4.5 8.7v3.2c0 1.2 2.5 2.2 5.5 2.2s5.5-1 5.5-2.2V8.7"/><path d="M4.5 11.9v2.4c0 1.2 2.5 2.2 5.5 2.2s5.5-1 5.5-2.2v-2.4"/></svg>
            </span>
            <span class="jcc-ov-k">Memory</span>
            <span class="jcc-ov-v" data-ov-live="memory">
              <span class="jcc-ov-num" data-ov-num="memory"></span>
              <span class="jcc-ov-unit" data-ov-unit="memory"></span>
            </span>
          </li>
          <li class="jcc-ov-row" data-row="voice">
            <span class="jcc-ov-ico" data-tone="cyan" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor"><rect x="2" y="8" width="2" height="4" rx="0.6"/><rect x="5.5" y="5" width="2" height="10" rx="0.6"/><rect x="9" y="3" width="2" height="14" rx="0.6"/><rect x="12.5" y="6" width="2" height="8" rx="0.6"/><rect x="16" y="8.5" width="2" height="3" rx="0.6"/></svg>
            </span>
            <span class="jcc-ov-k">Voice</span>
            <span class="jcc-ov-v" data-ov-live="voice"></span>
          </li>
          <li class="jcc-ov-row" data-row="agents">
            <span class="jcc-ov-ico" data-tone="cyan" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="10" cy="7" r="3"/><path d="M4.5 16.5c1.2-3 3-4.5 5.5-4.5s4.3 1.5 5.5 4.5"/></svg>
            </span>
            <span class="jcc-ov-k">Agents</span>
            <span class="jcc-ov-v" data-ov-live="agents">
              <span class="jcc-ov-num" data-ov-num="agents"></span>
              <span class="jcc-ov-unit" data-ov-unit="agents"></span>
            </span>
          </li>
          <li class="jcc-ov-row" data-row="llms">
            <span class="jcc-ov-ico" data-tone="cyan" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3.5 6.5h13M3.5 10h13M3.5 13.5h13"/><circle cx="7" cy="6.5" r="1.2" fill="currentColor" stroke="none"/><circle cx="12" cy="10" r="1.2" fill="currentColor" stroke="none"/><circle cx="9" cy="13.5" r="1.2" fill="currentColor" stroke="none"/></svg>
            </span>
            <span class="jcc-ov-k">LLMs</span>
            <span class="jcc-ov-v" data-ov-live="llms">
              <span class="jcc-ov-num" data-ov-num="llms"></span>
              <span class="jcc-ov-unit" data-ov-unit="llms"></span>
            </span>
          </li>
          <li class="jcc-ov-row" data-row="system">
            <span class="jcc-ov-ico" data-tone="ok" aria-hidden="true">
              <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M10 2.5l6 2.2v5.1c0 3.4-2.4 5.8-6 7.2-3.6-1.4-6-3.8-6-7.2V4.7L10 2.5z"/><path d="M7.2 10.1l1.9 1.9 3.7-3.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <span class="jcc-ov-k">System</span>
            <span class="jcc-ov-v" data-ov-live="system"></span>
          </li>
        </ul>
      </section>'''

NEW_CSS = r'''/* Overview — Workstation Overview (functional: real values or blank; no dummies) */
.jcc-overview {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 12px 14px 10px;
  background: rgba(5, 22, 34, 0.82);
  border-color: rgba(0, 212, 255, 0.28);
  box-shadow:
    var(--cortana-shadow-card),
    inset 0 0 24px rgba(0, 212, 255, 0.04);
}

.jcc-overview .jcc-ov-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 12px;
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--cortana-cyan);
  font-weight: 700;
  text-shadow: var(--cortana-text-glow-soft);
}

.jcc-ov-title-ico {
  display: inline-grid;
  place-items: center;
  color: var(--cortana-cyan);
  opacity: 0.9;
  flex-shrink: 0;
}

.jcc-ov-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
}

.jcc-ov-row {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: 10px;
  align-items: center;
  min-height: 34px;
  padding: 5px 0;
  border-bottom: 1px solid rgba(0, 212, 255, 0.07);
  font-size: 11px;
}

.jcc-ov-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.jcc-ov-ico {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  background: rgba(0, 28, 48, 0.85);
  border: 1px solid rgba(0, 212, 255, 0.22);
  color: var(--cortana-cyan-soft);
  box-shadow: inset 0 0 10px rgba(0, 212, 255, 0.08);
  flex-shrink: 0;
}

.jcc-ov-ico[data-tone="ok"] {
  color: var(--cortana-ok-bright);
  border-color: rgba(61, 214, 140, 0.35);
  box-shadow: inset 0 0 10px rgba(61, 214, 140, 0.1);
}

.jcc-ov-ico[data-tone="cyan"] {
  color: var(--cortana-cyan-soft);
}

.jcc-ov-ico svg {
  display: block;
}

.jcc-ov-k {
  color: var(--cortana-text-dim, #7a8fa3);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.jcc-ov-v {
  font-weight: 650;
  letter-spacing: 0.02em;
  text-align: right;
  white-space: nowrap;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
  color: var(--cortana-text-dim, #7a8fa3);
}

.jcc-ov-v:empty {
  min-width: 0;
}

.jcc-ov-v[data-tone="ok"] {
  color: var(--cortana-ok-bright, #3dd68c);
  text-shadow: 0 0 8px rgba(61, 214, 140, 0.35);
}

.jcc-ov-num {
  color: var(--cortana-cyan-soft, #00f2ff);
  font-weight: 700;
  text-shadow: var(--cortana-text-glow-soft);
}

/* Live fill only: set --ov-* on .jcc-overview when real counts exist */
.jcc-overview[style*="--ov-memory"] .jcc-ov-num[data-ov-num="memory"]::before {
  content: var(--ov-memory);
}

.jcc-overview[style*="--ov-agents"] .jcc-ov-num[data-ov-num="agents"]::before {
  content: var(--ov-agents);
}

.jcc-overview[style*="--ov-llms"] .jcc-ov-num[data-ov-num="llms"]::before {
  content: var(--ov-llms);
}

.jcc-ov-unit {
  color: var(--cortana-text-dim, #7a8fa3);
  font-weight: 500;
}

.jcc-ov-unit:empty {
  display: none;
}

.jcc-ov-unit.ok {
  color: var(--cortana-ok-bright, #3dd68c);
  font-weight: 650;
  text-shadow: 0 0 8px rgba(61, 214, 140, 0.3);
}

'''

html = MARKUP.read_text(encoding="utf-8")
html_pat = re.compile(
    r"      <section\n        class=\"jcc-panel jcc-overview\"[\s\S]*?</section>(?=\n\n      <section class=\"jcc-panel jcc-hero\")",
)
m = html_pat.search(html)
if not m:
    raise SystemExit("overview section not found in markup")
MARKUP.write_text(html[: m.start()] + NEW_SECTION + html[m.end() :], encoding="utf-8")
print("markup patched", m.start(), m.end())

css = CSS.read_text(encoding="utf-8")
css_pat = re.compile(
    r"/\* Overview — Workstation Overview.*?\*/\s*.*?(?=\n/\* Hero globe)",
    re.S,
)
m2 = css_pat.search(css)
if not m2:
    raise SystemExit("overview CSS block not found")
CSS.write_text(css[: m2.start()] + NEW_CSS + css[m2.end() :], encoding="utf-8")
print("css patched", m2.start(), m2.end())

# Verify no dummy strings remain in overview section
html2 = MARKUP.read_text(encoding="utf-8")
sec = re.search(r'class="jcc-panel jcc-overview"[\s\S]*?</section>', html2).group(0)
for bad in ("Active", "Online", "Optimal", "3,380", "stored", "Running", "Connected", "—"):
    if bad in sec and bad not in ("Active",):  # check carefully
        pass
dummies = []
for bad in ["Active", "Online", "Optimal", "3,380", "stored", "Running", "Connected"]:
    if bad in sec:
        dummies.append(bad)
# em dash in attrs
if "—" in sec or "'2'" in sec or "'4'" in sec:
    dummies.append("dash-or-count-attr")
print("remaining dummies in overview:", dummies or "none")
