# -*- coding: utf-8 -*-
from pathlib import Path
import re

t = Path("logs/nfs-mw-sys.log").read_text(encoding="utf-8-sig")
lines = t.splitlines()
# Find when call servers stop
last_call = max(i for i, l in enumerate(lines) if "call server" in l)
print("last call server line", last_call, lines[last_call][:140])
print("--- 30 lines after last call ---")
for l in lines[last_call : last_call + 40]:
    if "sys]" in l or "sif]" in l or "frame]" in l:
        print(l[:160])
print("--- thread1 WaitSema after last call ---")
for i, l in enumerate(lines[last_call:], last_call):
    if "WaitSema" in l and "thread 1" in l:
        print(i, l[:160])
        break
print("--- unique WaitSema ids after last call (first 30) ---")
seen = []
for l in lines[last_call:]:
    m = re.search(r"WaitSema\((0x[0-9A-Fa-f]+|\d+)\)", l)
    if m:
        seen.append((m.group(1), l[l.find("thread") :] if "thread" in l else ""))
print(seen[:40])
