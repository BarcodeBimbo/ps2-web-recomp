# JARVIS Theme Master — Cold Reopen

> ## REBUILD LIVE — God ordered full rebuild (Nov 7 ~1:42 AM)
>
> **Status:** Pause lifted. Four workers running: **A** splash PNG + animated progress/bg · **B** one-to-one HUD vs `reference-command-center-2.png` · **C** full IDE theming unison · **D** fail-safes + package. Injection only; overlays out; fail-safes 1–3 preserved.
>
> See **§ Session log (tonight)** below. Pristine workbench bak still available if Disable/restore is needed.

**Authority:** God (team) · **Operator:** Joshua · **Date locked:** Nov 7, 2026  
**Canonical plan:** `jarvis_pro_recreation_a1985356` (plan wins on lock conflicts).  
**Extension root:** `C:\PS2Recomp\jarvis-cursor-ui` · **v0.5.0** · workbench inject markers present under Program Files (see session log)

---

## Session log (tonight) — Nov 6–7, 2026

**Written into this file for cold reopen.** Chronological record of what actually happened; agents paused after this entry.

### 1) Phase 6 injection build started
- Work began on Custom CSS / workbench injection per this master and plan `jarvis_pro_recreation_a1985356`.
- Produced on disk under `C:\PS2Recomp\jarvis-cursor-ui\`:
  - `src/workbenchInject.js` (inject engine)
  - `media/inject/tokens.css` (token system)
  - `media/inject/boot.css` (calibrating splash sheet)
  - `media/inject/hud.css` (HUD chrome sheet)
  - `package.json` + `src/extension.js` (`jarvis.injection.enable` / disable / reenableAfterUpdate / healthCheck / status)
- Boot asset: `media/reference-calibrating-splash.png`. Overlays forbidden. Studio YES / Active support OUT / three fail-safes locked in sibling docs.

### 2) Program Files install attempted
- Install target (not a delivery folder):  
  `C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench\workbench.html`
- Goal: patch workbench with marked JARVIS CSS + stage `jarvis-boot-splash.png` beside it.

### 3) EACCES — Cursor was not elevated
- Josh ran **JARVIS: Enable Workbench Injection** while logged in as an admin **account**, but the **Cursor process token was not elevated** (Medium integrity; Administrators group present as “deny only”).
- Result: `EACCES: Cannot write Cursor workbench files under Program Files` — same message as soft-fail in `workbenchInject.js`.
- Agent shell was also non-elevated (`SHELL_ADMIN=False`); could not write Program Files either.

### 4) Fix that unblocked Enable
1. Quit **all** Cursor windows, **including the tray**.
2. Right-click Cursor (`C:\Program Files\cursor\Cursor.exe` or Start Menu) → **Run as administrator** → UAC Yes.
3. Re-run **JARVIS: Enable Workbench Injection**.
4. **Reload Window**.
5. After that, workbench.html was observed patched (~44KB, JARVIS-INJECT-START/END, ~1:34 AM) with bak + splash present.

### 5) Corrupt-install warning
- Appeared (or expected) after sealed install files were modified.
- **Expected / accepted.** Do **not** run Fix Checksums. Dismiss and continue.

### 6) Two Cursor windows conflict blocked workspace loading
- Cursor session restore had been dual-tracking `C:\PS2Recomp` **and** `E:\PS2Recomp.code-workspace`, plus empty windows → second IDE / “cannot open any workspace” style failure.
- Earlier mitigations: `window.restoreWindows: "one"`, `window.openFoldersInNewWindow: "off"`, restore trimmed toward one Recomp folder (`STARTUP-IDE-ONLY.md`).
- After Enable, workspace-open failure was reported again; diagnose found inject HTML structurally closed (`</head>`, `workbench.js` present) and pristine `workbench.jarvis.*.bak.html` (~1824 B) available. **Restore was not applied** because pause was ordered — Josh owns whether to Disable/restore.

### 7) Name rule
- **God** = team / account label (locks, God-as-builder, filenames such as `GOD-ADMIN-ENABLE.md`). Do **not** blanket-replace.
- **Joshua** = the individual person in docs (Admin Enable / operator).
- On voice calls, address him as **Josh**.
- Do **not** rename files or folders for this.

### 8) Delivery folder abandoned
- `C:\PS2Recomp\jarvis-phase6-delivery` was created briefly as a copy-paste drop, then **abandoned and deleted**.
- Install path remains Program Files Cursor + extension under `~\.cursor\extensions\ps2recomp-local.jarvis-cursor-ui-0.5.0`.

### 9) All work paused
- Josh ordered: master session log + pause only; switching to JARVIS himself.
- Diagnose / Program Files / name-update workers **stopped**. No new builds or installs until Josh resumes.

### Current state snapshot

| Piece | State at pause |
|-------|----------------|
| Phase 6 build (engine/tokens/boot/hud/commands) | Started and on disk in extension root |
| Program Files inject | Attempted; after elevated Enable, `workbench.html` **patched** |
| EACCES | Hit, then fixed via full quit + Run as administrator |
| Corrupt warning | Expected |
| Dual-window / workspace load | Conflicted; one-window settings applied; restore optional |
| Delivery folder | Abandoned / gone |
| Agents | Paused |

### If Josh needs emergency restore
Admin Cursor → **JARVIS: Disable Workbench Injection**, or copy `workbench.jarvis.*.bak.html` over `workbench.html` in the workbench folder, then restart Cursor.

---

## Sibling docs (sources of truth — do not invent conflicts)

| Doc | Role |
|-----|------|
| Plan `jarvis_pro_recreation_a1985356` | Phase status + Phase 6 ordered build; **wins on conflicts** |
| [`GOD-REQUIREMENTS-PHASE6.md`](./GOD-REQUIREMENTS-PHASE6.md) | God YES checklist; Active support EXCLUDED; Studio column |
| [`phase6-injection-build.md`](./phase6-injection-build.md) | Build mirror of Phase 6 sub-phases |
| [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md) | God Admin enable steps (resume gate) |
| [`INJECTION-APPROACH.md`](./INJECTION-APPROACH.md) | Rank-1 inject audit; fail-safe outline; Cursor install facts |
| [`VISUAL-SPEC-FROM-REFERENCE.md`](./VISUAL-SPEC-FROM-REFERENCE.md) | Pixel/UX from reference PNGs |
| [`PALETTE-MARKETPLACE-VS-REFERENCE.md`](./PALETTE-MARKETPLACE-VS-REFERENCE.md) | Hybrid palette (PNG boot vs marketplace brand) |
| [`MARKETPLACE-JARVIS-3D-EXTRACT.md`](./MARKETPLACE-JARVIS-3D-EXTRACT.md) | Pattern map + Studio matrix; copy patterns only |
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
| **6 — Injection foundation** | **IN PROGRESS** — workbench inject **installed** (Program Files patched); HUD/Studio polish still open |

### Phase 6 sub-phases

| Sub-phase | Intent | Checkpoint |
|-----------|--------|------------|
| **6.3.A Scaffold** | `workbenchInject.js`, `media/inject/{tokens,boot,hud}.css`, `jarvis.injection.*` settings/commands, `extension.js` gate | **Done** — synced to installed `0.5.0` |
| **6.3.B Fail-safe 1** | Auto-disable on Cursor update (fingerprint) | Wired; fingerprint stored at enable |
| **6.3.C Fail-safe 2** | Disable on patch/probe fail | Wired; markers present on disk |
| **6.3.D Fail-safe 3** | Joshua-as-builder docs (**not** Active support) | Documented in README / this master |
| **6.3.E Boot** | Full-bleed calibrating PNG → `bootMs` → reveal | **Installed** (`jarvis-boot-splash.png` staged); **QA pending** after reload |
| **6.3.F HUD** | Inject CC regions; Studio YES (3D/anim/arc/tracking/…) | **Scaffold CSS injected** — Studio YES completeness still open |
| **6.3.G Demote** | Webview not primary when inject on; no overlays | Partial (`fallbackWebview` false; setting enabled) |
| **6.3.H Verify + package** | PNG QA, Studio checklist, fail-safe tests, VSIX | **Pending** |
| **6.3.J Title bar** | Custom `titleBarStyle` + inject CSS (chrome + top-corner icon styling) | **`window.titleBarStyle: custom` set** + hud.css titlebar rules injected |
| **6.3.I Taskbar `.ico`** | Electron/app or shortcut icon replace | **OUT OF SCOPE for now** |

**Do not** reopen Phases 1–5 unless Joshua explicitly reopens them.  
**Do not** implement Active support. **Do not** add overlays. **Do not** depend on a third-party CSS loader.

---

## Visual targets (from reference PNGs)

**Primary boot / first-paint:** [`media/reference-calibrating-splash.png`](../media/reference-calibrating-splash.png) (638×480)

- Full-bleed on IDE launch via **injection** (not a separate exe).
- Copy stack: `J.A.R.V.I.S.` → `JUST A RATHER VERY INTELLIGENT SYSTEM` → `CALIBRATING` → `N%` → five step dots.
- Charcoal void ≈ `#0E121A`; cyan bloom / ring / bar from splash samples (`#0FDEFF`–`#00f2ff` family).
- Detail geometry, tokens, acceptance: [`VISUAL-SPEC-FROM-REFERENCE.md`](./VISUAL-SPEC-FROM-REFERENCE.md) §1.

