# CORTANA Theme Master — Cold Reopen

> ## CORTANA WORKSTATION 0.5.7 — inject live (Nov 7 ~4:55 AM)
>
> **Branding:** Cortana Workstation. **Physical folder** `jarvis-cursor-ui`; **junction** `C:\PS2Recomp\cortana-cursor-ui`.  
> **Package:** `cortana-cursor-ui-0.5.7.vsix` → `~\.cursor\extensions\ps2recomp-local.cortana-cursor-ui-0.5.7`.  
> **Admin Enable:** elevated **OK** — Program Files `workbench.html` ~1.56 MB patched; HUD + Manhattan + staged `cortana-hud-*.js` (CSP-safe, no inline scripts). Wake lives in `cortana-hud-wake.js`.  
> **Settings:** `cortana.injection.enabled=true`. **Reload Cursor** required to see inject.  
> **Splash:** still deprioritized. Fail-safes 1–3 preserved.

**Authority:** God (team) · **Operator:** Joshua · **Date locked:** Nov 7, 2026  
**Canonical plan:** `cortana_pro_recreation_a1985356` (plan wins on lock conflicts).  
**Extension root:** `C:\PS2Recomp\cortana-cursor-ui` (junction) / physical `jarvis-cursor-ui` · **v0.5.7** · **Admin Enable = Joshua / elevated script**

### Workers (God rebuild NOW)

| Worker | Owns | Must not |
|--------|------|----------|
| **A** | Splash / `boot.css` — real PNG cover + animated progress/bg | Drop PNG path / overlays |
| **B** | HUD one-to-one vs `reference-command-center-2.png` (`hud.css`) | Overlays |
| **C** | Full IDE theme unison (themes + tokens alignment) | Break inject markers |
| **D** | Fail-safes 1–3 + package / VSIX / this status sync | Delete fail-safe code; fight A–C CSS |

---

## Session log (tonight) — Nov 6–7, 2026

**Written into this file for cold reopen.** Earlier rebuild (~1:42 AM) + late-night Cortana Workstation ship attempt (~3–4 AM) + post-audit fix wave (~4:50 AM).

### A2) Fix wave — Cortana Workstation 0.5.7 (after five-domain audit)

1. **P1 inject restored:** crash-guard strip uses lookahead for `workbench.js`; HUD scripts staged as `'self'` `.js` files (CSP blocks inline); Admin Enable prefers newest install; `voiceBridge` → `composer.toggleVoiceDictation`.
2. **Enable probes:** hasHud/hasManhattan true; wbBytes ~1.56MB; wake in staged JS; badges Tasks 3 / Conversations 12 / Tools 18 stamped.
3. **P2 Focus surface (partial):** `cortana-focus-mode` body class + opaque part backgrounds when Focus ON (no transparent hole-punch). Full IDE glass/menus still open.
4. **P3 window chrome (partial):** broader stock caption hide; Cortana `#cortana-win-chrome` always visible (not opacity-0).
5. **P4/P5:** nav pill rows + parallelogram Focus Mode control; sidebar badges filled.
6. **Still open:** most of V-001–200 visual deltas; THEME-001–180 depth; Focus still not a full Cortana IDE skin; voice needs Cursor reload + mic permission live confirm.

### A) Late session — Cortana Workstation 0.5.5 (before Josh restart)

