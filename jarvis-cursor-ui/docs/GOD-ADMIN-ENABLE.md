# God Admin Enable — Phase 6 scaffold ready

Workers **cannot elevate**. Joshua runs Admin Enable manually. Scaffold is ready **now**. Parallel polish continues and must **not** block this gate.

## Already done (workers)

- Source: `C:\PS2Recomp\cortana-cursor-ui` **v0.5.2**
- `src/workbenchInject.js` — Rank-1 patch + 3 fail-safes + **product.json checksum sync** (suppresses corrupt toast)
- `media/inject/{tokens,boot,hud}.css` — CC-2 PNG boot + chrome
- Commands wired in `extension.js` / `package.json`
- QA checklist: [`REBUILD-STATUS.md`](./REBUILD-STATUS.md)

## Joshua steps (fast path)

1. **Install / sync 0.5.2** to  
   `%USERPROFILE%\.cursor\extensions\ps2recomp-local.cortana-cursor-ui-0.5.2`  
   (or install the VSIX `cortana-cursor-ui-0.5.2.vsix`).  
   **Reload Window** once (or skip to step 2 if you prefer a clean Admin launch).  
   Re-sync later if needed: copy from `C:\PS2Recomp\cortana-cursor-ui` or  
   `cursor --install-extension "C:\PS2Recomp\cortana-cursor-ui" --force`.

2. **Quit Cursor** completely.

3. **Relaunch Cursor as Administrator** (right-click → Run as administrator).  
   Needed once to write `C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench\workbench.html`.

4. Command Palette → **CORTANA: Enable Workbench Injection**

5. Prompt → **Reload Window**

6. Expect **Command Center PNG** splash (`reference-command-center-2.png` staged beside workbench) full-bleed briefly, then navy/cyan chrome.  
   **Corrupt-install toast should be suppressed** — Enable syncs `product.json` workbench checksum. If it still appears, re-run Enable as Admin once.

7. Optional: **CORTANA: Injection Status** / **CORTANA: Injection Health Check**

8. After success, quit Admin Cursor and run normally. Patch stays until Disable or Cursor update (fail-safe auto-disables).

## Disable (Admin once)

**CORTANA: Disable Workbench Injection** → Reload.

## Worker rule

Do **not** wait for Enable. Do **not** attempt elevation. Soft-fail with Admin message only.

## IDE-only boot (no Startup exe)

Splash is workbench-injection only. Prefer opening folder `C:\PS2Recomp` (not dual-open with `E:\PS2Recomp.code-workspace`). Details: [`STARTUP-IDE-ONLY.md`](STARTUP-IDE-ONLY.md).