**Post-boot Command Center chrome:**  
[`media/reference-command-center.png`](../media/reference-command-center.png) + [`-2.png`](../media/reference-command-center-2.png) (1024×573)

- Glass navy dashboard; left nav; SYSTEM STATUS · OPTIMAL; cyan clock; globe hero; Talk capsule; footer meta.
- Injection must restyle the **entire Cursor window** (title bar, activity bar, sidebar, tabs, panel, status bar) — webview alone is insufficient.
- Detail: visual-spec §2–§3.

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
| 9 | **Classic Jarvis theme + icon** | Classic color theme + icon theme |
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
| **Boot / splash** | **Splash PNG samples** (`#0E121A`, `#0FDEFF`–`#00f2ff`, bar/ring/dots) | Pixel-match calibrating primary |
| **Brand / product cyan** | **Marketplace** primary `#00d9ff` (and related brand tokens where not splash-locked) | Suit / theme / listing coherence |
| **CC glass / Optimal green when matching refs** | **PNG / CC samples** | Screenshot match (muted teal-green, not neon `#00ff9f`) |

Do **not** replace splash bloom cyan with marketplace `#00d9ff` if that softens the calibrating still. Dual vars OK (`--jarvis-cyan-brand` + bloom `--jarvis-cyan`).  
Detail table: [`PALETTE-MARKETPLACE-VS-REFERENCE.md`](./PALETTE-MARKETPLACE-VS-REFERENCE.md).

