# Hitman web rebuild success → same crash (2026-11-07)

**Time:** ~08:56–08:57 local  
**Game:** Hitman Blood Money `a2116d2ac08a7be4db4e8455ad58d2e5`

## Rebuild — SUCCESS

- Command: `windows_port.build_web` (Python 3.10)
- Exit: **0**
- Published: `build/web-a2116d2ac08a7be4db4e8455ad58d2e5/ps2web.wasm` @ **2026-11-07 08:56:51** (55,353,839 bytes)
- Full build log: `logs/hitman-web-rebuild-2026-11-07.log`

## Harness re-verify on new player — SAME CRASH (still broken)

- Harness: `tools/_cyberarcade_live_harness.py 45 Hitman_BM`
- Run dir: `logs/harness-runs/20261107T135712Z/`
- Screenshots (harness Playwright UI only): `logs/screenshots/harness-20261107T135712Z/hitman_bm/`
- `#boot-status`: Game stopped — crash log saved
- Halt / help text: **The browser engine script could not load. Rebuild this game or check the server.**
- Console: `net::ERR_CONTENT_LENGTH_MISMATCH` (and a 404)
- Result: `booted=False`, `abort_seen=True`, `max_prims=0` — never reached menu / prior black-canvas path

## Serve note

After publish, `GET/HEAD http://127.0.0.1:8620/play/a2116…/ps2web.js` Content-Length **244503** ≠ disk **241343** → script load abort.

## Cross-ref

Full bisect narrative: `verification/recovery/hitman-ui-regression-bisect-2026-11-07.md`