1. **Brand:** JARVIS → **Cortana Workstation** throughout (`package.json` displayName/name, inject IDs `cortana-*`, commands, themes). Jarvis marketplace display leaks cleaned.
2. **Legacy installs deleted:** `~\.cursor\extensions\ps2recomp-local.jarvis-cursor-ui-0.5.0` and `…-0.5.2` removed.
3. **Junction:** `C:\PS2Recomp\cortana-cursor-ui` → `jarvis-cursor-ui`. Physical rename **skipped per God** (Cursor locks tree).
4. **Docs:** `GOD-ADMIN-ENABLE.md`, crash-window notes → Cortana 0.5.4/0.5.5; `SPLICE-ELEMENT-INVENTORY-CC2.md` + `SPLICE-THEMING-CC2.md` written; `PIXEL-CROSSCHECK.md` written.
5. **Font pass:** one geometric UI sans (**Segoe UI** stack) — not Orbitron.
6. **Palette / chrome:** dual cyan-green accent; amber legal **outside** top bar; glass = opacity+glow not heavy blur; void `#030D19`–`#020817`, panels `#091A2B`–`#0E2538`, cyan `#00D4FF`/`#4AD1F1`, OK `#3DD68C`, warn `#FFAB00`.
7. **Parallelograms:** brand skew **−22°**, status **−14°**. Panel **L-brackets all 4 corners**.
8. **Eleven visual fixes:** (1) search expand-corners icon (2) operator chip text-left + avatar-right (3) header order apps→bell→gear (4) LLM provider logos (5) Agents View All footer (6) Quick Command SVG icons (7) footer meta pin/sun/wifi (8) panel glass (9) header/voice scanline surface (10) feed/agent glyph weights (11) captions hover-reveal on min/max/close + related chrome polish.
9. **Icon rebuild (God: no AI slop):** clean hairline SVG stroke **1.25** — nav, overview, agents, feed severity (no unicode i/!/✦/◉), LLM **brand marks not letter wells**, footer meta, Quick Command, header tools. PNG mush wells removed from overview.
10. **Stroke weights (photo → tokens):** panel/rail/bracket/divider **1px**; gauge rings **4**; wave bars **2**; para-foot **4**; grid gutter **10**.
11. **Pixel measurements @ reference-command-center-2.png 1024×573:** rail **157**, header **46**, panel boxes logged in `media/inject/PIXEL-CROSSCHECK.md`; radii ~6; skews as above.
12. **Animations kept:** globe orbits/live layers; scanline; mic ripple bottom-left; middle audio wave + animated dots; footer Talk bead strip; nebula glows; LIVE pulse; L-bracket breathe; neuron/constellation pulse; gauge glow.
13. **Wake:** Hey Cortana / Hey Cortana Workstation via `buildHudWakeScript()` + SpeechRecognition (in inject when Enable succeeds).
14. **Data rules:** only hardcode **Manhattan, New York** (`HUD_FOOTER_LOCATION`); all else live Cursor (models, feed, agents, gauges, git, problems).
15. **Integrated Cortana window controls** with hover-reveal captions; Executive Briefing wired; Manage Providers; timeline leading trails; nav badges; voice header chevron; real Cursor LLM grid + panels.
16. **Package 0.5.5:** `npx @vscode/vsce package` → `cortana-cursor-ui-0.5.5.vsix` (~10.19 MB) → `cursor --install-extension … --force` → `ps2recomp-local.cortana-cursor-ui-0.5.5`.
17. **Admin Enable elevated** (`scripts/admin-enable-elevated.js` + UAC): **FAILED** with  
    `Inject block would sit outside </body> (scripts/HUD after body)`.  
    Cause: `validateHudPatchPlacement` treated **Cursor’s own** `<script src="./workbench.js">` after `</body>` as illegal. Modern Cursor workbench is ~**1824 B** pristine shell (body empty; startup script after body).
18. **“Feature flags” HUD/Wake/Manhattan/wbBytes = false:** **not** `package.json` toggles. They are **post-Enable probes** in `scripts/admin-enable-elevated.js` reading Program Files `workbench.html`. Because Enable refused write, probes stay false / wbBytes=1824. They **should all be true** after a successful Enable (HUD root + wake script + Manhattan stamp in patched HTML; wbBytes ≫ 1824).
19. **Crash-guard repair (source only):** `workbenchInject.js` now strips Cursor `workbench.js` from the post-body tail before refusing. **Installed 0.5.5 copy still has old guard** — must sync/repackage/re-Enable before probes flip true.
20. **Splash:** deprioritized for now (God later plan). Boot still stages calibrating/CC assets when Enable runs.
21. **To-do rollup (~41 items):** nearly all complete (globe/overview/feed/agents/talk/header/sidebar/memory/LLM/interact/theme/font/audit/11 fixes/legacy cleanup/captions/L-brackets/agent SVG/LLM marks/icons/pixel/stroke). **Open/blocked:** package+Admin Enable clean success; live visual confirm by God vs `reference-command-center-2.png`. Rename physical folder **cancelled**.