---

## Three fail-safes (LOCKED)

1. **Auto-disable on update** — Cursor version/commit (fingerprint) change → teardown patch, disable, notify; **never** auto-re-enable.
2. **Disable on patch detect** — Missing/corrupt markers or health-probe fail → teardown, disable, notify.
3. **Joshua-as-builder / no outside-support gap** — Joshua owns Admin enable, integrity warning, rebuilds, re-enable after verify. **This is NOT marketplace “Active support.”** Do not rebrand fail-safe 3 as community/vendor support.

Integrity / “corrupt installation” warning: **accepted** — do **not** implement Fix Checksums; do **not** block Phase 6 on it.

---

## Injection standard (LOCKED)

**Pattern class:** Custom CSS Loader / CSS Injector / Custom UI Style — **extension-owned** `workbench.html` inject.

| Rule | Value |
|------|--------|
| Module | `src/workbenchInject.js` |
| CSS | Marked inline `<style>` from `media/inject/{tokens,boot,hud}.css` before `</head>` |
| Third-party loader | **No runtime dependency** (be5invis / YUYUMOE / APC are research refs only) |
| Default enabled | `jarvis.injection.enabled` = **false** until Joshua Enable (now **true** — installed) |
| CSP | CSS-first; do **not** strip Cursor CSP for CSS-only path |
| Write ACL | Program Files → **Admin once** for Enable/Disable; soft-fail with clear message |
| Commands | `jarvis.injection.enable` / `disable` / `reenableAfterUpdate` / `healthCheck` / `status` |

Audit detail: [`INJECTION-APPROACH.md`](./INJECTION-APPROACH.md).

---

## Title bar / icons / taskbar

