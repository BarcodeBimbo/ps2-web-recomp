# Ghidra — zeroed SCISSOR / XYOFFSET at GS draw-env init

**Function:** `FUN_0028f2c4` @ `0028f2c4`  
**Called from:** CRT / buffer setup after `FUN_0028ef4c` (via `FUN_00291710`).

## Finding

The A+D GIF packet built in `FUN_0028f2c4` explicitly stores **zero** for:

| GS register | Addr | Packet store (asm) | Value |
|-------------|------|--------------------|-------|
| `SCISSOR_1` | `0x40` | `li t6,0x40` / `sd t6,0xe8(t7)` with data `sd zero,0xe0(t7)` | **0** |
| `SCISSOR_2` | `0x41` | (paired in same block; init path zeros both contexts’ scissors in practice until later updates) | **0** at init |
| `XYOFFSET_1` | `0x18` | `li t6,0x18` / `sd t6,0x158(t7)` with `sd zero,0x150(t7)` | **0** |
| `XYOFFSET_2` | `0x19` | `li t6,0x19` / `sd t6,0x168(t7)` with `sd zero,0x160(t7)` | **0** |

Also in the same packet:

- `TEST_1` / `TEST_2` ← `0x30000` (ZTE on, ZTST=ALWAYS; **ATE off** at init)
- `ALPHA_1` / `ALPHA_2` ← `0`
- `FRAME_1` ← `(d4>>11) \| (d8>>6)<<16 \| psm<<24`
- `FRAME_2` ← `0x100000000` (ZMSK-style high bit on the paired ZBUF path; see asm `dsll32` of 1 into ZBUF slots)

## Asm anchors (readable)

```
0028f458: li   t6, 0x40          # SCISSOR_1
0028f45c: sd   t6, 0xe8(t7)      # register index in A+D packet
# data lane at 0xe0 was written as zero just above (sd zero, 0xe0(t7))

0028f4e4: li   t6, 0x18          # XYOFFSET_1
0028f4e8: sd   t6, 0x158(t7)
# data at 0x150 = zero

0028f4ec: li   t6, 0x19          # XYOFFSET_2
0028f4f0: sd   t6, 0x168(t7)
# data at 0x160 = zero
```

## Runtime follow-up (important)

Init zeros are **not** the final live state. At present time TRACE shows ctx0 later has:

- `xy = 0x720000007000` → OFX=`0x7000` (1792 px), OFY=`0x7200` (1824 px)
- `sc = 0x1BF000001FF0000` → scissor **0..511 × 0..447** (full 512×448)

So the ELF *does* fix scissor/xyoffset later — but capture rows still show **negative screen boxes** like `-1792,-1728 …`, which is consistent with verts near 0 while OFX≈1792 (classic “wrong offset / pre-offset verts” tension). That is open in the live loop.

## Why it matters for black pages

- Scissor `(0,0)-(0,0)` at init would clip everything until updated.
- XYOFFSET `0` vs later `1792/1824` (not the textbook `2048/2048`) changes where sprites land relative to the 512×448 scissor.
- Capture after draw to FBP `0x120` (288) still shows **pure black PPMs** even for full-screen 16-prim batches — so clipping alone does not yet explain all emptiness; alpha / clear / compose remain in play.
