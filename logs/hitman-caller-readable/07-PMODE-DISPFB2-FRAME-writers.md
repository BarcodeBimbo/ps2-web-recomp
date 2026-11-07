# Hitman GS writers catalog (trusted VAs — ELF load `0x00100000`)

| Register   | Primary writer | Notes |
|------------|----------------|-------|
| PMODE      | `FUN_0028ef4c` @ `0x0028ef4c` | `REG_GS_PMODE = 0x66` (EN2) |
| DISPFB2    | `FUN_0028ef4c` @ `0x0028ef4c` | FBP from `*(disp+0xd4)>>11`; observed `0x1190` |
| DISPLAY2   | `FUN_0028ef4c` / `FUN_0028f248` | 512×448 decode verified |
| FRAME (ctx0) | `FUN_0028f2c4` @ `0x0028f2c4` | Initial GIF draw env; FRAME page **288** in traces |
| SCISSOR    | `FUN_0028f2c4` | 512×448 at boot |
| XYOFFSET   | `FUN_0028f2c4` | Zero at init; live game updates via GIF |

Cross-refs: `05-ghidra-decompiled-gs-init.md`, `02-ghidra-zeroed-scissor-xyoffset.md`, `logs/hitman-display2-mode-verdict-2026-11-07.md`.