| Target | Lock | Method |
|--------|------|--------|
| **Title bar chrome** (colors, glow, controls styling) | **YES** | `"window.titleBarStyle": "custom"` + inject CSS (`.part.titlebar` / custom-titlebar) |
| **Top-corner / in-window app icon styling** | **YES** | Same custom titleBar + inject CSS (e.g. `.window-appicon` size/filter/hide/tint). Bitmap **replacement** still needs `.ico` if God later wants a new glyph — not required for YES chrome path |
| **Windows taskbar icon** | **OUT OF SCOPE for now** | Needs exe / resource / shortcut `.ico` replace — **not** pure CSS. Do not schedule 6.I until God reopens |

---

## On-disk scaffold inventory (installed — keep)

Do **not** delete. Engine + CSS are live under Program Files inject; continue HUD polish on these files.

| Path | Role |
|------|------|
| `src/workbenchInject.js` | Rank-1 inject engine (locate / backup / patch / teardown / fingerprint / health) |
| `media/inject/tokens.css` | Calibrated / 30% palette CSS variables |
| `media/inject/boot.css` | Calibrating splash cover |
| `media/inject/hud.css` | Post-boot chrome hooks (scaffold; Studio YES HUD incomplete) |
| `media/reference-calibrating-splash.png` | Boot asset (staged/copied on enable per inject engine) |
| `package.json` → `jarvis.injection.*` | Settings: `enabled`, `bootMs`, `fallbackWebview` |
| Commands | `jarvis.injection.enable` / `disable` / `reenableAfterUpdate` / `healthCheck` / `status` |
| `src/extension.js` | Activate gate → reconcile; command wiring |

Phases 1–5 modules remain: `suitModes`, `gitHud`, `threatHints`, `sessionCinema`, `workspacePresets`, `voiceBridge`, themes, Command Center webview (demoted / fallback).

---

## Boot on IDE launch

- **Asset:** `reference-calibrating-splash.png` only (not command-center PNG as boot).
- **Delivery:** Workbench injection on Cursor/IDE launch → full-bleed cover → hold `jarvis.injection.bootMs` (default 1200) → fade/reveal HUD.
- **Not** a separate splash executable.
- Corrupt warning after patch is expected UX.

---

## Startup scope — Recomp folder IDE-only

| Lock | Value |
|------|--------|
| **Primary product scope** | JARVIS inject / theme work targets the **Recomp folder IDE** session (`C:\PS2Recomp` / this extension workspace) |
| **Document** | Treat Recomp Cursor window as the verify / Admin-enable / QA surface |
| **One window** | `window.restoreWindows: "one"`; do **not** dual-restore `E:\PS2Recomp.code-workspace` + folder; no Startup-folder Cursor shortcuts |
| **Splash** | Injection path only (`boot.css` / `jarvis.injection.*`) — never a separate splash exe or new window to show it |
| **Sibling note** | A sibling agent or other Cursor window **may apply settings** that affect user/global Cursor config; that does not expand product scope — still document and verify against **Recomp IDE** |

Full write-up: [`STARTUP-IDE-ONLY.md`](./STARTUP-IDE-ONLY.md). Workers soft-fail on Admin; Joshua enables inject in the Recomp-scoped Admin session per [`GOD-ADMIN-ENABLE.md`](./GOD-ADMIN-ENABLE.md).

---

## Architecture (target)

```mermaid
flowchart TB
  ext[extension.js]
  inject[workbenchInject Rank-1]
  boot[boot splash calibrating PNG]
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

Core idea: IDE launch → calibrating PNG via inject → Command Center chrome with Studio YES completeness. No overlay path. No Gumroad. No Active support.

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

## Continue checklist (paused — Joshua)

- [x] Cold-reopen this master + plan  
- [x] Scaffold files still present (inventory above)  
- [x] Admin Enable attempted / Program Files patched (see session log)  
- [ ] Confirm IDE opens workspaces cleanly after elevation/restore if needed  
- [ ] Boot splash matches calibrating PNG (QA)  
- [ ] Fail-safes 1–2 behave on fake update / broken markers  
- [ ] Continue **6.3.E QA → 6.3.F → 6.3.G → 6.3.H** when Joshua resumes  
- [ ] Leave taskbar `.ico` alone until 6.I reopened  
- [ ] Keep Active support OUT; keep hybrid palette; keep Recomp IDE as verify scope  

---

*Master consolidate for cold reopen. Sibling docs remain authoritative detail; plan wins on lock conflicts. **PAUSED** — agents stopped; Joshua switching to JARVIS personally. Session log above is the night record.*
