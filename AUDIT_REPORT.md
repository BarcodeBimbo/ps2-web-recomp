> Historical report. See [FIX_REPORT.md](FIX_REPORT.md) for the current direct-only Store, console startup and test limits.

> Earlier report. See [FIX_REPORT.md](FIX_REPORT.md) for the current setup/mobile/Store changes, tests and unresolved runtime cases.

# Current update verification

See [UPDATE_NOTES.md](UPDATE_NOTES.md) for this update’s changes, tests, and live-provider limitation. The report below came with the preceding build and is historical; it does not describe tests performed for this update.

---

# Security and compatibility review

Review date: November 5, 2026. Baseline: the supplied `ps2-web-recomp-final.zip`. This report replaces the previous audit report; it distinguishes this review's checks from earlier claims.

## Result

This update repairs concrete startup, input, native-parser, archive and serving problems, adds the missing mobile controls, and adds a live RAM-cheat interface and configurable cutscene-skip input. A synthetic browser game successfully compiles and links with the pinned Emscripten 6.0.11 toolchain, including the WebGPU backend and new exports. Native Clang targets also build without compiler warnings.

Correct booting and rendering of every PS2 title is not established. No playable disc/ELF for the affected games was supplied. This is an audited source update with synthetic integration coverage, not a claim that Sly Cooper's missing geometry, every loading-screen hang, or all game crashes have been repaired.

## Plan followed

1. Compare the supplied release with the work in progress; retain newer startup/archive fixes.
2. Review browser startup, input, worker callbacks, disc streaming, native ELF/relocation parsing, state loading, server routes, queue ownership and installer downloads.
3. Correct demonstrated defects; add bounded archive import, mobile input, authenticated mobile serving and the requested menu features.
4. Run parser/security, concurrency, archive, CHD, HTTPS and DOM input regressions. Obtain the pinned Emscripten toolchain and link a synthetic browser game.
5. Package the source, reproducible tests, usage guides and remaining limitations.

## Findings and fixes

| Area | Finding | Change |
|---|---|---|
| ELF loading | Segment copies could exceed their allocation; arithmetic and header/symbol/string bounds were incomplete | Overflow-safe table/segment bounds, allocation/input/symbol budgets, bounded string termination, malformed-file rejection |
| Runtime ELF loading | Header-table reads and RAM/scratchpad bounds could overflow | Validate program-header extents and use widened bounds before copying |
| Relocation parsing | Table arithmetic could wrap; XFF patch locations lacked complete write bounds | Widen table arithmetic and validate the entire section/write range |
| Runtime ISO parsing | Directory allocation/record/extent bounds were incomplete; layer-1 state could survive reopening | Bound directory allocation and recursion, validate records/extents and reset disc-index state |
| Save states | Untrusted vector lengths could request excessive allocations | Per-container and aggregate allocation limits before resize/assign |
| Controller input | Browser/native host setters wrote plain controller fields read by the emulator | Atomic host input; the emulation thread copies values into its protocol state |
| Keyboard remapping | An armed remap could consume a settings-button click; key repeat could repulse input | Exclude UI controls from mouse binding capture; ignore duplicate held-key presses; neutralize input while dialogs are open |
| Touch input | Right stick and L3/R3 were missing; interrupted touches could stay active | Two captured analog regions, complete button set, multi-finger input, cancellation/focus/rotation cleanup, per-game touch mappings and opacity/dead-zone settings |
| Mouse input | Different games use different camera-axis conventions | Preserve independent per-game X/Y inversion switches and test both directions |
| Start/fullscreen | The menu was inaccessible when the bottom bar was hidden | Top-toolbar Start/Menu buttons; Start sends the pad action independently of remapping |
| Halt recovery | Removed overlay was looked up by ID, losing the node required for recovery | Keep the launch-overlay reference; restore it on halt and require a clean reload |
| GPU selection | Default-adapter probe and C++ adapter request could disagree; private adapter metadata could falsely look like failure | Try high/low/default preferences, pass default preference to the backend, accept a usable adapter without identifying strings |
| GPU callbacks | Native completion flags used across callbacks were plain booleans | Atomic completion flags; graphics-device loss requests a thread-safe halt |
| Threaded halt | Concurrent halt writers could modify the reason unsafely | Atomic halted state, serialized first reason, stable publication |
| Disc streaming | Failed asynchronous probes could retry forever; blocking reads could wait indefinitely; range bodies were unbounded | Terminal streaming errors, bounded waits and reads, 30-second blocking-read deadline and explicit error state |
| Browser initialization | GPU setup/engine script failures could leave loading UI indefinitely | Bounded GPU probing, software fallback, script-load error reporting, avoid loading the engine when required browser features are missing |
| HTTP serving | Standalone server could serve unrelated outputs/linked files; room storage and threads were unbounded | Static player-file allowlist, containment checks, bounded requests/rooms/peers/messages, read timeout, Host/Origin/Fetch-Metadata validation, duplicate-header rejection and security headers |
| Mobile network access | Plain LAN HTTP is insufficient for the runtime's secure-context requirements | Separate TLS listener for one selected game, private token exchange, Secure/HttpOnly/SameSite cookie, no administration or room mutation |
| Build queue | Concurrent jobs must not reserve the same tool directory | Preserve lock-protected queue/slot reservation; bound queued imports and retest concurrent enqueue/worker-failure cleanup |
| Archives | Full verification then bulk extraction used unnecessary I/O and could expand unrelated members | List headers, select one member, stream to a fixed filename with output/time limits; reject ambiguous multi-disc archives and excessive nesting |
| Passwords | UI always showed a field; encrypted headers need special handling | Inspect archive headers before import; show the password field only when needed, detect incorrect passwords during extraction, never save passwords to metadata/logs |
| CHD | Expanded size could greatly exceed compressed size | Validate CHD v5 logical size; bound conversion time and final output; test CD and DVD round trips with real chdman |
| Installer | Old Python bootstrap lacked a digest pin; emsdk archive lacked a complete pin | Pin Python 3.14.10 embedded package SHA-256; pin the full emsdk commit and archive SHA-256; refresh the MSYS tool stamp for this update |
| Library metadata | One damaged manifest could break library enumeration | Expose a recoverable failed entry instead of failing every library request |

