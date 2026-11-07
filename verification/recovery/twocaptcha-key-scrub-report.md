# 2Captcha key scrub report

**Date:** 2026-11-06  
**Rule (corrected):** The key lives in **browser localStorage only** (Settings cog → `ps2-twocaptcha-api-key`). It must travel **panel → request body → job JSON stdin → worker**. Do **not** use or recommend `process.env.TWOCAPTCHA_API_KEY` / shell export.

Raw key values are never printed here. Any historical secret is shown as `***REMOVED***`.

---

## Verdict

| Check | Result |
|--------|--------|
| Hardcoded key in current working tree | **Not found** |
| `config/store.private.json` | **Absent** (scrub ran; nothing to delete) |
| `.env` / `*.env` with captcha fields | **None found** |
| Chrome downloader profile storage | **No captcha key strings found** |
| Known key fragment in RomDL/scripts/downloader/web/config/verification | **No hits** |
| Git history (commit `e99ef4a`) | **Did contain a hardcoded literal** in `RomDL/Downloader.ts` |
| **Rotate key?** | **Yes** — it was committed once; treat as exposed |

---

## Where it was found

### Current tree (safe)

- **No hardcoded `clientKey: '…'` / string-literal API key** in `RomDL/Downloader.ts`, `downloader/worker.mjs`, `downloader/solver.js`, `web/panel.html`, or `scripts/*`.
- Panel already keeps the secret client-side:
  - localStorage name: `ps2-twocaptcha-api-key`
  - Save on Settings form submit via `setTwocaptchaKey()` (does **not** POST the key to `/api/settings`)
  - Download calls wrap payloads with `withTwocaptcha()` so the key rides on the request body only for that job

### Legacy / history (exposed)

- Commit **`e99ef4a`** (“Initial Windows CyberArcade tree”) added `RomDL/Downloader.ts` with a **hardcoded** captcha client key literal (`hardcoded_literal_in_diff: True`). Current HEAD no longer has that literal; it still reads `process.env.TWOCAPTCHA_API_KEY` until the parent’s localStorage→stdin path lands.
- Recovery note `verification/recovery/08d63_full_extract.md` (and agent-tools extract) still **mentions** that old hardcode existed — documentation only, not a live secret.
- Prior session tools searched for fragment `30FA9CE98`; that fragment is **not** present in the scanned source/config paths above.

### Server-side copies

| Location | Status |
|----------|--------|
| `config/store.private.json` | Missing. `scripts/store_settings.scrub_private_file()` strips `twocaptcha_api_key` and deletes empty files — ran successfully. |
| `.env` files | None under the repo (excluding ignored chrome/node trees). |
| Process environment `TWOCAPTCHA_API_KEY` | Not set in this scrub shell. |

---

## Where it was removed / already clean

- Working-tree hardcode: already gone (env/variable only; no secret string).
- Server persistence of captcha: already scrubbed by design in `store_settings.py` (field popped; public API returns empty key + `twocaptcha_storage: localStorage`).
- No scrub commit required for leftover hardcodes — nothing secret remained to delete in source.

---

## Still present (non-secret / pending parent fix)

These are **code paths / names**, not hardcoded secrets. **Parent landed the stdin job JSON path** (2026-11-06): `runtime_env()` no longer sets/inherits `TWOCAPTCHA_API_KEY`; `store._run_node_worker` puts `twocaptcha_api_key` on the job; `downloader/worker.mjs` and `RomDL/Downloader.ts` no longer read process env for captcha.

Was pending (now done):

| File | What remains |
|------|----------------|
| `RomDL/Downloader.ts` | Still reads `process.env.TWOCAPTCHA_API_KEY` (must become job/local path only). |
| `downloader/worker.mjs` | Still `process.env.TWOCAPTCHA_API_KEY \|\| ''`. |
| `scripts/downloader_runtime.py` | Still injects `TWOCAPTCHA_API_KEY` into the Node env from the per-job argument (or ambient env). |
| `scripts/store.py` | Still passes normalized request-body key into `runtime_env(...)`. |
| `verification/recovery/08d63_full_extract.md` | Historical warning text only. |

**Intended end state (parent):** Settings cog → localStorage → download request body → job JSON on stdin → worker/solver. No env export. No disk copy.

---

## Panel localStorage — how to clear

Key name: **`ps2-twocaptcha-api-key`**

**In the running CyberArcade panel (recommended):**

1. Open Settings (cog).
2. Clear the 2Captcha field.
3. Save — UI should say “Saved in this browser only.” Empty save calls `localStorage.removeItem('ps2-twocaptcha-api-key')`.

**Or DevTools on the panel origin:**

```js
localStorage.removeItem('ps2-twocaptcha-api-key');
```

**This scrub session:** IDE browser had **no open panel tabs**; localhost panel ports checked were **down**, so automated clear was **not** performed. If you already cleared it manually, that matches the intended empty state. Re-check after the panel is up.

---

## Rotate key?

**Yes.** Because a real-looking key was committed in `e99ef4a`, rotate/revoke it at 2Captcha and paste the new key **only** into the Settings cog (localStorage). Do not put it in `.env`, `store.private.json`, source, or chat.

---

## Open follow-up (user cut off)

The user also started describing **another fix** and got cut off. That item remains open — pick it up when they say what it was. See also `verification/recovery/open-followups.md`.
