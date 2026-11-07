# -*- coding: utf-8 -*-
from pathlib import Path
import re

raw = Path("logs/cnk-ig4.log").read_bytes()
t = raw.decode("utf-8-sig") if raw.startswith(b"\xef\xbb\xbf") else raw.decode("utf-8", errors="replace")
lines = t.splitlines()
print("EE threads / sema at end:")
for l in lines:
    if l.startswith("[thread]") or l.startswith("[sema]") or l.startswith("[ee]"):
        print(l[:160])
print("igfileio methods:")
for l in lines:
    if "igfileio" in l or "igumouse" in l or "igukbd" in l:
        print(l[:160])
print("fileio opens", [l for l in lines if "[fileio]" in l])
print("cdvd searches", [l for l in lines if "search" in l])
print("frame max prim", max((int(b) for a,b in re.findall(r"\[frame\] (\d+) prims (\d+)", t)), default=0))
