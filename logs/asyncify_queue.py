import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
import panel

root = Path(r"C:\PS2Recomp")
need = []
for lib in (root / "games").glob("*/library.json"):
    data = json.loads(lib.read_text(encoding="utf-8"))
    if data.get("status") != "ready":
        continue
    gid = data["id"]
    mode = panel.resolve_async_mode(gid)
    title = data.get("title", "?")
    print(f"{gid} {title:40s} {mode}")
    if mode != "asyncify":
        need.append(gid)
print("NEED", len(need))
(root / "logs" / "asyncify_queue.txt").write_text("\n".join(need), encoding="utf-8")
