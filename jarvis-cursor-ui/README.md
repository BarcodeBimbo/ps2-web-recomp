# JARVIS Command Center UI

Local Cursor / VS Code extension: **full JARVIS Command Center HUD** via **Custom CSS workbench injection**, with Suit Modes, FX, GitHUD, Threat Fix Hints, Session Cinema, Focus Fortress, Stream Pack, Voice/TTS hooks, F.R.I.D.A.Y. mode, Workspace Presets, and a large **File Map**.

**Status:** Phases 1–5 complete. **Phase 6 (injection) scaffold shipped in v0.5.0** — see plan `jarvis_pro_recreation_a1985356`.

**Visual targets (locked):** Boot/loading splash **and** the entire UI look = [`media/reference-calibrating-splash.png`](media/reference-calibrating-splash.png) (calibrating aesthetic). Command-center PNGs are supporting composition refs only. Custom CSS / workbench **injection is required**; overlays are **definitively out**.

**v0.5.0:** Injection packaging + activation wiring (`workbenchInject` enable/disable/reconcile/health). Default `jarvis.injection.enabled` = **false** until Joshua enables.

**Boot path:** Calibrating splash runs on **Cursor IDE launch via workbench injection** (`media/inject/boot.css` + `jarvis.injection.bootMs`). There is **no** separate Jarvis splash `.exe` and **no** Windows Startup shortcut for splash. See [`docs/STARTUP-IDE-ONLY.md`](docs/STARTUP-IDE-ONLY.md).

## Credits & pattern sources

| Source | Link | Role |
|--------|------|------|
| **jarvis.institute** | https://jarvis.institute/ | Pattern source for Command Center composition / Voice Status / Talk to JARVIS |
| **Boot + UI look PNG** | `media/reference-calibrating-splash.png` | **Authoritative** Cursor boot splash **and** entire UI visual target (calibrating aesthetic) |
| **Command Center PNGs** | `media/reference-command-center.png`, `media/reference-command-center-2.png` | Supporting composition refs (not the primary look lock) |
| **Jarvis 3D Theme** (NextGenCode) | https://marketplace.visualstudio.com/items?itemName=nextgencode.jarvis-3d-theme | PRO feature *patterns* (Suit Modes, particles/arc/streams, F.R.I.D.A.Y., TTS/SFX, Session Cinema, Stream Pack, Focus Fortress, Threat Fix Hints, GitHUD, presets) |

This extension is a **custom reimplementation** for Cursor/Windows. It does **not** wrap, bundle, or require upstream Jarvis 3D, jarvis.institute binaries, or any third-party Custom CSS marketplace extension. Assets and logic are original to this repo.

## Support model

**God (local owner)** builds, fixes, and rebuilds this extension. There is **no outside/vendor support dependency** and **no third-party Custom CSS extension required**. Fail-safes exist so Cursor updates do not silently leave a broken patch in place; God re-enables after verify.

## License note

Local / personal tooling under this workspace. Jarvis 3D marketplace listing is freemium (PRO via Gumroad); we reimplemented equivalent capabilities unlocked for local use — we did **not** copy their VSIX, CSS, or proprietary shaders.

## What shipped (PRO map)

| Marketplace PRO idea | Our module |
|----------------------|------------|
| Suit Modes (Mark I / 50 / Endgame / Stealth) | 4 color themes + AI Core suit switcher |
| Particles / Arc pulse / Data Streams / glow | Canvas FX + CSS streams + glow slider (injected chrome) |
| F.R.I.D.A.Y. | Tools toggle + chrome rename |
| Voice TTS | Talk to JARVIS → Cursor Voice/Chat; Web Speech announcements |
| Sound Design | Optional UI beeps (mute in Tools) |
| Session Cinema | Timed HUD (injected chrome) + keystroke energy |
| Stream Pack | Dense HUD + optional watermark |
| Focus Fortress | Dims nonessential panels |
| Threat Fix Hints | Problems API → Threats panel |
| GitHUD | Live `git` branch/dirty/ahead-behind |
| Dashboard | Full nav shell (injection primary; webview optional fallback) |
| AI Companion hooks | Chat / Voice commands |
| Workspace Presets | Save/apply suit + mode combo |

### Intentionally different / stripped vs upstreams

