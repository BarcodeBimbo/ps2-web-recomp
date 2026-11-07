# W-NFS fresh — NFS GPU / hitch diagnosis (2026-11-07 ~18:50 local)

**Worker:** W-NFS  
**Game id:** `60c82f4a111da300ac23bbec85272788` (Need for Speed — Most Wanted)  
**Locks:** acquired+released `logs/locks/native-60c82f4a111da300ac23bbec85272788.lock` (W-NFS smoke). **Did not touch** Hitman `web-a2116…` lock (campaign-owner-fresh).  
**Quarantine:** no CNK/Alchemy patches.

---

## Open plan checkboxes (§2b)

| Checkbox | Status |
|----------|--------|
| Same GS A–H checklist | [x] prior `W-NFS-report-2026-11-07.md` |
| Matrix `fileio` scorer | [x] prior |
| **NFS Chrome flawless + ≥60 FPS** | **[ ] still open** — this pass diagnoses root cause; no Chrome re-harness |

---

## Fresh native smoke (safe, no kills)

```text
build/native-60c82f4a…/ps2run.exe games/…/disc/boot.elf --disc games/…/disc.iso --frames 300
```

| Field | Result |
|-------|--------|
| Exit | frame limit reached |
| Prims | **12895** (early boot window) |
| Disc | `[fileio] open cdrom:\NFS\IRX281A.BUN` |
| SIF | `0 packets wait` |
| Log | `logs/autonomous-pipeline/60c82f4a111da300ac23bbec85272788-smoke-W-NFS-20261107T184648Z.log` |

Prior 500f autonomous still stands: **140753** prims, matrix pass (`…-500f-20261107T153240Z.log`). Native disc path is healthy; Chrome is the FPS gate.

---

## Chrome vs Hitman (shot-compare, harness `20261107T131057Z`)

| Metric | NFS_MW | Hitman_BM |
|--------|--------|-----------|
| Goal | `gpu_boot` **ok** | menu / canvas fail |
| `software` | **False** (renderer=`gpu`) | False |
| Boot `canvas_lum` | **20.39** | **0.18** |
| Mid `canvas_lum` | **0.997** (transient black) | **0.13** (sustained) |
| End `canvas_lum` | **7.43** (recovers) | **0.14** (stuck) |
| Overlay FPS avg | **~20** (min ~9) | **~55–60** |
| Hitch peak | **~1110 ms** (steady ~500 ms) | boot hitch then stable |
| Console `[stats]` | `vu 100% gs 99%` **idle**, `audio 2–12 ms`, prims flat **~52308** | `vu/gs ~89%` idle labels differ; `audio ~80 ms` at 60 FPS |

**Conclusion:** NFS is **not** Hitman-class sustained black canvas and **not** software-render fallback. `gpu_boot` already passes. Failures are **Chrome ≥60 / hitch / mid-shot lum dip**.

---

## Top root-cause hypothesis

**EE disc-stream stall on web range-fetch, not VU/GS thrash and not software GS.**

Harness lines look like “VU/GS saturated,” but `web/shell.html` labels are **idle** percentages:

- `vu` = `ps2web_idle_ms(2)` → `vu_thread_idle_ms()`
- `gs` = `ps2web_idle_ms(1)` → render-thread idle (`g_render_idle`)
- `idle emu` = pace/vblank sleep only

So NFS mid-run `vu 100% / gs 99% / idle emu 4% / GPU ~0–4% / hitch ~500 ms / prims flat` means: **VU + GS workers asleep**, **EE not in pace-sleep**, presents arrive every ~500 ms, draws stop advancing. That matches **blocking in web disc `chunk()`** while HTTP `Range` fetches fill slots (`emscripten_futex_wait` up to 1 s), especially after a seek resets `g_run` (FMV / level / large FILEIO reads — NFS pattern).

**“Audio lag”** is secondary: queued audio collapses to **2–12 ms** (underrun) because frames/presents stall — not a primary SPU backlog (Hitman holds ~80 ms at 60 FPS).

Native ISO path has no HTTP chunk futex → continues drawing (500f ~140k prims).

---

## Concrete next fix (file + function)

1. **Primary:** `host/web.cpp` — `read_ahead()` / `want()` / `chunk()` / `service_disc()`  
   - After seek (`g_run → 0`), deepen prefetch + allow more concurrent `ps2web_fetch` in-flight so EE does not serialize on cold chunks.  
   - Optionally shrink futex wait quantum and ensure `ps2web_busy_heartbeat(1)` is visible to harness as `discWaiting` for shot-compare.  
   - Do **not** force `PS2_GS=software`.

2. **Validate:** re-run Chrome harness NFS-only; expect hitch ≪500 ms, prims keep climbing past ~52k, overlay ≥60, mid `canvas_lum` stays ≫1 (same A–H shared path — no Hitman present hacks).

3. **Out of scope here:** Hitman DISPFB/FRAME black canvas (`gs.cpp` `resolve_present_source`) — different symptom class.

---

## Evidence paths

| Kind | Path |
|------|------|
| Fresh native smoke | `logs/autonomous-pipeline/60c82f4a111da300ac23bbec85272788-smoke-W-NFS-20261107T184648Z.log` |
| Prior 500f + matrix | `logs/autonomous-pipeline/60c82f4a111da300ac23bbec85272788-500f-20261107T153240Z.log` |
| Chrome NFS+Hitman compare | `logs/harness-runs/20261107T131057Z/summary.json` (+ `run.log`) |
| NFS shots | `logs/screenshots/harness-20261107T131057Z/nfs_mw/` |
| Prior A–H report | `logs/workers/W-NFS-report-2026-11-07.md` |
| Disc chunk wait code | `host/web.cpp` (`chunk`, `read_ahead`, `ps2web_fetch`) |
| Stats idle semantics | `web/shell.html` `onFrame` / `_ps2web_idle_ms` |

---

## Master plan

**No §2b checkbox flip** — Chrome flawless/≥60 still unverified. Native smoke reconfirmed only.

*W-NFS — diagnose → evidence → next fix named.*
