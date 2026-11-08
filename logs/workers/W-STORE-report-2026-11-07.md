# W-STORE report — 2026-11-07

**Worker:** W-STORE  
**Repo:** `C:\PS2Recomp`  
**Panel:** unchanged — `scripts/panel.py` `PORT = 8620`, CyberArcade branding preserved  

## Mission summary

Additive post-download / post-build hooks for the store → import → build chain, gap documentation, optional strict verify, manifest stub, regression tests.

## Shipped

| Item | Path | Notes |
|------|------|-------|
| Hook module | `scripts/store_pipeline_hooks.py` | Manifest, pipeline jsonl, `PS2_STRICT_VERIFY`, strict health gate |
| Import | `panel.import_game` | Writes `install_manifest.json` at queue time; logs store download job id |
| Build | `panel.build` | `finalize_post_build` after `install_health` + `self_heal` |
| Download | `store.download` / `store.py` | Passes `download_job_id` into importer payload |
| Gaps doc | `verification/recovery/autonomous-pipeline-2026-11-07.md` | Store hooks table + documented non-goals |
| Tests | `tests/store_pipeline.py` | **17/17 OK** (manifest, strict verify, job id, inline verify) |

## Manifest stub (`games/<id>/install_manifest.json`)

- `schema`, `game_id`, `title`, `download_job_id`
- `source`: `sha256`, `bytes`, `path_basename`
- `timestamps`: `import_queued_at`, `build_completed_at`
- `health_status` / reasons / warnings after build
- `pipeline.autonomous_verify_inline`: set **true** when `PS2_INLINE_VERIFY=1` ran on a full install

## Environment

- `PS2_STRICT_VERIFY=1` (or `true`/`yes`/`on`): full installs fail on health **fail** (existing `gate_ready`) or **warn** (`gate_strict_ready`).
- `PS2_INLINE_VERIFY=1`: full installs run `autonomous_verify.py` smoke before `ready` (`PS2_INLINE_VERIFY_FRAMES`, default 200).

## Documented gaps (remaining)

1. **Nightly download → build → heal → verify** — event log exists (`store-pipeline-events.jsonl`); no scheduler in repo.
2. **Chrome harness `canvas_lum` at install** — still self-heal / web rebuild lane.
3. **Store pull → Chrome flawless without manual steps** — depends on Hitman/web matrix campaign (§1–§2).

## Master plan §3 checkboxes

- [x] Post-build hooks + post-download events
- [x] `install_manifest.json`
- [x] `PS2_STRICT_VERIFY`
- [x] Inline autonomous_verify before ready (`PS2_INLINE_VERIFY=1`; see `logs/workers/W-STORE-platform-2026-11-07.md`)
- [ ] Nightly pipeline
- [ ] Store → Chrome definition of done

## Test command / evidence

```text
py -3 c:\PS2Recomp\tests\store_pipeline.py -v
Ran 17 tests in 0.238s — OK
```


## Files touched

- `scripts/store_pipeline_hooks.py` (new)
- `scripts/panel.py`
- `scripts/store.py`
- `tests/store_pipeline.py`
- `verification/recovery/autonomous-pipeline-2026-11-07.md`
- `logs/master-campaign-plan-2026-11-07.md`
