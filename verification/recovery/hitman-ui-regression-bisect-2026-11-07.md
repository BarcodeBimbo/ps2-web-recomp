# Hitman UI regression bisect — 2026-11-07

**Priority:** restore Hitman past first loading bar / visible UI (harness Chrome only for shots).

## What God reported

Previously Hitman reached real UI / game parts, then crashed after NTS load. Now black before the first loading bar.

## Candidate “~34 files” delta

Closest match in history: commit **`ffdc179`** (2026-11-07 ~07:52) — **37 files**, Alchemy `cdvdfsv.cpp` + `igfileio.cpp` intro-hold / soft-arm (plus logs). Follow-ups: `7d7eb41` (cdvdfsv), `a002696` (obj+0x20 restore).

Harness / shell changes this morning are separate (tools + uncommitted `web/shell.html` abort guards).

## Evidence

### Native (post-Alchemy `ps2run`, rebuilt ~07:44+)

Command: `ps2run games/…/disc/boot.elf --disc …/disc.iso --frames 900`  
Log: `logs/hitman-native-postalchemy-900.log`

- BOOTMENU.ZIP / WHD / WAV **found**
- **261,904** primitives, exit 0, frame limit
- **No** butanim/intro-gate spam (virt/Alchemy path not entered)
- Verdict: Alchemy soft-arm / intro-hold **did not break** Hitman native boot→BOOTMENU path

### Web harness (Playwright Chrome only — God screenshot rule)

Run: `logs/harness-runs/20261107T131504Z/` + shots under `logs/screenshots/harness-20261107T131504Z/hitman_bm/`

- Disc mounts; BOOTMENU searches **found** in `console.jsonl`
- WebGPU present; 60 FPS overlay; prims grow to **~675k**
- Canvas luminance stays **~0.1–0.2** (pure black) for boot/mid/end — **no visible loading bar/UI**
- Compare same run: GoW canvas mid/end **~47**; Sly **~14**; Hitman stays black

### Web binary age

`build/web-a2116d2…/ps2web.wasm` last built **2026-11-06 ~12:23** — **before** today’s Alchemy commits. Panel injects live `web/shell.html` over that wasm (`scripts/panel.py` `serve_player_shell`).

So today’s Alchemy edits are **not** inside the Hitman web wasm. Black canvas is a **web present/UI** failure while the EE still advances BOOTMENU work.

### Shell abort-guard (uncommitted)

`web/shell.html` safe `_ps2web_frames` guards — live via panel. Harness Hitman was already canvas-black **before** that edit (08:08 run). Guard is not the black-screen root cause; it only stops the early `ps2web_frames` assert.

## Conclusion (current)

| Change | Breaks Hitman UI? |
|--------|-------------------|
| Alchemy `ffdc179` / `7d7eb41` / `a002696` | **No** for native BOOTMENU; not in web wasm |
| Harness Python | No — observes black; does not alter GS |
| `web/shell.html` abort guards | No — black predated them |
| Stale Hitman **web** player (Nov 6 wasm) vs current native | **Likely gap** for web visuals; rebuild + harness re-verify required |

## Next actions

1. Rebuild Hitman `build/web-a2116d2…` so web runtime matches native disc-fix.
2. Re-run `_cyberarcade_live_harness.py` Hitman-only; shots **only** from harness Playwright page; require canvas_lum ≥ threshold + BOOTMENU still in console.
3. Keep Alchemy virt-gated; do not apply CNK soft-arm to Hitman.
4. After UI visible again: chase post-NTS abort separately.

---

## Rebuild success + same crash (2026-11-07 ~08:57) — LOGGED

**Rebuild:** `windows_port.build_web('a2116d2a…')` **PASS** exit 0 (~37 min).  
Artifacts: `build/web-a2116d2ac08a7be4db4e8455ad58d2e5/`  
- `ps2web.wasm` **55,353,839** B @ **2026-11-07 08:56:51** (was Nov 6 12:23)  
- `ps2web.js` **241,343** B @ 08:56:53  
Terminal: agent shell `830623` / log `logs/hitman-web-rebuild-2026-11-07.log`

**Immediate harness re-verify (new player build) — SAME CRASH class / still broken:**

| Item | Value |
|------|--------|
| Run | `logs/harness-runs/20261107T135712Z/` |
| Shots (harness UI only) | `logs/screenshots/harness-20261107T135712Z/hitman_bm/` (`00_halt.png`, `01_boot.png`, …) |
| Boot status | `Game stopped — crash log saved` |
| On-screen / help | **The browser engine script could not load. Rebuild this game or check the server.** |
| Console | `net::ERR_CONTENT_LENGTH_MISMATCH` + prior `404` |
| Harness summary | `booted=False` `abort_seen=True` `max_prims=0` `ok=False` |
| Alias | `logs/cyberarcade-live-harness-latest.json` |

**Serve check after rebuild:** panel `HEAD` for `ps2web.js` advertised **Content-Length 244503** while disk file is **241343** → browser aborts script load (`ERR_CONTENT_LENGTH_MISMATCH`). Wasm/data lengths matched disk. HTML path is shell-injected (hdr ≠ disk `ps2web.html` is expected).

**Plain verdict:** New Hitman web player **did build**, but first harness load after publish **still crashes** — engine script failed to load (length mismatch / serve), so the session never reached the prior black-canvas BOOTMENU path. Treat as **same product failure after rebuild** (player unusable in Chrome harness) until panel serve / Content-Length is fixed and harness shows non-abort boot.

Also mirrored: `logs/hitman-web-rebuild-then-same-crash-2026-11-07.md`
