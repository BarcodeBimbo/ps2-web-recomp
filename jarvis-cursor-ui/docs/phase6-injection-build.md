# Phase 6 — Injection build plan

> ## PAUSED
>
> **Phase 6 is PAUSED** at a safe checkpoint: scaffold on disk (`workbenchInject.js`, `media/inject/*`, `package.json` injection commands); full Studio HUD verify **pending**.
>
> Do **not** launch Enable injection against Program Files while paused.
>
> **Resume / theme authority:** [`JARVIS-THEME-MASTER.md`](./JARVIS-THEME-MASTER.md)

**Source of truth:** plan `jarvis_pro_recreation_a1985356` (Phases 1–5 completed; Phase 6 **PAUSED**). If this doc disagrees with the plan locks, **the plan wins**.

**God feature lock:** [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md) — Studio-tier completeness; all God-listed features **YES** on his theme; unlocked locally; **no Gumroad**; **Active support EXCLUDED**.

## Locks

| Item | Value |
|------|--------|
| Mechanism | Custom CSS / workbench injection **required** |
| Overlays | **Forbidden** (no floating / editor-wide overlay HUD) |
| Boot splash | `media/reference-calibrating-splash.png` (638×480) |
| Full chrome | `media/reference-command-center.png` + `-2.png` (1024×573) |
| Fail-safes | (1) auto-disable on Cursor update (2) disable on patch/probe fail (3) **God-as-builder / local-owner** — **NOT** marketplace “Active support” |
| Licensing | All Studio / PRO options unlocked locally — **no Gumroad** |
| Studio parity | **EVERY Studio option = YES** on God's theme (multi-device N/A local; stream watermark optional local) |
| Active support | **EXCLUDED** — God was only reading the marketplace list |
| Peer innovation | First-party innovation parity goals — **NOT** third-party peer support |

## God YES feature checklist (all required)

1. **3D theme** — real depth (not flat visual only)
2. **Real-time animation**
3. **Active responses** — activity-aware
4. **Arc reactor pulses**
5. **Peer innovation** → first-party innovation goals (not peer support)
6. **Real-time tracking** — coding / energy / session metrics
7. **30% optimized colors** — calibrated palette; God “30%” vs stock Cursor contrast
8. **Built-in HUD**
9. **Classic Jarvis theme + icon theme**
10. **Basic HUD**
11. **Arc reactor + energy**
12. **EVERY Studio option = YES** (classic+icons, basic HUD/arc/energy, standard perf, Suit Modes, particles/arc/streams/glow, F.R.I.D.A.Y./TTS/sound, Session Cinema/Stream Pack/Focus Fortress, Threat/GitHUD/Dashboard, AI Companion/presets, multi-device N/A local, stream watermark optional local, seasonal suits)

See full Studio column map in [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md).

## Gap vs v0.4.0

Phases 1–5 modules exist (`suitModes`, `gitHud`, `threatHints`, `sessionCinema`, `workspacePresets`, `voiceBridge`, themes, Command Center **webview**). Presentation is still activity-bar webview-first with an in-webview calibrating `#splash`. Injection scaffolding, workbench boot PNG cover, `jarvis.injection.*` settings, the three fail-safes, inject-path **3D/anim/arc/tracking/30% palette/Studio YES** completeness, and classic+icon finish on the inject path are **missing**. README still incorrectly names command-center PNG as boot — sync to plan. Do **not** add Active support.

## Ordered sub-phases

1. **6.3.A Scaffold** — `workbenchInject.js`, `media/inject/{tokens,boot,hud}.css` (tokens lock 30% palette), settings/commands, `extension.js` gate
2. **6.3.B Fail-safe 1** — fingerprint in `globalState`; version change → disable + teardown + notify
3. **6.3.C Fail-safe 2** — health probe; fail → disable + teardown + notify; soft re-probe
4. **6.3.D Fail-safe 3** — README God-as-builder / local-owner (**not** Active support; no third-party support dep)
5. **6.3.E Boot** — full-bleed calibrating PNG cover → hold `bootMs` → reveal HUD
6. **6.3.F HUD** — inject all command-center regions; **3D depth**, live anim, activity-aware responses, arc pulses + energy, real-time tracking; bridge all Studio YES modules; classic theme + icon theme
7. **6.3.G Demote** — webview not primary when inject on; no overlays; Active support EXCLUDED in docs
8. **6.3.H Verify + package** — PNG QA, Studio YES checklist, fail-safe tests, bump `0.5.0`, VSIX
9. **6.3.I Optional** — Windows taskbar / app `.ico` (CSS alone **cannot**; Admin resource/shortcut patch + fail-safes)
10. **6.3.J Optional** — Title bar chrome via inject when `titleBarStyle` is custom; title/taskbar **icon** needs resource/shortcut `.ico` (same Admin + fail-safes)

