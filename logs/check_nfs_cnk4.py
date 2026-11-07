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


text = load("logs/nfs-mw-dst0.log")
lines = text.splitlines()
# Find last call servers / activity
calls = [(i, l) for i, l in enumerate(lines) if "call server" in l]
print("last 15 calls:")
for i, l in calls[-15:]:
    print(i, l[:160])
print("last binds:")
for i, l in enumerate(lines):
    if "[sif] bind" in l:
        print(i, l[:120])
print("frames around 150-250:")
for l in lines:
    if l.startswith("[frame]"):
        fn = int(l.split()[1])
        if 100 <= fn <= 250:
            print(l)
print("END:")
for l in lines[-40:]:
    if l.startswith("[thread]") or l.startswith("[sema]") or "reboot" in l or "soft" in l:
        print(l[:160])

print("\n==== CNK mouse/kbd ====")
text = load("logs/cnk-ig3.log")
for l in text.splitlines():
    if any(k in l for k in ("12112", "12113", "12114", "12115", "IGU", "igfileio", "method", "timed out", "ASSETS", "prims")):
        print(l[:160])
