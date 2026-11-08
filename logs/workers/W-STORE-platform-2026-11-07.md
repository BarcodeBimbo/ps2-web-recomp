# W-STORE platform — 2026-11-07

**Worker:** W-STORE  
**Lane:** Store → downloader → install → ready + panel web shell  
**Heartbeat:** `logs/workers/W-STORE-platform-heartbeat.log`

## Checkbox moved (§3)

| Item | Was | Now |
|------|-----|-----|
| Inline `autonomous_verify` smoke before `ready` | open (CLI/nightly gap only) | **[x]** opt-in gate on hot path |

**Evidence:** `scripts/store_pipeline_hooks.py` (`inline_verify_enabled`, `run_inline_autonomous_verify`, `gate_inline_verify` → called from `finalize_post_build`); `tests/store_pipeline.py` (3 new cases); plan mark in `logs/master-campaign-plan-2026-11-07.md`; architecture note in `verification/recovery/autonomous-pipeline-2026-11-07.md`.

## Behavior

- Default: unchanged — no smoke on every install.
- `PS2_INLINE_VERIFY=1` (full installs only): runs `scripts/autonomous_verify.py --game <id> --frames N --json` before panel sets `ready`.
- Frames: `PS2_INLINE_VERIFY_FRAMES` (default **200**, min 30).
- Fail / error statuses raise `RuntimeError` → install does not become ready; manifest records `pipeline.autonomous_verify_inline` + status/error; event on `logs/autonomous-pipeline/store-pipeline-events.jsonl` (`kind=inline_verify`).
- Pass / skipped: manifest timestamps `inline_verify_at`, status + log path.

## Tests

```text
py -3 tests/store_pipeline.py -v
Ran 17 tests in 0.238s — OK
```

New: `test_inline_verify_skipped_unless_env`, `test_inline_verify_blocks_fail_status`, `test_finalize_runs_inline_verify_and_updates_manifest`.

Incidental fix (unblocks existing web publish test): hoist `_rmtree_onerror` in `windows_port.build_web` so backup cleanup always has the handler in scope.

## Still open (§3)

- [ ] Nightly: download → build → heal → verify log under `logs/autonomous-pipeline/`
- [ ] Store pull → playable in Chrome without manual patch steps

## Non-goals this turn

No Alchemy / Hitman GS / game-specific registry edits.
