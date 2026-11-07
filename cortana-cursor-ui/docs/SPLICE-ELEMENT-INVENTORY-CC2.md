# CC-2 full visual inventory + God-missed flags

**Authority:** `media/reference-command-center-2.png` (1024×573)  
**Builds on:** `docs/SPLICE-THEMING-CC2.md`  
**Mode:** Analysis only — no rebuild locks from this doc until God directs.

---

## 1. Proper theme color (sampled from the photo — not guessed)

| Role | Sampled hex (photo) | Where |
|------|---------------------|--------|
| Void / deepest dark | `#030D19` → `#020817` | Corners, gaps between modules |
| App / rail void | `#041324` → `#061A2A` | Sidebar idle, footer void |
| Panel fill (glass well) | `#091A2B` → `#0E2538` | Overview / agents / feed wells |
| Panel darker pocket | `#020D1B` → `#031329` | Inner dark spots inside panels |
| Hairline border cyan | ~`rgba(0,160,200,0.25–0.45)` → glow `#2F7F98` | Panel rims |
| Primary accent / bloom | `#00D4FF` → `#4AD1F1` → `#5CF9FF` | Clock, talk rim, active chrome |
| Soft cyan wash | `#74AEC1` / `#4089A8` | Brand trap glow, globe bloom |
| Talk capsule fill | dark `#021827` + rim glow `#3D94B0` | Bottom Talk stadium |
| Status OK green | `#00E676` / `#3DD68C` range | SYSTEM STATUS · OPTIMAL, LIVE, Connected |
| Warn amber (feed only) | `#FFAB00` / warm orange | Feed WARN rows — **not** header |
| Tip / info cyan-blue | `#40C4FF` / `#4AD1F1` | Feed INFO / TIP |
| Agent / LLM accent purple | `#7C4DFF` / `#C084FC` | Memory agent, some LLM chips |
| Agent / LLM gold | `#FFD740` / `#FBBF24` | Browser agent, Groq-like chips |
| Danger / urgent coral | `#FF5252` | Feed urgent / View Tasks |
| Muted slate text | `#52667A` / `#7A8FA3` | Idle labels, Not Linked |
| Bright label text | `#E8F7FF` / near-white cyan | Titles, values |

**Theme sentence:** Cool void-navy base + electric cyan bloom accents + uneven dark pockets; green = healthy; amber/red only in feed/alerts; purple/gold only as per-agent or per-provider accents — never as global grade.

---

## 2. Shape language (global)

| Shape class | Geometry | Used on |
|-------------|----------|---------|
| **Parallelogram trap** | Vertical left, right edge skewed ~15–25° | Brand block; System Status outer shell (shallower slant than brand) |
| **Stadium / pill** | Fully rounded ends | Search, Focus Mode, Talk capsule, Executive Briefing, status pill inner, operator chip |
| **Rounded rect panel** | ~6–10px radius, 1px cyan rim | All main grid panels |
| **HUD L-brackets** | Bright L corner marks, often offset from rim | Panel corners (overview, feed, monitor, memory, LLM, agents) |
| **Squircle icon well** | Rounded square (~5–6px) | Agent icons, overview row icons, LLM provider logos, header icon buttons |
| **Circle** | True circle | Brand iris, mic button, status dots, nav badges, operator avatar ring, gauge rings |
| **Concentric rings** | Circles / ellipses around core | Brand iris, mic ripples, globe orbits, gauge tracks |
| **Card tile** | Smaller rounded rect inside panel | Agent cards, feed rows, LLM chips, Quick Command buttons |
| **Hairline divider** | 1px vertical/horizontal cyan | Rail | main split; footer top edge |

**Windows:** The reference is a **single full-bleed dashboard** — no OS titlebar chrome, no overlapping floating windows. “Windows” = the **panel cards** in the grid + the **rail column** + the **header strip** + the **footer strip**.

---

## 3. Complete element inventory

Legend: **I** = icon/symbol required · **T** = text · **I+T** = icon + text · **Shape** as above.

