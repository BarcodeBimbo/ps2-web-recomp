# Marketplace extract — nextgencode.jarvis-3d-theme

**Source:** [VS Marketplace — Jarvis 3D - Iron Man Theme](https://marketplace.visualstudio.com/items?itemName=nextgencode.jarvis-3d-theme) (NextGenCode / Mattzey jarvis-3d-vscode-theme lineage)  
**Purpose:** Phase-6 injection **pattern mapping only**. Do not steal VSIX, Gumroad keys, or their assets.  
**Our locks win:** injection required · **no overlays** · calibrating splash from **our** PNGs · God fail-safes · **every Studio option YES locally** · **Active support EXCLUDED**.

---

## Speakable summary (parent / God)

Marketplace Jarvis 3D sells a freemium Iron Man HUD theme. Marketing says “no plugins,” but FAQ/troubleshooting admit **Custom CSS** — file `custom-styles/jarvis-3d-effects.css`, absolute paths, enable Custom CSS and JS, restart — and the **corrupt-install warning** is expected. Stack claim: CSS3 + extension JS listeners + Canvas particles + SVG Arc Reactor. Free = classic theme/icons/basic HUD; PRO $4.99/2 devices; Studio $24.99/5 + stream white-label; Gumroad live keys + 7-day trial. **Copy patterns only** (workbench CSS inject, glow tokens, settings polish, command taxonomy ideas). **Do not copy** their VSIX, Gumroad, overlay HUD/Konami overlays, or their boot art. **Diff vs us:** we own inject (no third-party loader dependency), forbid overlays, boot from **our** calibrating PNG, and ship three God fail-safes they don’t document. **God lock:** every Studio marketplace option = **YES** on the local theme (unlocked); **Active support = NO** (excluded — God-as-builder only). Title-bar chrome via `titleBarStyle: custom` + inject CSS; taskbar icon needs `.ico`/shortcut replace — **not** pure CSS.

---

## 1) Confirmed injection mechanism (how THEIR product injects)

### Public story (marketing)

- “Built-in 3D visual effects — **no extra plugins required**”
- Install theme → select “Jarvis 3D” → “all 3D effects automatically enabled”
- “Zero configuration”

### Confirmed mechanism (FAQ + Troubleshooting + Customization)

| Signal | What the page says |
|--------|-------------------|
| CSS file | Edit `custom-styles/jarvis-3d-effects.css` (glow `box-shadow`, scanning-line, primary `#00d9ff`) |
| Custom CSS Loader | FAQ: to remove corrupt warning completely → install **Custom CSS and JS Loader** |
| Corrupt warning | Expected when using custom CSS; “editor is NOT corrupted”; click Don’t show again |
| Troubleshooting “Custom CSS Not Working” | (1) absolute path in settings (2) forward slashes `/` on Windows (3) Enable “Custom CSS and JS” from Command Palette (4) full restart |
| Settings hint | `"window.titleBarStyle": "custom"` annotated “optional — **requires custom CSS**” |

**Summary for build:** Their deep chrome effects are **workbench Custom CSS injection** (be5invis-style loader + their `jarvis-3d-effects.css`), not theme-JSON alone. Marketing “auto / no plugins” conflicts with troubleshooting; treat CSS inject as the real path. Extension API JS still drives HUD/stats/commands; particles/reactor are Canvas/SVG layered on that chrome.

**Our mapping:** Same *pattern class* as plan Rank 1 — but **extension-owned** `workbenchInject.js` (no required be5invis dependency). Accept corrupt warning (God lock: no Fix Checksums).

---

## 2) Exact color hex table (from page)

| Color | Hex | Usage (page) |
|-------|-----|----------------|
| Primary Cyan | `#00d9ff` | Highlights, keywords, active elements |
| Blue | `#4d9fff` | UI elements, functions |
| Deep Blue | `#0a1628` | Editor background |
| Dark Navy | `#050d1a` | Activity bar, status bar |
| Green | `#00ff9f` | Strings, success states |
| Yellow | `#ffd95a` | Numbers, warnings |
| Orange | `#ff9d5a` | Constants |
| Red | `#ff4757` | Errors, deletions |

**Alt accents suggested on page (not core table):** Red Tony `#ff0040`, Purple Cyberpunk `#b000ff`, Green Matrix `#00ff00`.

**Vs our reference PNGs:** Keep **our** splash/CC samples (`#0E121A`, `#0FDEFF`/`#00D4FF`–`#4AD1F1`, etc.). Their table is competitor syntax/chrome reference only — do not replace our visual-spec tokens with theirs.

---

## 3) Free vs PRO vs Studio matrix

| Feature | Free | PRO — $4.99 lifetime | Studio — $24.99 |
|---------|------|----------------------|-----------------|
| Classic Jarvis theme + icon theme | Yes | Yes | Yes |
| Basic HUD / Arc Reactor / energy | Yes | Yes | Yes |
| Standard performance mode | Yes | Yes | Yes |
| Suit Modes (Mark I / 50 / Endgame / Stealth) | — | Yes | Yes |
| Particles, Arc pulse, Data Streams, full glow | — | Yes | Yes |
| F.R.I.D.A.Y., Voice TTS, Sound Design | — | Yes | Yes |
| Session Cinema, Stream Pack, Focus Fortress | — | Yes | Yes |
| Threat Fix Hints, GitHUD, Dashboard | — | Yes | Yes |
| AI Companion hooks, Workspace Presets | — | Yes | Yes |
| Devices | 1 | 2 | 5 |
| Stream white-label watermark | — | — | Yes |
| Seasonal Suit Pack DLC | — | optional $1.99 | included with PRO suits |

**Licensing notes (page):** 7-day free trial → then 24h soft-lock preview with unlock overlay → Free limits; keys validated live with **Gumroad**; Ko-fi tips do **not** unlock PRO.

---

## 4) Recommended `settings.json` block (verbatim from page)

```json
{
  "editor.fontFamily": "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
  "editor.fontLigatures": true,
  "editor.fontSize": 14,
  "editor.cursorStyle": "line",
  "editor.cursorBlinking": "smooth",
  "editor.cursorSmoothCaretAnimation": "on",
  "editor.smoothScrolling": true,
  "workbench.list.smoothScrolling": true,
  "terminal.integrated.smoothScrolling": true,
  "editor.renderLineHighlight": "all",
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,
  "editor.minimap.enabled": true,
  "editor.minimap.renderCharacters": false,
  "window.titleBarStyle": "custom",
  "workbench.colorTheme": "Jarvis 3D"
}
```

Also mentioned elsewhere: `"jarvis.enableSoundEffects": true` (experimental).

**Our mapping:** Optional polish defaults for docs/README — do **not** force their theme id; use our suit theme ids + `jarvis.injection.*`.

---

## 5) Commands list (page)

### Core

| Command | Description | Shortcut |
|---------|-------------|----------|
| `JARVIS: Show H.U.D.` | Real-time coding stats | `Ctrl+Alt+H` |
| `JARVIS: Show Dashboard` | Stark Industries Dashboard | `Ctrl+Alt+D` |
| `JARVIS: Toggle Assistant` | JARVIS / F.R.I.D.A.Y. | `Ctrl+Alt+A` |
| `JARVIS: Show Arc Reactor Energy` | Energy analysis | `Ctrl+Alt+E` |
| `JARVIS: Show Threat Panel` | Security analysis | `Ctrl+Alt+S` |
| `JARVIS: Cycle Profile` | Coding profiles | `Ctrl+Alt+P` |

### Community

- `JARVIS: Support Development ☕`
- `JARVIS: Rate Extension ⭐`
- `JARVIS: Share Theme 🔗`

### Visual effects

- `JARVIS: Show Holographic Data Monitor`
- `JARVIS: Show Arc Reactor Core`

### Other named commands (FAQ / secrets)

- `Jarvis: Start 7-Day FREE Trial`
- `Jarvis: Enter License Key` (Gumroad — PRO; from Gumroad product page)
- `Jarvis: Load Stark Legacy` / `War Machine` / `Rescue` / `Matrix Mode`
- Secret: type `Jarvis: ` then `Ctrl+Shift+Alt+J` ×3 rapidly (“Protocol Override”)
- Konami in editor → “HUD **overlay**” boot sequence (10s)

---

## 6) Technical stack claims (page)

```
CSS3 Animations (60 FPS)
  @keyframes, transform: translateZ(), backdrop-filter, will-change

JavaScript Event Listeners
  onDidChangeTextDocument, onDidSaveTextDocument,
  workspace state, real-time metrics

Particle System Engine
  Canvas API, rAF loops, physics movement, collision detection

Arc Reactor Core
  SVG + SMIL, animated radial gradients,
  box-shadow glow stacks, 3D rotation transforms
```

Also claims: “CSS3 + GPU transforms + **WebGL shaders**” (FAQ) — stack diagram does **not** list WebGL; treat WebGL as marketing fluff unless verified in their VSIX (we won’t unpack for theft).

**Perf claims:** +2–5 MB RAM · &lt;1% CPU idle · GPU accelerated · +0.2s startup · pause when unfocused.

---

## 7) PATTERNS to copy vs MUST NOT copy

### Copy as patterns only

| Pattern | Why |
|---------|-----|
| Workbench Custom CSS inject + marked CSS file | Matches our Rank-1 / phase-6 lock |
| Accept corrupt-install warning UX | Same integrity reality; God locked no checksum fix |
| CSS variables / cyan glow / glass / scanning-line *ideas* | Technique class, not their file |
| Extension listeners for typing/save → FX intensity | Activity-aware chrome |
| Canvas particles + SVG reactor *as techniques* | Optional post-boot FX under inject — not as floating overlays |
| Freemium feature matrix shape | We already parallel PRO modules in phases 1–5 |
| Command taxonomy (HUD / threat / suit cycle) | Naming/UX inspiration only |
| Recommended editor polish settings | Optional docs defaults |
| Pause FX when unfocused | Fail-soft perf |

### Must NOT copy

| Forbidden | Why |
|-----------|-----|
| Their VSIX / package contents / CSS verbatim | IP / theft |
| Gumroad license flow, trial soft-lock **unlock overlay**, live key validation | Not our product; overlay violates lock |
| Ko-fi / marketplace rate/share as product core | Noise |
| “No plugins / auto effects” lie as our install story | We document Admin inject + warning honestly |
| Hexagon grid / particle **overlays** on editor | Plan: **no overlays** |
| Konami / Protocol Override HUD overlay | Overlay forbidden |
| Their boot / gallery art / Arc Reactor SVG assets | Boot = **our** `reference-calibrating-splash.png` |
| Depending on Custom CSS and JS Loader at runtime | D2: extension-owned inject |
| MIT claim as excuse to paste their code | Still don’t ship their product |

---

## 8) Diff vs our plan locks

| Lock (ours) | Their marketplace product | Action |
|-------------|---------------------------|--------|
| Injection **required** | Theme + Custom CSS path (admitted in FAQ) | Align: own inject module |
| **No overlays** | HUD overlay (Konami), unlock overlay after trial, hexagon grid overlay marketing | Reject overlay paths; chrome via inject + demoted webview |
| Calibrating splash from **our** PNGs | No calibrating-splash product; marketing Arc Reactor / gallery | Boot = our calibrating asset only |
| Fail-safe 1: auto-disable on Cursor update | Not documented | Ours only |
| Fail-safe 2: disable on patch/probe fail | Troubleshooting only (manual CSS tips) | Ours only |
| Fail-safe 3: God-as-builder / local-owner | Community Discord / Ko-fi / marketplace support framing | Ours: God owns rebuild; no vendor support gap |
| No third-party loader dependency | FAQ pushes Custom CSS and JS Loader | Do not require it |
| Accept corrupt warning | Same | Match |
| PRO modules (suits, cinema, TTS, GitHUD, threats, presets) | PRO/Studio paywall via Gumroad | We already building in-repo; no Gumroad |

---

## Marketplace → phase-6 build mapping (quick)

| Their piece | Our phase-6 slot |
|-------------|------------------|
| `custom-styles/jarvis-3d-effects.css` | `media/inject/{tokens,boot,hud}.css` |
| Custom CSS Loader enable/restart | `jarvis.injection.enable/disable` + Admin write + reload |
| Corrupt warning FAQ | README fail-safe / risk note |
| Canvas/SVG FX | Optional in `hud` after boot; never as editor overlay |
| Free/PRO matrix | Existing modules + injection gate; no Gumroad |
| Settings.json polish | Optional recommended block with **our** theme id |
| Show HUD/Dashboard commands | Bridge to injected chrome / fallback webview — not floating overlay |

---

## GOD LOCKS (Nov 7, 2026) — Studio = YES / Active support = NO

**Authority:** God. Full checklist also in [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md). Do not delete sibling marketplace / palette extract content above — this section **adds** locks.

### Policy

| Lock | Value |
|------|--------|
| Studio marketplace options on **local** theme | **EVERY option = YES** (unlocked; no Gumroad) |
| **Active support** / community / vendor support row | **NO — EXCLUDED** (God was only reading the list) |
| Fail-safe 3 | **God-as-builder / local-owner** — never rename or sell as “Active support” |
| Overlays | Still **forbidden**; Studio HUD via **inject**, not floating overlays |

### 1) How marketplace Jarvis 3D itself uses Custom CSS (corrupt FAQ) — confirmed

Their public product path (despite “no plugins / auto effects” marketing):

1. Ship / edit `custom-styles/jarvis-3d-effects.css` (glow, scan-line, primary `#00d9ff`).
2. Point settings at that file with an **absolute** path (Windows: forward slashes).
3. Command Palette → **Enable Custom CSS and JS** → **full restart**.
4. Cursor/VS Code may show a **corrupt / integrity** warning — FAQ says editor is **not** corrupted; dismiss / Don’t show again.
5. Optional quieting: install third-party **Custom CSS and JS Loader** (we do **not** require this — Rank-1 extension-owned inject).

**Our parity:** Same *mechanism class* (workbench Custom CSS), owned by `workbenchInject.js` + `media/inject/*.css`. Accept corrupt warning; no Fix Checksums.

### 2) Taskbar icon + title bar — Windows Cursor feasibility

| Target | Verdict | Method |
|--------|---------|--------|
| **Title bar chrome** (colors, glow, layout, window controls styling) | **YES** | Set `"window.titleBarStyle": "custom"` + inject CSS targeting `.monaco-workbench .part.titlebar` (and related custom-titlebar selectors). Fits phase-6 inject + fail-safes. |
| **Title-bar corner / window app icon** (in-window) | **PARTIAL** | Custom titleBarStyle exposes `.window-appicon` for CSS size/filter/hide; **replacing the bitmap** still needs an `.ico`/resource swap (not pure CSS). |
| **Windows taskbar icon** | **NO via CSS alone** | OS taskbar uses Electron/`Cursor.exe` icon + pinned **shortcut** `.ico`. Pure workbench CSS cannot reliably change it. |

**Feasible non-CSS methods (optional Phase 6.I / 6.J — Admin + same fail-safes):**

- Replace / patch icons under Cursor install, e.g. `C:\Program Files\cursor\resources\app\resources\win32\code.ico` (and related win32 icons); `Cursor.exe` resource icon may also drive the running app — update wipe risk.
- Point Start Menu / Desktop / pinned taskbar **shortcut** at a custom `.ico` (safest for shortcut-only branding; may not change an already-running process icon until relaunch / re-pin).
- Document restore-on-disable / restore-on-update alongside workbench.html backup.

**Do not** claim taskbar branding as a Custom CSS deliverable.

### 3) Feature checklist — Studio row → our module / inject CSS deliverable

Every Studio row = **YES** on God's local theme except Active support = **EXCLUDED**.

| Studio / marketplace row | Local = | Our module / surface | Inject / CSS deliverable |
|--------------------------|---------|----------------------|---------------------------|
| Classic Jarvis theme + icon theme | **YES** | `themes/jarvis-*-color-theme.json` + activity/icon assets | Theme JSON + optional icon theme; chrome tokens in `media/inject/tokens.css` |
| Basic HUD / Arc Reactor / energy | **YES** | Command Center shell + `media/arc-reactor.svg` | `media/inject/hud.css` (+ boot settle via `boot.css`) |
| Standard performance mode | **YES** | Default FX budget / pause-when-unfocused | Perf flags in inject HUD; no paid tier |
| Suit Modes (Mark I / 50 / Endgame / Stealth) | **YES** | `src/suitModes.js` + 4 themes | Suit CSS variables bridged into inject tokens |
| Particles, Arc pulse, Data Streams, full glow | **YES** | Phase-2 FX (canvas/CSS streams) | `hud.css` animations + depth layers (not overlays) |
| F.R.I.D.A.Y., Voice TTS, Sound Design | **YES** | `src/voiceBridge.js` + CC toggles | Injected chrome rename / mute hooks; Cursor Voice/Chat channel |
| Session Cinema, Stream Pack, Focus Fortress | **YES** | `src/sessionCinema.js` + toggles | Inject HUD density / dim / watermark classes |
| Threat Fix Hints, GitHUD, Dashboard | **YES** | `src/threatHints.js`, `src/gitHud.js`, CC dashboard | Live panels in injected HUD regions |
| AI Companion hooks, Workspace Presets | **YES** | Voice/chat commands + `src/workspacePresets.js` | Preset → suit/theme/inject class apply |
| Devices (5) | **N/A local** | Single-machine install | No cloud device product |
| Stream white-label watermark | **YES (optional local)** | Stream Pack toggle | Optional watermark CSS in inject HUD |
| Seasonal Suit Pack | **YES** | Suit variants / seasonal packs | Theme + inject token packs |
| **Active support** | **NO — EXCLUDE** | — | Do **not** ship Discord/Ko-fi/vendor SLA; God-as-builder only |

God marketing bullets that must also be YES (see GOD-REQUIREMENTS): 3D depth, real-time animation, active responses, arc pulses, first-party innovation (not peer support), real-time tracking, 30% optimized colors, built-in HUD.

---

*Extracted for parent agent marketplace→build mapping. Parallel siblings may cover injection audit / visual spec / plan — this file remains competitor-page extract **plus** God locks above.*
