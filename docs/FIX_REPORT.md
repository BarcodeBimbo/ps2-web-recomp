# Console startup and download update — 2026-11-05

Current follow-up: [NFS_RPC_FIX.md](NFS_RPC_FIX.md) documents the repaired NFS polling-RPC deadlock and its captured-request replay. This is the broader update report. RELEASE_AUDIT.md, AUDIT_REPORT.md and older verification
logs describe earlier revisions; their browser-backed Store and solver sections
are superseded. This update is not a verified all-game release.

## 1. Root-cause findings

| Issue | Evidence and conclusion |
|---|---|
| NFS Most Wanted black screen | The supplied exploration log stops at 3,600 frames: all five EE threads wait on semaphores, one SIF request is queued at 0x000A1160, zero GPU submits and zero GS primitives. The supplied ELF confirms the main thread's return address 0x00497C00 follows a WaitSema in the RPC-call path. This is a startup synchronization stall before drawing, not evidence of a GPU adapter failure. The subsequently supplied RAM/bundles identify SND function 0 and missing polling RPC APIs. These are now implemented; replay of the captured real driver completes that request and advances beyond its polling loop. Full game rendering remains unverified; see NFS_RPC_FIX.md. |
| Excessive frame rate without graphics | The diagnostics report about 4,952 emulated fps and zero audio queued. host/web.cpp returned from pace() whenever audio was active, bypassing its wall clock even with an empty ring. Fixed: audio backpressure supplements a PAL/NTSC wall clock; stalled audio waits are bounded. |
| JSPI error on iPhone | Existing players are compiled with JSPI, tail calls and Wasm exception features. Changing a feature-warning string cannot make those binaries compatible. New builds default to Asyncify, a generated-code dispatch trampoline and JS exception handling. Legacy players retain accurate JSPI diagnostics until rebuilt. |
| Compiler crash in 76615f99-build.log | Both failing generated units report `LLVM ERROR: out of memory`, followed by Windows error 0x5AA. Default compilation now uses one job; browser translations use 4 KiB guest units rather than 16 KiB. No promise that arbitrary games fit every machine's RAM/pagefile. |
| Additional Start and details clicks | Poster/title handlers opened the info dialog; the player only launched from a Start handler and awaited audio resume. Posters now link directly to the player, runtime initialization launches automatically, and suspended audio no longer blocks launch. Information stays optional in the action menu. |
| Ugly loading card | Replaced poster/modal presentation with a full-screen black boot surface, CyberArcade identity, restrained gold light bar, loading status and the game title. It stays until GS primitives are observed. This is not a fabricated percentage or a claim that a commercial BIOS runs. |
| Store parser/WAF failures | Per the latest request, provider parsing, search, pagination, solver and browser provisioning are removed. Only direct HTTPS disc/archive links are accepted. No 2Captcha key/API is required or used. |
| Download management | Added bounded FIFO transfers, pause/resume/cancel, queued-transfer removal, queued-build removal, failed-file cleanup and failed/cancelled row expiry after 15 seconds. |
| Browser-visible counters | EE frame and GS primitive totals previously exposed non-atomic counters across workers. UI reads now use atomic snapshots published by their owning workers. |

Files inspected: the actual project sources; ps2-diagnostics.json; explore(1).log;
boot(1).elf; entries.txt; build(1).log; 76615f99-build.log; earlier Underground 2
exploration log and supplied UI captures. The original `explore_ram.bin` upload was unavailable. The replacement `explore_ram(1).bin` and IRX281A/B.BUN were subsequently read and used for the RPC follow-up. The commercial ELF and generated commercial game code are not
included in this source distribution.

## 2. Prioritized implementation plan and outcome

1. Identify whether startup reaches drawing: inspected diagnostics, EE waits and SIF state; added worker-safe snapshots with RPC owner/function detail.
2. Fix demonstrated runtime/build defects: pacing, counter publication, JSPI build dependency and generated-unit compiler memory pressure — implemented and compiled.
3. Remove launch friction: direct poster launch, automatic startup, independent audio unlock and console boot — implemented; DOM tests pass.
4. Simplify Store and finish transfer state handling — implemented; controlled HTTP fixtures pass.
5. Recheck setup, mobile boundaries, archive/ELF parsing, queue isolation and publication rollback — regression results included.
6. Verify physical Windows/browser/phone/game behavior — not available here; acceptance checklist below remains necessary.

## 3. File-by-file patches

`changes.patch` contains the full unified diff against the original supplied source.
The ZIP contains complete replacement files, not only snippets.

