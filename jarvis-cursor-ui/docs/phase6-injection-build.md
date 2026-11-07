# Phase 6 — Injection build plan

**Source of truth:** plan `jarvis_pro_recreation_a1985356` (Phases 1–5 completed; Phase 6 NEXT). If this doc disagrees with the plan locks, **the plan wins**.

## Locks

| Item | Value |
|------|--------|
| Mechanism | Custom CSS / workbench injection **required** |
| Overlays | **Forbidden** (no floating / editor-wide overlay HUD) |
| Boot splash | `media/reference-calibrating-splash.png` (638×480) |
| Full chrome | `media/reference-command-center.png` + `-2.png` (1024×573) |
| Fail-safes | (1) auto-disable on Cursor update (2) disable on patch/probe fail (3) God-as-builder / local-owner support |

## Gap vs v0.4.0

Phases 1–5 modules exist (`suitModes`, `gitHud`, `threatHints`, `sessionCinema`, `workspacePresets`, `voiceBridge`, themes, Command Center **webview**). Presentation is still activity-bar webview-first with an in-webview calibrating `#splash`. Injection scaffolding, workbench boot PNG cover, `jarvis.injection.*` settings, and the three fail-safes are **missing**. README still incorrectly names command-center PNG as boot — sync to plan.

## Ordered sub-phases

1. **6.3.A Scaffold** — `workbenchInject.js`, `media/inject/{tokens,boot,hud}.css`, settings/commands, `extension.js` gate
2. **6.3.B Fail-safe 1** — fingerprint in `globalState`; version change → disable + teardown + notify
3. **6.3.C Fail-safe 2** — health probe; fail → disable + teardown + notify; soft re-probe
4. **6.3.D Fail-safe 3** — README God-as-builder / local-owner (no third-party support dep)
5. **6.3.E Boot** — full-bleed calibrating PNG cover → hold `bootMs` → reveal HUD
6. **6.3.F HUD** — inject all command-center regions; bridge PRO modules
7. **6.3.G Demote** — webview not primary when inject on; no overlays
8. **6.3.H Verify + package** — PNG QA, fail-safe tests, bump `0.5.0`, VSIX

## Exact first build steps

1. Confirm locks (boot = calibrating; chrome = command-center; no overlays).
2. Create `src/workbenchInject.js` skeleton (`onActivateGate`, fingerprint, inject, teardown, health stubs).
3. Create `media/inject/tokens.css` + `boot.css` (calibrating cover only).
4. Add `jarvis.injection.enabled` / `bootMs` / `fallbackWebview` + enable/disable/re-enable/health commands; wire `extension.js`.
5. Implement fail-safes 1–2 on skeleton; README fail-safe 3 + fix boot/chrome wording.
6. Manual test: enable → boot → disable restores stock; fake fingerprint → auto-disable; break marker → auto-disable.
7. Then `hud.css` / HUD DOM + bridge modules.
8. Demote `commandCenterView`; package when acceptance passes.

**Do not** port entire webview HTML first. **Do not** build overlays. Order: scaffold → fail-safes → boot → HUD → demote → package.

## God-only decisions (defaults if silent)

| ID | Topic | Default |
|----|--------|---------|
| D1 | Boot asset | **Resolved** — calibrating splash |
| D2 | Inject host | In-repo workbench patch loading our CSS/JS (no required third-party CSS extension) |
| D3 | Legacy Command Center webview | Fallback only (`jarvis.injection.fallbackWebview` default false) |
| D4 | Install-dir write / elevation | Soft-fail clear message; never half-patch |
| D5 | Fingerprint | `vscode.version` + product.json version when readable (± workbench hash) |

## Acceptance (abbreviated)

Injection-only path; calibrating boot full-bleed; chrome matches refs; fail-safes 1–2 tear down cleanly; README documents God-as-builder; disable restores stock; PRO modules wired or explicitly gated.

## File touch list

- **CREATE:** `src/workbenchInject.js`, `media/inject/tokens.css`, `boot.css`, `hud.css` (+ optional `hud.js`)
- **EDIT:** `src/extension.js`, `src/commandCenterView.js`, `package.json`, `README.md`
- **USE:** calibrating PNG (boot), command-center PNGs (chrome QA)
- **KEEP:** `themes/*`, phase 1–5 module sources

## Sibling docs (optional)

- `docs/injection-audit.md` — host mechanics
- `docs/visual-spec.md` — pixel/region spec
