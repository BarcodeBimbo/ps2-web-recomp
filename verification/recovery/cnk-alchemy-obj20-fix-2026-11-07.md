# CNK Alchemy obj+0x20 fix attempt — 2026-11-07

**GID:** `b49f2e769315347e8bda839feb705744`  
**Mode:** Implement (Target 3 Alchemy continuation)

---

## Summary

**BLOCKED** — obj+0x20 restoration implemented but timing prevents vt+108 retry.

The fix captures and restores obj+0x20/+0x14 when cleared, but the guest vt+108 runs with +0x20=0 in one uninterruptible EE execution burst before our HLE restoration can intervene. By the time restoration runs, vt+108 has already set +0xFF and the slot is at status 3 (past the finalize stage that would re-call vt+108).

---

## What was attempted

### 1. Capture and restore obj+0x20 (igfileio.cpp)

Added globals to track soft-arm values:
- `g_butanim_soft_o20` — captured obj+0x20 at soft-arm time
- `g_butanim_soft_o14` — captured obj+0x14 at soft-arm time  
- `g_butanim_o20_restore_count` — limit restoration attempts

Added `try_restore_butanim_o20()`:
- Detects when obj+0x20 is cleared (was captured non-zero)
- Restores obj+0x20 and obj+0x14 from captured values
- If +0xFF already set (vt+108 ran with +20=0), clears +0xFF to allow retry
- Called from multiple locations: `service_pending_stblz`, `rearm_alchemy_timer_intc`, `poll_butanim_parse_complete`, `try_kick_alchemy_font_tick`

### 2. Preserve +0x20 during soft-arm (cdvdfsv.cpp)

Modified the butanim soft-arm path to:
- Capture obj+0x14/+0x20 before arming +45
- Immediately re-write them after setting +45 to prevent guest clearing

### 3. Verification with *(obj+0x20)+0x24

Restoration logs confirm the attach chain is valid:
```
restored butanim obj+0x20=0x7462F8 +0x14=0x16B06E8 (was 0, +0xFF=1→0, *(+0x20)+0x24=0x1, count=1)
```

The value `*(+0x20)+0x24=0x1` (non-zero) means the 0x51C100 ingest condition WOULD pass if vt+108 re-ran.

---

## Timing analysis

| Step | What happens | When our HLE runs |
|------|--------------|-------------------|
| 1 | soft-arm captures +20=0x7462F8 | ✓ |
| 2 | Guest EE returns from IOP completion callback | — |
| 3 | Guest clears obj+0x20 (reason unknown) | ✗ no HLE hook |
| 4 | Guest FCE0 → 0x110100 → vt+108 runs with +20=0 | ✗ no HLE hook |
| 5 | vt+108 sees +20=0, skips 0x51C100, sets +0xFF=1 | ✗ no HLE hook |
| 6 | Guest slot advances to status 3 | — |
| 7 | Our restoration runs, restores +20, clears +0xFF | ✓ |

Steps 2-6 execute as one uninterruptible EE code block. Our HLE restoration (step 7) is too late.

---

## Why restoration after-the-fact doesn't help

1. vt+108 only runs during finalize (status 1 → vt+108 → status 3)
2. By restoration time, slot is already status 3 (finalized)
3. Clearing +0xFF allows our poll to re-detect, but guest won't re-call vt+108
4. Re-arming status to 1 crashes (ra=0x110224) — explicitly forbidden

---

## Log evidence

From `cnk-o20-fix3-2026-11-07-080022.log`:
```
[igfileio] noted butanim soft-arm obj=0x975498 (cleared +0xFF) +8=15 +14=0x16B06E8 +20=0x7462F8 assemble_butanim=1
...
[igfileio] restored butanim obj+0x20=0x7462F8 +0x14=0x16B06E8 (was 0, +0xFF=1→0, *(+0x20)+0x24=0x1, count=1)
...
[gs] 2 primitives drawn
```

Restoration ran successfully, but prims still stuck at 2.

---

## What would actually fix this

1. **Intercept the guest code that clears +0x20** — requires identifying the exact EE instruction and hooking it in the recompiled code, or using memory watchpoints that fire during EE execution.

2. **Host-call vt+108 directly** — risky because vt+108 (0x5032E0) has context dependencies (needs correct tid mapping, may access thread-local state). Prior attempts at host_call 0x10FCE0 crashed on tid mismatch (ra=0x51ACEC).

3. **Understand what clears +0x20** — the guest EE code between soft-arm and vt+108 includes the sceCdRead completion callback and possibly object state transitions. Need Ghidra analysis of 0x110100 / vt+108's early path.

4. **Fix _CdAlignReadBuffer equivalent** — retail path would wire up +0x14/+0x20 properly through the readee/curReadPos completion fields. For virt-GFC reads, ee1 dest stays 0 so that path never runs.

---

## Files changed

- `runtime/src/iop/igfileio.cpp` — added obj+0x20/+0x14 capture and restoration
- `runtime/src/iop/cdvdfsv.cpp` — added +0x20 preservation during soft-arm

---

## Return blob

```
prims_before: 2
prims_after: 2
crash: no
files: runtime/src/iop/igfileio.cpp, runtime/src/iop/cdvdfsv.cpp
log: logs/cnk-o20-fix3-2026-11-07-080022.log
blocked_or_verified: BLOCKED — restoration works but vt+108 already ran with +20=0; need earlier interception
```

---

## Hard rules compliance

- ✓ CNK/Alchemy-gated only (all paths behind alchemy_stbl_pending / virt-GFC checks)
- ✓ NO host_call(0x10FCE0)
- ✓ NO aggressive status=1 re-arm
- ✓ Verified with real CNK smoke (8000 frames, no crash)
- ✓ Hitman/NFS disc path untouched
