# JARVIS Command Center UI

Local Cursor / VS Code extension: **full JARVIS Command Center HUD** with Suit Modes, FX, GitHUD, Threat Fix Hints, Session Cinema, Focus Fortress, Stream Pack, Voice/TTS hooks, F.R.I.D.A.Y. mode, Workspace Presets, and a large **File Map**.

**Visual target (locked):** [`media/reference-command-center.png`](media/reference-command-center.png) is both the **Cursor boot/loading screen** and the **exact** full-UI design target — match pixel composition; do not approximate. Custom CSS / workbench **injection is required**; overlays are **definitively out** (caller: that look is impossible via overlay).

**v0.4.0 baseline:** Prior shell shipped PRO modules; rebuild toward injection + exact `reference-command-center.png` match (see plan `jarvis_pro_recreation_a1985356`).

## Credits & pattern sources

| Source | Link | Role |
|--------|------|------|
| **jarvis.institute** | https://jarvis.institute/ | Pattern source for Command Center composition / Voice Status / Talk to JARVIS |
| **Local reference PNG** | `media/reference-command-center.png` | **Authoritative** boot splash + full UI visual target (exact match) |
| **Jarvis 3D Theme** (NextGenCode) | https://marketplace.visualstudio.com/items?itemName=nextgencode.jarvis-3d-theme | PRO feature *patterns* (Suit Modes, particles/arc/streams, F.R.I.D.A.Y., TTS/SFX, Session Cinema, Stream Pack, Focus Fortress, Threat Fix Hints, GitHUD, presets) |

This extension is a **custom reimplementation** for Cursor/Windows. It does **not** wrap, bundle, or require upstream Jarvis 3D or jarvis.institute binaries. Assets and logic are original to this repo.

## License note

Local / personal tooling under this workspace. Jarvis 3D marketplace listing is freemium (PRO via Gumroad); we reimplemented equivalent capabilities unlocked for local use — we did **not** copy their VSIX, CSS, or proprietary shaders.

## What shipped (PRO map)

| Marketplace PRO idea | Our module |
|----------------------|------------|
| Suit Modes (Mark I / 50 / Endgame / Stealth) | 4 color themes + AI Core suit switcher |
| Particles / Arc pulse / Data Streams / glow | Canvas FX + CSS streams + glow slider |
| F.R.I.D.A.Y. | Tools toggle + chrome rename |
| Voice TTS | Talk to JARVIS → Cursor Voice/Chat; Web Speech announcements |
| Sound Design | Optional UI beeps (mute in Tools) |
| Session Cinema | Timed HUD (injected chrome / Command Center) + keystroke energy |
| Stream Pack | Dense HUD + optional watermark |
| Focus Fortress | Dims nonessential panels |
| Threat Fix Hints | Problems API → Threats panel |
| GitHUD | Live `git` branch/dirty/ahead-behind |
| Dashboard | Full nav shell matching institute layout |
| AI Companion hooks | Chat / Voice commands |
| Workspace Presets | Save/apply suit + mode combo |

### Intentionally different / stripped vs upstreams

- No Gumroad license, trial, or soft-lock paywall
- Custom CSS / workbench injection required; no floating/editor overlays
- Calendar / Knowledge / Workflows panels are stubs until wired
- CPU/Disk gauges remain illustrative; RAM is live from the host
- Voice channel opens **Cursor** voice/chat (not a separate LLM runtime)

## Install in Cursor

```powershell
cursor --install-extension "C:\PS2Recomp\jarvis-cursor-ui" --force
```

Or: **Extensions → … → Install from VSIX…** → `jarvis-cursor-ui-0.4.0.vsix`

Then:

1. Command Palette → **Color Theme** → **JARVIS Mark I** (or Endgame / Mark 50 / Stealth)
2. Or **JARVIS: Apply Active Suit Theme**
3. Open the **JARVIS** activity-bar icon → Command Center + File Map
4. **Talk to JARVIS** / mic → Cursor Voice or Chat

## Commands

- `JARVIS: Suit Mode…`
- `JARVIS: Talk / Start Voice`
- `JARVIS: Toggle Focus Fortress` / `Session Cinema` / `Stream Pack` / `F.R.I.D.A.Y. Mode`
- `JARVIS: Save / Apply Workspace Preset`
- `JARVIS: Refresh HUD`

## Layout

```
jarvis-cursor-ui/
  package.json
  README.md
  themes/          # Command + Mark I/50/Endgame/Stealth
  media/
  src/
    extension.js
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
