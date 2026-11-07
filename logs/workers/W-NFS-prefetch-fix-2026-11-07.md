# W-NFS-2 — web disc prefetch fix (2026-11-07)

**Worker:** W-NFS-2  
**Game id:** `60c82f4a111da300ac23bbec85272788` (NFS Most Wanted)  
**Prior diagnosis:** `logs/workers/W-NFS-fresh-2026-11-07.md`  
**Quarantine:** no CNK/Alchemy; Hitman `web-a2116*` / `native-a2116*` trees not touched.

---

## Lock status

| Lock | Status |
|------|--------|
| `logs/locks/web-60c82f4a111da300ac23bbec85272788.lock` | **Held** by W-NFS-2 (rebuild in flight) |
| Hitman `web-a2116*` / `native-a2116*` | Untouched (campaign-owner-fresh) |

---

## Before (trusted prior harness)

From `W-NFS-fresh-2026-11-07.md` / shot-compare `20261107T131057Z`:

| Metric | Before |
|--------|--------|
| Overlay FPS avg | ~20 (min ~9) |
| Hitch | steady ~500 ms (peak ~1110 ms) |
| Prims | flat ~52308 mid-run |
| `vu`/`gs` overlay | ~100% / 99% **idle** (workers asleep) |
| Root cause | EE stall in `host/web.cpp` `chunk()` / `read_ahead()` / `ps2web_fetch` after seek (`g_run → 0`) |

Prior `read_ahead` floor was **8** chunks, cap **16**; `service_disc` fired **all** Wanted slots with no priority / no in-flight cap; far Wanted slots were not reclaimable after seek.

---

## Change (`host/web.cpp` only — shared web host)

| Area | Change |
|------|--------|
| `read_ahead()` | Post-seek min depth **16** (was 8); grow `g_run*2+8` up to cap **32** (was 16) |
| `want()` | Reclaim **far** `kWanted` (not yet Loading) slots after seek so new focus can warm |
| `service_disc()` | Cap concurrent Range fetches (**12** default); start Wanted slots **closest to `g_last_chunk` first** |
| `chunk()` | Futex wait quantum **250 ms** (was 1000) so `discWaiting` heartbeat + render `service_disc` re-enter sooner |
| Env gates | `PS2_DISC_READAHEAD` (4–64), `PS2_DISC_PREFETCH_MIN` (1–64), `PS2_DISC_MAX_FETCHES` (1–64) |

Defaults are general (all games). Env knobs allow dialing back without a code revert if Hitman/other titles regress.

**Not done:** software GS; Hitman present hacks; CNK Alchemy on NFS path.

---

## Rebuild

| Field | Value |
|-------|--------|
| Started | yes — `python -u logs/workers/W-NFS-rebuild-web.py` |
| Log | `logs/workers/W-NFS-web-rebuild-2026-11-07.log` |
| Err | `logs/workers/W-NFS-web-rebuild-2026-11-07.err.log` |
| Target | `build/web-60c82f4a111da300ac23bbec85272788` via `windows_port.build_web` (`-next` then publish) |

---

## After evidence

| Gate | Status |
|------|--------|
| NFS web rebuild complete | **In flight** at report write |
| Chrome harness ≥60 FPS / hitch ≪500 ms / prims climbing | **Not yet** — do not flip master-plan checkbox |
| Master plan `NFS Chrome flawless + ≥60 FPS harness` | **Left open** |

**Expected after publish + harness:** hitch collapse, overlay ≥60, mid `canvas_lum` stays ≫1, prims past ~52k. Re-run NFS-only Chrome harness; append results here and flip `logs/master-campaign-plan-2026-11-07.md` §2b checkbox only on proof.

---

## Files changed

- `host/web.cpp` — disc stream prefetch / concurrent fetch policy
- `logs/workers/W-NFS-rebuild-web.py` — NFS-only rebuild helper
- `logs/workers/W-NFS-prefetch-fix-2026-11-07.md` — this report
- `logs/workers/W-NFS-heartbeat.log` — heartbeats
- `logs/locks/web-60c82f4a111da300ac23bbec85272788.lock` — acquired
