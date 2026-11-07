# -*- coding: utf-8 -*-
from pathlib import Path
import re


def load(p):
    raw = Path(p).read_bytes()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16")
    # utf-8 with BOM possible
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8", errors="replace")


for name in ["logs/nfs-mw-sif0hold.log", "logs/cnk-igfileio-hle.log"]:
    text = load(name)
    lines = text.splitlines()
    print("====", name, "lines", len(lines))
    prims = re.findall(r"\[gs\].*?(\d+) primitives", text)
    frame_prims = re.findall(r"\[frame\] (\d+) prims (\d+)", text)
    print("gs prims totals", prims[-3:] if prims else None)
    if frame_prims:
        nonzero = [(f, p) for f, p in frame_prims if int(p) > 0]
        print("last frames", frame_prims[-5:], "nonzero count", len(nonzero), "max prims", max(int(p) for _, p in frame_prims))
    for key in [
        "soft reset",
        "sif0 held",
        "IOP reboot",
        "IGFILEIO",
        "IGUMOUSE",
        "IGUKBD",
        "cannot read module",
        "call server",
        "bind ",
        "WaitSema",
        "frame limit",
        "halted",
    ]:
        hits = [l for l in lines if key in l]
        print(f"  {key}: {len(hits)}")
        for l in hits[:3]:
            print("   ", l[:140])
        if len(hits) > 3:
            print("   ...", hits[-1][:140])
    # post empty reboot activity for nfs
    if "nfs" in name:
        try:
            idx = next(i for i, l in enumerate(lines) if 'IOP reboot requested with ""' in l)
        except StopIteration:
            print("no empty reboot")
            continue
        after = lines[idx:]
        calls = [l for l in after if "call server" in l]
        binds = [l for l in after if "[sif] bind" in l]
        cmd1 = [l for l in after if "command 0x00000001" in l]
        print(f"  after empty: calls={len(calls)} binds={len(binds)} cmd1={len(cmd1)}")
        for l in calls[:8]:
            print("   ", l[:140])
        for l in binds[:8]:
            print("   ", l[:140])
        for l in lines[-35:]:
            if l.startswith("[thread]") or l.startswith("[sema]") or "primitives" in l or "prims" in l:
                print("   END", l[:140])
    if "cnk" in name:
        for l in lines[-40:]:
            if l.startswith("[thread]") or l.startswith("[sema]") or "primitives" in l or "IGFILE" in l or "module" in l:
                print("   END", l[:140])
