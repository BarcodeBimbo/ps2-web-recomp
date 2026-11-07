# CORTANA rebuild status — Admin Enable QA

**When:** Nov 7, 2026 · God rebuild LIVE · Workers A–D  
**Extension:** `C:\PS2Recomp\jarvis-cursor-ui` · package target **0.5.1**  
**Operator:** Joshua (Admin Enable only — workers do not elevate)

## Fail-safes (Worker D — verified in code)

| # | Behavior | Commands / paths |
|---|----------|------------------|
| 1 | Cursor fingerprint change → teardown, disable, notify; **never** auto-re-enable | `reconcileOnActivate` → `disabled-due-to-update` → warning + **Re-enable after verify** → `CORTANA.injection.reenableAfterUpdate` |
| 2 | Missing/corrupt markers or CSS health probe fail → teardown, disable, notify | Activate + ~60s soft re-probe → `health-fail` / periodic disable |
| 3 | Joshua-as-builder | Docs + Admin Enable / reenableAfterUpdate — **not** marketplace Active support |

Smoke: `node scripts/verify-fail-safes.js`

## What each area needs before / during Joshua Admin Enable QA

### A — Splash / boot
- [ ] `media/inject/boot.css` keeps **real PNG** cover (`./CORTANA-boot-splash.png`) — no CSS-only primary
- [ ] Engine stages `media/reference-command-center-2.png` on Enable
- [ ] After Reload: full-bleed CC-2 still → progress/fade → HUD (match `bootMs`)
- [ ] Keep `CORTANA-HEALTH` comment in `boot.css`

### B — HUD (CC-2 one-to-one)
- [ ] `media/inject/hud.css` restyles full workbench chrome toward CC / CC-2
- [ ] No overlays / floating editor HUD
- [ ] Keep `CORTANA-HEALTH` comment in `hud.css`

### C — Themes unison
- [ ] Suit themes + `tokens.css` cyan/navy aligned with inject
- [ ] Apply suit theme after Enable; chrome should not fight inject

### D — Inject engine + package
- [x] Fail-safe wiring + notify status codes fixed
- [x] PNG required on Enable; health probe + soft re-probe
- [x] Ship `C:\PS2Recomp\jarvis-cursor-ui\jarvis-cursor-ui-0.5.1.vsix` (~419 KB; includes CC-2 PNG)
- [ ] Joshua installs / syncs extension (not Program Files by agents)

## Joshua Admin Enable QA steps

1. Install or sync **0.5.1** from  
   `C:\PS2Recomp\jarvis-cursor-ui\jarvis-cursor-ui-0.5.1.vsix`  
   (or copy tree into `%USERPROFILE%\.cursor\extensions\ps2recomp-local.jarvis-cursor-ui-0.5.1`).
2. Quit Cursor **including tray**.
3. **Run Cursor as Administrator** → open `C:\PS2Recomp`.
4. Command Palette → **CORTANA: Injection Health Check** (expect issues if not yet enabled).
5. **CORTANA: Enable Workbench Injection** → Reload when prompted.
6. Dismiss corrupt-install warning (expected).
7. Confirm: CC-2 PNG splash → HUD chrome; no overlay panels.
8. **CORTANA: Injection Status** → `enabled/active`, markers valid, splash staged.
9. Optional fail-safe smoke: break a marker or fake fingerprint → must auto-disable + offer Re-enable (never silent re-patch).
10. Quit Admin Cursor; run normally. Patch persists until Disable or Cursor update.

Full path: [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md) · master: [`CORTANA-THEME-MASTER.md`](./CORTANA-THEME-MASTER.md)
