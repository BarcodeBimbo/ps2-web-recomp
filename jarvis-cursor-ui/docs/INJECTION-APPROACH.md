# JARVIS workbench injection — approach audit (phase 6)

**Date:** 2026-11-07  
**Scope:** How to implement Custom CSS / workbench injection for Cursor on Windows inside `jarvis-cursor-ui`, with fail-safes.  
**Status:** Audit only — no full injection implemented.

---

## 0) Current state (what activate does today)

| Path | Role | Injects workbench? |
|------|------|--------------------|
| `src/extension.js` `activate()` | Registers webview providers, suit/theme commands, cinema toggles, presets, voice, file watchers | **No** |
| `src/commandCenterView.js` | Webview HUD (sidebar) | Overlay-style presentation only |
| `src/fileMapProvider.js` | Webview File Map | No |
| `themes/*.json` | Color theme tokens | Theme tokens only — **cannot** match `reference-command-center.png` |
| Installed copy | `C:\Users\joshy\.cursor\extensions\ps2recomp-local.jarvis-cursor-ui-0.4.0\` | Same as source; no inject module |

**Verdict:** v0.4.0 ships themes + sidebar webviews. Nothing patches Cursor’s `workbench.html` / CSS / JS. Phase 6 must add a first-party inject module; overlays remain forbidden for the visual target.

---

## 1) Cursor install facts (this machine)

| Item | Value |
|------|--------|
| App | `C:\Program Files\cursor\` (DisplayVersion **3.29.9**) |
| `product.json` | `version=3.29.9`, `commit=306d153d51d714882ab7b1bc49649cab624e8a30`, `quality=stable` |
| Workbench HTML | `C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench\workbench.html` (~1824 B) |
| Sibling | `workbench.js` (module entry) |
| Checksums | `product.json` lists `vs/code/electron-sandbox/workbench/workbench.html` (and main.js/css) — **any patch triggers integrity warning** |
| ACL | `BUILTIN\Users:(RX)` — **write requires Admin** (or ACL grant) |
| Patch markers today | **None** — pristine stock HTML |
| User dir | `C:\Users\joshy\AppData\Roaming\Cursor\` — no `vscode_custom_css` / APC settings in use |
| CSP note | `style-src 'self' 'unsafe-inline'` → **inlined CSS OK**; `require-trusted-types-for 'script'` + Cursor-specific trusted-types → **raw JS injection is harder / riskier** than CSS |

Upstream Custom CSS Loader already knows Cursor: it probes `workbench-apc-extension.html` and `electron-sandbox/workbench/workbench.html` (present here).

---

## 2) Ranked injection approaches (phase 6)

### Rank 1 — **Recommended:** First-party “Custom CSS Loader” pattern (extension-owned)

**Pattern:** Own a `workbenchInject.js` that:

1. Resolves app root → `…/electron-sandbox/workbench/workbench.html` (fallback candidates like be5invis).
2. On **Enable:** backup pristine HTML → insert **marked** inline `<style>` (+ later optional guarded `<script>` / boot CSS) before `</head>`.
3. On **Disable / fail-safe:** restore from backup (or strip markers if backup missing).
4. Persist `jarvis.injection.enabled`, Cursor `version`+`commit`, backup path, marker UUID in `globalState`.

**Why #1**

- Extension **owns** enable/disable → fail-safes 1–2 are natural.
- Matches locked mechanism (Custom CSS / workbench injection).
- Proven on Cursor (be5invis / CSS Injector / theme glow patches).
- CSS-first stays inside CSP (`unsafe-inline`); avoid stripping CSP meta unless JS boot truly needs it.
- Smaller blast radius than APC multi-file patches.

**Risks:** Program Files write (Admin); update wipe; integrity warning; selector skew after Cursor updates.

### Rank 2 — CSS-only minimal patch (phase-6 scaffolding subset of Rank 1)

Same as Rank 1 but **CSS-only** for the first shippable scaffold: markers + backup + fail-safes + boot splash via CSS (`#jarvis-boot` / body background using `file://` or data-URI / copied asset under `out/`). Defer DOM-mutating JS until Trusted Types strategy is decided.

**Use when:** God wants safest first mechanical step before full HUD DOM.

### Rank 3 — APC Customize UI++–style multi-file patch

Patches `workbench.html` **plus** `bootstrap-amd.js` / `main.js` (and sometimes iframe HTML). More layout control; worse update breakage, more checksums, harder restore. Only if Rank 1 CSS+light JS cannot reshape chrome enough for the reference PNG.