Archive extensions include ZIP/ZIPX, 7z, RAR, TAR, GZip/TGZ, BZip2/TBZ, XZ/TXZ, Zstd, LZMA, CAB, ARJ, LZH/LHA, CPIO, XAR and Z, using the installed 7-Zip engine. Recognition does not mean every damaged, proprietary, multipart or multidisc variant can be imported. Select the first volume of a multipart archive and keep its other volumes beside it. An ISO/raw PS2 disc merely named `.rom` is accepted; cartridge ROMs for other consoles are not PS2 discs.

Passwords are checked, not guessed or cracked. Supported Python ZIP decryption remains in-process. 7-Zip requires a temporary password command-line argument for encrypted formats; local process-inspection tools may see it during that operation. The importer never writes it into the game manifest or normal build log.

## Added menu features

- Per-game PNACH RAM-write list with individual toggles, file import and Disable all. Up to 128 aligned writes inside EE RAM; changes are queued to the emulation thread. Unsupported boot/code/conditional operations are rejected. Compiled code patches require rebuilding.
- Configurable cutscene-skip button sending Start/Cross/Circle/Triangle. A game must support the selected skip input.
- Downloadable diagnostics with bounded runtime output and current browser/disc/GPU/renderer information.
- Reference VU mode for differential diagnosis of missing geometry, alongside software-renderer comparison. These modes can be slow and do not establish emulation correctness.

## Tests actually run in this review

