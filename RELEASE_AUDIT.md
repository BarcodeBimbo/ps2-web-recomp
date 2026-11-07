> Historical report. See [FIX_REPORT.md](FIX_REPORT.md) for the current direct-only Store, console startup and test limits.

> Historical audit. The current launcher/mobile/Store behavior and remaining runtime limits are in [FIX_REPORT.md](FIX_REPORT.md).

# CyberArcade — source audit candidate, 2026-11-05

Status: concrete fixes implemented, but **not release-certified**. The attached source was inspected and edited in Linux; C:\PS2Recomp was not accessible. No game discs, generated game C++, emsdk, or working hardware-browser environment were supplied. Do not interpret synthetic tests as proof that the listed commercial games now work.

## 1. Root-cause audit findings

| Finding | Evidence and disposition |
|---|---|
| `setBindGroup` rejects resizable backing buffers | Existing compatibility code patched only GPUQueue.writeBuffer. The renderer passes Wasm heap dynamic offsets at gpu.cpp's compute bind calls. Added fixed Uint32Array slices to compute, render and bundle encoder methods, including worker injection through the existing server prefix. |
| Library/build flicker | `render()` called `replaceChildren()` for the entire library on every changed JSON snapshot, including progress. Cards, posters, links and progress elements now retain identity across progress updates. Downloads use the same strategy; quick launch updates only when its ready-game metadata changes. |
| Mobile `import panel` | Windows embedded Python's isolated path configuration omits the script directory. `panel` is scripts/panel.py, not a PyPI dependency. Explicit sibling path setup fixes isolated startup. |
| Windows queue wake mismatch | wait_for_work uses a condition variable on Windows, while post previously notified only an atomic word. Publication now uses wake(), which selects the correct wait primitive. |
| Queue hang at oversized/wrapped messages | Oversized messages previously waited indefinitely; wrap padding plus a large valid packet could also prevent progress. Invalid messages fail explicitly; wrap markers are published and consumed independently, including waking the producer after wrap consumption. |
| Host memory boundary access | Fast paths checked only the first byte; slow paths memcpy'd full values without remaining-region checks. Added width-aware checks for RAM/scratchpad and guarded slow VU/RAM/scratchpad spans. Crossing-region accesses now report an error; this is safety handling, not a new emulation model for invalid guest accesses. |
| Reported empty character literal | The uploaded web.cpp already had `Content-Range` and empty fallback double-quoted. Converted its remaining embedded JS single-quoted strings to double quotes as well; no warning suppression. |
| Downloader integration | Supplied Downloader.ts was interactive, used one persistent browser profile, embedded a service credential, forwarded all cookies to the file host, and wrote directly to its final filename. Added a structured browser worker and store queue bridge. |
| High-GPU black frames/missing buildings | Not reproduced or claimed fixed. GPU callback errors and queue/memory defects are concrete fixes, but shader/VU/game-specific compatibility still needs per-title captures. A 30-second missing-frame warning now exposes stalls without automatically restarting workers. It cannot detect a black image when frame callbacks continue. |

Existing X/Y inversion, repeat-safe remapping, touch controls, bounded PNACH cheats, cutscene button pulse, software fallback diagnostics, CHD conversion and password fields were inspected and retained. The cutscene action sends a configured controller button; it is not a universal cutscene patch. Cheats accept supported raw EE writes, not all encrypted cheat formats.

## 2. Prioritized implementation plan and outcome

1. Startup blockers: GPU offsets, local Python imports and C++/JS literals — implemented; synthetic tests pass.
2. UI: stable cards/progress, accessible poster play, intentional two-line branding, remove redundant Local library label — implemented; DOM tests pass; visual browser testing remains blocked.
3. Concurrency/memory: queue wake, wrap/oversize bounds and guest memory spans — implemented; sanitizer tests pass under the conditions below.
4. Downloader: browser adapter, store jobs, stream validation and atomic completion — implemented; contract and subprocess/import tests pass; real provider verification remains open.
5. Compatibility/release gate: Windows/em++ builds, Chrome/Firefox GPU, physical phones and named games — not completed in this environment.

## 3. Concrete changes by file

The included `changes.patch` contains the full unified source diff against the uploaded ZIP.

