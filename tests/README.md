# Recompiler regressions

These tests construct small ELF files from synthetic instructions and need no
game data. Build the recompiler and run them from the repository root:

```sh
cmake -S . -B build/tools -DCMAKE_BUILD_TYPE=Release
cmake --build build/tools --target eerecomp
python3 tests/analysis_tailcall.py
python3 tests/elf_bss.py
python3 tests/codegen_fallthrough.py
```

Each script accepts `--recompiler /path/to/eerecomp` to check another build.
The fallthrough test also uses `clang++` or `g++` from `PATH` to check that the
generated C++ compiles.

Disc-image parsing and archive handling can be checked without game data:

```sh
python3 tests/disc_archive.py
```

The encrypted-ZIP test uses the system `zip` utility to create a temporary ZipCrypto fixture and is skipped when that utility is unavailable. CHD extraction requires MAME `chdman`; encrypted 7z/RAR extraction requires 7-Zip/7zz.

Windows installer archive extraction and checksum validation can be checked without downloading toolchains:

```sh
python3 tests/windows_setup_archive.py
```

The local HTTP server's byte-range behavior can also be checked without a browser:

```sh
python3 tests/serve_range.py
python3 tests/panel_build_queue.py
```

Run every repository-level regression test from the project root with:

```sh
python3 tests/analysis_tailcall.py
python3 tests/elf_bss.py
python3 tests/codegen_fallthrough.py
python3 tests/disc_archive.py
python3 tests/windows_setup_archive.py
python3 tests/serve_range.py
python3 tests/panel_build_queue.py
python3 scripts/test_vu_codegen.py
```

## Security, mobile and runtime update checks

```sh
python3 tests/security_review.py
python3 tests/mobile_https.py
python3 tests/elf_security.py --recompiler build/tools/eerecomp
PS2_7ZIP=/path/to/7zz python3 tests/archive_integration.py
CHDMAN=/path/to/chdman python3 tests/chd_integration.py
```

`mobile_https.py` uses OpenSSL to generate a temporary trusted test certificate. The archive and CHD integration suites use real utilities and synthetic discs. They are skipped unless the corresponding environment variable points to the utility; a skip is not validation.

```sh
clang++ -std=c++20 -pthread -fsanitize=address,undefined -Iruntime/include tests/live_patches.cpp -o /tmp/ps2-live-patches
/tmp/ps2-live-patches
npm install --prefix /tmp/ps2-test-dom linkedom
node tests/player_logic.cjs
```

The DOM test executes the complete shell without a game engine and validates input, recovery, cheat parsing and GPU selection logic. It uses `linkedom` from Node resolution, `LINKEDOM_PATH`, or the temporary installation above. It does not render CSS or prove actual WebGPU output.

`tests/mobile_controls.cjs` is a separate Playwright/Chromium layout and multi-touch test at several phone sizes. Set `CHROMIUM_PATH` to an installed Chromium executable if needed. Install Playwright and its browser before running it. This review's environment blocked Chromium startup; this test is included but was not marked as passed. Physical phones and Firefox hardware still need live-game testing.

## Update regressions

```sh
python3 tests/store_pipeline.py
python3 tests/gpu_arena.py
node tests/panel_logic.cjs
node tests/player_logic.cjs
```

The allocator regression uses g++ and ASan/UBSan. The panel/player tests use linkedom.
The store test downloads synthetic bytes through a controlled response and verifies
that an incomplete download never reaches import. It also verifies that compilation
failure preserves the previous browser player. No commercial game data is needed.

## Console startup and direct downloads

```sh
python3 tests/download_controls.py
python3 tests/store_pipeline.py
python3 tests/installation_flow.py
python3 tests/panel_build_queue.py
python3 tests/setup_reporting.py
python3 tests/mobile_auto.py
python3 tests/mobile_https.py
node tests/gpu_upload_compat.cjs
node tests/panel_logic.cjs
node tests/player_logic.cjs
PS2_TEST_ASYNC_MODE=asyncify PS2_TEST_NO_JSPI=1 node tests/player_logic.cjs
g++ -std=c++17 tests/frame_clock.cpp -o /tmp/frame-clock && /tmp/frame-clock
```

DOM tests use linkedom (`npm install --prefix /tmp/ps2-test-dom linkedom`).
Transfer tests use controlled responses, not a live provider. They cover Range/
If-Range, changed content, pause/resume/cancel, failed-file cleanup and row expiry.
Compatibility tests execute the real dispatch trampoline and validate a full
Emscripten build with synthetic code. See ../FIX_REPORT.md and
../verification/console-results.json for exact results and platform limits.
There is no Store browser, provider parser, solver or separate downloader setup.

## IOP polling RPC

See [NFS_RPC_FIX.md](../NFS_RPC_FIX.md) for build commands, captured-state replay
and verification limits. Enable PS2_BUILD_TESTS with native Clang and run CTest.
The synthetic iop_rpc_poll test needs no game files. iop_rpc_snapshot specifically
uses the uploaded NFS capture and does not run automatically without that file.
