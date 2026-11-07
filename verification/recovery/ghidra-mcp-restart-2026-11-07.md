# Ghidra MCP restart / status — 2026-11-07

## Verdict

| Field | Value |
|---|---|
| **mcp_up** | **true** |
| **url** | `http://127.0.0.1:8089` |
| **action taken** | No process restart — headless MCP already healthy; Cursor bridge `connect_instance` to `PS2Elves` |
| **blocker** | none |

## Process / PID

| Item | Value |
|---|---|
| MCP Java PID | **3152** (matches `logs/ghidra-ps2/mcp.pid`) |
| Started | 2026-11-07 07:02:50 AM (local) |
| Command | `com.xebyte.headless.GhidraMCPHeadlessServer --port 8089 --bind 127.0.0.1 --project C:\Users\joshy\ghidra_projects\PS2Elves.gpr` |
| Ghidra home | `C:\Users\joshy\ghidra_12.1.2_PUBLIC` (USR) |
| JAR | `C:\Tools\ghidra-mcp\target\GhidraMCP-6.0.0.jar` |
| Bridge PIDs | python 6000 / 17724 (`bridge-mcp-ghidra.exe`) — already running |

Silent pipeline was **not** re-run (`-Action all` / import skipped). Existing `PS2Elves.gpr` + open programs reused. No disc-fix / R5 / CNK patches.

## HTTP checks

| Endpoint | Result |
|---|---|
| `GET /` | 404 (expected; no root handler) |
| `GET /health` | **200** — `status=healthy`, `version=6.0.0-headless`, `program_loaded=true`, `program_name=cnk_boot.elf` |
| `GET /list_open_programs` | **200** — count=2 |
| `GET /get_project_info` | **200** — `project_name=PS2Elves`, `program_count=2` |
| `GET /get_metadata` | **200** — current = `cnk_boot.elf`, lang `r5900:LE:32:default` |

## Programs loaded

| Program | Path | Current | Functions | Language |
|---|---|---|---|---|
| `gow_boot.elf` | `/gow_boot.elf` | no | 5692 | `r5900:LE:32:default` |
| `cnk_boot.elf` | `/cnk_boot.elf` | **yes** | 19188 | `r5900:LE:32:default` |

## Cursor MCP (`user-ghidra`)

1. Initial `list_instances` → empty (bridge had no active TCP session).
2. `connect_instance(project="PS2Elves")` → **connected** via TCP `http://127.0.0.1:8089`, 214 tools registered.
3. Post-connect `list_instances` → one instance, `connected=true`, `current_program=cnk_boot.elf`, `program_count=2`.

## Recovery note

If HTTP dies later, restart MCP only (no re-import):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\joshy\ghidra_exports\ps2-elves\Run-SilentGhidraPs2.ps1" -Action mcp
```

Then re-run Cursor MCP `connect_instance` with project `PS2Elves`.
