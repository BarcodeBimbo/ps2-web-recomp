# W-RES worker report — resource accessibility probe (2026-11-07)

**Worker:** W-RES  
**Plan:** `logs/master-campaign-plan-2026-11-07.md` §6  
**Method:** Live path/HTTP/MCP probes (no game patches)

---

## Pass / fail matrix

| Resource | Verdict | Evidence |
|----------|---------|----------|
| **Ghidra 12.1.2 install** | **PASS** | `C:\Users\joshy\ghidra_12.1.2_PUBLIC\ghidraRun.bat` exists |
| **EE Reloaded extension** | **PASS** | `...\Ghidra\Extensions\ghidra-emotionengine-reloaded\` present |
| **Project `PS2Elves`** | **PASS** | `C:\Users\joshy\ghidra_projects\PS2Elves.gpr` + `.rep` tree |
| **Ghidra MCP HTTP `:8089`** | **PASS** | `GET http://127.0.0.1:8089/get_project_info` → 200, `project_name=PS2Elves`, `program_count=4`; `list_open_programs` includes `hitman_boot.elf` (current); Java pid **3152** (headless server) |
| **Ghidra MCP (Cursor bridge)** | **PASS** | `connect_instance` → `localhost:8089`, **214** tools registered |
| **Alchemy tree** | **PASS** | `C:\usr\alchemy\` — `AlchemyEvalKit`, scripts, game stubs; `ps2tek\` mirror **277** files, `index.html` present |
| **SCE SDK 3.0.3** | **PASS** | `E:\usr\local\sce\` — `readme-3.0.3.txt`, `common\include\libver.h` → `SCE_LIBRARY_VERSION 0x3030`, `ee\lib\libcdvd.a`, `iop\modules\padman.irx` |
| **`tools/ps2-alchemy-dumper`** | **PASS** | Dir exists; `python -m ps2_alchemy_dumper --help` OK (`list-iso`, `map`, `verify`, `optical`); prior `out/` + `out-cnk/` artifacts on disk |
| **ps2tek (live URL)** | **PASS** | `https://israpps.github.io/ps2tek/` → HTTP **200** (~279 KB body) |
| **ps2tek (local mirror)** | **PASS** | `C:\usr\alchemy\ps2tek\` (campaign primary offline copy) |
| **`E:\AI Browser Games\ps2_sdks`** | **PASS** | Path exists; **30** top-level entries (CD/DVD generators, CodeWarrior archives, etc.) |
| **binwalk on PATH** | **FAIL** | `where binwalk` empty; `python -m binwalk` — no module |
| **binwalk substitute (structural walks)** | **PASS** | Documented in `verification/recovery/alchemy-rebuild-w2-cnk-binwalk-toc-2026-11-07.md`, `_w2_cnk_binwalk_scan.py`, `_gow_structural_walk.py`, `gow-structural-walk-2026-11-07.md` |

**Overall:** **11 PASS / 1 FAIL** (binwalk CLI only; structural Python walks are the approved fallback).

---

## Probe detail

### Ghidra + MCP

- Install root: `C:\Users\joshy\ghidra_12.1.2_PUBLIC` (not the project file location).
- Project GPR: `C:\Users\joshy\ghidra_projects\PS2Elves.gpr` (matches `logs/ghidra-ps2/mcp-server.out.log` and `verification/recovery/ghidra-mcp-restart-2026-11-07.md`).
- MCP bind: `127.0.0.1:8089` — root `/` returns 404 (expected); use REST tool paths (e.g. `/get_project_info`).
- Default Cursor Ghidra MCP config may target **:13100** until `connect_instance` targets **:8089**.

### Alchemy + dumper

- Alchemy root is vocabulary / kit reference per master plan — not byte-identical to CNK runtime.
- Dumper is the in-repo ISO→`alchemy-map.json` path; run from `tools/ps2-alchemy-dumper` as `python -m ps2_alchemy_dumper`.

### SCE

- Research path rule: **only** `E:\usr\local\sce` for SDK macros (`.cursor/rules/ps2-sdk-research-path.mdc`).

### binwalk

- Do not block CNK/Alchemy TOC work: use existing `verification/recovery/*binwalk*` scanners until binwalk CLI is installed.

---

## Master plan §6

- [x] 2026-11-07 — W-RES accessibility probe (this report; binwalk CLI absent, structural walks documented)

---

## Open / follow-ups

| Item | Action |
|------|--------|
| binwalk CLI | Optional install to PATH for parity with upstream binwalk reports; not required while `_w2_cnk_binwalk_scan.py` remains canonical |
| MCP idle | If `:8089` stops responding, re-run headless per `verification/recovery/ghidra-mcp-restart-2026-11-07.md` or `Run-SilentGhidraPs2.ps1` |