### Rank 4 — Depend on external loader (be5invis / YUYUMOE CSS Injector)

Works technically; **fails** “extension owns auto-disable” and “God is the builder” (outside-support / version-skew gap). Do **not** make this the product core. Optional research reference only.

### Rank 5 — Theme tokens / colorCustomizations only

**Insufficient** for locked visual target. Keep as suit-mode color packs **under** injection, not instead of it.

### Explicitly out

- Floating / editor overlays, webview-as-main-UI (current Command Center path demoted).
- Shipping or requiring upstream `redumper`-style binaries (N/A here) or wrapping marketplace Jarvis 3D VSIX.

---

## 3) First mechanical steps (do not implement full HUD yet)

### Files to create

| File | Purpose |
|------|---------|
| `src/workbenchInject.js` | Locate HTML, backup/restore, patch/unpatch, version probe, health check |
| `media/inject/jarvis-workbench.css` | Phase-6 scaffold CSS (markers, boot layer, minimal chrome hooks) |
| `media/inject/jarvis-boot.css` (optional split) | Boot splash using `reference-command-center.png` |
| `docs/INJECTION-APPROACH.md` | This audit (done) |

### Files to change (later in phase 6)

| File | Change |
|------|--------|
| `src/extension.js` | On `activate`: call `workbenchInject.reconcileOnActivate(context)` — **never** auto-enable without God; auto-**disable** on version/marker fail |
| `package.json` | Commands: `jarvis.injection.enable` / `disable` / `status`; settings: `jarvis.injection.enabled` (default false until God enables) |
| `README.md` | Injection credits/risks, fail-safes, Admin note, corrupt-install warning, God-owns-rebuild |

### What to patch

**Primary target:**

```
C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench\workbench.html
```

**Patch shape (recommended):**

```html
<!-- JARVIS-INJECT-START uuid=… cursorVersion=… cursorCommit=… -->
<style id="jarvis-workbench-css">…inlined CSS…</style>
<!-- optional later: boot/DOM helper script with Trusted Types plan -->
<!-- JARVIS-INJECT-END -->
```

Insert immediately before `</head>` (after stock CSS link).  
**Do not** remove Cursor’s CSP meta unless a later JS requirement proves it necessary (be5invis strips CSP — avoid that on Cursor unless forced).

**Backup:**

```
workbench.jarvis.<uuid>.bak.html
```

same directory; never overwrite a pristine backup with an already-patched file (classic Custom CSS bug).

**Asset staging:** Prefer inlining CSS (no runtime `file://` fetch needed). For boot PNG, either:

