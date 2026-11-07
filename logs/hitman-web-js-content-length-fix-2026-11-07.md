# Hitman web `ps2web.js` Content-Length mismatch — root cause + fix (2026-11-07)

**Game:** Hitman Blood Money `a2116d2ac08a7be4db4e8455ad58d2e5`  
**Symptom:** After rebuild PASS, harness abort — “The browser engine script could not load” / `net::ERR_CONTENT_LENGTH_MISMATCH`  
**Prior note:** `logs/hitman-web-rebuild-then-same-crash-2026-11-07.md`

## Verify

| Check | Result |
|---|---|
| Disk `ps2web.js` | 241343 B @ 08:56:53 |
| `HEAD/GET` Content-Length | **244503** (= 3159 compat + 1 + 241343 glue) |
| Bytes actually received | **3160** (compat prefix only) → IncompleteRead / ERR_CONTENT_LENGTH_MISMATCH |
| Other games’ `/play/…/ps2web.js` | **OK** full body (prefix+glue) |
| Hitman `ps2web.wasm` / `.data` / shell HTML | **OK** full body |

## Root cause

Not a general Content-Length math bug. `serve_player_js` correctly prefixes `web/gpu_upload_compat.js` and advertises `len(prefix)+size(js)`.

**Only Hitman’s freshly rebuilt `ps2web.js` was unreadable by the non-elevated panel process.**

ACL after rebuild (bad):

```
NT AUTHORITY\SYSTEM:(F)
BUILTIN\Administrators:(F)
OWNER RIGHTS:(F)
```

No `BUILTIN\Users:(RX)` / `Authenticated Users` — unlike sibling assets in the same folder (`ps2web.wasm`, `.data`, `.html`) and unlike other games’ `ps2web.js`. Owner was `BUILTIN\Administrators`.

Panel could `getsize()` (attributes) → correct Content-Length, then failed `open()` for read → wrote only the already-buffered compat prefix → browser abort.

Isolated repro of prefix+`copyfileobj` on Python 3.14 with the same files **succeeds**; other games on the live panel **succeed** — confirms file ACL, not the stream pattern itself.

## Fix applied

1. **Immediate:** `icacls build/web-a2116…/ps2web.js /reset` → inherited Users RX. Re-GET → **GOT 244503** (match CL).
2. **Publish hardening:** `windows_port.ensure_web_build_readable()` runs `icacls /reset` on published player assets after `build_web` swap.
3. **Serve hardening:** `serve.serve_player_js` reads compat+glue **before** headers; on `OSError` returns HTTP 500 instead of advertising length and truncating (needs panel restart to load).

## Re-verify serve (post-ACL)

```
ps2web.js   200 CL 244503 GOT 244503
ps2web.wasm 200 CL 55353839 GOT 55353839
ps2web.data 200 CL 4971519 GOT 4971519
ps2web.html 200 CL 151920 GOT 151920
```

## Harness re-check (post-ACL)

- Run: `logs/harness-runs/20261107T140555Z/`
- Shots: `logs/screenshots/harness-20261107T140555Z/hitman_bm/`
- **abort_seen=False**, **booted=True**, max_prims≈865k, GPU, overlay ~60 FPS
- Script-load crash **cleared**
- Remaining product issue (pre-existing): **black canvas** (`canvas_lum≈0.14`, UI chrome + FPS overlay visible) — same black-screen path as pre-rebuild harness `20261107T131504Z`, not the serve abort

## Code changes

- `scripts/windows_port.py` — `ensure_web_build_readable()` after publish
- `scripts/serve.py` — `serve_player_js` reads full body before headers; OSError → 500 (panel restart to pick up)
