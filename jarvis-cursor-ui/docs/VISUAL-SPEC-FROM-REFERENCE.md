# JARVIS Visual Spec (from reference imagery)

**Purpose:** Pixel / UX target for the **injection build** (Custom CSS / workbench injection). Overlays are out of scope.

**Authoritative sources (read order):**

| # | File | Role |
|---|------|------|
| 1 | `media/reference-calibrating-splash.png` | **PRIMARY** — boot / loading splash + overall glow / typography character |
| 2 | `media/reference-command-center.png` | Post-boot Command Center composition |
| 3 | `media/reference-command-center-2.png` | Same Command Center frame (confirm / alternate crop); treat as identical target to #2 |
| — | Cursor project asset `image-23b432d7-574f-449b-8897-ac9b4e68c2a2.png` | Extra Command Center still (same layout); useful for cross-check only |

Colors below are **sampled from the PNGs** (approximate hex; glow blooms will read brighter than solid fills). Geometry uses image pixel coords and **fractions of image height/width**.

---

## 1. Splash — calibrating boot (`reference-calibrating-splash.png`)

**Image:** `638×480`. Full-bleed dark field; no window chrome in the reference.

### 1.1 Exact visible text (top → bottom)

1. **`J.A.R.V.I.S.`** — title (wide-tracked, dotted initials; trailing period present in reference character)
2. **`JUST A RATHER VERY INTELLIGENT SYSTEM`** — subtitle, single line, uppercase
3. **`CALIBRATING`** — status label above the bar
4. **`33%`** — percentage centered under the bar (dynamic in product; reference shows **33**)
5. No other copy on the splash

### 1.2 Layout geometry (centered column)

All major elements are **horizontally centered** on the canvas midline (`x ≈ 319`).

| Element | Approx Y (px) | Y fraction | Notes |
|---------|---------------|------------|--------|
| Title glyph / glow band | 132–152 | ~0.28–0.32 | Title sits in **upper third** |
| Subtitle | ~165 | ~0.34 | Tight under title |
| Ring (outer) | 194–252 | ~0.40–0.53 | Circle diameter **~58px**; center **`(319, 223)`** |
| Ring center dot | ~223 | ~0.46 | Single filled cyan point at ring center |
| `CALIBRATING` | ~278–283 | ~0.58 | Mid column under ring |
| Progress bar | 311–314 | ~0.65 | Height **~4px**; width **~282px** (`x ≈ 178–459`) |
| Percent | ~325–329 | ~0.68 | Directly under bar |
| Step dots | ~346–352 | ~0.72–0.73 | Near lower third; five indicators |

**Ring**

- Thin circular stroke (≈1–2px).
- **Lit arc / leading segment** in bright cyan; remainder of ring **dim / near-bg** (very low contrast).
- Soft outer bloom on the lit segment.
- **Center:** solid cyan dot with small glow (sampled core ≈ `#0DA6CC`).

**Progress bar**

- Capsule / fully rounded track.
- Filled segment ≈ **33%** of bar width (measured cyan fill ≈ `x 181–272` ≈ **32.6%** of track) — must stay locked to the percent label.
- Fill: bright cyan with slight left→right intensity; sampled fill mid ≈ `#28CAFF`.
- Unfilled track: near-black navy, barely lighter than bg (sampled ≈ `#151626`).
- Optional thin cyan edge glow on the filled portion only.

**Step dots**

- **Five** small **square** (or soft-square) markers, evenly spaced (~7–8px centers).
- **Leftmost 1–2 active** (cyan glow); remaining **dim charcoal** (sampled dim ≈ `#292D35`).
- Active cluster centered near `x ≈ 300–310` at `y ≈ 348–351`.

**Negative space:** Large empty margins; no cards, no sidebar, no Talk bar on splash.

### 1.3 Colors (splash)