### A. Header / top bar

| # | Element | Shape | Color notes | I / T |
|---|---------|-------|-------------|-------|
| A1 | Brand plate | **Parallelogram** | Fill gradient cyan→navy; rim cyan | — |
| A2 | Brand iris | **Circle + dashed concentric rings** | Core bright cyan `#328199+` | **I** (orb / reactor — not a letter) |
| A3 | Brand title | Text on plate | Bright cyan-white | **T** (“JARVIS” in photo → product: CORTANA) |
| A4 | Brand subtitle | Text under title | Dimmer cyan, wide tracking | **T** (“COMMAND CENTER” / WORKSTATION) |
| A5 | System Status outer | Shallow **parallelogram** shell | Dark navy + scan texture | — |
| A6 | System Status pill | **Pill** inside A5 | Border cyan; fill `#081723` | **I+T** (green **dot** + “SYSTEM STATUS · OPTIMAL”) |
| A7 | Date | Plain text | Cool white/grey | **T** |
| A8 | Clock | Large display text + soft oval glow / arc | Bright cyan `#4089A8+` bloom | **T** (digits; arc is **shape**, not text) |
| A9 | Search field | **Stadium** | Fill `#0A1C33`; rim cyan | **I+T** (magnifier **I** + “Search…” **T**; trailing expand corners **I**) |
| A10 | Grid / apps btn | **Squircle** | Dark `#071628` | **I** only (2×2 grid) |
| A11 | Notifications btn | **Squircle** | Same | **I** only (bell) |
| A12 | Settings btn | **Squircle** | Same | **I** only (cog) |
| A13 | Operator chip | **Pill** | `#111F2F` | **T** (“Operator” / “Commander”) + **I** (person silhouette in double ring) |

### B. Left rail / sidebar

| # | Element | Shape | Color notes | I / T |
|---|---------|-------|-------------|-------|
| B1 | Nav row idle | Rounded rect wash (subtle) | `#0A2033` | **I+T** (line icon + label) |
| B2 | Nav row active | Rounded rect + left cyan bar | Lifted `#0F2D43` | **I+T** |
| B3 | Nav icons | Hairline stroke symbols | Cyan | **I** (power/core, robot, doc, calendar, db, chat, molecule, wrench, links) |
| B4 | Nav badges | **Circle** | Indigo fill, cyan numeral | **T** inside circle (`3`, `12`, `18`) — badge is icon-shaped |
| B5 | Rail | main divider | Vertical hairline | Cyan glow | shape |
| B6 | Voice Status panel | Rounded rect | `#020B18`, cyan rim | **T** header + optional **`>`** chevron **I** |
| B7 | Voice waveform | Bar graphic | Cyan bloom | **I** / viz (not words) |
| B8 | Listening label | Text | Cyan | **T** |
| B9 | Mic button | **Circle** + concentric ripples | Fill/rim cyan gradient | **I** (mic glyph) |
| B10 | Tap to Speak | Text under mic | Cyan | **T** |
| B11 | Focus Mode | **Stadium** | Dark fill, cyan rim | **I+T** (sparkle/star **I** + “Focus Mode”) |

### C. Main grid panels

