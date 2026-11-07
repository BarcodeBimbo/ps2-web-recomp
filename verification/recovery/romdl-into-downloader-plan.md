# RomDL → main Downloader plan (simple)

**Date:** 2026-11-06  
**Correction:** Do **not** put RomDL into Settings. Useful parts go into the main `downloader/` package (`downloader.js` + workers). Skip WebDL-style one-or-two-URL helpers.

---

## 1) Line-one error — fixed

| Item | Detail |
|------|--------|
| Error | `Cannot find module 'phantomwright'` on `RomDL/Downloader.ts` line 1 |
| Cause | RomDL had **no** `package.json` / `node_modules`; npm package name is **`phantomwright`** (not a separate “Phantom Wright” package) |
| Fix | Added `RomDL/package.json` + `tsconfig.json`, ran `npm install` (`phantomwright@1.59.3` + TypeScript/`@types/node`) |
| Check | `npx tsc --noEmit` in `RomDL/` → **exit 0** |

Production browser downloads already use `downloader/worker.mjs`, which imports the same `phantomwright` from `downloader/package.json` (already installed).

---

## 2) What already lives in main `downloader/`

| Need | Status |
|------|--------|
| Parse store pages / search | **`downloader.js`**: `catalogURL`, `fetchProvider`, `searchRoms` (comment: retained from RomDL) |
| Fresh CDN / browser download | **`worker.mjs`**: origin-IP + captcha job key + CDN transfer |
| Torrent backup | **`torrent_worker.mjs`** + store.py fail-over when CDN blocked |

So the **architecture** is already the main Downloader folder — RomDL is a leftover CLI side project.

---

## 3) Gaps to carry from `RomDL/Downloader.ts` into `downloader.js`

Only the useful differences — **not** Settings UI, **not** WebDL:

1. **Titles from the web store**  
   RomDL `searchRoms` returns `{ title, url }` (slug → readable title).  
   Current `downloader.js` returns `{ html, urls }` only.  
   **Plan:** extend `searchRoms` to also return `games: [{ title, url }]` (keep `urls` for compatibility).

2. **USA / demo filtering helpers**  
   RomDL has `US_RE` / `DEMO_RE` and version picking. Main `worker.mjs` already has `chooseVersion`.  
   **Plan:** move shared regex/helpers into `downloader.js` if store catalog UI needs them; avoid duplicating worker logic.

3. **Fresh download polish**  
   Compare RomDL `processDownload` (ad-block route list, filename cleaning) vs `worker.mjs`.  
   **Plan:** port any missing ad-block domains / `cleanFilename` into worker or a small `downloader.js` helper — only if store path lacks them.

4. **Torrent backup**  
   Already in main path — **no RomDL port needed**. Confirm store.py still fails over CDN → torrent (already does).

5. **Do not carry**  
   - WebDL / single-URL toys  
   - RomDL CLI interactive prompts as the product UX (Store tab stays the UI)  
   - Putting download UI into **Settings** (captcha key stays in Settings; downloads stay Store/Downloads)

---

## 4) Suggested order (no big bang)

1. ~~Fix phantomwright / typecheck~~ **done**  
2. Enrich `downloader.js` `searchRoms` with titles  
3. Wire store catalog API/panel to show those titles if not already parsing HTML client-side  
4. Diff RomDL vs worker for download/filename gaps; small patches only  
5. Mark `RomDL/Downloader.ts` as legacy CLI (or thin wrapper calling `downloader.js`) once parity is enough  

**No commits until a stable build** (per project rule).

---

## 5) Open

User still has a cut-off “other fix” — pick up when named.
