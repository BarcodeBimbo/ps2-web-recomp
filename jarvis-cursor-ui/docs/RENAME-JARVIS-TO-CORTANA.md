# Rename: Jarvis → Cortana

**Date:** Nov 7, 2026 · **Ordered by:** God · **Operator:** Joshua  
**Constraint:** Side work — did **not** rewrite hot files mid-edit by the four rebuild workers.

## Product rename rules

| Keep | Change |
|------|--------|
| **God** (team / account) | — |
| **Joshua / Josh** (person) | — |
| External credits: `jarvis.institute`, marketplace **Jarvis 3D** / `nextgencode.jarvis-3d-theme` | Unchanged (upstream product names) |
| Our product / assistant / UI brand | **Jarvis / JARVIS / jarvis → Cortana / CORTANA / cortana** |

## Done now (side pass)

- All `docs/*.md` product brand → **Cortana / CORTANA**; master file moved to **`docs/CORTANA-THEME-MASTER.md`**
- `README.md`, `MASTER-CONTEXT.md`, plan `jarvis_pro_recreation_a1985356.plan.md` (content brand)
- Cooler modules: `suitModes.js`, `voiceBridge.js`, `sessionCinema.js`, `workspacePresets.js`, `fileMapProvider.js`
- Helper scripts: `enable-workbench-inject-standalone.js`, `verify-fail-safes.js`, `_gen-themes-worker-c.js`, last-run json
- **Preserved:** `jarvis.institute`, marketplace **Jarvis 3D** credits, on-disk folder `jarvis-cursor-ui\`, live setting/command **IDs** `jarvis.*` until hot pass (display brand already Cortana in docs)

## Deferred until rebuild workers finish (hot files)

Do **not** run while Workers A–D are writing these. After they complete:

```powershell
cd C:\PS2Recomp\jarvis-cursor-ui
powershell -ExecutionPolicy Bypass -File .\scripts\rename-jarvis-to-cortana-hotfiles.ps1
```

That script updates:

- `media/inject/{hud,tokens,boot}.css`, `hud-markup.html`
- `src/workbenchInject.js`, `extension.js`, `commandCenterView.js`
- `package.json` (display names, command **titles**, theme labels; IDs become `cortana.*`)
- `themes/jarvis-*.json` → `themes/cortana-*.json` + path fixes

Then: rebuild VSIX → Admin Cursor → **Disable** then **Enable** injection (markers may say CORTANA) → Reload.

## Intentionally not renamed yet

| Item | Why |
|------|-----|
| Folder `jarvis-cursor-ui\` | Path breaks installs/workers mid-flight; rename later if desired |
| Plan filename `jarvis_pro_recreation_*.plan.md` | Cursor plan id; content already says Cortana |
| Installed extension under `~\.cursor\extensions\ps2recomp-local.jarvis-cursor-ui-*` | Reinstall after hot-file rename |
| Program Files inject markers | Re-Enable after hot rename |

## Display command titles (after hot pass)

Example: **Cortana: Enable Workbench Injection** (was JARVIS: …).
