# God requirements — Phase 6 (LOCKED)

**Authority:** God (Nov 7, 2026). All items below must be **YES** on God's theme — Studio-tier completeness, unlocked locally, **no Gumroad**.

**Canonical plan:** `jarvis_pro_recreation_a1985356`  
**Build mirror:** [`phase6-injection-build.md`](./phase6-injection-build.md)  
**Marketplace extract / Studio→module map:** [`MARKETPLACE-CORTANA-3D-EXTRACT.md`](./MARKETPLACE-CORTANA-3D-EXTRACT.md) (§ GOD LOCKS)

If docs disagree, **the plan wins**; this file is the explicit God feature checklist for Phase 6.

---

## Explicit exclusions

| Marketplace row / wording | Status |
|---------------------------|--------|
| **Active support** / community support | **EXCLUDED** — God was only reading the marketplace list. Do **not** ship, market, or plan “active support.” |
| Fail-safe 3 | Remains **God-as-builder / local-owner** — **not** “active support.” |
| Gumroad / paid unlock | **Forbidden** — everything unlocked locally. |
| Third-party peer / marketplace “support” product | **Forbidden** as a dependency or product claim. |

---

## God feature list — ALL must be YES

| # | God wording | Interpretation / delivery | Status target |
|---|-------------|---------------------------|---------------|
| 1 | **3D theme** | Real depth (parallax / layered z / perspective chrome) — **not** flat visual-only skins | YES |
| 2 | **Real-time animation** | Continuous live motion on HUD / FX / reactors (60fps-class where host allows) | YES |
| 3 | **Active responses** | Activity-aware UI (coding / focus / agent / threat / voice state drives chrome) | YES |
| 4 | **Arc reactor pulses** | Pulsing arc-reactor motif synced to energy / activity | YES |
| 5 | **Peer innovation** | **First-party innovation parity** with marketplace “pure innovation” claims — cutting-edge in-house goals. **NOT** third-party peer support | YES (innovation) / N/A (peer support) |
| 6 | **Real-time tracking** | Coding / energy / session metrics live in HUD | YES |
| 7 | **30% optimized colors** | Marketplace “optimized colors” / eye-strain claim → lock a **calibrated palette**; **“30%”** is God-dictated optimization target vs stock Cursor contrast | YES |
| 8 | **Built-in HUD** | Command Center chrome injected into workbench (not overlay-only) | YES |
| 9 | **Classic CORTANA theme + icon theme** | Classic CORTANA color theme + matching icon theme pack | YES |
| 10 | **Basic HUD** | Studio “basic HUD” tier present (status strips, reactor, core chips) | YES |
| 11 | **Arc reactor + energy** | As on Studio / marketplace — reactor + energy readouts | YES |
| 12 | **EVERY Studio option = YES** | Full Studio column mapped below — all YES on God's theme (local unlock) | YES |

---

## Studio column → God's theme (every option YES)

| Studio / marketplace option | On God's theme | Notes |
|-----------------------------|----------------|-------|
| Classic theme + icons | **YES** | Theme JSON + icon theme |
| Basic HUD / arc / energy | **YES** | Injected chrome |
| Standard performance | **YES** | No paid “perf tier”; ship optimized default |
| Suit Modes | **YES** | Phase 2 packs + inject bridge |
| Particles / arc / streams / glow | **YES** | Phase 2 FX → inject |
| F.R.I.D.A.Y. / TTS / sound | **YES** | Assistant mode + Cursor voice channel + SFX |
| Session Cinema / Stream Pack / Focus Fortress | **YES** | Phase 4 → inject |
| Threat / GitHUD / Dashboard | **YES** | Phase 3 + injected Command Center |
| AI Companion / presets | **YES** | Companion mode + workspace presets |
| Multi-device | **N/A (local)** | Single-machine local install; no cloud multi-device product |
| Stream watermark | **Optional local** | Local toggle only; not a paid/cloud feature |
| Seasonal suits | **YES** | Suit Variants / seasonal packs |
| **Active support** (marketplace row) | **EXCLUDED** | Do not implement or claim |

---

## First-party innovation goals (item 5 — not peer support)

Documented goals for cutting-edge parity (in-repo, God-owned):

- Real depth 3D chrome + live FX (not flat CSS tint alone)
- Activity-aware responses tied to editor/session/agent signals
- Calibrated “30%” palette vs stock Cursor contrast
- Full Studio feature parity unlocked locally without Gumroad
- Injection fail-safes owned by God-as-builder

**Do not** interpret “peer innovation” as Discord/community peer support or a third-party support SLA.

---

## Color optimization lock (item 7)

