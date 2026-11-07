# NFS startup RPC fix — November 5, 2026

## Diagnosis

The uploaded RAM snapshot and both IRX bundles identify the blocked request:

- Driver: `SND_Library_EE_Driver` from `IRX281B.BUN`.
- RPC server `0x00534E44` (SND), function **0**, 20 input bytes, no receive buffer.
- Queue `0x000A1160`, server descriptor `0x000A1178`, callback `0x000930A0`.
- The captured worker is asleep immediately before PC `0x00093554`.
- Its custom loop calls IOP `sifcmd` imports **20 / 21**:
  `sceSifGetNextRequest` and `sceSifExecRequest`. Neither was implemented.
- Delivery only woke `kWaitRpc` workers. This custom worker uses `SleepThread`,
  so its queued request remained unprocessed and the EE waited for its reply.

The runtime now implements these polling APIs and wakes sleeping queue owners.
It preserves a wake credit for arrival between an empty poll and SleepThread,
respects suspended/unrelated waits, and retains the built-in sceSifRpcLoop path.
This is a generic SIF runtime correction, with no title/address-specific patch in
production code. The addresses above are only used by the captured-state QA test.

## Changes

| File | Concrete change |
|---|---|
| runtime/src/iop/sif.cpp | Poll/dequeue/execute APIs; sleep wake/credit handling; preserve caller continuation across blocking callbacks; publish RPC descriptor fields; validate touched RAM extents and reject length overflow before rounding/copying. |
| runtime/src/iop/kernel.hpp | Track the polling RPC return PC on each IOP thread. |
| runtime/src/iop/kernel.cpp | Reset RPC context on thread restart; serialize the return PC for state version 7; initialize it to zero when loading older states. |
| runtime/src/system.cpp | Save-state version 7 for the added continuation field. Older accepted state versions keep their existing field layout. New version-7 quick states require this updated runtime. Memory-card format is unchanged. |
| scripts/panel.py, web/panel.html | Add Re-explore and rebuild using the installed ISO, so native discovery can reach paths previously blocked by this deadlock. |
| CMakeLists.txt | Optional native RPC test targets via PS2_BUILD_TESTS. |
| tests/iop_rpc_poll.cpp | Synthetic IRX imports, actual IOP scheduler/SIF execution, blocking callback, stack/ABI preservation, replies, wake race, unrelated waits, built-in RPC loop, version-7 save/restore, version-6 field compatibility, RAM/length guards. |
| tests/iop_rpc_snapshot.cpp | Replays the uploaded NFS IOP polling code and its real function-0 handler. Requires that capture as a local argument; no game binary/data is shipped. |

`nfs-rpc.patch` is the focused code diff against the prior console-update ZIP.
`changes.patch` is the cumulative diff against the original supplied project.

## Verified results

1. **Before:** the focused baseline reproduction fails: queued RPC does not wake
   the sleeping polling worker. It also reports missing `sifcmd #20`.
2. **After:** synthetic regression passes, including an RPC callback that sleeps,
   is saved/restored, then resumes and returns to its polling caller. The built-in
   RPC-loop regression also passes, with no guest-stack leak.
3. **Captured NFS request:** the actual driver polling code and actual function-0
   callback from the snapshot execute and produce the reply after **377 slices**
   of 800 EE-equivalent cycles. The worker advances to **0x000935B0**, beyond the
   polling loop. The baseline cannot wake this captured worker.
4. **Sanitizers:** the SIF/test translation unit passes ASan/UBSan while linked
   against the normal Clang-built runtime. This does not claim whole-runtime
   sanitizer coverage.
5. **Builds:** native Clang runtime and both test executables build; CTest passes.
   Emscripten 6.0.11 compiles and links the complete updated runtime with a synthetic
   player in Asyncify mode. The existing pthread/memory-growth performance warning
   remains visible; it is not suppressed.

Exact commands/results and input SHA-256 values are under `verification/nfs-rpc-*`.
The earlier 24 passing regression groups remain recorded in console-results.json.
This follow-up also reran install/queue and panel DOM tests after adding the
re-exploration action; Store transfers and launch behavior were not changed.

### Reproduce synthetic test

Use Clang (the runtime uses Clang vector builtins):

```sh
cmake -S . -B build/rpc-tests -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_COMPILER=clang++ -DPS2_BUILD_TESTS=ON
cmake --build build/rpc-tests --target iop_rpc_poll iop_rpc_snapshot
ctest --test-dir build/rpc-tests --output-on-failure
```

The optional captured-state test takes the specific uploaded capture:

```sh
build/rpc-tests/iop_rpc_snapshot "/path/to/explore_ram(1).bin"
```

On Windows, use the bundled Clang/CMake/Ninja paths or a shell containing those
tools; the test executable ends in `.exe`.

## Apply and verify on the host

1. Close the host/player, extract the complete ZIP over `C:\PS2Recomp`, run Setup.cmd.
2. For Most Wanted, choose **… → Re-explore and rebuild** once. Rebuilding is
   required: replacing source/HTML cannot alter the already compiled runtime.
   Re-exploration also discovers code paths beyond the old stall; a web-only
   rebuild would retain the earlier exploration coverage.
3. Launch via the poster. Confirm the loading screen advances to game video and
   test menus/gameplay, sound, memory-card load and subsequent loading screens.
4. If another stall occurs, download the updated diagnostics and provide that
   output; this fixes the demonstrated RPC deadlock, not every possible later
   emulation fault.

## Limits

The captured RPC completing is verified. Full game rendering/gameplay on Windows,
Chrome, Firefox and a physical phone is still not verified here; the environment
blocks live Chromium launch and the complete disc is not present. The capture
replay reconstructs the blocked IOP worker and runtime imports; it is not a full
machine-state restore. No further uploads are needed to apply this fix.

Primary API reference reviewed: PS2SDK's IOP SIF RPC implementation, including
request wakeups, polling and execution:
[PS2SDK IOP SIF RPC source](https://github.com/ps2dev/ps2sdk/blob/master/iop/system/sifcmd/src/sifrpc.c)
