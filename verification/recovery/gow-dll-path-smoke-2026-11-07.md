# GoW USA native DLL-path smoke — 2026-11-07

**GID:** `695b874b308a4e5353767bb6df8ba697` (God of War USA)  
**Scope:** Verify restored runtime DLLs resolve under PS2Recomp.cmd-equivalent `PATH`. No disc-fix / R5 / CNK / IOP/CDVD edits.

## Locate

| Item | Path |
|------|------|
| Native exe | `build/native-695b874b308a4e5353767bb6df8ba697/ps2run.exe` |
| ELF | `games/695b874b308a4e5353767bb6df8ba697/disc/boot.elf` (= `SCUS_973.99`) |
| Disc | `games/695b874b308a4e5353767bb6df8ba697/disc.iso` |
| Wrapper | `PS2Recomp.cmd` prepends `runtime-deps`; `tools\msys64\clang64\bin`; `third_party\wgpu-native\lib` (then calls `Setup.cmd` — **not** used for this smoke) |

**DLLs beside exe (already present):** `wgpu_native.dll`, `SDL2.dll`, `libc++.dll`, `libunwind.dll`  
**Also under:** `runtime-deps/` (same four)

## Launch

Cwd: `C:\PS2Recomp`. PATH mirrored from `PS2Recomp.cmd` (without hosting `Setup.cmd`).

```text
build\native-695b874b308a4e5353767bb6df8ba697\ps2run.exe ^
  games\695b874b308a4e5353767bb6df8ba697\disc\boot.elf ^
  --disc games\695b874b308a4e5353767bb6df8ba697\disc.iso ^
  --memcard logs\gow-dll-path-smoke-2026-11-07\card.ps2 ^
  --frames 600
```

**Note:** Absolute ELF/disc paths made the title try `host0:IOP_MOD/*.irx` and starve IOP (2 prims). Relative paths (as prior patientzero) boot `cdrom0:\IOPRP300.IMG` and load IRX from disc — used for the recorded result.

## Result

| Metric | Value |
|--------|-------|
| Launch OK | **Yes** |
| Exit code | `0` |
| Frames | `600` (frame limit reached) |
| Primitives | `6,964,754` |
| Cycles | `2,952,076,442` |
| Wall time | ~4.9 s (~122 host frames/s throughput; headless — no `[fps]` line) |
| DLL load | **Success** — `[gpu] NVIDIA GeForce RTX 3050 (621.14)`; zero `STATUS_DLL_NOT_FOUND` / missing-module lines |
| IOP path | `cdrom0:` IRX loads OK (SIO2MAN → SMPD_IOP) |

## Logs

- `logs/gow-dll-path-smoke-2026-11-07/err.log` (primary stderr / metrics)
- `logs/gow-dll-path-smoke-2026-11-07/run.log` (stdout empty)
- `logs/gow-dll-path-smoke-2026-11-07/card.ps2`

## Blocked / next

- **Not blocked** on DLL PATH — restored deps + beside-exe copies are sufficient.
- Next (out of this mission): longer patientzero-class smoke / windowed FPS if product needs on-screen rate; keep relative disc/ELF paths for GoW host boots.
- **Hard ban held:** no disc-fix, R5, CNK, or runtime IOP/CDVD edits.