| Token | Approx hex | Use |
|-------|------------|-----|
| `--splash-bg` | `#0E121A` | Solid matte charcoal-navy (uniform; no vignette required) |
| `--splash-cyan` | `#0FDEFF` / `#1BE4FF` | Title glow, ring lit stroke, bar fill, active dots (mode `#0FDEFF`) |
| `--splash-cyan-deep` | `#086473` / `#0A6C84` | Glow falloff / darker cyan |
| `--splash-subtitle` | `#52565E` / `#464950` | Subtitle |
| `--splash-calibrating` | `#B9EBF4` → `#87939C` | Status word (pale cyan-white, not pure `#FFF`) |
| `--splash-percent` | `#656C73` | `33%` |
| `--splash-bar-track` | `#151626` | Unfilled bar |
| `--splash-dot-off` | `#292D35` | Inactive steps |

### 1.4 Typography character (splash)

- **Title:** Bold, wide, square / techno-gothic; **very large letter-spacing** (≈ `0.25–0.35em`); cyan fill + heavy outer glow (`text-shadow` / bloom), reads as emissive light.
- **Subtitle:** Thin / light sans, all-caps, wide tracking, muted grey; much smaller than title (~10–11px at this asset scale).
- **CALIBRATING:** Mid-weight sans, all-caps, wide tracking (`~0.35–0.45em`), pale near-white with cool tint.
- **Percent:** Small tabular/sans, muted grey, normal tracking.
- Stack preference for injection: geometric UI sans (e.g. Rajdhani / Orbitron-like for title if available; else condensed bold + tracking). Avoid soft rounded display faces.

### 1.5 Background (splash)

- Flat `#0E121A` (or identical `#0E121A`–`#0E131B` noise-free).
- No grid, no particles required on the reference still (product FX may exist **after** splash, not on this frame).
- No glass panels on splash.

---

## 2. Post-boot Command Center (`reference-command-center.png` / `-2`)

**Image:** `1024×573`. Full dashboard; glassmorphism on deep navy.

`reference-command-center.png` and `reference-command-center-2.png` are the **same composition** for injection purposes. Extra asset `image-23b432d7-…` matches the same layout.

### 2.1 Global palette & surface style

| Token | Approx hex | Use |
|-------|------------|-----|
| `--bg-deep` | `#020817` → `#091D35` | App / editor void (darker at edges, slightly lifted in content wells) |
| `--sidebar-fill` | `#001020` / `#061729` | Left nav column |
| `--panel-glass` | `#000F24` @ high opacity + blur | Card interiors |
| `--border-cyan` | `#0A3852` / `rgba(0, 212, 255, 0.18–0.28)` | 1px panel borders |
| `--accent` | `#4AD1F1` / `#00D4FF` / `#40A7CA` | Clock, glows, active chrome (bright clock sample `#4AD1F1`) |
| `--talk-fill` | `#001E32` / `#042335` | Talk capsule interior |
| `--talk-rim` | `#0C79A0` / `#57A3C3` | Talk bar outer glow / rim |
| `--ok` | `#2FA58F` / `#3DD68C` | SYSTEM STATUS · Optimal |
| `--warn` | amber / gold | Feed warnings, overdue |
| `--danger` | red / coral | Urgent feed |
| `--text` | `#BECEDB` / `#C8D6E5` | Primary labels |
| `--muted` | blue-grey | Secondary meta |

**Glass / panel style (mandatory):**

- Rounded panels ≈ **8–12px** radius.
- Semi-transparent dark fills over navy void.
- **1px** cool cyan borders; soft inner glow optional.
- Thin corner accents acceptable; no heavy drop shadows (prefer cyan bloom).
- Cards sit in a **dense dashboard grid**, not a single scrolling list.

### 2.2 Layout regions

```
┌─ Title / brand strip ─────────────────────────────────────────────┐
│ JARVIS COMMAND CENTER │ SYSTEM STATUS ● OPTIMAL │ clock │ search… │
├─ Left nav ──────┬─ Main dashboard grid ───────────────────────────┤
│ Command Center  │ AI Core Overview │ Globe hero │ Live Feed        │
│ AI Core         │ Active Agents    │ Timeline   │ Quick Commands   │
│ Agents …        │ System Monitor   │ Memory     │ LLM Status       │
│ Voice Status    │                                                     │
│ Focus Mode      │                                                     │
├─────────────────┴─────────────────────────────────────────────────┤
│ Location / Weather / Network │ TALK TO JARVIS capsule │ Briefing  │
└───────────────────────────────────────────────────────────────────┘
```

