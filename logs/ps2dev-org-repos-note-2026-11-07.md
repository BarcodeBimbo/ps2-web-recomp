# ps2dev GitHub org — community repos note (2026-11-07)

**Authoritative SDK:** local `E:\usr\local\sce` (Runtime Library 3.0.3) — **not** any GitHub tree.  
**Org:** https://github.com/ps2dev (~30 public repos). Unofficial / homebrew only.

## Repos that may help beyond “SDK” (especially GS / tooling)

| Repo | Why it may help |
|------|-----------------|
| [gsKit](https://github.com/ps2dev/gsKit) | C API to GS — FRAME/DISPFB/ALPHA patterns for comparison |
| [gsKit_examples](https://github.com/ps2dev/gsKit_examples) | Working draw/display samples |
| [ps2stuff](https://github.com/ps2dev/ps2stuff) | Low-level helpers often near GIF/GS |
| [ps2client](https://github.com/ps2dev/ps2client) / [ps2link](https://github.com/ps2dev/ps2link) / [ps2linkui](https://github.com/ps2dev/ps2linkui) | Host↔EE debug link |
| [ps2gdb](https://github.com/ps2dev/ps2gdb) | EE debugging |
| [debugear](https://github.com/ps2dev/debugear) | Debug tooling |
| [ps2-packer](https://github.com/ps2dev/ps2-packer) | ELF packing (Hitman-style binaries) |
| [ps2-etv](https://github.com/ps2dev/ps2-etv) | Extra tooling |
| [mymc](https://github.com/ps2dev/mymc) | Memory-card images |
| [ps2iconfactory](https://github.com/ps2dev/ps2iconfactory) | Icons |
| [libapa](https://github.com/ps2dev/libapa) / [libhdd](https://github.com/ps2dev/libhdd) / [libpfs](https://github.com/ps2dev/libpfs) / [libcdvd](https://github.com/ps2dev/libcdvd) | Storage / disc FS ports |
| [ps2eth](https://github.com/ps2dev/ps2eth) | Ethernet |
| [ps2sdk-ports](https://github.com/ps2dev/ps2sdk-ports) | Third-party lib ports onto homebrew SDK |
| [ps2toolchain](https://github.com/ps2dev/ps2toolchain) / [ps2toolchain-ee](https://github.com/ps2dev/ps2toolchain-ee) / [ps2toolchain-iop](https://github.com/ps2dev/ps2toolchain-iop) / [ps2toolchain-dvp](https://github.com/ps2dev/ps2toolchain-dvp) | Toolchain pieces |
| [ps2dev](https://github.com/ps2dev/ps2dev) | Meta “build whole env” |
| [ps2sdk](https://github.com/ps2dev/ps2sdk) | **Homebrew** SDK — do **not** use as Sony 3.0.3 substitute |
| [ps2sdk-docs](https://github.com/ps2dev/ps2sdk-docs) | Docs for homebrew SDK only |
| [ps2fire](https://github.com/ps2dev/ps2fire) / misc samples | Demos |

Full API dump: agent-tools `a8e937f4-…` (orgs/ps2dev/repos JSON).

## Hitman FB note (Ghidra in progress)

`boot.elf` display setup (`FUN_0018ff4c`) writes **circuit 2**: `PMODE=0x66`, `DISPFB2`, `DISPLAY2`, `SMODE2`. Host `gs.cpp` selects circuit via `(pmode&2)?1:(pmode&1)?0:-1` → circuit 1 = DISPFB2 — **aligned** with Hitman’s path. Black canvas is therefore less likely “wrong circuit,” more likely **draw FBP vs DISPFB base**, **psm/mask/alpha**, or **present readback**.
