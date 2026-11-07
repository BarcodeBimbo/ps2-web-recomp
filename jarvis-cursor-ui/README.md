# Cursor Command Center UI

Local Cursor / VS Code extension: **Command Center layout + cyan HUD theme + large File Map**.

Visual structure is inspired by [jarvis.institute](https://jarvis.institute/) (Microsoft Store Windows assistant, ~$9.99 lifetime).  
**Voice and copy are Cursor’s coding agent** — not JARVIS / Iron Man persona, wake-words, or “Talk to Jarvis” branding.

> Note: `jarvis.institution` / `www.jarvis.institution` do **not** resolve. The product site is **`https://jarvis.institute`**.

## Marketplace research (context)

| Reference | Role |
|-----------|------|
| [JARVIS HUD](https://marketplace.visualstudio.com/items?itemName=iareebahmad.jarvis-hud) | Closest free cyan-on-near-black *theme* |
| [Jarvis 3D](https://marketplace.visualstudio.com/items?itemName=nextgencode.jarvis-3d-theme) | Heavier HUD / effects product |
| [jarvis.institute](https://jarvis.institute/) | App blueprint: Command Center, AI Core, agents, system monitor, bottom interaction bar |

None of the marketplace themes ship a large custom **File Map** sidebar — this extension adds one.

## What we took from jarvis.institute (structure only)

- Activity-bar **Command Center** container
- Overview cards: workspace pulse, core status, active lanes, quick actions, live feed
- Separate **File Map** view (holographic tree) as the project-structure surface
- Dark navy + cyan accent panels

## What we intentionally changed

| jarvis.institute | This extension |
|------------------|----------------|
| JARVIS / Iron Man voice | **Cursor coding-agent voice** |
| “Talk to Jarvis”, wake word | Neutral Cursor CTAs (“Ready when you are…”) |
| Full Electron agent product | Theme + sidebar webviews for Cursor |

## Install in Cursor

```powershell
# From this folder (Developer: Install Extension from Location), or:
cursor --install-extension "C:\PS2Recomp\jarvis-cursor-ui"
```

Then:

1. Command Palette → **Color Theme** → **JARVIS Command** (palette name; UI copy is Cursor)
2. Or run **Command Center: Apply Recommended Theme**
3. Open the **Command Center** activity-bar icon → **Command Center** + **File Map**

## Layout

```
jarvis-cursor-ui/
  package.json
  README.md
  themes/jarvis-command-color-theme.json
  media/
  src/
    extension.js
    commandCenterView.js
    fileMapProvider.js
```

Does not modify PS2 recomp runtime or project sources — this folder is standalone.