### B) Earlier same night — Phase 6 rebuild start

### 1) Phase 6 injection build started
- Work began on Custom CSS / workbench injection per this master and plan `cortana_pro_recreation_a1985356`.
- Produced on disk under `C:\PS2Recomp\cortana-cursor-ui\`:
  - `src/workbenchInject.js` (inject engine)
  - `media/inject/tokens.css` (token system)
  - `media/inject/boot.css` (Command Center PNG boot sheet + animated progress/bg)
  - `media/inject/hud.css` (HUD chrome sheet)
  - `package.json` + `src/extension.js` (`CORTANA.injection.enable` / disable / reenableAfterUpdate / healthCheck / status)
- Boot asset (God lock rebuild): `media/reference-command-center-2.png` (same frame as `reference-command-center.png`), staged as `CORTANA-boot-splash.png`. Calibrating PNG = optional archive. Overlays forbidden. Studio YES / Active support OUT / three fail-safes locked.

### 2) Program Files install attempted
- Install target (not a delivery folder):  
  `C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench\workbench.html`
- Goal: patch workbench with marked CORTANA CSS + stage `CORTANA-boot-splash.png` beside it.

### 3) EACCES — Cursor was not elevated
- Josh ran **CORTANA: Enable Workbench Injection** while logged in as an admin **account**, but the **Cursor process token was not elevated** (Medium integrity; Administrators group present as “deny only”).
- Result: `EACCES: Cannot write Cursor workbench files under Program Files` — same message as soft-fail in `workbenchInject.js`.
- Agent shell was also non-elevated (`SHELL_ADMIN=False`); could not write Program Files either.

### 4) Fix that unblocked Enable
1. Quit **all** Cursor windows, **including the tray**.
2. Right-click Cursor (`C:\Program Files\cursor\Cursor.exe` or Start Menu) → **Run as administrator** → UAC Yes.
3. Re-run **CORTANA: Enable Workbench Injection**.
4. **Reload Window**.
5. After that, workbench.html was observed patched (~44KB, CORTANA-INJECT-START/END, ~1:34 AM) with bak + splash present.

### 5) Corrupt-install warning
- Appeared (or expected) after sealed install files were modified.
- **Expected / accepted.** Do **not** run Fix Checksums. Dismiss and continue.

### 6) Two Cursor windows conflict blocked workspace loading
- Cursor session restore had been dual-tracking `C:\PS2Recomp` **and** `E:\PS2Recomp.code-workspace`, plus empty windows → second IDE / “cannot open any workspace” style failure.
- Earlier mitigations: `window.restoreWindows: "one"`, `window.openFoldersInNewWindow: "off"`, restore trimmed toward one Recomp folder (`STARTUP-IDE-ONLY.md`).
- After Enable, workspace-open failure was reported again; diagnose found inject HTML structurally closed (`</head>`, `workbench.js` present) and pristine `workbench.CORTANA.*.bak.html` (~1824 B) available. **Restore was not applied** because pause was ordered — Josh owns whether to Disable/restore.

### 7) Name rule
- **God** = team / account label (locks, God-as-builder, filenames such as `GOD-ADMIN-ENABLE.md`). Do **not** blanket-replace.
- **Joshua** = the individual person in docs (Admin Enable / operator).
- On voice calls, address him as **Josh**.
- Do **not** rename files or folders for this.

### 8) Delivery folder abandoned
- `C:\PS2Recomp\CORTANA-phase6-delivery` was created briefly as a copy-paste drop, then **abandoned and deleted**.
- Install path remains Program Files Cursor + extension under `~\.cursor\extensions\ps2recomp-local.cortana-cursor-ui-0.5.0`.

### 9) Brief pause, then God rebuild
- Josh briefly paused agents (~1:37 AM), then God ordered **full rebuild NOW** (~1:42 AM).
- Workers **A–D** resumed: splash / HUD / themes / fail-safe+package. Fail-safes 1–3 remain LOCKED.

### 10) Worker D fail-safe harden (rebuild)
- Fixed reconcile status mismatch: engine now returns `disabled-due-to-update` / `health-fail` so extension notify + **Re-enable after verify** fires (was returning `auto-disabled` only).
- Hardened CSS health probe (`CORTANA-HEALTH` needles), splash PNG required on Enable, ~60s soft re-probe.
- Boot stage source locked to **`reference-command-center-2.png`** (real PNG; not CSS-only fallback).

### Current state snapshot (as of ~4:22 AM)

| Piece | State |
|-------|--------|
| Brand / version | **Cortana Workstation 0.5.5** |
| Source tree | Junction `cortana-cursor-ui` → physical `jarvis-cursor-ui`; crash-guard **fixed in source** |
| Installed extension | `ps2recomp-local.cortana-cursor-ui-0.5.5` — **stale** (pre crash-guard fix) |
| Program Files `workbench.html` | Pristine ~1824 B — **not patched** (Enable refused) |
| Probes HUD / Wake / Manhattan | **false** (no inject written yet) |
| VSIX | `cortana-cursor-ui-0.5.5.vsix` on disk |
| Next gate | Sync fix into install → elevated Enable → God live visual confirm |

### If Josh needs emergency restore
Admin Cursor → **CORTANA: Disable Workbench Injection**, or copy `workbench.CORTANA.*.bak.html` over `workbench.html` in the workbench folder, then restart Cursor.

---

## Sibling docs (sources of truth — do not invent conflicts)

| Doc | Role |
|-----|------|
| Plan `cortana_pro_recreation_a1985356` | Phase status + Phase 6 ordered build; **wins on conflicts** |
| [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md) | God YES checklist; Active support EXCLUDED; Studio column |
| [`phase6-injection-build.md`](./phase6-injection-build.md) | Build mirror of Phase 6 sub-phases |
| [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md) | God Admin enable steps (resume gate) |
| [`INJECTION-APPROACH.md`](./INJECTION-APPROACH.md) | Rank-1 inject audit; fail-safe outline; Cursor install facts |
| [`VISUAL-SPEC-FROM-REFERENCE.md`](./VISUAL-SPEC-FROM-REFERENCE.md) | Pixel/UX from reference PNGs |
| [`PALETTE-MARKETPLACE-VS-REFERENCE.md`](./PALETTE-MARKETPLACE-VS-REFERENCE.md) | Hybrid palette (PNG boot vs marketplace brand) |
| [`MARKETPLACE-CORTANA-3D-EXTRACT.md`](./MARKETPLACE-CORTANA-3D-EXTRACT.md) | Pattern map + Studio matrix; copy patterns only |
| [`REBUILD-STATUS.md`](./REBUILD-STATUS.md) | Worker A–D QA checklist for Joshua Admin Enable |
| [`SPLICE-ELEMENT-INVENTORY-CC2.md`](./SPLICE-ELEMENT-INVENTORY-CC2.md) | CC-2 element inventory |
| [`SPLICE-THEMING-CC2.md`](./SPLICE-THEMING-CC2.md) | CC-2 theming splice notes |
| [`../media/inject/PIXEL-CROSSCHECK.md`](../media/inject/PIXEL-CROSSCHECK.md) | Photo vs inject pixel + stroke audit |
| [`../README.md`](../README.md) | User-facing install, fail-safes, commands |

---

## Phase status

| Phase | Status |
|-------|--------|
| **1 — Shell + boot imagery** | **Done** |
| **2 — Suit Modes + FX** | **Done** |
| **3 — Ops HUD** | **Done** |
| **4 — Session / focus / stream** | **Done** |
| **5 — Presets + package** | **Done** |
| **6 — Injection foundation** | **REBUILD IN PROGRESS** — God resume; Workers A–D; inject engine + fail-safes locked; HUD/splash/themes polishing |

### Phase 6 sub-phases

| Sub-phase | Intent | Checkpoint |
|-----------|--------|------------|
| **6.3.A Scaffold** | `workbenchInject.js`, `media/inject/{tokens,boot,hud}.css`, `CORTANA.injection.*` settings/commands, `extension.js` gate | **Done** — synced to installed `0.5.0` |
| **6.3.B Fail-safe 1** | Auto-disable on Cursor update (fingerprint) | **Verified** — teardown + disable + notify; never auto-re-enable |
| **6.3.C Fail-safe 2** | Disable on patch/probe fail | **Verified** — markers + `CORTANA-HEALTH` CSS probe + ~60s soft re-probe |
| **6.3.D Fail-safe 3** | Joshua-as-builder docs (**not** Active support) | Documented — Admin Enable / reenableAfterUpdate only |
| **6.3.E Boot** | Full-bleed **CC-2 PNG** → `bootMs` → reveal | Real PNG staged as `CORTANA-boot-splash.png`; **QA pending** (Joshua Admin) |
| **6.3.F HUD** | Inject CC regions vs CC / CC-2; Studio YES | Worker B polishing — Studio YES completeness open |
| **6.3.G Demote** | Webview not primary when inject on; no overlays | Partial (`fallbackWebview` false) |
| **6.3.H Verify + package** | PNG QA, Studio checklist, fail-safe tests, VSIX | Worker D — **0.5.1** package path |
| **6.3.J Title bar** | Custom `titleBarStyle` + inject CSS (chrome + top-corner icon styling) | **`window.titleBarStyle: custom` set** + hud.css titlebar rules injected |
| **6.3.I Taskbar `.ico`** | Electron/app or shortcut icon replace | **OUT OF SCOPE for now** |

**Do not** reopen Phases 1–5 unless Joshua explicitly reopens them.  
**Do not** implement Active support. **Do not** add overlays. **Do not** depend on a third-party CSS loader.

---

## Visual targets (from reference PNGs) — God rebuild

**Primary boot / first-paint (LOCKED):**  
[`media/reference-command-center-2.png`](../media/reference-command-center-2.png) (same frame family as [`reference-command-center.png`](../media/reference-command-center.png))

- Full-bleed on IDE launch via **injection** only (not a separate exe).
- **Must be a real PNG** staged beside workbench as `CORTANA-boot-splash.png` — **not** a CSS-only calibrating fallback.
- Engine Enable **fails** if the PNG cannot be staged.
- Animated progress / parallax / fade timing: Worker A (`boot.css` + `CORTANA.injection.bootMs`).
- **PAUSED:** false — rebuild resumed.

**Post-boot Command Center chrome:** same CC / CC-2 PNGs (1024×573)

- Glass navy dashboard; left nav; SYSTEM STATUS · OPTIMAL; cyan clock; globe hero; Talk capsule; footer meta.
- Injection must restyle the **entire Cursor window** (title bar, activity bar, sidebar, tabs, panel, status bar) — webview alone is insufficient.
- Detail: visual-spec §2–§3; Worker B owns one-to-one HUD.

**Legacy asset retained:** [`media/reference-calibrating-splash.png`](../media/reference-calibrating-splash.png) kept on disk for reference; **not** the Enable stage source under current God lock.

**Overlays:** Forbidden (no floating / editor-wide overlay HUD).

---

## Marketplace / God Studio YES list

God lock: every Studio-tier option **YES** on the local theme — unlocked, **no Gumroad**.  
**Active support = EXPLICITLY OUT** (God was only reading the marketplace list).

### God marketing / feature bullets (all YES)

| # | Item | Meaning |
|---|------|---------|
| 1 | **3D real depth** | Layered z / perspective / parallax — not flat tint only |
| 2 | **Realtime animation** | Continuous live HUD/FX motion |
| 3 | **Active responses** | Activity-aware chrome (editor/session/agent/threat/voice) |
| 4 | **Arc pulses** | Pulsing arc-reactor motif synced to energy/activity |
| 5 | **Peer innovation** | = **first-party innovation** parity goals — **NOT** active/peer support |
| 6 | **Realtime tracking** | Coding / energy / session metrics in HUD |
| 7 | **30% optimized colors** | Calibrated palette; God “30%” vs stock Cursor contrast |
| 8 | **Built-in HUD** | Injected Command Center chrome |
| 9 | **Classic CORTANA theme + icon** | Classic color theme + icon theme |
| 10 | **Basic HUD** | Status strips, reactor, core chips |
| 11 | **Arc + energy** | Reactor + energy readouts |
| 12 | **EVERY studio option YES** | Full Studio column (below) |

### Studio column (local)

| Studio / marketplace row | On God's theme |
|--------------------------|----------------|
| Classic theme + icons | **YES** |
| Basic HUD / arc / energy | **YES** |
| Standard performance | **YES** |
| Suit Modes | **YES** |
| Particles / arc / streams / glow | **YES** |
| F.R.I.D.A.Y. / TTS / sound | **YES** |
| Session Cinema / Stream Pack / Focus Fortress | **YES** |
| Threat / GitHUD / Dashboard | **YES** |
| AI Companion / presets | **YES** |
| Multi-device | **N/A (local)** |
| Stream watermark | **Optional local** |
| Seasonal suits | **YES** |
| **Active support** | **EXCLUDED — OUT** |

Full module → inject map: [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md).

---

## Hybrid palette (locked)

| Surface | Prefer | Why |
|---------|--------|-----|
| **Boot / splash** | **CC PNG samples** + cyan progress overlay (`#0E121A` / `#00f2ff` family) | Pixel-match Command Center boot still |
| **Brand / product cyan** | **Marketplace** primary `#00d9ff` (and related brand tokens where not splash-locked) | Suit / theme / listing coherence |
| **CC glass / Optimal green when matching refs** | **PNG / CC samples** | Screenshot match (muted teal-green, not neon `#00ff9f`) |