#### Left sidebar (nav + voice)

- Header: **`JARVIS COMMAND CENTER`** + circular radar / globe icon (cyan pulse).
- Vertical nav (reference labels):
  - Command Center *(active)*
  - AI Core
  - Agents
  - Tasks *(badge `3`)*
  - Calendar
  - Memory
  - Conversations *(badge `12`)*
  - Knowledge Base
  - Tools & Skills *(badge `18`)*
  - Workflows
- **Active nav:** left cyan vertical bar + subtle blue wash background; white/near-white label.
- **Badges:** small filled cyan circles, white numerals.
- **Voice Status** (sidebar bottom): waveform + circular mic + **`Tap to Speak`** / listening state.
- **Focus Mode** control under voice block.

#### Top header

- Left/system: pill **`SYSTEM STATUS ● OPTIMAL`** (green dot + green text/border).
- Center: live clock — reference shows e.g. **`Monday, 15 June 2026 | 11:18:21 am`** in bright cyan (date + time).
- Right: ghost search field, layout / notification / settings icons, profile pill **`Operator: Commander`**.

#### Main grid (post-boot home)

| Region | Content cues |
|--------|----------------|
| AI Core Overview | Rows: AI Core Active, Memory count, Voice Online, Agents running, LLMs connected, System Optimal — tinted icons |
| Center hero | 3D / wireframe globe + orbital rings; overlay **`JARVIS AI CORE v3.0.0`** |
| Live Intelligence Feed | Color-coded events (Info / Warn / Tip / Live / Urgent) |
| Active Agents | Cards: Coding, Research, Memory, Browser, Task, System — mini waveforms + status |
| Mission Timeline | Vertical nodes + cyan spine; tasks with progress |
| Quick Commands | Bordered action tiles (Start New Task, Open Calendar, …) |
| System Monitor | Circular gauges — reference CPU **15%**, RAM **54%**, Disk **40%** |
| Memory Insights | Node-link / constellation viz + memory / tool-call counts |
| LLM Status | Provider tiles (Claude, GPT, Gemini, …) Connected vs Not Linked |

#### Bottom bar

- Left meta: **Location**, **Weather** (e.g. `28°C Overcast`), **Network** (e.g. `Excellent`).
- Center — primary CTA: wide **glowing capsule**  
  **`TALK TO JARVIS`** + waveform + **`I am listening...`**
  Heavy cyan outer bloom; darkest fill inside; dominant focal point of the chrome.
- Right: **`Executive Briefing`** (or equivalent action) button.

### 2.3 Typography (Command Center)

- Clean geometric sans throughout; uppercase + wide tracking on section headers and status pills.
- Clock: medium-bold cyan, high legibility.
- Body/meta: smaller, muted; avoid dense paragraph text in cards.

### 2.4 Motion (visual, not overlay)

- Globe / orbit subtle motion.
- Waveforms on agents + Talk bar + Voice Status.
- Status dot pulse (Optimal).
- Splash ring rotation only during calibrating phase.

---

## 3. What “IDE looks exactly like reference when loaded” means (injection)

Target is **workbench CSS injection** so the **entire Cursor window**, once past splash, reads as the Command Center frame — not a webview floating on default IDE chrome.

### 3.1 Surfaces that must change

| Workbench surface | Must become |
|-------------------|-------------|
| **Window / title bar** | Deep navy `#02080F`–`#020817`; cyan-leaning borders; brand-compatible title treatment |
| **Activity Bar** | Left icon rail matching Command Center nav character (dark `#030A12` / `#001020`, cyan active indicator, cyan badges) |
| **Side Bar** | Glass column: navy fill, cyan 1px borders, section headers like CC cards; hosts Command Center webview **flush** with injected chrome |
| **Editor group + tabs** | Tabs/header restyled to glass navy; active tab cyan top border; editor bg `#050D16`–`#091D35` void — no bright VS Code greys |
| **Breadcrumbs / editor widgets** | Same palette; cyan accents on focus |
| **Panel** (terminal / problems) | Same glass + cyan active tab underline |
| **Status Bar** | Remap toward **footer meta** strip (host / network / suit); darkest navy; cyan hover |
| **Quick Input / Command Palette / Chat / Composer** | Restyle toward **Talk to JARVIS** capsule language (glow rim, cyan focus, dark fill) wherever injection allows |
| **Scrollbars, badges, progress** | Cyan accent tokens from theme JSON + injected CSS |
| **Notifications** | Glass navy + cyan border |

