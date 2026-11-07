# W-NFS-2 — web disc stream prefetch deepen (2026-11-07)

**Worker:** W-NFS-2  
**Game id:** `60c82f4a111da300ac23bbec85272788` (Need for Speed — Most Wanted)  
**Shared file:** `host/web.cpp` (game-agnostic; affects all web titles)  
**Quarantine:** no CNK / Alchemy on NFS path  
**Hitman locks:** **not touched** (`web-a2116…` remains `campaign-owner-fresh`)

---

## Prior diagnosis (trusted)

Chrome ~13 FPS / ~500 ms hitches = EE stalls in `chunk()` / `read_ahead()` / `ps2web_fetch`, not software GS.  
Evidence: `logs/workers/W-NFS-fresh-2026-11-07.md`. `gpu_boot` OK; `canvas_lum` recovers.

---

## Before → after (hypothesis)

| Knob | Before (stale shipped wasm / early path) | After (this change) |
|------|------------------------------------------|---------------------|
| Max read-ahead depth | 16 chunks (4 MiB) | **48** chunks (~12 MiB); env `PS2_DISC_READAHEAD` 4..64 |
| Post-seek min depth (`g_run→0`) | 8 (or prior 16 mid-pass) | **24** chunks (~6 MiB); env `PS2_DISC_PREFETCH_MIN` |
| Concurrent `ps2web_fetch` | Uncapped start-all **or** mid-pass cap 12 | **16** closest-to-focus; env `PS2_DISC_MAX_FETCHES` |
| Futex wait quantum in `chunk()` | 1000 ms | **250 ms** (keeps `discWaiting` + render `service_disc`) |
| `want()` after seek | Far stale `kWanted` blocked new focus | Steal far Wanted beyond `2×readahead` |

**Hypothesis:** Deeper post-seek warm + more concurrent Range fetches (priority nearest to EE focus) cuts cold-chunk serialization so VU/GS stay fed, hitch ≪500 ms, overlay can reach ≥60. **Not proven until Chrome harness.** Do **not** flip §2b Chrome≥60 checkbox.

---

## Code touch points

- `host/web.cpp`: `kReadAheadDefault` / `kPrefetchMinDefault` / `kMaxFetchesDefault`
- `read_ahead()`, `want()`, `service_disc()`, `chunk()` (already priority + steal path)

---

## Lock / rebuild status

| Item | Status |
|------|--------|
| `logs/locks/web-60c82f4a….lock` | Held by **W-NFS-2** |
| NFS web rebuild | In flight / monitored under `build/web-60c82f4a…-next` (do not kill) |
| Published `ps2web.wasm` | Stale until `-next` promotes (was 2026-11-06 ~11:11) |
| Hitman `web-a2116` rebuild | **Still required** for shared `host/web.cpp` — leave to campaign owner; do not steal lock |

---

## Owner note (Hitman)

`host/web.cpp` is shared. NFS rebuild alone does **not** ship the stream fix into `build/web-a2116d2ac08a7be4db4e8455ad58d2e5/`. Campaign owner must rebuild Hitman web when their lock/`checkbox=hitman-black-fix` work allows.

---

## Chrome ≥60

**Unchecked.** Harness proof still required after NFS wasm publish.

*W-NFS-2 — deepen → rebuild under lock → evidence; no checkbox flip.*
