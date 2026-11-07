# Current update

Close the host, extract this full update over C:\PS2Recomp and run Setup.cmd.
Rebuild existing games once from their … menu to apply the new runtime.
See [FIX_REPORT.md](FIX_REPORT.md) for current findings, changes and test limits.
The Store now accepts direct links only. Posters launch players automatically.

## Historical update notes

> Earlier report. See [FIX_REPORT.md](FIX_REPORT.md) for the current setup/mobile/Store changes, tests and unresolved runtime cases.

# CyberArcade — November 5, 2026

## Install this update

1. Close the panel terminal and all player tabs.
2. Extract the ZIP contents into your existing project folder, for example `C:\PS2Recomp`, replacing matching source files. Keep `games`, `generated`, `tools`, `third_party`, and `build`.
3. Run `Setup.cmd` again. Reopen the player in a new tab.
4. If importing previously failed at “Preparing executable” with `invalid or unsafe ISO filename`, add the original ISO/archive again. Failed imports may not have generated the code needed for a browser-only rebuild.

The served JavaScript now applies the WebGPU upload fix to existing browser builds and their workers. You do not need to rebuild every game just to fix the reported `GPUQueue.writeBuffer` initialization error. A future **Rebuild browser player** also switches off growable buffer views at compile time while keeping WebAssembly memory growth enabled.

## Player fix

WebGPU upload data is copied to a fixed backing store only when its original buffer is resizable or growable. The compatibility patch preserves typed-array element offsets, DataView byte offsets, and the selected upload range. One staging allocation is reused within each worker. Fixed buffers retain their existing upload path.

The current WebGPU renderer, software fallback, Firefox capability handling, mobile controls, and player UI remain in place. The old attached build was used as a reference, not as the replacement player.

## ISO reader fix

Disc browsing no longer rejects legal ISO identifiers just because Windows cannot use them as filenames. For example, `DATA.;1` becomes the readable disc identifier `DATA.`. Scanning for the optional `CORE.GT4` file now passes these records. Host-path restrictions still apply when exporting disc-named files; boot extraction uses its fixed local name. Malformed records, traversal, cycles, and out-of-image extents remain rejected.

## Archive passwords and Store

- Store version downloads and direct-link downloads default to the supplied password `romsfun.com`. You can change or clear it.
- Opening a game page through **Add download link** now carries your chosen password into the version dialog.
- **Add downloaded file** prefills the store password for an import retry.
- Local **Add game** still accepts any known archive password and preserves it if submission fails.
- Normal provider cookies are shared between catalog requests and downloads. Failed catalog loads can be retried by returning to Store.
- Provider HTTP 401/403/429 errors explain the download-and-local-import recovery path. **Open provider** opens the source in your browser.

The live provider could not be inspected from this environment: the browser security policy denied access to romsfun.com, and web retrieval did not return its page. No claim is made that its HTTP 403 restriction or current live version-link format is fixed. The existing parser remains in place. If the provider still refuses automated requests, download in your own browser and import the archive using its password.

Passwords remain absent from saved game metadata and download jobs. For encrypted 7z/RAR/AES ZIP extraction, 7-Zip temporarily receives the password as its documented command-line argument.

## Branding

- Home: **CyberArcade - Home**
- Library: **CyberArcade - Library**
- Store: **CyberArcade - Store**
- Downloads: **CyberArcade - Downloads**
- Player: **CyberArcade - [game title]**

Click the sidebar brand to return Home. The sidebar and README use the new name.

## Verification for this update

Passed JavaScript regressions for the growable/resizable upload failure, offset handling, buffer growth, fixed-buffer fast path, idempotent installation, player logic, and panel navigation/password handoff/branding.

Passed Python regressions for ISO trailing periods and device names, extraction boundaries, malformed images, range serving, existing-player script prefixing (GET/HEAD), store defaults and HTTP errors, synthetic downloads, build publication, queue handling, and server access checks. Real 7-Zip integration passed for ZipCrypto, AES-256 ZIP, encrypted 7z headers, wrong passwords, RAR, TAR, and nested TAR.GZ using synthetic discs.

No commercial game, Windows toolchain build, or physical GPU gameplay session was available here. The exact data-upload restriction was reproduced with native resizable/growable JavaScript buffers and a queue contract test; actual Chrome/Firefox gameplay on your PC still needs confirmation.
