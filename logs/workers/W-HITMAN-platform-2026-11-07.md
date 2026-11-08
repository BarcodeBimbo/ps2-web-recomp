# W-HITMAN platform — 2026-11-07

**Lane:** Hitman only (`a2116d2ac08a7be4db4e8455ad58d2e5`)  
**Quarantine:** no CNK Alchemy patches

## Lock status

| Lock | Status |
|------|--------|
| `native-a2116…` | **Held by W-HITMAN** (pid of rebuild shell). Prior `campaign-owner-fresh` pid **20640 DEAD**. |
| `web-a2116…` | **Held by W-HITMAN** — note: *not* building published web; monitoring only. |
| `web-a2116…-next` | **Live build** — cmake **29328** / ninja **5044** (`-j1 ps2web`). Stale note from dead campaign-owner 17900; **do not** start competing ninja. Progress ~**455/931** at report time. |

## Build status

| Tree | Status |
|------|--------|
| `build/native-a2116…` | **OK** — `ps2run.exe` linked **2026-11-07 19:14** after type-7 FST fix (`logs/workers/W-HITMAN-native-type7fst-build.log`). |
| `build/web-a2116…-next` | **In flight** (~455/931 game units). Current tree **predates** type-7 FST source edit → needs a **follow-up** web rebuild after this -next finishes/publishes. |
| Published `build/web-a2116…` | Stale wasm **11:09** (XYOFFSET era); **no** harness flip yet. |

## Concrete action taken (this slice)

**(B) sprite/tex path — PRIM type 7 × FST empty-UV**

Evidence from post-XYOFFSET `draws.tsv`: all **150** `0x7FF` (type **7** + **FST** + TME) batches log texel AABB `0.0,0.0-0.0,0.0` (UV never written). Sprite remap of type 7 already falsified (black quads).

**Code:** when remapping undefined PRIM 7 → POINT, also **clear FST** so textured kicks sample sticky **ST/Q**:

- `runtime/src/gs/gpu/gpu.cpp` — `draw`
- `runtime/src/gs/raster.cpp` — `make_setup`
- `runtime/src/gs/gs.cpp` — comments + capture texel AABB matches draw path

Native **180f** smoke (`logs/hitman-capture-type7fst-180-2026-11-07/`):

| Page | Late full-page nz (512×H) | Notes |
|------|---------------------------:|-------|
| FBP 400 | ~10188 / mean ~0.0035 | ≈ prior post-XYOFFSET residual |
| FBP 288 | ~435 / mean ~0.0001 | Still near-empty in display crop |

Clear sprite boxes land at **`0..512×448`** (16-bit XYOFFSET confirmed). **Not** a `canvas_lum` pass — DISPFB page still sparse; host 288→400 blit remains deferred.

## Master-plan checkboxes

- [ ] `canvas_lum` pass — **not flipped** (no web publish + harness yet; native lum still fail-class).
- [ ] DISPFB vs FRAME compose blit — **not flipped** (research (B) in progress; raster still non-empty gate unmet).

## Next step

1. Let **web-next** finish → publish (WinError-32-safe) **without** killing ninja.
2. Rebuild web once more (or incremental) so **type-7 FST clear** is in `ps2web.wasm`.
3. Harness: `python scripts/autonomous_verify.py --game a2116… --frames 600 --json` → flip `canvas_lum` only if pass.
4. If still ~0.14: continue (B) on remaining empty-ST TME batches / ATE (`PS2_GS_NO_ATE` already opt-in) — not host blit.

*Worker: W-HITMAN platform — 2026-11-07*