| Files | Change |
|---|---|
| web/gpu_upload_compat.js | Preserve fixed-buffer fast path; copy only selected dynamic offsets for resizable/growable buffers; native handling for invalid inputs; idempotent installation. |
| web/panel.html | Keyed library/download reconciliation, stable progress, native accessible poster anchors, separate Actions button, title layout, browser download action. |
| web/shell.html | Missing-frame warning, visibility reset, additional diagnostic timestamp, truthful halt text that does not assert every worker has stopped. |
| host/web.cpp | Double-quoted embedded JS literals. |
| runtime/src/gs/queue.cpp | Correct condition-variable publication, bounded inputs, independently published wrap marker and producer wake. |
| runtime/include/ps2/memory.hpp; runtime/src/memory.cpp | Width-aware fast paths, slow-path span checks, bounded watch diagnostics. |
| scripts/mobile.py; Mobile.cmd | Local module resolution, helpful missing-file/certificate/bind errors, venv selection, preserved exit status. |
| SetupRuntime.cmd; requirements.txt | Optional Python 3.11+ venv setup. Server dependencies are standard-library-only. |
| downloader/worker.mjs; package.json; package-lock.json; SetupDownloader.cmd | Browser discovery adapted from supplied TypeScript; pinned phantomwright; no embedded credential; ephemeral browser context; public HTTPS validation; URL-scoped cookies; bounded streaming; exclusive partial file followed by rename. |
| scripts/store.py | Browser jobs share the existing serialized queue/import path; bounded JSON-lines IPC; completed-file/path checks; process-tree cleanup on timeout. |
| CMakeLists.txt | Explain retained memory flags without hiding the performance warning. |
| tests/* | New/expanded GPU offset, DOM identity, watchdog, queue, memory, downloader and subprocess contract regressions. |

The browser worker uses visible provider verification. The supplied automated CAPTCHA-service integration and credential are not included. Rotate that exposed service key. The browser action chooses the first eligible USA version, otherwise the first non-demo version; the existing version picker remains available for explicit selection.

## 4. Test/build commands and results

See verification/test-output.txt and results.json for full Python outputs. `archive_integration` records an overall failure because its RAR fixture is unsupported by the available 7za utility; the ZIP and 7z cases pass. CHD tests report skips, not success.

Passed:

- Native `cmake -S . -B build/tools -G Ninja -DCMAKE_BUILD_TYPE=Release` and `cmake --build build/tools --target eerecomp -j 4`.
- Recompiler tail-call, BSS, generated fallthrough compilation and malicious ELF fixtures.
- Disc/archive unit tests; installer path traversal/device-name/link/checksum tests; server byte ranges; concurrent build reservation; security review tests; HTTPS mobile cookie/routing/isolation/ranges.
- Store stream/import and transactional rebuild tests; real subprocess browser-worker contract into store import, using synthetic bytes.
- Actual 7za fixtures: normal ZIP/7z, encrypted ZIP/7z, incorrect passwords, encrypted 7z headers, AES ZIP fallback, TAR and traversal-named members.
- `node tests/gpu_upload_compat.cjs`: writeBuffer and compute/render/bundle dynamic offsets, resizable/growable buffers, invalid inputs and duplicate installation.
- `node tests/panel_logic.cjs`: card/poster/progress identity, accessible poster link and store/password workflows.
- `node tests/player_logic.cjs`: input, dual sticks, mouse inversion, cheats, halt behavior, stall-warning recovery and synthetic GPU selection.
- `node tests/downloader_contract.mjs`: public/private URL checks, version selection, complete/truncated streams, redirect rejection.
- ASan/UBSan memory-boundary, live-patch and queue tests. Queue tests execute both Linux futex and the condition-variable branch using `-U__linux__`. Each queue path passed ten runs of 20,000 alternating small/full-capacity messages after the final wrap-wait race fix. This does NOT constitute a Windows binary test.
- GPU upload arena ASan/UBSan regression; Python compileall; Node syntax; git diff --check.
- npm audit reports zero known advisories for the locked downloader dependencies; this is not a supply-chain certification.

Sanitizer commands (from project root):

```sh
g++ -std=c++20 -pthread -fsanitize=address,undefined -Iruntime/src tests/queue_stress.cpp runtime/src/gs/queue.cpp -o /tmp/queue-stress
ASAN_OPTIONS=detect_leaks=0 timeout 30 /tmp/queue-stress
g++ -std=c++20 -pthread -U__linux__ -fsanitize=address,undefined -Iruntime/src tests/queue_stress.cpp runtime/src/gs/queue.cpp -o /tmp/queue-cv-stress
ASAN_OPTIONS=detect_leaks=0 timeout 30 /tmp/queue-cv-stress
g++ -std=c++20 -pthread -fsanitize=address,undefined -Iruntime/include -Iruntime/src tests/memory_bounds.cpp runtime/src/memory.cpp -o /tmp/memory-bounds
ASAN_OPTIONS=detect_leaks=0 /tmp/memory-bounds
```

LeakSanitizer could not operate under the host's tracing setup; leak detection was disabled, not passed. No ThreadSanitizer claim is made.

Blocked/failed checks:

- Full native GCC build stops at pre-existing Clang builtins in vu_ops.hpp (`__builtin_elementwise_min`, `__builtin_reduce_or`). The intended Windows toolchain uses Clang. No speculative intrinsic substitution was made.
- Windows and Emscripten build unavailable; no em++ or game-generated translation units here.
- Playwright browser download returned invalid/truncated archives. Chrome/Firefox screenshots, actual adapters and mobile rendering were not verified.
- CHD CD/DVD round trips skipped because chdman was unavailable.
- RAR fixture fails with this environment's reduced 7za utility. Use full 7-Zip and rerun before claiming RAR support.
- Real provider/browser download, browser verification and Windows child-process termination need live testing.

## 5. Security and compatibility findings

Archive extraction streams a selected member to a fixed local filename, never an archive-provided extraction path. Bounds exist for member size/count, nesting, output size and subprocess duration. Passwords remain transient and are omitted from job metadata; published/user-provided passwords are supported, not brute-force recovery. Existing 7-Zip CLI invocation places passwords in process arguments, which remain observable to sufficiently privileged local processes. This was not solved by pretending argv is secret.

Downloader checks require HTTPS, reject credentials/nonstandard ports/private resolved addresses, recheck redirects, and select cookies for each destination. Output is named by a generated job ID; incomplete files never enter import. DNS checks and subsequent connection resolution are separate: DNS rebinding is a residual risk in both existing urllib and browser/network paths. Browser subprocesses also inherit the desktop user's OS permissions. Do not expose this administrative downloader outside the existing authenticated loopback service. No complete network-egress sandbox is claimed.

C++ bounds fixes and sanitizer fixtures reduce demonstrated risks; they are not a full runtime memory-safety proof. Other DMA/device/game-specific paths need broader fuzzing and real-game coverage. Rejecting a crossing-region guest operation may expose a previously hidden emulation bug, now as a reported failure.

Browser fallback cannot create hardware support that Firefox/OS/drivers lack. The current shell checks required Wasm features and uses existing software fallback/error surfaces. Full mobile performance and compatibility remain device-specific. Secure HTTPS plus COOP/COEP is necessary for the mobile threaded runtime; mobile authentication tests pass, physical devices remain untested.

Memory flags remain `-pthread -sALLOW_MEMORY_GROWTH=1 -sGROWABLE_ARRAYBUFFERS=0`, with 256 MiB initial memory and existing worker pool. This preserves the existing compatibility choice and retains the real pthread-growth performance warning. Changing to =2 was not verified and is not claimed as an optimization. Current Emscripten documentation describes =1 as auto-detect and =2 as requiring growable views; version-specific SDK behavior must be checked against the pinned 6.0.11 toolchain before changing flags. Fixed-memory builds avoid growth overhead but require reserving enough memory up front and can fail under mobile memory limits.

Primary API references reviewed:

- https://emscripten.org/docs/tools_reference/settings_reference.html#growable-arraybuffers
- https://emscripten.org/docs/porting/pthreads.html
- https://gpuweb.github.io/types/interfaces/GPUBindingCommandsMixin.html

## 6. Update steps, residual risks and release blockers

1. Close running players and the local server. Back up the installation. Overlay this source onto C:\PS2Recomp; do not delete games, generated, tools, builds or saves. None are bundled here.
2. Run Setup.cmd for the main toolchain and downloader together; it automatically provisions private Node.js, locked npm dependencies and the browser. No separate downloader command or system Node installation is needed; optional SetupRuntime.cmd provides a standard Python venv. `Mobile.cmd --help` should now work without installing PyPI panel.
3. Restart the panel and reload players. The existing server prefixes the GPU compatibility shim into ps2web.js, including workers. Rebuild games to pick up C++ queue/memory/literal changes.
4. On Windows, run the normal game rebuild and retain the complete em++ output; run archive/CHD suites with full 7-Zip and chdman paths set.
5. For each failing game, test the same disc/version with WebGPU, software, and the existing reference-VU mode; export diagnostics and a frame capture. Check cold start, loading transitions, missing geometry, input remapping, repeated reloads and concurrent game tabs. No named game's compatibility is certified here.
6. Verify poster focus/Enter behavior, independent Actions button, scrolling/focus during active builds, visible provider verification, completed import and wrong-password recovery on the actual desktop. Check Android/iOS portrait and landscape touch, audio, memory pressure and HTTPS trust.

Minimum remaining evidence for the rendering failures: the affected game's exported diagnostics and frame capture, exact disc/build identity, and Windows build output. The entire game library is not needed to begin that diagnosis. Universal game startup/rendering, full mobile support and a release-quality Windows build remain open requirements.

## Unified launcher follow-up

Setup.cmd now also runs install_downloader() under the existing setup lock. The MSYS2 package manager installs private Node.js when missing; npm is called through its verified installed JavaScript entry-point path, avoiding .cmd shell invocation. The browser CLI is the actual phantomwright-driver/cli.js shipped by the installed package. Setup and Store workers share PLAYWRIGHT_BROWSERS_PATH under tools/downloader-browsers. Package/lockfile fingerprints avoid redundant npm installs; an executable check repairs a missing browser. SetupDownloader.cmd is only a compatibility alias to Setup.cmd.

Four mocked provisioning tests pass: first install/reuse, browser repair, lockfile change, and failure without a completion stamp. Installer archive and store/import regression tests also pass. The browser CLI help command was executed successfully. Full Windows installation is still not executed in this Linux environment.

MSYS2 package files verified against https://packages.msys2.org/packages/mingw-w64-clang-x86_64-nodejs .
