# Hitman `boot.elf` vs ps2dev/ps2-packer (2026-11-07)

**File:** `games/a2116d2ac08a7be4db4e8455ad58d2e5/disc/boot.elf` (4,971,496 B)  
**Reference only:** https://github.com/ps2dev/ps2-packer (not executed)  
**Authoritative SDK:** still `E:\usr\local\sce` — packer is homebrew tooling only.

## Verdict

**Does not match ps2-packer (any module: lzma / lzo / lz4 / zlib / null).**  
Hitman `boot.elf` is a **normal stripped commercial EE ELF**, fully expanded on disc — not a stub+compressed payload.

## ps2-packer fingerprints (from README + `ps2-packer.c`)

| Fingerprint | Typical packed output | Hitman |
|-------------|----------------------|--------|
| Entry | Stub PC (`0x01D00008` or `0x00088008`) | **`0x0010001C`** (normal EE `_start`) |
| Program headers | 1 PH (stub+payload) or 2 PH (alt) | **1 PH** load @ `0x00100000`, filesz≈4.8 MB |
| Section headers | Usually **`shnum=0`** | **`shnum=16`** (`.text`, `.vutext`, `.data`, `.rodata`, `.bss`, …) |
| Stub bases | High (`0x01D00000`) or `0x00088000` | Load base **`0x00100000`** only |
| Magic / strings | Packer/stub signature in stub; no game lib strings until unpack | **`sceGs`**, **`libgraph`** present; **no** `PS2PACKER` / `UPX!` / `NRV2` / `lzma` / `lzo1x` |
| Entropy (256 KiB sample) | High (compressed blob) | **~5.87**, **23.6% zeros** — normal code/data mix |
| Size ratio | Much smaller than unpacked | Full game-sized PT_LOAD |

## Why Ghidra looked “packed”

- Early analysis still climbing (~7.6k → ~17k functions while auto-analyze runs).
- Symbols stripped → all `FUN_*`.
- Ghidra `image_base`/`ram` mapping starts at `00000000` while ELF `p_vaddr` is `0x00100000` — load quirk, **not** a packer stub.
- Large overlay / IO register spaces inflate “memory size” in metadata.

## Implication for FB/alpha trace

No unpack stub to reverse for Hitman. Continue GS trace on the **already-expanded** ELF (`FUN_0018ff4c` already shows live `PMODE`/`DISPFB2`/`DISPLAY2` setup).
