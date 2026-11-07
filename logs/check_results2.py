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


for name in ["logs/nfs-mw-subaddr.log", "logs/cnk-igfileio-rpc.log"]:
    text = load(name)
    lines = text.splitlines()
    print("====", name, "lines", len(lines), "bytes", Path(name).stat().st_size)
    print("tail:")
    for l in lines[-25:]:
        print(" ", l[:160])
    prims = re.findall(r"(\d+) primitives drawn", text)
    print("prims", prims)
    frames = re.findall(r"stopped after (\d+) frames", text)
    print("stopped", frames)
    if "nfs" in name:
        idx = text.find('IOP reboot requested with ""')
        after = text[idx:]
        print("empty reboot found", idx >= 0)
        print("calls after", after.count("call server"))
        print("binds after", after.count("[sif] bind"))
        print("80000002 after", after.count("command 0x80000002"))
        print("soft resets", [l for l in lines if "soft reset" in l or "sif0" in l][:8])
    if "cnk" in name:
        print("IGFILEIO lines:")
        for l in lines:
            if "IGFILEIO" in l or "igfileio" in l or "0x00012114" in l or "12114" in l:
                print(" ", l[:160])
        print("ASSETS", [l for l in lines if "ASSETS" in l])
        print("prims frames", re.findall(r"\[frame\] (\d+) prims (\d+)", text)[-8:])