Do **not** replace CC/boot bloom cyan with marketplace `#00d9ff` if that softens the boot still. Dual vars OK (`--CORTANA-cyan-brand` + bloom `--CORTANA-cyan`).  
Detail table: [`PALETTE-MARKETPLACE-VS-REFERENCE.md`](./PALETTE-MARKETPLACE-VS-REFERENCE.md).

---

## Three fail-safes (LOCKED — never drop)

1. **Auto-disable on update** — Cursor `product.json` version/commit + `vscode.version` fingerprint change → teardown patch, disable, notify (`disabled-due-to-update`); **never** auto-re-enable.
2. **Disable on injection break** — Missing/corrupt markers, wrong uuid, missing `CORTANA-workbench-css`, or `CORTANA-HEALTH` / CSS needle probe fail (activate + ~60s soft re-probe) → teardown, disable, notify (`health-fail`).
3. **Joshua-as-builder ownership** — Docs/commands for **Admin Enable**, **Re-enable Injection After Update** after verify. **NOT** marketplace Active support. Workers never elevate; Joshua alone writes Program Files.

Integrity / “corrupt installation” toast: **suppressed** — Enable/Disable/restore syncs `product.json` checksums for `workbench.html` (SHA-256 base64). Inject unchanged; Admin write required once for the sync.

