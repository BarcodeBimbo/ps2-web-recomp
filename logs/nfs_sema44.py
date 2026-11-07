# -*- coding: utf-8 -*-
from pathlib import Path
raw = Path("logs/nfs-mw-softreset3.log").read_bytes()
text = raw.decode("utf-16") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", errors="replace")
lines = text.splitlines()
# print full thread dump near end
start = next(i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("[ee] halted") or "frame limit" in lines[i])
for l in lines[start - 40 : start + 5]:
    print(l)
print("---")
# any sif activity counts after empty
idx = next(i for i, l in enumerate(lines) if 'IOP reboot requested with ""' in l)
after = lines[idx:]
from collections import Counter
c = Counter()
for l in after:
    if l.startswith("[sif]"):
        c[l.split(":")[0][:50] if False else l[:60]] += 1
print("sif line kinds after empty (top):")
for k, v in c.most_common(15):
    print(v, k)