- No Gumroad license, trial, or soft-lock paywall
- Custom CSS / workbench injection required; floating/editor overlays are **out**
- Boot + entire UI look = `reference-calibrating-splash.png`; command-center PNGs are supporting only
- Calendar / Knowledge / Workflows panels are stubs until wired — **visual chrome must still match the calibrating aesthetic**
- CPU/Disk gauges remain illustrative until wired; RAM is live from the host
- Voice channel opens **Cursor** voice/chat (not a separate JARVIS TTS persona); UI copy is full JARVIS branding

## Injection fail-safes (three)

1. **Auto-disable on Cursor update** — `reconcileOnActivate` detects an update / install change and disables the patch so a stale inject does not break the workbench.
2. **Disable on health / patch break** — health-fail or broken markers disable injection; status surfaces the reason.
3. **God re-enable after verify** — no automatic silent re-patch; use **JARVIS: Re-enable Injection After Update** (or Enable) after God confirms Cursor is healthy. God builds/fixes/rebuilds — no vendor support gap.

**Integrity warning:** Cursor may show a corrupt-install / integrity warning after workbench patch. **God accepts reinstall / re-enable**; do **not** treat that dialog as a blocker to the injection approach.

**Admin:** Enabling injection may require **Admin once** (write under Program Files). Run Cursor or the enable path elevated if you hit `EACCES`.

## Install in Cursor (v0.5.0)

```powershell
cursor --install-extension "C:\PS2Recomp\jarvis-cursor-ui" --force
```

Or: **Extensions → … → Install from VSIX…** → `jarvis-cursor-ui-0.5.0.vsix`

Then:

1. Command Palette → **Color Theme** → **JARVIS Mark I** (or Endgame / Mark 50 / Stealth)
2. Or **JARVIS: Apply Active Suit Theme**
3. **JARVIS: Enable Workbench Injection** (Admin once if needed) → **Reload Window** when prompted
4. Optional: **JARVIS: Injection Health Check** / **Injection Status**
5. Open the **JARVIS** activity-bar icon → File Map (Command Center webview is demoted when injection is primary and `jarvis.injection.fallbackWebview` is false)
6. **Talk to JARVIS** / mic → Cursor Voice or Chat

Settings (defaults):

| Setting | Default | Notes |
|---------|---------|--------|
| `jarvis.injection.enabled` | `false` | Flip via Enable command / after reconcile (God + Admin); leave false until then |
| `jarvis.injection.bootMs` | `1200` | Calibrating splash settle time → injected `--jarvis-boot-ms` |
| `jarvis.injection.fallbackWebview` | `false` | Keep false so injection stays primary HUD |

## Commands

- `JARVIS: Suit Mode…`
- `JARVIS: Talk / Start Voice`
- `JARVIS: Toggle Focus Fortress` / `Session Cinema` / `Stream Pack` / `F.R.I.D.A.Y. Mode`
- `JARVIS: Save / Apply Workspace Preset`
- `JARVIS: Refresh HUD`
- `JARVIS: Enable Workbench Injection`
- `JARVIS: Disable Workbench Injection`
- `JARVIS: Re-enable Injection After Update`
- `JARVIS: Injection Health Check`
- `JARVIS: Injection Status`

## Change log

### 0.5.0 — Phase 6 injection scaffold

- Package + activation wiring for Custom CSS workbench injection (`./workbenchInject`)
- Config: `jarvis.injection.enabled` / `bootMs` / `fallbackWebview`
- Commands: enable, disable, re-enable after update, health check, status
- Activate: `reconcileOnActivate` with warning + Re-enable after verify when disabled-due-to-update or health-fail
- When injection is primary, Command Center webview is not force-focused as the HUD
- README locks: calibrating splash = boot **and** UI look; injection required; overlays out; three fail-safes; God support model
- IDE-only boot: `bootMs` → `--jarvis-boot-ms` in inject bundle; docs `STARTUP-IDE-ONLY.md` (no Startup splash exe)

### 0.4.0 — Phases 1–5 baseline

- PRO modules: suit modes, FX, GitHUD, threats, cinema, fortress, stream pack, voice hooks, presets, File Map

## Layout

```
jarvis-cursor-ui/
  package.json
  README.md
  themes/          # Command + Mark I/50/Endgame/Stealth
  media/
  src/
    extension.js
    workbenchInject.js   # Phase 6 (sibling-owned)
    commandCenterView.js
    fileMapProvider.js
    suitModes.js
    voiceBridge.js
    gitHud.js
    threatHints.js
    sessionCinema.js
    workspacePresets.js
```

Does not modify PS2 recomp runtime — this folder is standalone.
