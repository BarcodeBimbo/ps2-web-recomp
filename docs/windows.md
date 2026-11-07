For the current automatic phone access, setup logs, Store changes and release limits, see [FIX_REPORT.md](../FIX_REPORT.md).

**One launcher:** `Setup.cmd` now provisions Store Node.js, dependencies and its browser automatically, along with the emulator toolchain. Run it again for normal startup. No separate downloader setup is required.

# Native Windows setup

Extract the archive to a writable local folder with a short path and no spaces, such as `C:\PS2Recomp`. On Windows 11 x64, double-click **Setup.cmd** and keep its console window open. The first run needs internet access to install Python, a Windows Clang toolchain, SDL2, wgpu-native and the Emscripten SDK into the project folder. Later launches reuse those downloads. The panel opens at `http://127.0.0.1:8620/`. For browser play, open that address in Chrome or Edge.

1. Click **Browse…** in the panel and select a disc image in the Windows file picker. You can also paste a full path.
2. Click **Add and build**. Follow **Build log** for the compiler output and **Exploration log** for the last run. A build can take several minutes and uses a managed disc copy plus space for the generated code.
3. Choose **Play** to open the browser player. The browser stores its memory card per game and can import or export it.
4. Close the game before deleting it. **Delete** removes the managed copy, generated files and desktop card. The original disc image remains in place. Export browser saves before deleting a title so you can import them if you add it again.

Gran Turismo 4 and God of War II are the two titles demonstrated upstream. A build that finishes can still hit unsupported PS2 hardware behavior in play. If exploration stops before a later menu or level, the exploration log can identify where it halted. The Windows panel exposes frame and round settings. The original Unix CLI also exposes scripted button inputs, patch selection and desktop-only builds.

## Implementation plan and references