**Verify script:** `node scripts/verify-fail-safes.js` (wiring smoke).

---

## Injection standard (LOCKED)

**Pattern class:** Custom CSS Loader / CSS Injector / Custom UI Style — **extension-owned** `workbench.html` inject.

| Rule | Value |
|------|--------|
| Module | `src/workbenchInject.js` |
| CSS | Marked inline `<style>` from `media/inject/{tokens,boot,hud}.css` before `</head>` |
| Third-party loader | **No runtime dependency** (be5invis / YUYUMOE / APC are research refs only) |
| Default enabled | `CORTANA.injection.enabled` = **false** until Joshua Enable (now **true** — installed) |
| CSP | CSS-first; do **not** strip Cursor CSP for CSS-only path |
| Write ACL | Program Files → **Admin once** for Enable/Disable; soft-fail with clear message |
| Commands | `CORTANA.injection.enable` / `disable` / `reenableAfterUpdate` / `healthCheck` / `status` |

Audit detail: [`INJECTION-APPROACH.md`](./INJECTION-APPROACH.md).

---

## Title bar / icons / taskbar

| Target | Lock | Method |
|--------|------|--------|
| **Title bar chrome** (colors, glow, controls styling) | **YES** | `"window.titleBarStyle": "custom"` + inject CSS (`.part.titlebar` / custom-titlebar) |
| **Stock min / max / close** | **HIDDEN always** | Never show Windows caption buttons (`.window-controls-container` / `.codicon-chrome-*`) — HUD **and** Focus Mode |
| **Integrated window controls (God confirm)** | **YES** | Merge min / max / close into Cortana chrome `#cortana-win-chrome` — reference icon-btn shapes, top-right; functional via stock node click fallback + `workbench.action.*`. Focus Mode keeps Cortana controls (does **not** restore stock Win buttons) |
| **Top-corner / in-window app icon styling** | **YES** | Same custom titleBar + inject CSS (e.g. `.window-appicon` size/filter/hide/tint). Bitmap **replacement** still needs `.ico` if God later wants a new glyph — not required for YES chrome path |
| **Windows taskbar icon** | **OUT OF SCOPE for now** | Needs exe / resource / shortcut `.ico` replace — **not** pure CSS. Do not schedule 6.I until God reopens |