### 3.2 Splash vs post-boot (injection sequence)

1. **Boot / loading:** Full-window calibrating splash matching §1 (solid `#0E121A`, ring, bar, dots, copy). This is the **PRIMARY** visual for first paint / reload cinema — *not* a screenshot of the Command Center grid.
2. **After calibrate:** Crossfade/hide splash → Command Center regions (§2) with **injected** activity bar / sidebar / editor / status bar already in JARVIS chrome so the IDE does not “flash” default theme.
3. Command Center **webview** supplies the dashboard grid + Talk bar content; **injection** supplies the surrounding IDE shell so the *window* matches the reference, not only the view.

### 3.3 Explicit non-goals

- No floating editor overlays, no transparent HUD layers on top of unmodified chrome.
- Do not treat “theme JSON alone” as sufficient for pixel match — **injection CSS is required** for activity bar geometry, Talk-bar glow, glass radii, and splash full-bleed.
- Do not leave default blue/grey Cursor accents visible on activity bar, status bar, or tab strip when JARVIS suit is active.

---

## 4. Acceptance checklist (pixel / UX match)

### Splash

- [ ] Background solid ≈ `#0E121A` (no light grey / default workbench flash)
- [ ] Copy exact: `J.A.R.V.I.S.` → subtitle uppercase expansion → `CALIBRATING` → `N%` → five dots
- [ ] Title cyan with visible bloom; tracking wide
- [ ] Ring ≈ square aspect, thin stroke, center cyan dot, spinning / advancing lit segment
- [ ] Bar height ≈ 4–6px, width ≈ 40–45% of viewport, fill % matches label (~33% in reference still)
- [ ] Five step dots; active cyan, inactive dim; bottom-centered
- [ ] No Talk bar / nav / cards visible during splash

### Command Center (post-boot)

- [ ] Deep navy void + cyan accent reads immediately (side-by-side with `reference-command-center.png`)
- [ ] Left nav labels + badges present; active item has **left cyan bar**
- [ ] `SYSTEM STATUS ● OPTIMAL` green pill visible
- [ ] Cyan clock (date + time) in header
- [ ] Glass cards with ~8–12px radius and 1px cyan-tint borders
- [ ] Center AI Core globe / hero + `JARVIS AI CORE v…` treatment
- [ ] Feed / agents / timeline / gauges / LLM grid recognizable vs reference regions
- [ ] Bottom **Talk to JARVIS** capsule is the brightest glow on screen; listening subcopy present
- [ ] Footer meta (location / weather / network or IDE equivalents) flanking Talk bar

### Injection / IDE shell

- [ ] Activity bar, sidebar, editor tabs, panel, status bar all use JARVIS navy/cyan — **no stock Cursor purple/grey strip**
- [ ] Reload / cold start shows calibrating splash (§1) before CC
- [ ] After load, full window matches reference composition language without overlay windows
- [ ] Focus / hover / selection states use cyan wash, not default blue
- [ ] Suit theme tokens and injected CSS stay aligned (accent hex within splash/CC sampled range `#00D4FF`–`#4AD1F1`)

### Fail conditions

- Splash uses Command Center screenshot as boot (wrong primary).
- Only webview themed; surrounding IDE still default.
- Talk bar is a plain button without capsule glow.
- Overlays used to fake chrome.

---

## 5. Build notes (for implementers)

- Prefer CSS variables aligned to §1.3 and §2.1 in both **webview** and **injected workbench** sheets.
- Splash percent and bar width must share one progress source.
- Nav badge numbers in reference (`3`, `12`, `18`) are composition targets; live data may substitute but badge **shape/color** must match.
- `README` historically called `reference-command-center.png` the boot target; **this spec supersedes that for splash:** boot = `reference-calibrating-splash.png`; loaded IDE = Command Center references via injection + CC view.

---

*Generated from direct reads of the reference PNGs + pixel sampling. Injection CSS is the delivery mechanism.*
