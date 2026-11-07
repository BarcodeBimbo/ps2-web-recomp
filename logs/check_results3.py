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


for name in ["logs/nfs-mw-dst0.log", "logs/cnk-ig3.log"]:
    text = load(name)
    lines = text.splitlines()
    print("====", name, "lines", len(lines))
    print("prims", re.findall(r"(\d+) primitives drawn", text))
    print("stopped", re.findall(r"stopped after (\d+) frames", text))
    print("reboots", [l for l in lines if "IOP reboot" in l or "soft reset" in l])
    if "nfs" in name:
        idx = text.find('IOP reboot requested with ""')
        after = text[idx:] if idx >= 0 else ""
        print("empty", idx >= 0, "calls after", after.count("call server"), "binds after", after.count("[sif] bind"))
        print("sample calls after:")
        for l in after.splitlines():
            if "call server" in l or "[sif] bind" in l:
                print(" ", l[:140])
                break
        # count all call servers
        print("total calls", text.count("call server"), "total binds", text.count("[sif] bind"))
    if "cnk" in name:
        for l in lines:
            if any(k in l for k in ("IGFILEIO", "igfileio", "12114", "ASSETS", "cannot read", "HLE stub", "timed out")):
                print(" ", l[:160])
    print("END threads:")
    for l in lines[-20:]:
        if l.startswith("[thread]") or l.startswith("[sema]") or "primitives" in l:
            print(" ", l[:140])