---

## On-disk scaffold inventory (installed — keep)

Do **not** delete. Engine + CSS are live under Program Files inject; continue HUD polish on these files.

| Path | Role |
|------|------|
| `src/workbenchInject.js` | Rank-1 inject engine (locate / backup / patch / teardown / fingerprint / health) |
| `media/inject/tokens.css` | Calibrated / 30% palette CSS variables |
| `media/inject/boot.css` | CC PNG full-bleed + animated progress / particle bg |
| `media/inject/hud.css` | Post-boot chrome hooks (scaffold; Studio YES HUD incomplete) |
| `media/reference-command-center-2.png` | Boot asset staged on Enable as `CORTANA-boot-splash.png` |
| `media/reference-calibrating-splash.png` | Legacy calibrating still (retained; not Enable stage source) |
| `package.json` → `CORTANA.injection.*` | Settings: `enabled`, `bootMs`, `fallbackWebview` |
| Commands | `CORTANA.injection.enable` / `disable` / `reenableAfterUpdate` / `healthCheck` / `status` |
| `src/extension.js` | Activate gate → reconcile; command wiring |

Phases 1–5 modules remain: `suitModes`, `gitHud`, `threatHints`, `sessionCinema`, `workspacePresets`, `voiceBridge`, themes, Command Center webview (demoted / fallback).