- Lock a calibrated CORTANA palette in `media/inject/tokens.css` (and theme JSON).
- **“30% optimized colors”** = God-dictated marketing/engineering target: reduce eye-strain / improve contrast comfort ~30% vs stock Cursor defaults (measure via luminance/contrast checklist in visual QA; document baseline vs CORTANA tokens).
- Palette remains cyan/navy Command Center family; do not drift to unrelated themes.

---

## Icon / chrome feasibility (God ask)

### Windows taskbar icon

| Approach | Feasible? | Notes |
|----------|-----------|-------|
| CSS / workbench injection alone | **NO** | Does **not** reliably change the OS taskbar icon |
| Electron / app `.ico` / shortcut | **YES (optional)** | Requires resource/icon patch or shortcut `.ico` — same Admin patch posture + fail-safes as workbench inject |

→ Optional sub-phase **6.I** if God wants taskbar branding.

### Top-left / title bar corner icon + title bar chrome

| Surface | Feasible with inject? | Notes |
|---------|----------------------|-------|
| Title bar **chrome** (colors, height, buttons styling) | **YES when** `window.titleBarStyle` is **custom** | Injected CSS can restyle custom title bar |
| Window / app **icon** in title bar / taskbar | **Not CSS-alone** | Needs resource/icon patch or shortcut `.ico` |

→ Optional sub-phase **6.J** for title-bar chrome (CSS) + optional icon resource patch under same Admin + fail-safe rules.

### Concrete Windows Cursor methods (marketplace-mapping append)

| Goal | Method | Fits inject fail-safes? |
|------|--------|-------------------------|
| Title bar HUD look | `"window.titleBarStyle": "custom"` + CSS on `.monaco-workbench .part.titlebar` / custom-titlebar nodes via `media/inject/hud.css` | **YES** — same workbench patch |
| In-window appicon tint/size | CSS on `.window-appicon` (custom title bar only) | **YES** for style; bitmap swap still needs `.ico` |
| Taskbar / pinned icon | Replace install icons under `C:\Program Files\cursor\resources\app\resources\win32\` (e.g. `code.ico`) and/or set shortcut `.ico`; `Cursor.exe` embeds the process icon | **Optional 6.I** — Admin, backup, restore on disable/update; **not** pure CSS |
| Marketplace Custom CSS parallel | Their FAQ: `CORTANA-3d-effects.css` + Loader + corrupt warning | Ours: extension-owned inject; accept corrupt warning; no third-party Loader |

Cross-ref detail: [`MARKETPLACE-CORTANA-3D-EXTRACT.md`](./MARKETPLACE-CORTANA-3D-EXTRACT.md) § GOD LOCKS.

---

## Studio row → module / inject CSS deliverable (checklist)

| Studio / marketplace row | Local | Module / surface | Inject / CSS deliverable |
|--------------------------|-------|------------------|--------------------------|
| Classic theme + icons | **YES** | `themes/*`, icon/activity assets | Theme JSON + `media/inject/tokens.css` |
| Basic HUD / arc / energy | **YES** | CC shell, `media/arc-reactor.svg` | `media/inject/hud.css` + `boot.css` |
| Standard performance | **YES** | Default FX budget | Inject perf / pause-unfocused |
| Suit Modes | **YES** | `src/suitModes.js` | Suit vars → inject tokens |
| Particles / arc / streams / glow | **YES** | Phase-2 FX | `hud.css` depth + motion (no overlays) |
| F.R.I.D.A.Y. / TTS / sound | **YES** | `src/voiceBridge.js` | Chrome rename + mute hooks |
| Session Cinema / Stream / Focus | **YES** | `src/sessionCinema.js` | Density / dim / watermark classes |
| Threat / GitHUD / Dashboard | **YES** | `threatHints.js`, `gitHud.js`, CC | Injected HUD panels |
| AI Companion / presets | **YES** | Voice/chat + `workspacePresets.js` | Preset → inject class apply |
| Multi-device | **N/A local** | — | No cloud device product |
| Stream watermark | **Optional local** | Stream Pack | Optional watermark CSS |
| Seasonal suits | **YES** | Suit variants | Theme + token packs |
| **Active support** | **EXCLUDED** | — | God-as-builder only |

---

## Marketplace Custom CSS (their product) — short lock

Jarvis 3D marketplace FAQ admits **Custom CSS** (`custom-styles/jarvis-3d-effects.css`, absolute paths, Enable Custom CSS and JS, restart) and treats the **corrupt-install warning** as expected. Marketing “no plugins” conflicts with troubleshooting. We mirror the **pattern** with first-party inject — we do **not** depend on their Loader or VSIX.

---

## Acceptance cross-check

Phase 6 is incomplete until every row in **God feature list** is YES (or explicitly N/A/optional as mapped), Studio column is fully YES (except Active support EXCLUDED), and fail-safe 3 remains God-as-builder — never “active support.”