1. Install CLANG64 packages with the MSYS2 package manager and invoke the Win32 compiler, CMake and Ninja directly for builds. The package manager uses its own shell for setup. Building and playing run without WSL. [MSYS2 installer](https://www.msys2.org/docs/installer/) · [MSYS2 environments](https://www.msys2.org/docs/environments/)
2. Run the existing disc extraction and EE/VU recompilers from Python. Keep the native exploration loop so newly discovered entry points, overlays and VU programs reach the final builds.
3. Build the desktop player with SDL2, Win32 window handles and wgpu-native. Build the browser player with the Windows Emscripten SDK and keep the cross-origin isolation and byte-range disc server. [wgpu-native releases](https://github.com/gfx-rs/wgpu-native/releases/tag/v29.0.1.1) · [Emscripten installation](https://emscripten.org/docs/getting_started/downloads.html)
4. Expose the build pipeline behind a loopback-only panel. Queue builds in one isolated slot, retain logs, and assign each game its own URL and save path. Keep the original disc outside the managed library.
5. Verify on a clean Windows 11 x64 machine by running setup twice, building a known disc, launching both players, reloading saves, and deleting the managed game. Run those checks with WSL disabled.

## Troubleshooting

- If setup cannot bind the port, close the other process using port 8620, or open the existing panel if it is already running.
- If setup fails during a download, run **Setup.cmd** again. Successful installs are reused.
- If browser compilation fails after disc preparation, use **Retry build** to reuse the extracted disc and generated code.
- Keep the library on a drive with room for the toolchain, a copy of each disc and its build output. Recompilation across active games is limited to four concurrent compiler jobs to reduce memory pressure.

## Keyboard and mouse

WASD is the default for every game. Open **Remap controls** in the browser toolbar to see the disc boot ID, switch presets and change bindings.

In WASD mode, use **WASD** for the left stick and the **arrow keys** for the D-pad. **Space** sends Cross; **Enter** sends Start, **E** sends Circle, **R** sends Square, and **Q** sends Triangle. **C/V** send L1/R1, **Left Ctrl/Left Shift** send L2/R2, and **P** also sends Start; **Backspace** sends Select.

Choose **Capture mouse** in the toolbar. Press **Esc** to release browser pointer lock. Mouse motion drives the right stick in games that use it.

To update an existing title, close its browser tab and select **Rebuild browser player** in the library.

If a scene has corrupted graphics, compare the same scene using **Menu → Renderer: software** at native resolution. Changing the renderer reloads the game. The software path can be slower. If the same corruption appears in both paths, record the scene and disc ID so the shared graphics pipeline can be investigated.

In WASD mode, **Z** also sends L2 without using a browser Ctrl shortcut.

## Library actions

Right-click a game cover or use its three-dot button to open actions. **Add poster** accepts a local PNG, JPEG or WebP up to 5 MB. **View logs** opens a separate viewer with Build, Exploration and Desktop tabs in the log selector, plus a full log download.

The panel builds one game at a time and queues the rest. Each build uses up to two compiler jobs. Progress reflects the current stage and compiler task count, so it is an estimate of the work completed.

The library looks up cover art by disc serial using [PS2 Covers](https://github.com/xlenore/ps2-covers). Existing games with a recorded boot ID pick up art when you open the library. The lookup sends the serial to GitHub and caches successful downloads locally. If a match is unavailable, the card shows the default artwork. A poster you add manually takes priority.

**Remap controls** opens settings on demand. Click a binding, then press a key or mouse button. Use **Clear** to unbind an action. Layout, bindings, mouse settings and volume are saved per game in the browser.

The same toolbar is available in fullscreen. If a game uses the right stick for moves, bind those directions to keys and turn off mouse movement for the right stick.

Playback is browser-only. Importing and compiling discs still uses the installed local toolchain. Native exploration is optional and is skipped when maximum rounds is set to zero. Browser rebuilds reuse the prepared game and skip native compilation.

### Collect a game-drawn prompt for replacement

In windowed browser play, wait until the PS2 button prompt appears. Open **Menu → Capture prompt frame** and keep the prompt visible until the download starts. The capture is a local diagnostic with the disc boot ID, one frame of GS draw calls and 4 MiB of GS memory. Capture the same scene with the prompt absent if possible so the draw lists can be compared. This tool collects evidence for identifying prompt textures and does not modify the game's artwork.

The capture starts with a UTF-8 JSON line. Read the next `drawsBytes` bytes as the draw TSV and the next `vramBytes` bytes as the GS memory snapshot.

The local library serves the current player interface with existing game builds. After updating the project and restarting setup, reopen the game to load interface changes. Changes to the WebAssembly engine still require a browser rebuild.

In the WASD preset, **Enter** and **P** send Start, and **Space** sends Cross. Existing custom bindings are kept. **Menu → Press Start** sends Start independently of your saved keyboard layout.

When diagnosing missing geometry, compare the same scene with **Renderer: software** at native resolution. If only WebGPU is affected, collect a frame from each renderer. If both are affected, collect the build and exploration logs as well. The browser streams the original disc as the game requests resources.


### Disc formats and encrypted archives

The library accepts ISO, BIN, CUE, IMG, CHD, ZIP, 7z and RAR inputs. Setup installs the MAME 0.289 `chdman` utility into `tools/chdman` and the 7-Zip command-line tool into the project's MSYS2 tools folder. The MAME installer is downloaded from the official MAME release and checked against a pinned SHA-256 before it runs. The CHD utility is optional for non-CHD users; if installation fails, rerun `Setup.cmd` or set `CHDMAN` to a compatible `chdman.exe`. For an encrypted ZIP/7z/RAR file, enter its known password in the always-available archive password field. Leave the field empty for an unencrypted archive—password entry is never required unless the archive is actually encrypted. Unsupported ZIP compression methods are handed to the bundled 7-Zip tool. The importer checks the supplied password and reports a wrong password or damaged archive; it does not guess passwords. Passwords are omitted from saved library metadata and build logs. Python's native ZIP path keeps them in-process; 7-Zip's documented CLI requires a temporary `-p{password}` process argument for encrypted 7z/RAR and unsupported ZIP variants, so local process-inspection tools may briefly see it while extraction runs.

### Mobile and browser limitations

The player includes touch controls and responsive layouts, but a mobile browser must still implement the WebAssembly features listed on the start screen and provide cross-origin isolation for threads. Mobile compatibility therefore varies by device, browser and OS version. Firefox is tested through the same WebGPU adapter/presentation probe as other browsers; the code no longer disables direct presentation solely because the user agent contains `Firefox`. A browser without a usable adapter uses the software fallback, which may be too slow for 3D games.


## Updated controls and mobile access

See [controls and cheats](controls-and-cheats.md) for fullscreen Start/Menu, per-game X/Y mouse inversion, reference VU comparison, diagnostics downloads and live PNACH RAM cheats. See [mobile play](mobile.md) for complete dual-stick controls and the separate authenticated HTTPS listener. A phone needs a trusted HTTPS certificate and all runtime feature checks to pass.

CHD is decoded with MAME chdman before building. RAR, TAR and other supported archives use 7-Zip; single-member bounded extraction replaces bulk extraction. The importer never tries to guess an unknown archive password. See the [review report](../AUDIT_REPORT.md) for tested formats and validation limits.