---

## Boot on IDE launch

- **Asset:** `reference-command-center-2.png` / `reference-command-center.png` (same frame) → staged `CORTANA-boot-splash.png`.
- **PAUSED:** false — rebuild resumed (Worker A).
- **Motion:** progress fill 0→100% + live % + stepped dots over `CORTANA.injection.bootMs`; navy particle / data-stream field behind/around PNG; fade into HUD after hold (~70% of `bootMs`).
- **Delivery:** Workbench injection on Cursor/IDE launch → full-bleed PNG cover → fade/reveal HUD.
- **Not** a separate splash executable; **not** CSS-only calibrating fallback as primary.
- Calibrating PNG = optional archive only.
- Corrupt warning after patch is expected UX.

---

## Startup scope — Recomp folder IDE-only

| Lock | Value |
|------|--------|
| **Primary product scope** | CORTANA inject / theme work targets the **Recomp folder IDE** session (`C:\PS2Recomp` / this extension workspace) |
| **Document** | Treat Recomp Cursor window as the verify / Admin-enable / QA surface |
| **One window** | `window.restoreWindows: "one"`; do **not** dual-restore `E:\PS2Recomp.code-workspace` + folder; no Startup-folder Cursor shortcuts |
| **Splash** | Injection path only (`boot.css` / `CORTANA.injection.*`) — never a separate splash exe or new window to show it |
| **Sibling note** | A sibling agent or other Cursor window **may apply settings** that affect user/global Cursor config; that does not expand product scope — still document and verify against **Recomp IDE** |