| # | Panel | Outer shape | Inner elements | I / T notes |
|---|-------|-------------|----------------|-------------|
| C1 | AI Core Overview | Rounded rect + L-brackets | Rows: **squircle icon** + title + status | Each row **I+T**; icons are **symbols** (circuit, db, mic, agents, LLM cluster, shield) — not word chips |
| C2 | Globe / AI Core hero | Panel well; content is sphere | Wire mesh sphere, **elliptical orbits**, nodes, pedestal rings, particles, equator scanline | Orbits/nodes/pedestal = **shapes**; label **T** (JARVIS/CORTANA + AI CORE + v3.0.0) |
| C3 | Live Intelligence Feed | Rounded rect + L-brackets + LIVE pill | Rows: **square/squircle glyph** + body + optional status/action | Glyphs **I** (not “INFO” text bars); LIVE = **I** (dot) + **T**; footer “View All Intelligence >” **T+chevron** |
| C4 | Active Agents | Rounded rect | 3×2 **cards**; each: squircle icon, name, **square status dot**, mini waveform | Icons **I** (`</>`, search, db, globe, checklist, shield); status **I** (dot) + **T** (Active/Standby); waveform **viz** |
| C5 | Mission Timeline | Rounded rect + L-brackets | Vertical spine + **circle nodes** + time **T** + task **T** + progress bars | Nodes **I**; bars **shape**; “View Full Schedule >” **T** |
| C6 | Quick Commands | Rounded rect | 2×2 **rounded-rect / pill buttons** | Each **I+T** (+, calendar, mic, play) |
| C7 | System Monitor | Rounded rect + L-brackets | Three **circular gauges** | Rings **shape**; center % **T**; labels CPU/RAM/Disk **T** |
| C8 | Memory Insights | Rounded rect + L-brackets | Neuron **constellation** (dots+lines) + stat column | Map = **I**/viz; stats label **T** + value **T** |
| C9 | LLM Status | Rounded rect + L-brackets | Provider **chips** grid; “Manage Providers >” | Logo wells **I**; name **T**; Connected/Not Linked **T** (green vs muted); footer **T+chevron** |

### D. Footer

| # | Element | Shape | Color notes | I / T |
|---|---------|-------|-------------|-------|
| D1 | Footer bar | Full-width strip, top cyan hairline | Void navy | — |
| D2 | Location chip | Rounded rect | `#0F1F2F` | **I+T** (pin **I** + Location / value) |
| D3 | Weather chip | Rounded rect | Same | **I+T** (sun **I** — slight warm tint + Weather / value) |
| D4 | Network chip | Rounded rect | Same | **I+T** (wifi **I** mint/green + Network / value) |
| D5 | Dot bead row | Small circles | Cyan pulse | **I** / decorative |
| D6 | Talk capsule | Large **stadium** + cyan bloom | Fill `#0F3D52` / rim `#3D94B0` | Waveforms **I**/viz + **T** (“TALK TO …” / listening line) |
| D7 | Talk meter | Thin bar under capsule | Cyan fill | **shape** |
| D8 | Executive Briefing | **Stadium** | `#08192B` | **I+T** (play triangle **I** + label) |
| D9 | Tech tick line | Dashed hairline | Cyan | decorative |

---

## 4. Icon-vs-text rule (lock for rebuild)

**Must be real icons/symbols (never text substitutes):**

- Brand iris, header search magnifier, expand corners, grid, bell, cog, operator avatar  
- All sidebar nav glyphs; mic; Focus sparkle  
- Overview row glyphs; agent squircle glyphs; feed severity glyphs (square with symbol, not “INFO”/“WARN” word pills)  
- Timeline nodes; Quick Command leading icons; gauge rings  
- Memory constellation; LLM brand logos  
- Footer pin / sun / wifi; Talk waveforms; Briefing play  

**Text is correct for:** titles, labels, values, status words (Active, Standby, Connected, Optimal), Talk headline, nav names, clock/date digits.

---

## 5. God-missed flags (notable — he has not explicitly locked these)

These are **in the photo** or are **reference inconsistencies** worth his call before rebuild locks.

### A. Reference content vs product intent

1. **Baked “JARVIS” everywhere** in the photo (brand, globe, Talk). Product is Cortana Workstation — rebuild must **not** copy those glyphs; scrub/replace while keeping shapes.  
2. **Footer location in photo is “Bhimber, Paki…”** — God already locked **Manhattan, New York** as the intentional fiction. Confirm: do **not** 1:1 the photo’s location string.  
3. **Overview / Memory / Feed / Timeline bake demo numbers and meetings** (e.g. 3,380 memories, fake schedule). God wants **live Cursor data** — the photo is a **layout/theme** authority, not a content authority.  
4. **Clock date in photo: “Monday, 15 June 2026”** — live clock should use **real now**, not that printed date.

