# Hitman black-canvas — caller-readable analysis pack

**Updated:** 2026-11-07 (during live TRACE / Ghidra pass)  
**Game:** `a2116d2ac08a7be4db4e8455ad58d2e5` (Hitman Blood Money PS2)  
**ELF:** `games/…/disc/boot.elf` in Ghidra as `hitman_boot.elf`

Read in this order (or jump by interest):

| # | File | What it is |
|---|------|------------|
| 1 | [`01-TRACE-highlights.txt`](01-TRACE-highlights.txt) | Short TRACE excerpts (PCRTC + present/drawenv) |
| 1b | [`01b-TRACE-full-latest.log`](01b-TRACE-full-latest.log) | Full latest runtime TRACE log (large) |
| 1c | [`01c-TRACE-draws-frame180.tsv`](01c-TRACE-draws-frame180.tsv) | Per-draw capture (`PS2_CAPTURE`) around frame 180 |
| 2 | [`02-ghidra-zeroed-scissor-xyoffset.md`](02-ghidra-zeroed-scissor-xyoffset.md) | Ghidra: init GIF writes **SCISSOR=0**, **XYOFFSET=0** |
| 3 | [`03-alpha-test-ATE-GREATER.md`](03-alpha-test-ATE-GREATER.md) | Live drawenv: **ATE on, ATST=GREATER, AREF=2** |
| 4 | [`04-mode-verdict-DISPFB-vs-FRAME.md`](04-mode-verdict-DISPFB-vs-FRAME.md) | Width modes A/C out; Mode B page split 400 vs 288 |
| 5 | [`05-ghidra-decompiled-gs-init.md`](05-ghidra-decompiled-gs-init.md) | Decompiled CRT / DISPFB / draw-env setup |
| 6 | [`06-ATE-off-experiment.md`](06-ATE-off-experiment.md) | Forced ATE off — **no luminance change** (ATE not sole cause) |

**Standing status:** TRACE + fix loop still running; this pack is a snapshot for reading, not a freeze.
