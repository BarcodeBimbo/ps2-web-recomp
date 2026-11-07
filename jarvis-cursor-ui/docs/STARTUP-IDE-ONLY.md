# Startup — IDE-only (no separate splash exe)

Recomp / JARVIS boot is **Cursor IDE launch only**. There is **no** Windows Startup shortcut, **no** standalone Jarvis splash `.exe`, and **no** second process for the calibrating cover.

## Root cause (second IDE window)

Not a Startup-folder `cursor.exe` shortcut (none present). Cursor **session restore** had tracked multiple windows:

1. folder `C:\PS2Recomp`
2. workspace `E:\PS2Recomp.code-workspace` (same tree)
3. empty-window backups (Agents/glass empty sessions)

On reload, `windowsState.openedWindows` restored the folder **and** an empty window → looked like a brand-new IDE. Suspect worker `6cb14ea4` did **not** launch `cursor C:\PS2Recomp` or create Startup `.lnk` files; the dual restore state predated its settings write.

## Preferred workspace

| Prefer | Avoid for dual-window |
|--------|------------------------|
| Folder `C:\PS2Recomp` | Opening `E:\PS2Recomp.code-workspace` **and** the folder at once |
| Reload Window in-session | `Ctrl+Shift+N` / **Open IDE** (opens another IDE window) |

User settings use `window.restoreWindows: "one"` and `window.openFoldersInNewWindow: "off"`. Cursor restore state was trimmed so backup restore targets **`file:///c%3A/PS2Recomp`** only (`.code-workspace` + emptyWindows cleared from `backupWorkspaces`; `windowsState` kept one folder window).

If a second window still appears after an old session: close the extra window, leave only `C:\PS2Recomp`, then quit Cursor once so restore remembers a single folder window.

## Calibrating splash (injection-scoped)

Splash appears **inside** the Cursor workbench after **JARVIS: Enable Workbench Injection** (Admin once) + Reload:

| Piece | Role |
|-------|------|
| `media/inject/boot.css` | Full-bleed calibrating cover lifecycle (`--jarvis-boot-ms`) |
| `media/reference-calibrating-splash.png` | Staged beside `workbench.html` as `jarvis-boot-splash.png` |
| `jarvis.injection.bootMs` | Injected into CSS as `--jarvis-boot-ms` (User default **1200**) |
| `jarvis.injection.enabled` | Left **`false`** until God enables (do not force-enable without Admin) |

### God resume (when ready)

1. Follow [`GOD-ADMIN-ENABLE.md`](GOD-ADMIN-ENABLE.md) (elevate Cursor once).
2. Command Palette → **JARVIS: Enable Workbench Injection** → Reload.
3. Expect calibrating splash briefly, then navy/cyan HUD. Integrity warning is expected.

Workers must **not** flip `jarvis.injection.enabled` to `true` or write under Program Files.

## Chat / aux panel on launch

Cursor has **no reliable built-in** “never open chat on launch” toggle. Best-effort User settings applied:

- `workbench.auxiliaryBar.visible`: `false`
- `workbench.panel.opensMaximized`: `never`
- `workbench.startupEditor`: `none`
- `workbench.sideBar.location`: `left`

If Agent/Chat still opens once: close it (`Ctrl+Alt+B`), quit, and relaunch — layout usually sticks. Do **not** add a Startup-folder helper exe for this.

## Confirmation

Splash = **IDE workbench injection only** (`boot.css` + staged PNG via `workbenchInject`). Not a separate executable path.