## Icon / chrome feasibility (God ask)

| Target | CSS workbench inject alone? | Path if scheduled |
|--------|----------------------------|-------------------|
| Windows **taskbar** icon | **NO** | Electron/app `.ico` or shortcut `.ico` — optional **6.I**, same Admin patch posture + fail-safes |
| Title bar **chrome** (colors/buttons) | **YES** when `window.titleBarStyle` is **custom** | Injected CSS — optional **6.J** |
| Title bar / app **icon** | **NO** (not CSS-alone) | Resource/icon patch or shortcut — optional **6.J** with 6.I |

## Scaffold status — **PAUSED** (safe checkpoint)

Scaffold intact on disk; **Enable injection against Program Files is deferred** until Phase 6 resumes per [`JARVIS-THEME-MASTER.md`](./JARVIS-THEME-MASTER.md).

**Workers do not elevate.** Admin Enable remains **God-only** when resumed — see [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md). Do **not** run Enable during this pause.

## Exact first build steps

1. ~~Confirm locks~~ ✓
2. ~~`workbenchInject.js`~~ ✓
3. ~~`media/inject/{tokens,boot,hud}.css`~~ ✓
4. ~~settings/commands + `extension.js`~~ ✓
5. ~~Fail-safes 1–3 in engine + God-as-builder docs~~ ✓
6. **PAUSED** — Admin Enable deferred (do not run against Program Files)
7. On resume: HUD Studio YES polish + full verify (3D/anim/arc/tracking)
8. Demote webview / package iterate after Joshua confirms splash+chrome live
9. Optional 6.I / 6.J only if God schedules

**Do not** Enable while paused. **Do not** build overlays. **Do not** implement Active support.

## God-only decisions (defaults if silent)

| ID | Topic | Default |
|----|--------|---------|
| D1 | Boot asset | **Resolved** — calibrating splash |
| D2 | Inject host | **Resolved** — Rank-1 Custom CSS Loader in-repo |
| D3 | Legacy Command Center webview | Fallback only (`jarvis.injection.fallbackWebview` default false) |
| D4 | Install-dir write / elevation | **LOCKED:** Workers soft-fail only; **Joshua runs Admin Enable manually** — see `GOD-ADMIN-ENABLE.md` |
| D5 | Fingerprint | `vscode.version` + product.json version when readable (± workbench hash) |
| D6 | Studio YES / no Gumroad | **Resolved** — full Studio column YES; unlocked locally |
| D7 | Active support | **Resolved — EXCLUDED**; fail-safe 3 = God-as-builder only |
| D8 | Taskbar / title icons | Optional 6.I / 6.J; CSS alone ≠ OS taskbar icon |

## Acceptance (abbreviated)

Injection-only path; calibrating boot full-bleed; chrome matches refs; **all God YES items** (3D, anim, active responses, arc pulses/energy, tracking, 30% palette, built-in+basic HUD, classic+icons, full Studio column); Active support EXCLUDED; peer innovation = first-party goals; no Gumroad; fail-safes 1–2 tear down cleanly; README documents God-as-builder (**not** active support); disable restores stock; PRO modules wired or explicitly gated; optional 6.I/6.J only if scheduled and correctly scoped (CSS ≠ taskbar icon).

## File touch list

- **CREATE:** `src/workbenchInject.js`, `media/inject/tokens.css`, `boot.css`, `hud.css` (+ optional `hud.js`)
- **CREATE/UPDATE:** `docs/GOD-REQUIREMENTS-PHASE6.md`
- **EDIT:** `src/extension.js`, `src/commandCenterView.js`, `package.json`, `README.md`
- **USE:** calibrating PNG (boot), command-center PNGs (chrome QA)
- **KEEP / complete:** `themes/*`, icon theme, phase 1–5 module sources
- **OPTIONAL:** app/shortcut `.ico` patch helpers if 6.I / 6.J scheduled

## Sibling docs

- `docs/GOD-REQUIREMENTS-PHASE6.md` — **God YES checklist**, exclusions, icon feasibility
- `docs/injection-audit.md` — host mechanics (optional)
- `docs/visual-spec.md` — pixel/region spec (optional)
