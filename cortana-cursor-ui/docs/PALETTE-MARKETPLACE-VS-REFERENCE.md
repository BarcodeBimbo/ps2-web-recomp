# Palette: Jarvis 3D marketplace vs our reference samples vs theme JSON

**Sources**

| Source | Role |
|--------|------|
| Jarvis 3D marketplace listing (stated brand tokens) | Named product palette |
| `docs/VISUAL-SPEC-FROM-REFERENCE.md` + `media/reference-*.png` | Pixel samples for splash / Command Center (injection visual lock) |
| `themes/CORTANA-*-color-theme.json` + `src/suitModes.js` | Shipped VS Code theme / suit accents |
| `media/inject/tokens.css` | Phase-6 injection CSS variables (current) |

**No theme JSON edits in this pass** — themes already mix marketplace and sample hex; changing them is optional later (see § Recommendation).

---

## Alignment table

| Token (marketplace name) | Marketplace | Our PNG / visual-spec samples | Theme JSON (Mark I / Command; others noted) | Current phase-6 `tokens.css` |
|--------------------------|-------------|-------------------------------|---------------------------------------------|------------------------------|
| **Primary Cyan** | `#00d9ff` | Splash mode ≈ `#0FDEFF` / `#1BE4FF`; bar mid ≈ `#28CAFF`; CC accent ≈ `#4AD1F1` / `#00D4FF` / `#40A7CA` | **Exact** on `icon.foreground`, `focusBorder` (`#00d9ff` / `#00d9ff66`); most chrome uses **`#00d4ff`** (near CC) | **Brighter bloom:** `--CORTANA-cyan: #00f2ff`; soft `#0fdeff`; mid `#00d4ff` — *not* marketplace primary |
| **Blue** | `#4d9fff` | Not a discrete sampled fill (CC leans cyan, not mid-blue) | **Exact** `terminal.ansiBlue`; Mark I `suitModes.accent2` | Absent as named token |
| **Deep Blue** | `#0a1628` | CC wells ≈ `#000F24` / `#001020` / `#061729`; void `#020817`→`#091D35` | Nearby only (`#0a2540`, `#071828`, `#061320`…) — **no exact `#0a1628`** | Nearby panels (`#0a1018`, `#080c14`) — **no exact** |
| **Dark Navy** | `#050d1a` | Splash bg **`#0E121A`** (lighter charcoal); editor void `#050D16`–`#091D35` | Editor `#050d16` (1-step off); Mark I suit `bg: #050d1a` **exact** | Splash-locked **`#0e121a`** / `#0b0e14` — prefers PNG splash, not marketplace navy |
| **Green** | `#00ff9f` | CC Optimal ≈ `#2FA58F` / `#3DD68C` (muted teal-green) | `#3dd68c` (gutter / ansi / git) — **not** marketplace neon | `--CORTANA-ok: #2fa58f` / bright `#3dd68c` — **PNG side**, not `#00ff9f` |
| **Yellow** | `#ffd95a` | Spec: “amber / gold” (no single hex) | Theme warn / ansiYellow **`#ffc94d`**; CC webview `--warn: #ffd95a` (**marketplace**) | `--CORTANA-warn: #ffc94d` — theme-aligned, **not** marketplace |
| **Orange** | `#ff9d5a` | Not sampled as a dedicated token | **Missing** as a first-class color | **Missing** |
| **Red** | `#ff4757` | Spec: “red / coral” | `errorForeground: #ff4757` (**exact**); many borders/ansi use softer `#ff6b7a` | `--CORTANA-danger: #ff4757` (**marketplace**) |

**Extra (ours only, not in marketplace 8):** splash subtitle/percent greys, bar track `#151626`, dot-off `#292D35`, text `#c8d6e5`, glass border `#0a3852` — keep from PNG/spec.

---

## Verdict (short)

- **Marketplace ↔ Mark I suit / partial theme:** Primary cyan, blue, dark navy (suit bg), and red already match marketplace in `suitModes` + key theme keys.
- **Marketplace ↔ PNG samples:** Cyan and navy diverge in expected ways — splash blooms read hotter/lighter (`#0FDEFF`…`#00f2ff`) than brand `#00d9ff`; splash void `#0E121A` ≠ `#050d1a`. Green is the largest semantic gap (`#00ff9f` vs muted `#2FA58F`/`#3DD68C`).
- **Theme JSON:** Hybrid — marketplace primaries for a few keys, `#00d4ff` + sample-ish greens/yellows for most workbench chrome. Leaving JSON unchanged is fine unless we want one canonical cyan.

---

## Phase-6 CSS: prefer marketplace or PNG samples?

**Prefer PNG samples for surfaces that must pixel-match the reference stills; prefer marketplace for named semantic / brand tokens that the listing documents and that are not tightly locked by splash bloom.**

| Use | Prefer | Why |
|-----|--------|-----|
| Splash / boot void, neon cyan bloom, bar/ring/dots | **PNG samples** (`#0E121A`, `#0FDEFF`–`#00f2ff` family) | Phase-6 + visual-spec lock: calibrating PNG is primary |
| CC glass navy range, Optimal green tint when matching CC screenshot | **PNG samples** | Command Center refs use muted teal-green, not neon `#00ff9f` |
| Product / suit accent identity, error red, warn/yellow when not on splash | **Marketplace** (`#00d9ff`, `#ff4757`, `#ffd95a`; optionally `#4d9fff`, `#ff9d5a`) | Already in Mark I + `errorForeground`; keeps inject ↔ theme ↔ listing coherent |
| Map both | Keep dual vars if needed | e.g. `--CORTANA-cyan-brand: #00d9ff` + `--CORTANA-cyan: #00f2ff` (bloom) |

**Practical default for upcoming token edits (doc guidance only):** do **not** replace splash cyan with marketplace `#00d9ff` if that softens the calibrating bloom vs the PNG. Do adopt marketplace yellow/orange/red (and optionally brand cyan as a secondary token) where status UI and theme alignment matter more than still sampling. Green: keep PNG/CC muted greens for “SYSTEM STATUS · Optimal”; use marketplace `#00ff9f` only if we explicitly want listing-neon, not screenshot match.

**Theme JSON:** no change required for this note. Optional later: add exact `#0a1628` / `#050d1a` voids and `#ff9d5a` orange if we unify on marketplace; not clearly beneficial while PNG remains injection authority.
