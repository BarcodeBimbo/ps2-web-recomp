# -*- coding: utf-8 -*-
from pathlib import Path

lines = Path("logs/nfs-mw-sys.log").read_text(encoding="utf-8-sig").splitlines()
last_call = max(i for i, l in enumerate(lines) if "call server" in l)
print("from line", last_call)
for i, l in enumerate(lines[last_call : last_call + 120], last_call):
    if any(k in l for k in ("SifSetDma", "call server", "bind", "dest0", "command 0x", "IOP reboot", "to EE")):
        print(f"{i}: {l[:170]}")