- Copy/reference via CSS `url(...)` relative to workbench (fragile under Program Files), or  
- Embed small data-URI / copy PNG next to workbench on enable and delete on disable, or  
- Inline critical boot CSS + load image from extension path via `vscode-file:` / absolute `file:///` if CSP `img-src` allows (`https:` / `data:` / `vscode-*` — **file:// may need testing**; data-URI or copy-into-app-dir is safer).

### Resolve app root from extension

Prefer (in order): `require.main` / `_VSCODE_FILE_ROOT` patterns used by Custom CSS Loader → `path.join(vscode.env.appRoot, 'out/vs/code/electron-sandbox/workbench/workbench.html')` → hard probe under `process.execPath` → `C:\Program Files\cursor\resources\app\...`.

---

## 4) Fail-safe implementation outline

Persist in `context.globalState` (and mirror key flags in settings for visibility):

| Key | Meaning |
|-----|---------|
| `jarvis.injection.enabled` | User/God intent |
| `jarvis.injection.active` | Patch currently on disk |
| `jarvis.injection.cursorVersion` | e.g. `3.29.9` at last successful enable |
| `jarvis.injection.cursorCommit` | `product.json` commit |
| `jarvis.injection.backupUuid` | Backup filename token |
| `jarvis.injection.markerUuid` | Marker in HTML |
| `jarvis.injection.lastError` | Last disable reason |

### Fail-safe (1) — Auto-disable on Cursor update

On every `activate` / `onStartupFinished`:

1. Read `product.json` version + commit (or `vscode.version` + appRoot product).
2. If `enabled|active` and `(version, commit) !== stored` → **treat as update**:
   - Restore backup / strip markers.
   - Set `enabled=false`, `active=false`.
   - One notification: “Cursor updated — JARVIS injection disabled. Re-enable after verify.”
3. Do **not** auto-re-enable (God re-runs Enable after rebuild/verify).

### Fail-safe (2) — Disable on patch detection / health failure

On activate when `enabled`:

1. Read `workbench.html`.
2. **Missing markers** but `active` expected → update wipe or external restore → disable, clear state, notify.
3. **Markers present but corrupted** (start without end, wrong uuid, CSS id missing) → restore backup, disable.
4. **Optional runtime probe** (if JS inject later): look for `#jarvis-workbench-css` / expected DOM ids; if missing after reload → disable + restore.
5. **Write failure** (EACCES) → leave disk alone, set not-active, prompt Admin re-run.

### Fail-safe (3) — God is the builder / no outside-support gap

Document in README + this file:

- No Cursor Support / marketplace support expectation.
- God owns: Admin enable, dismissing/handling integrity warning, re-enable after updates, selector fixes, VSIX rebuilds.
- Disable always restores stock chrome so IDE remains usable.
- Commands: Enable / Disable / Status / “Open injection docs”.

### Reconcile algorithm (pseudo)

```
reconcileOnActivate():
  loc = locateWorkbench()
  if !loc → status=unavailable; return

  disk = readHtml()
  ver  = readProductVersion()

  if active || enabled:
    if ver != storedVer OR !markersValid(disk):
      restoreBackup()
      enabled=false; active=false
      notify(reason)
      return

  if enabled && !markersPresent(disk):
    // intentional re-apply only if God set autoApply; default: disable
    enabled=false; notify("patch missing — re-enable manually")
```

---

## 5) Risks (integrity / wipe / skew)

| Risk | Effect | Mitigation |
|------|--------|------------|
| Integrity / “corrupt installation” | Warning; Cursor may lack “Don’t show again” | God decision: live with warning, or Fix Checksums (extra core write), or accept Unsupported title |
| Update wipe | `workbench.html` replaced; backup may vanish with install dir | Fail-safe 1; keep a **copy of pristine HTML** also under extension `globalStorage` |
| Version skew | Selectors / layout break; half-broken HUD | Fail-safe 2 health/marker checks; CSS feature flags per Cursor major |
| Admin ACL | Enable fails silently / EACCES | Detect + clear message: run Cursor as Admin once for Enable/Disable |
| Trusted Types | Injected scripts may fail | CSS-first; JS only with TT-compatible policy or DOM built via allowed paths |
| Double-patch / backup poison | Disable restores patched file | Never backup already-patched HTML; clearExistingPatches before backup |
| CSP strip | Breaks Cursor-specific connect-src / trusted-types | Prefer keep CSP; inline CSS only |

---

## 6) IMPORTANT decisions (God)

1. **Corrupt-installation warning** — **LOCKED (God Nov 7):** Accept warning / reinstall-re-enable. Do **not** implement Fix Checksums. Do **not** block phase 6 on this.

2. **Inject host standard** — **LOCKED:** Rank 1 Custom CSS Loader / CSS Injector / Custom UI Style pattern (extension-owned `workbench.html` inline CSS). No third-party loader runtime dependency.

3. **Default `jarvis.injection.enabled`** — **`false`** until God runs Enable once.

4. **CSP stripping** — Do **not** strip Cursor CSP for CSS-only phase 6.

5. **Command Center webview** — Demote to optional fallback (`jarvis.injection.fallbackWebview` default false).

6. **Admin elevation** — Soft-fail with clear message; God runs Enable as Admin once if Program Files ACL blocks.

7. **Boot splash** — `reference-calibrating-splash.png` is boot **and** overall UI visual target (God).

---

## 7) Phase 6 success criteria (scaffold)

- [ ] `workbenchInject.js` can Enable → markers+CSS on disk; Disable → pristine restore  
- [ ] Version/commit change → auto-disable + restore  
- [ ] Missing/altered markers → auto-disable + restore  
- [ ] README states God-owned rebuild; no vendor-support blocker  
- [ ] No overlay as primary UI path for the reference look  
- [ ] Theme tokens remain suit packs under injection  

---

## 8) Reference links (patterns, not dependencies)

- [be5invis/vscode-custom-css](https://github.com/be5invis/vscode-custom-css/) — workbench.html inline CSS/JS  
- [YUYUMOE CSS Injector](https://marketplace.visualstudio.com/items?itemName=YUYUMOE.vscode-css-injector) — Cursor-aware inject + backup  
- [APC Customize UI++](https://marketplace.visualstudio.com/items?itemName=drcika.apc-extension) — multi-file patch (heavier)  
- [Fix VSCode Checksums Next](https://marketplace.visualstudio.com/items?itemName=RimuruChan.vscode-fix-checksums-next) — optional integrity quieting  
)