Full write-up: [`STARTUP-IDE-ONLY.md`](./STARTUP-IDE-ONLY.md). Workers soft-fail on Admin; Joshua enables inject in the Recomp-scoped Admin session per [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md).

---

## Architecture (target)

```mermaid
flowchart TB
  ext[extension.js]
  inject[workbenchInject Rank-1]
  boot[boot splash CC PNG]
  hud[injected CC chrome]
  ext --> inject
  inject --> boot
  boot --> hud
  hud --> depth[3D depth]
  hud --> metrics[realtime tracking]
  suits[suitModes] --> hud
  fx[arc pulses FX] --> hud
  git[gitHud] --> hud
  threat[threatHints] --> hud
  session[sessionCinema] --> hud
  presets[workspacePresets] --> hud
  voice[voiceBridge] --> hud
```

Core idea: IDE launch → Command Center PNG via inject (animated progress/bg) → CC chrome with Studio YES completeness. No overlay path. No Gumroad. No Active support.

---

## Explicit exclusions

- Marketplace **Active support** / community/vendor support product claims  
- Gumroad / paid unlock / trial soft-lock overlays  
- Third-party Custom CSS Loader as a **required** dependency  
- Floating / editor overlay HUD as primary UI  
- Windows **taskbar** `.ico` work (out of scope now)  
- Copying NextGenCode VSIX / CSS / assets  
- Fix Checksums as a Phase 6 blocker  
- Treating “peer innovation” as peer/third-party support  

---

## Continue checklist (rebuild LIVE — Joshua Admin gate)

- [x] Cold-reopen this master + plan  
- [x] Scaffold files still present (inventory above)  
- [x] Admin Enable attempted / Program Files patched (see session log)  
- [x] Fail-safe wiring verified (`scripts/verify-fail-safes.js`)  
- [x] Worker A: CC-2 PNG stage path + animated progress/bg in `boot.css` (re-Enable to stage new PNG)  
- [ ] Confirm IDE opens workspaces cleanly after elevation/restore if needed  
- [ ] Boot splash = **real CC-2 PNG** full-bleed (QA after Admin Enable / Reload)  
- [ ] HUD one-to-one vs CC-2 (Worker B) + theme unison (Worker C)  
- [ ] Fail-safes 1–2 behave on fake update / broken markers (manual QA)  
- [x] Package **0.5.5** VSIX + install to `~\.cursor\extensions\…-0.5.5`  
- [ ] Sync crash-guard fix into installed copy → elevated Admin Enable until probes true  
- [ ] God live visual confirm vs `reference-command-center-2.png`  
- [ ] Leave taskbar `.ico` alone until 6.I reopened  
- [ ] Keep Active support OUT; keep hybrid palette; keep Recomp IDE as verify scope  

See also: [`REBUILD-STATUS.md`](./REBUILD-STATUS.md), [`PIXEL-CROSSCHECK.md`](../media/inject/PIXEL-CROSSCHECK.md).

---

*Master consolidate for cold reopen. Sibling docs remain authoritative detail; plan wins on lock conflicts. **Cortana Workstation 0.5.5** — Enable blocked on stale install / crash-guard; Joshua owns elevated re-Enable after sync.*