| Check | Result |
|---|---|
| Disc/archive regressions | 11 passed |
| Windows installer extraction/bootstrap regressions | 9 passed; Windows installer execution itself is mocked |
| HTTP range-serving regressions | 4 passed |
| Concurrent build-queue/worker-failure regressions | 3 passed |
| Host/origin/range/room/file/auth/malformed-disc security tests | 7 passed |
| Real 7-Zip 26.05 integration | 7 passed, including encrypted ZIP/7z, encrypted headers, TAR/TAR.GZ, RAR4 stored member, path isolation and ambiguous discs |
| Real MAME 0.289 chdman integration | Synthetic CD and DVD CHD round trips passed byte-for-byte |
| Malformed ELF sanitizer fixtures | 8 rejected safely |
| Existing recompiler regressions | Tail-call, BSS and fallthrough passed |
| VU code generation | 10 native and 10 Wasm regressions passed using Clang and Node |
| Live patch queue/state allocation regression | Passed, including a 100,000-update producer/consumer stress run under ASan/UBSan |
| Player DOM/input regression | Passed for full shell execution, dual sticks, simultaneous action, Start, cancellation, remapping, modal isolation, repeat suppression, inversion, PNACH validation and halt recovery |
| GPU selection logic regression | Default-adapter fallback and scrubbed adapter metadata passed with simulated GPU API objects |
| HTTPS mobile server integration | Trusted test certificate, authentication, cookie, live shell, COOP/COEP, ranges, blocked administration/other games and token rotation passed |
| Native Clang build | eerecomp, vurecomp and ps2runtime built without compiler warnings |
| Emscripten 6.0.11 build | Synthetic ps2web.html/js/wasm/data linked, including WebGPU backend/new cheat export |
| Python/JavaScript/shell syntax | Python compilation, extracted JS node --check and shell syntax checks passed |

The browser linker emits the advisory about pthreads plus memory growth. `GROWABLE_ARRAYBUFFERS=1` is deliberate: it detects newer APIs and retains fallback support. Mode 2 would remove the fallback overhead while requiring the newer API, reducing support on older Firefox versions. The empty-character warning reported for `Content-Range` no longer appears.

## Capture analysis

Both supplied captures identify `SCUS_971.98` and contain a complete 4 MiB VRAM snapshot. Capture 1793851890061 contains 335 draw batches / 8,700 primitives / 305 textured batches. Capture 1793851984229 contains 1,592 batches / 8,762 primitives / 500 textured batches. The second also contains many line batches; they may be effects or geometry generated in that scene, not proof of a particular fault.

These records demonstrate active texture/geometry submission. They do not include the full EE/VU execution trace, every vertex, a known-correct reference image or an identical-scene software/GPU comparison. They cannot identify the missing-building cause conclusively. Extracting more files is not established as the fix: the game reads its complete managed disc image, including packed game resources. `scripts/inspect_capture.py` reproduces these summaries.

## Remaining validation and risks

- **Real-title boot and graphics remain unresolved.** Sly Cooper's missing geometry/textures and other title-specific loading failures require execution with the affected disc/revision. No universal rendering or controller-prompt replacement is implemented or claimed.
- **No real Windows, physical phone or Firefox GPU session was available.** Windows tool setup remains platform-specific. The browser visual test runner was blocked by the environment's Chromium socket restriction. The included Playwright layout suite is therefore unexecuted; DOM input tests and actual browser compilation are not visual or gameplay tests.
- **GPU driver correctness/performance is unverified.** A browser that exposes no usable WebGPU adapter cannot be made hardware-accelerated by application code. Software fallback can be very slow. No security/blocklist flags are changed.
- **Personal LAN hosting only.** The TLS listener has bounded resources and token authentication, but it is not a public multi-tenant service, a penetration-test certification or a replacement for a maintained production edge server. Users must configure a certificate trusted by their phone.
- **Third-party native parsers remain a boundary.** chdman/7-Zip/compiler/graphics-driver internals were not exhaustively audited or fuzzed. Use maintained utilities and discs/archives from trusted sources. Tests cover real synthetic CHD/archives, not all vendor format variants or malformed inputs.
- **A review is not proof of absence of every bug.** CPU, IOP, VIF, VU and GS emulation contain substantial title-dependent behavior. This release records verified defects and test coverage rather than asserting universal PS2 compatibility.

## Research sources

- [MAME chdman commands](https://docs.mamedev.org/tools/chdman.html)
- [7-Zip supported formats](https://www.7-zip.org/), [official downloads](https://www.7-zip.org/download.html)
- [Pointer Events and cancellation/capture](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)
- [SharedArrayBuffer secure-context/isolation requirements](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)
- [WebGPU implementation status](https://github.com/gpuweb/gpuweb/wiki/Implementation-Status)
- [WebAssembly JSPI](https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/JavaScript_interface/Suspending)
- [Emscripten growable-memory settings](https://emscripten.org/docs/tools_reference/settings_reference.html#growable-arraybuffers)
- [OWASP request-origin and Fetch Metadata guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Python release security update](https://blog.python.org/2026/10/python-3152-31410-31318-31216-31118/)