### B. Colors / theming he under-specified

5. **Amber/yellow exists legally in the photo** — weather sun (warm), feed WARN, browser-agent gold, some LLM chips. God’s “no yellow in the **top bar**” is specific; **do not purge all amber** from feed/agents or the weather icon will look wrong.  
6. **Network icon is mint/green**, not the same cyan as Location — per-chip hue variation is intentional.  
7. **Status OPTIMAL / Connected / LIVE greens** are a second accent family alongside cyan — theme is dual-accent (cyan + green), not cyan-only.  
8. **Purple + gold are agent/LLM accents only** — if they bleed into header/void, grade is wrong.

### C. Shapes / chrome he hasn’t named

9. **Two different parallelogram slant angles** — brand trap steeper than System Status shell. One skew token will look wrong.  
10. **Panel L-brackets / crop marks** on many cards — not just a plain 1px box. Easy to miss; strongly “HUD.”  
11. **Search has a trailing expand (four-corner) icon**, not only the magnifier.  
12. **Header has a Grid/Apps squircle** between search and notifications — often omitted in rebuilds.  
13. **Operator chip layout is text-left + avatar-right** (double ring) — not avatar-left.  
14. **Voice Status header includes a `>` chevron** (collapse/link affordance).  
15. **Mic uses multiple fading concentric ripples**, not a single ring.  
16. **Talk capsule sits on a wider footer band** with a **bead/dot strip** to the left of Talk — decorative data-flow, not empty gutter.  
17. **Talk has left+right waveform wings** and a thin **meter bar** under the stadium.  
18. **Nav badges (`3` / `12` / `18`)** are circular and right-aligned to the row — live counts vs chrome-only needs a decision.  
19. **LLM chips use real provider logos** with Connected glow vs desaturated Not Linked — more than generic cyan tiles.  
20. **“Manage Providers >”** under LLM and **“View All”** links on Agents/Feed/Timeline — text+chevron footers, easy to drop.  
21. **Quick Commands are icon+label tiles**, not text-only buttons.  
22. **Timeline progress bars** have a bright leading edge that fades (trail), not flat fills.  
23. **Clock sits in a soft elliptical glow / top arc** — shape chrome around type, not type alone.  
24. **Inner top-edge bevel/highlight** on pills and squircles (subtle 3D) — flat fills read “cheap” vs photo.  
25. **Scanline / fine noise** on some header/voice surfaces — texture, not pure flat vector.

### D. Possible reference inconsistencies (photo vs photo)

26. **Demo data contradicts itself across panels** (agent “2 Running” vs six agent cards with mixed Active/Standby; “4 Connected” LLM vs visible Connected count in crops). Treat as **mock UI**, not literal metrics to clone.  
27. **Aspect is a short wide mock (1024×573)** — real Cursor workbench is taller; vertical rhythm will need **scale/scroll**, not pixel-stretch.  
28. **No OS min/max/close in the photo** — God wants custom Cortana captions; they are an **add** relative to the reference, not extracted from it.  
29. **Glass without heavy blur** — panels look translucent via fill opacity + glow more than CSS `backdrop-filter` fog; over-blur will diverge.

### E. Process / authority clarifications for God

30. **Theme authority = this photo’s grade + shapes; content authority = live Cursor** (except Manhattan). Needs an explicit nod so rebuild doesn’t paste photo strings.  
31. **Full-app unison** (editor/plan/build) is **out of frame** in CC-2 — photo only covers the Command Center HUD; chrome outside the mock must be **inferred** from the same palette, not traced.

---

## 6. Analytic stage checklist (before fixes)

- [x] Sample real palette from photo  
- [x] Inventory buttons / panels / windows / icons / shapes  
- [x] Icon-vs-text map  
- [x] God-missed / inconsistency flags  
- [ ] God reviews inventory + flags  
- [ ] Then resume element fixes (brand → feed → agents → talk → theming tokens)

**No package until God signs off after pre-install audit.**