| Files | Changes |
|---|---|
| CMakeLists.txt | Explicit asyncify/jspi mode, matching exception/tail-call flags, generated shell marker, Asyncify stack and exported diagnostics. Retains pthreads, memory growth and GPU upload shim. |
| recomp/main.cpp, recomp/codegen.cpp | Validated --unit-bits 12..16; trampoline-aware generated cross-unit transfers. Default native unit size stays 16 KiB. |
| runtime/include/ps2/generated.hpp | Compatible dispatch-transfer macro; native/JSPI keeps tail transfers. |
| runtime/src/vu_jit.cpp | Compatibility microprogram blobs use call/return instead of Wasm return_call. |
| runtime/src/gs/queue.cpp | Promise/timer wait fallback when Atomics.waitAsync is unavailable; queue predicates are rechecked. Earlier queue wrap/wakeup corrections retained. |
| host/frame_clock.hpp, host/web.cpp | Testable frame deadlines; universal frame pacing, bounded audio backpressure, diagnostics bridge. Earlier fixed JS string literals retained. |
| runtime/include/ps2/system.hpp, runtime/src/system.cpp | Dispatcher-boundary diagnostics on the emulation worker; atomic frame snapshots. |
| runtime/src/gs/gs.cpp | Atomic published primitive total for UI reads. |
| runtime/src/iop/sif.cpp | Polling RPC APIs, sleep wake/credits, blocking callback continuations and bounded request/reply copies now repair the captured NFS initialization stall. Queued RPC diagnostics report owner/thread/server/function; no speculative semaphore wakeups. |
| scripts/windows_port.py | Regenerate current translation before web rebuild; browser unit size 4 KiB, asyncify default, build-mode metadata, default single compiler job. Existing transactional player publication retained. |
| scripts/panel.py | Inject actual build mode into the served shell, direct-transfer control API, remove obsolete Store parsing endpoints, remove queued builds safely, clean managed failed imports, repair static entries through a browser rebuild. |
| scripts/store.py | Direct-only streaming transfer queue; public HTTPS checks and redirect validation; Range/If-Range resume with validator/range checks, safe restart on HTTP 200, pause/cancel interruption, size/disk/time limits, failure cleanup and terminal row expiry. Passwords/response objects stay out of public job state. |
| scripts/windows_setup.py | Four setup stages; no Store Node/browser install. Installer heartbeat/log/report support retained. |
| Setup.cmd, scripts/setup-windows.ps1 | One Windows entry point; private Python bootstrap, exit status, obsolete launcher removal and hidden internal runtime folder. |
| scripts/mobile.py | Automatic private LAN IP, port 0, generated local HTTPS certificates, authenticated ready-game list, desktop/admin/private-key routes denied. |
| web/shell.html | Console boot, auto-start, independent sound enable, actual build-feature gating, boot/error diagnostics and worker snapshot download. Earlier mouse inversion, input and cheat validation retained. |
| web/panel.html | Direct clickable posters, optional information view, direct-only Store, transfer/build queue controls, friendly states and stable DOM progress updates. |
| tests/* | New frame-clock, transfer-control and dispatch-trampoline regressions; updated player/panel, pipeline, mobile and installation tests. Obsolete browser Store/solver tests removed with that feature. |
| downloader/*, scripts/downloader_runtime.py | Removed obsolete Store browser/solver implementation. Private Store credential config is excluded. |

## 4. Setup, mobile and tests

### Windows update/start

1. Close the existing host and player tabs. Extract the full update over C:\PS2Recomp.
2. Double-click **Setup.cmd**. It checks/downloads its pinned private Python,
   then runs **native tools → Emscripten → WebGPU libraries → optional CHD tool**.
   It opens the desktop library and starts automatic phone hosting. Keep that
   command window open: once it says the host is running, waiting is intentional.
3. Setup writes `tools/setup-report.json` and `tools/setup.log`. Tool commands
   stream output and emit elapsed/idle messages; bounded setup steps time out
   rather than remaining silent indefinitely. The old Chromium download stage
   shown at 100% in the screenshot no longer exists.
4. For each existing game, use its **… → Rebuild browser player** once. A source
   update cannot change an already compiled Wasm binary. Future poster clicks
   launch automatically; no second Start click is needed.

No separate Mobile/Downloader/Runtime launcher is needed. `runtime` is required
C++ source, not a separate user application; the Windows bootstrap hides that
folder. The obsolete downloader source folder is no longer shipped. Existing
unused browser caches are not silently deleted from an upgraded installation.

### Mobile flow

Setup detects the PC's private LAN IPv4, creates/reuses a local CA, generates a
server certificate for the detected IP, binds an OS-selected free port and shows
a link such as `https://192.168.1.112:<selected-port>/connect?...` under Phone access.
Use the same LAN/Wi-Fi. No manual PEM arguments are required. The phone still
needs to trust the public local CA once: plain HTTP on a LAN IP cannot provide
this player's secure context for WebGPU/threaded Wasm. Open the link in Safari
rather than Telegram's embedded browser. Browser/device feature support is
checked; physical iPhone compatibility has not been verified here.

### Automated results

`verification/console-results.json` records **24 passing groups, one blocked
live-browser group, zero failing code-test groups**. The test transcript is
`verification/console-tests.txt`; an initial ELF-test invocation omitted its
required --recompiler argument and was corrected and rerun successfully.

Passing groups cover disc/archive parsing, malformed ELF inputs, HTTP ranges,
installer archive safety, server security, mobile HTTPS/auto configuration,
setup reporting, transfer controls, install/dedupe/queue behavior, GPU upload
buffers/allocator, code generation, player/panel DOM, no-JSPI feature gating,
clock scheduling and the dispatch trampoline with ASan/UBSan.

Exact build evidence: Emscripten **6.0.11** full runtime + synthetic player compiled
and linked successfully in asyncify mode. Disassembly contains no return_call or
try_table instructions; generated glue has no WebAssembly.Suspending/promising
calls. `verification/emscripten-build.txt` records the command/result. The actual
supplied NFS ELF regenerated into **1,064** 4-KiB units; its largest source unit
(92,000 bytes) compiled to a Wasm object successfully. This is compilation
validation, not a successful commercial-game boot or a complete NFS web build.

Chromium's live-control test aborts at launch because this execution environment
denies its process-singleton socket. Browser assertions did not run. Windows
execution, physical Safari/iPhone, live Chrome/Firefox WebGPU and full game
startup remain unverified. The previous real encrypted-archive/CHD tests are
historical; this follow-up reran parser/security fixtures but did not provision
new 7-Zip/CHD tools for live round trips.

## 5. Security and compatibility

- Direct links must be public HTTPS without URL credentials/custom ports; DNS
  addresses and redirects are checked. The connection resolves/validates again,
  then connects to the validated numeric IP while TLS verifies the original
  hostname. Environment proxy discovery is disabled for these transfers so a
  proxy cannot bypass that address policy. Corporate HTTPS proxies are not
  supported by this direct-download path. Keep the administrative host local.
- Transfer limits: 16 active/queued/paused/importing transfers, 64 retained jobs,
  16-GiB file cap, free-space checks, four-hour active-transfer limit, network
  timeout, HTML rejection, truncation checks and no import of cancelled/partial
  files. Resume validates the entity and exact range. Without a usable validator,
  it safely restarts the file. Resume does not survive host restart.
- Pause/cancel flags update immediately; in-flight reads are interrupted in a
  helper thread where urllib exposes its socket, with response close as fallback.
  DNS/TLS/open operations may still wait; the OS DNS resolver is not bounded by the socket timeout. Once import has
  started, transfer cancellation is rejected; a queued game build can be removed
  separately. Active compilation is not killed by a queue-removal action.
- Failed transfer/import sources are deleted only within managed download paths;
  error/cancelled rows expire after 15 seconds. Original user files are preserved.
  Failed encrypted imports therefore require a fresh download or local original.
- Dedupe hashes normalized disc bytes, so equal discs in different containers
  share identity. Atomic file locking protects concurrent claims. Hashing happens
  during installation, not as a claim that a URL uniquely identifies a game.
- Archive extraction streams one selected member to managed output and enforces
  size limits; traversal/security fixtures pass. Passwords are not written to job
  metadata or logs. 7-Zip's command-line interface still exposes its password
  argument to processes with sufficient local inspection rights.
- Existing memory-access guards and queue checks remain. This is not a proof that
  all emulation/DMA memory paths are safe: SIF and other emulated-device code still
  contain raw copies and need a broader fuzzing effort. Do not run untrusted ROMs
  as if browser sandboxing protects the native host exploration process.
- pthreads + ALLOW_MEMORY_GROWTH retain GROWABLE_ARRAYBUFFERS=0 deliberately.
  The pinned SDK still warns about non-Wasm performance. The WebGPU shim copies
  growable/shared/resizable views at tested upload/bind-group boundaries; switching
  to =2 is not assumed to solve WebGPU's fixed-buffer restriction. Physical-browser
  growth/performance remains to be measured.
- Asyncify improves feature compatibility but adds code size/runtime overhead;
  the trampoline trades direct tail transfers for dispatcher returns. JSPI stays
  available with PS2_WEB_ASYNC_MODE=jspi for suitable desktop browsers. Threads,
  SIMD, isolation and audio-worklet requirements still apply.
- Static missing-code repair validates alignment and file-backed executable ELF
  coverage before adding an entry. Dynamic/decompressed/overlay code requires an
  actual capture; it is not replaced with guessed instructions or forced returns.

## 6. Remaining blockers and acceptance checklist

The captured NFS sound RPC stall is repaired and replayed successfully; full game
startup/rendering still needs host verification. See NFS_RPC_FIX.md. No more
uploads are required for this specific fix. Crash Nitro Kart/Ratchet missing-code
addresses remain separate issues requiring their own matching executable/capture.

- [ ] Windows: fresh install and upgrade, four phases visible, no Store browser
  provisioning, useful exit/report on tool failure; default single compile job.
- [ ] Rebuild existing games; confirm build metadata says asyncify and smaller
  units. Preserve previous working player when a rebuild fails.
- [ ] Desktop Chrome/Firefox: poster → player → automatic launch; no info/start
  detour. Check console boot layout, keyboard focus, reduced motion and sound unlock.
- [ ] Phone: trusted HTTPS LAN link on a random port; no manual PEM inputs,
  private-key/admin routes denied, Safari touch/multitouch and orientation tested.
- [ ] Store: direct file works; page links rejected helpfully, no WAF/search calls.
- [ ] Transfers: queued removal, pause/resume, ignored Range, changed ETag,
  cancel while streaming, failed cleanup and row expiry. Test a slow real server.
- [ ] Downloads: Installing/Verifying/Building progress; remove queued build,
  concurrent enqueue isolation, dedupe and success cleanup; original files remain.
- [ ] Encrypted ZIP/7z: correct/missing/wrong passwords; CHD DVD/CD round trips
  with the installed Windows tools.
- [x] NFS: identify and replay the blocked sound RPC; repair polling APIs and wakeup.
- [x] NFS MW/U2 host native explore: drawing confirmed after RPC-fixed rebuild
  (MW 164 GS primitives / U2 614; non-black PPM shots). Asyncify web players published
  for both (`build.json` `async_mode=asyncify`). Full menus/gameplay/audio in Chrome,
  Firefox and physical Safari remain unchecked.
- [x] Mobile JSPI gate root cause: legacy JSPI wasm + missing `async_mode` defaulted to
  `jspi`. Panel now infers mode from `ps2web.js`; U2/MW rebuilt Asyncify. Physical
  phone trust/play still needs a one-time CA trust on the device.
- [x] CNK `0x006C7B50` / `0x006C7D50` (and neighbors): file-backed jump-table targets
  from `0x004BA8F4`; entries harvested from ELF pointer tables; explore reaches 3600
  frames with no misses. Next CNK issue: EE WaitSema stall with only 2 primitives /
  black shots after EnableCache no-op. GT4 `0x00281360` is not a live halt (already
  translated; explore shows ~1.1M primitives).
- [ ] Each affected title: confirm no missing-code halt, no no-drawing warning,
  textures/objects correct and load/save transitions stable on actual browsers.

## 7. Host verification session — 2026-11-05

Machine inventory confirmed toolchains and game ISOs under `games/<id>/disc.iso`.
Details: `verification/host-session-2026-11-05.json`.

### Code changes in this session

| File | Change |
|---|---|
| `scripts/panel.py` | `resolve_async_mode()`: prefer `build.json`, else infer JSPI vs Asyncify from published `ps2web.js`; never claim Asyncify for Suspending glue. |
| `host/window.cpp` | Native pacing matches web: audio backpressure supplements `frame_clock` wall clock. |
| `CMakeLists.txt` | Register `iop_rpc_snapshot` ctest when MW `explore_ram.bin` exists. |
| `tests/mobile_https.py` | Cover metadata-missing inference paths. |
| `runtime/src/kernel.cpp` | Explicit no-ops for EE `KSeg0`/`EnableCache`/`DisableCache` (0x60–0x62). |
| CNK `entries.txt` | Jump-table + follow-on static entries from boot ELF (108+ targets). |

### Commands and outcomes

```text
cmake -S . -B build/rpc-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug -DPS2_BUILD_TESTS=ON ...
cmake --build build/rpc-tests --target iop_rpc_poll iop_rpc_snapshot
# with wgpu_native + clang64 on PATH:
build/rpc-tests/iop_rpc_poll.exe          -> PASS
build/rpc-tests/iop_rpc_snapshot.exe <current explore_ram.bin> -> FAIL (dump overwritten; see JSON)

python tests/mobile_https.py              -> PASS (incl. async-mode inference)
python tests/installation_flow.py         -> PASS (7 tests)

# NFS Most Wanted
build/native-60c82f4a…/ps2run.exe … --frames 3600  -> 164 primitives, shots non-black
python -u scripts/windows_port.py --web-only 60c82f4a111da300ac23bbec85272788 -> asyncify

# NFS Underground 2
build/native-c0671389…/ps2run.exe … --frames 3600  -> 614 primitives, shots non-black
python -u scripts/windows_port.py --web-only c0671389c296be6afe9e5224c97d30df -> asyncify

# Crash Nitro Kart
eerecomp + jump-table entries; native explore -> 3600 frames, 0 misses, 2 primitives, black shots
```

### Remaining failures / evidence needed

1. **CNK black boot after missing-code repair** — Legal `LEGENG.TGA` draws (2 prims) then EE WaitSema 43/45. Disc loads `CRI_ADXI` and finds `ASSETS.GFC`/`ASSETS.GOB`, but `MODULES/IGFILEIO.IRX` (plus mouse/kbd IG* modules) are **not on the ISO, IOPRP, or GOB**. Intrinsic Alchemy asset IO never starts; `VVAA.IRX` is present but unused.
2. **NFS MW/U2 post-title WaitSema** — Title art draws (MW 164 / U2 614 prims; browser MW logo confirmed). Trace shows a single completed SND RPC `0x00534E44` fn0, then empty `SifIopReset("")` x2, then all EE threads WaitSema(44) at ra `0x00497C00` with pad idle. Menus/gameplay still unproven.
3. **`iop_rpc_snapshot` local replay** — restore capture SHA-256 `2627bb0d…` (see `verification/nfs-rpc-results.json`) or keep relying on the recorded PASS. Current `explore_ram.bin` is post-title (`94332074…`).
4. **Physical phone Safari** — desktop panel + mobile HTTPS unit tests pass; live Safari-on-LAN trust/WebGPU not exercised overnight.
5. **Remaining library titles** — Asyncify queue rebuilding the rest after Ratchet + GoW II.

## 8. Overnight follow-up — 2026-11-05/06

Evidence: `verification/host-session-2026-11-05-overnight.json`.

| File | Change |
|---|---|
| `scripts/panel.py` | `sys.path` bootstrap + `if __name__ == '__main__'` so `python scripts/panel.py` actually serves. |
| `runtime/src/iop/sif.cpp` | `SIF_CMD_RESET_CMD` (0x80000003) handler; SMFLAG write-clear + republish SIFINIT/CMDINIT after Reset; SYSREG SUBADDR/MAINADDR/RPCINIT; polling `deliver_request` always wakes/credits; state v8 fields. |
| `runtime/src/system.cpp` | Save-state version **8**. |

Verified: panel `/` and `/play/<id>/` (asyncify inject); `tests/mobile_https.py` + `mobile_auto.py` PASS; `iop_rpc_poll` PASS; Chrome play MW reaches title; Asyncify published for MW/U2/CNK/Sly/Hot Shots/Ratchet/GoW II/GoW I (queue continuing).

## 9d. Autonomous SIF dest0 + CNK IG* HLE — 2026-11-06 ~03:00

| Item | Result |
|---|---|
| NFS “empty `SifIopReset("")`” | **Misdiagnosis corrected.** `set_dma` treated every `dst==0` transfer as reboot. Title-path issued zero-length dest0 probes → false empty reboot ×2 mid-CDVD. Now: reboot only when `cid==0x80000003`; `size<16` dest0 ignored. Logs no longer show empty reboot. |
| NFS MW / U2 gate | **Still blocked:** MW 164 prims `WaitSema(44)` `ra 0x00497C00`; U2 614 prims `WaitSema(48)`. Soft-reset / sif0-hold experiments did not advance past title. Web republish deferred. |
| CNK IGFILEIO | Disc lacks IRX. Added `register_hle_module` stubs for `IGFILEIO` / `IGUMOUSE` / `IGUKBD` plus RPC servers `0x12114` / `0x12112` / `0x12113`. Host-side HLE send snapshot (EE buffer clobbered across `sync_iop`). |
| CNK gate | **Partial:** past LoadModule fail; binds succeed; `POOLS.CSV`+`ASSETS.GFC/GOB` found; VIF1/GIF busy; still **2 prims** + WaitSema 45/47 (black after legal). |
| Hot Shots streamfix | **DONE** in `host/web.cpp` (4×25s fetch + 90s disc wait). |
| Asyncify queue | RE4 `ffb47d7e` still compiling; Def Jam retry next. |
| Regressions | `malware_guard` / `mobile_auto` / `player_crashlog` / `iop_rpc_poll` PASS. |

`verification/host-session-2026-11-06-autonomous.json` records this session.

## 9c. Render pacing + Hot Shots table seed — 2026-11-06 ~01:30

| File | Change |
|---|---|
| `runtime/src/gs/gpu/gpu.cpp` | Prefer **Mailbox → Fifo** present modes (Immediate only via `PS2_PRESENT=immediate`). Uncapped Immediate tore/juddered under Asyncify. |
| `host/web.cpp` | Always wait for displayed frame (removed idle-skip vsync that caused uneven pacing); raise render drain budget **6→10 ms**; disc chunk wait **30→90 s**; fetch retries **2×10s → 4×25s** with backoff. |
| `runtime/src/gs/gs.cpp` | Deeper present backlog before EE stall (web 4 / native 3) so brief GPU hitch does not freeze gameplay. |
| `web/shell.html` | Force scale **1×** on Asyncify/touch; default aspect **4:3**; `#stage-frame` letterboxes to aspect (stop stretching to window); clearer software-renderer lag warning; default **`PS2_NO_DEINTERLACE`** (bob) to stop weave ghost trails under Asyncify. |

Hot Shots Golf (`f29093e1…`): init dispatcher at `0x00100AF0` walks function pointers `0x00338300–0x00338388`. Seeded all 35 table targets (+ prologues) into `entries.txt` (58 total). Native retranslate + smoke: **120f PASS**, **600f PASS** (`235752` prims, no missing-code). Web republish **PASS** (`build.json` `async_mode=asyncify`, includes Mailbox/pacing host fixes).

## 9b. Continual debug — 2026-11-06 ~01:00

| Item | Result |
|---|---|
| GT4 asyncify | **PASS** `build/web-9ce58de3…/build.json` `async_mode=asyncify` (wasm-opt survived ~33 min / ~3.5 GiB). |
| Hitman BM `a2116d2a` | **PASS** asyncify published. |
| Hitman 2 `f141051d` | **PASS** asyncify published; queue advanced to RE4 `ffb47d7e`. |
| `install_identity.sha256` | Fixed for Python 3.10 (`hashlib.file_digest` → streaming `sha256`). `tests/installation_flow.py` PASS 7/7. |
| `windows_setup` checksums | Same 3.10-safe digest helper. |
| `iop_rpc_poll` | PASS with wgpu PATH. |
| NFS MW empty `SifIopReset("")` | Reproduced: 164 prims → empty reboot ×2 → EE WaitSema(44) `ra 0x00497C00`. Trace: reboot hits mid sound-worker RPC; afterward IOP only emits SREG `cmd 1` spam, no further EE CallRpc completions. Tried keeping RPC state on empty-path reboot (`sif.cpp`); **stall unchanged** (still 164 prims). Hypothesis narrowed; fix not yet found. |
| Malware / mobile / security | PASS. |

## 9a. Malware execution guards — 2026-11-06

| File | Change |
|---|---|
| `scripts/malware_guard.py` | Reject PE/MZ, host ELF, Mach-O, scripts, and dangerous extensions before import; Microsoft Defender custom scan when available (≤96 MiB); explicit refuse-to-execute API for imported content. |
| `scripts/panel.py` / `windows_port.py` / `archives.py` | Call `assert_safe_import` on Add/download/extract paths; archives never launch members (stdout stream only); host-only archives refused. |
| `tests/malware_guard.py` | 8 unit tests for PE-as-ISO, extensions, scripts, Defender threat abort, archive selection. |

Verified: `python tests/malware_guard.py` PASS; `tests/security_review.py` PASS; `tests/mobile_auto.py` PASS.

## 9. Overnight resume — 2026-11-06 (post-crash)

Cursor crashed mid-queue. UI fixes finished first; asyncify resume continued in background.

| File | Change |
|---|---|
| `web/mobile.html` | New themed mobile library (poster grid, dark panel look, search). |
| `scripts/mobile.py` | `/` (library mode) serves `web/mobile.html` with ready-game cards + `/play/<id>/?touch` links. |
| `web/panel.html` | Brand shortened to **CyberArcade**; hide Phone access + duplicate Library chrome under 640px. |
| `web/shell.html` | Brand/title shortened; Settings cog gold-highlighted; `?touch` still enables on-screen pad. |
| `tests/mobile_https.py`, `tests/mobile_auto.py` | Cover themed library, touch redirect, Settings control, no Phone-access chrome. |

### Asyncify queue

- **PASS already published:** `1e5a12a0`, `34402ee3`, `695b874b`, plus earlier MW/U2/CNK/Sly/Hot Shots (and skipped-listed `c0c45270`).
- **Def Jam `76615f99`:** FAILED at final `wasm-opt --asyncify` link (`returned 3221226505` / Windows abort). Compile reached `[663/664]` then wasm-opt crashed. Documented; queued for end retry after remaining titles.
- **GT4 `9ce58de3`:** Interrupted by crash at ~[230/1345]; **resume script restarted** (`logs/rebuild_asyncify_queue_resume.ps1`). Remaining after GT4: Hitman BM, Hitman 2, RE4, then Def Jam retry.
- Tests re-verified: `mobile_https` PASS, `mobile_auto` PASS.

## 9e. All-game health + MW overlay + Sly CLUT � 2026-11-06 ~04:20

Evidence: `verification/host-session-2026-11-06-0418.json`.

| Item | Result |
|---|---|
| Install health gate | **DONE.** `scripts/install_health.py` writes `games/<id>/health.json`; hooked in `windows_port.port` after explore and `panel.build` before ready. Full installs fail on missing-code / near-zero prims. Unit tests in `tests/installation_flow.py`. |
| Synthetic overlay capture | **DONE.** `scripts/windows.py capture` now builds RAM overlays for missing-code addresses when the ELF has no BSS windows (NFS MW class). |
| NFS MW `0x01A5BEA4` | **PASS native.** After overlay `01A53000_8A2468D3`: **500 frames, 134911 prims**, frame limit (was missing-code halt at 274f / 6420 prims). |
| NFS U2 | Native already past title (~252k prims). Web `--web-only` republish running. |
| CNK IGFILEIO | GFC/GOB host reader + open/read HLE in `runtime/src/iop/igfileio.cpp` (zlib). Method 19 stays cheap ack. Still **2 prims** � EE never issues further `0x12114` methods; stall is post-CDVD. Health correctly **fail** `near_zero_prims:2`. |
| Sly textures | GPU vs software **0% pixel diff** on broken gameplay frames ? shared GS path. Fixed CSM2 8-bit CLUT to 16�16 block in `gs.cpp` / `gs.wgsl` / `gpu.cpp`. Intro/logo scene unchanged by that fix; gameplay rooftops still show black dither/noise � more TEX/ATE work needed. |
| Regressions | `malware_guard` / `mobile_auto` / `player_crashlog` / `installation_flow` / `iop_rpc_poll.exe` **PASS**. Hot Shots `/play/` HTTP 200. |
| Asyncify queue | RE4 hit cmake 7200s timeout mid-link; orphan em++ may still run; Def Jam still pending. |


### Follow-up same session
| Item | Result |
|---|---|
| Sly PACKED STQ sticky Q | **Fixed** in `gs.cpp`: vertices use sticky `s.q`; STQ updates rgbaq.Q. Rooftop dark-pixel fraction **6.7% ? 0.4%** on frame 1800 (`logs/sly-gameplay-final`). |
| CNK GS FINISH deferral | FINISH no longer raised during GIF scan before Alchemy callback; counter `705C00` advances. WaitSema(47) wakeups via TIM0 + `iSignalSema` reschedule. **Still 2 prims** (legal only); SIID asset path runs but no new PRIM writes. |
| Emscripten zlib | `ps2runtime` now `-sUSE_ZLIB=1` on compile+link for `igfileio.cpp`. |

## 9f. Overnight CNK TIM0 / Alchemy attack — 2026-11-06 08:18

| Item | Result |
|---|---|
| EnableIntc wake-on-pending | Done. intc_set_mask(true) wakes idle if STAT already latched. |
| TIM0 count-enable hold | Done. While Alchemy STBL pending, guest MODE clears of bit 0x80 are held. |
| STBLz first-cluster repair | Still plants correct GOB block0 + walker flag. |
| Host full-file install | Reverted (overflowed 64KB work buffer; crashed). |
| Host-call walker | Reverted (handler WaitSema spin). |
| FINISH deadlock catchup | One-shot gap>=3; still 2 prims / fonts not consumed. |
| RE4 asyncify | Aborted: wasm-opt hung 5.7h with no wasm mtime change. logs/web-re4-wasm-opt-abort.log |
| CNK gate | OPEN: legal only (2 prims). |


## 9g. Overnight continued — 2026-11-06 08:41

| Item | Result |
|---|---|
| RE4 wasm-opt | Aborted hung 5.7h link (no wasm mtime). |
| Def Jam asyncify | **Published** `build/web-76615f…/ps2web.html` (~08:37); play HTTP 200. |
| windows.py synthetic overlays | Now captures misses **outside** ELF windows (Alchemy RAM code), not only no-window ELFs. |
| CNK Alchemy overlay retranslate | Captured 5.6MB `00100000_*`; eerecomp 134k entries / 684 units; native rebuild OK. Gate gap improved (~2); **still 2 prims**, fonts STBL uncleared. |
| CNK remaining | EE WaitSema/FINISH vs GOB walker; igctx@7430C0 left zero by method-19 HLE (filling it previously zeroed prims). |


### Follow-up overnight (TIM0)

- Root cause candidate for Alchemy delay: host kick wrote `COMP=count+64` with reset-on-compare, causing **TIM0 IRQ storm** (count=comp=64 forever). Removed.
- TIM0 compare IRQs do fire with real comps after STBL repair; later dump still shows count frozen at 371 vs comp ~53k while threads WaitSema(45/47) in delay helpers (`0x423004` / `0x427234`), not the GOB walker.
- Def Jam web asyncify **shipped**; MW/U2/Sly/Hot Shots HTTP 200.
- `windows.py` now synthetic-captures misses outside ELF windows (Alchemy RAM). CNK retranslated+rebuilt; still 2 prims.

## 9h. Overnight CNK continued — 2026-11-06 ~09:00

Evidence: `verification/host-session-2026-11-06-overnight-cnk.json`, `logs/cnk-tim-pulse-5000.log`.

| Fix | Result |
|---|---|
| TIM0 MODE hold without `timer_set_count` | Stops count snapshot-freeze at 371 on high-freq MODE writes |
| `alchemy_stbl_pending` ignores walker flag | Hold survives guest clearing `0x6F5B20` while WaitSema-parked |
| Repair want/cap recovery | Guest `want=547` no longer skips repair; STBL0 65541B @ `0x762390`, `first=2005` |
| FINISH target-pull default | Gate advances; still legal-only |
| Periodic `timer_arm_compare_pulse` | Count advances (e.g. 4277); still 2 prims |
| Host-write `0x7AF300` | **Unsafe** — overwrites live objects → null vtable → `jalr 0` ra `0x10C4B8`. Gated off |
| DisableIntc(TIM0/1) hold | Added; guest rarely hits it vs MODE clear |

**CNK still OPEN:** 2 prims, `igctx@7430C0=0`, walker `cur=first=2005` with STBL0 ready but not consumed. Rebuild-all deferred.

### 9h addendum — FINISH unmask

- Clearing GS IMR bit `0x200` while STBL pending closes the Alchemy FINISH gate (**gap 0–1** at 6k–10k frames).
- Delay-sema pulse re-opens gap to 3 — left behind `PS2_ALCHEMY_KICK`.
- Host-call pump `0x23ED50` (even late, gate healthy) still `jalr 0` at ra `0x2381DC` (null vtable +88). Not safe.
- SIID status word at `0x155F948` keeps advancing; fonts path still not consumed.


## 9i. Overnight TIM0 drain + host gob-extract � 2026-11-06 ~night

| Fix | Result |
|---|---|
| Force TIM0 INTC while `705DF8>0` | DF8 drains (35?0); handler `0x426EF0` runs; COUNT no longer stuck at 371 |
| TIM0-complete IRQ when DF8==0 + gate healthy | `iSignalSema` path hits; delay waiters re-arm (loop) |
| Hold TIM0/1 via INTC_MASK MMIO | Mask stays `0x601` (GS+TIM0+TIM1) |
| `alchemy_stbl_pending` requires `STBL0` | Stops pre-repair TIM0-complete from clearing `705BF0/BE0` |
| Never host-signal FINISH sema 45 from delay kick | Avoids reopening gap treadmill |
| Host-call pump `0x23ED50` / walker `0x242480` | **Unsafe** (jalr 0 / hang) � env-gated only |
| Host gob-extract fonts CRC?`0x1A00000` (80812B) | Works; `cur=0x7FFF` `remain=0`; **still 2 prims**, `igctx=0` |
| Pad Start/Cross mash to 30k | No change � still legal splash |

**CNK still OPEN.** TIM0/FINISH plumbing is healthy; GOB bind/pump still never runs on EE threads (WaitSema 45/47). Rebuild-all still deferred. Disk ~19.3GB free.


### 9i addendum � sema2 / VSINT

- IMR `0x7400` already has VSINT (`0x800`) and FINISH (`0x200`) clear � not the main-thread stall.
- Thread 2 (prio 0) loops `WaitSema(2)` at `0x43D7E0` (event queue). **No guest Signal/iSignalSema(2) observed** across 8k frames; only host pulses wake it, then it re-waits.
- Event enable flag `0x657F78=2` (armed). Producers at `0x43D9C0+` exist but are not reached.
- Other-game smoke (`34402ee3�`, 1000f): **5.7M prims** � TIM0/INTC holds did not break non-CNK.


### 9i addendum2 � sema2 queue
- Thread2 event loop at  x43D7E0; **zero guest SignalSema(2)**.
- Host queue post cmd=1 + signal: thread consumes once (Wait count=1) then re-parks; still **2 prims**.
- Non-CNK smoke still healthy earlier.

