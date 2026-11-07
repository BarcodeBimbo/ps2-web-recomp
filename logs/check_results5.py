# -*- coding: utf-8 -*-
from pathlib import Path
import re


def load(p):
    raw = Path(p).read_bytes()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8", errors="replace")


print("==== CNK ====")
t = load("logs/cnk-ig4.log")
lines = t.splitlines()
# activity after IGUKBD
idx = next(i for i, l in enumerate(lines) if "IGUKBD" in l)
for l in lines[idx : idx + 80]:
    print(l[:160])
print("...")
for l in lines[-30:]:
    print(l[:160])

print("\n==== NFS sound / late ====")
t = load("logs/nfs-mw-dest0cmd.log")
lines = t.splitlines()
for i, l in enumerate(lines):
    if "00534E44" in l or "dest0" in l or (i > 1300 and ("call server" in l or "bind" in l or "to EE" in l)):
        if i < 1400 or "dest0" in l or "00534E44" in l:
            print(i, l[:160])
print("END state:")
for l in lines[-35:]:
    if l.startswith("[thread]") or l.startswith("[sema]") or "primitives" in l or "Sound" in l:
        print(l[:160])
