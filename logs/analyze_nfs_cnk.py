# -*- coding: utf-8 -*-
from pathlib import Path

def load(p):
    raw = Path(p).read_bytes()
    if raw[:2] == b"\xff\xfe":
        return raw.decode("utf-16")
    return raw.decode("utf-8", errors="replace")

for name in ["logs/nfs-mw-softreset3.log", "logs/cnk-baseline.log"]:
    text = load(name)
    lines = text.splitlines()
    print("====", name, "lines", len(lines))
    if "nfs" in name:
        idx = next(i for i, l in enumerate(lines) if 'IOP reboot requested with ""' in l)
        print("empty reboot at line", idx)
        after = lines[idx:]
        print("call server after?", any("call server" in l for l in after))
        print("bind after?", any("[sif] bind" in l for l in after))
        for l in lines[-60:]:
            if l.startswith("[thread]") or l.startswith("[sema]") or "WaitSema" in l or "prims" in l:
                print(l)
    else:
        ai = next(i for i, l in enumerate(lines) if "ASSETS.GOB" in l)
        sectors = []
        for l in lines[ai:]:
            if "call server 0x80000595 fn 1" in l and "args" in l:
                parts = l.split("args")[-1].split()
                if parts:
                    sectors.append(int(parts[0], 16))
        print("gob reads", len(sectors), "first", hex(sectors[0]) if sectors else None, "last", hex(sectors[-1]) if sectors else None)
        if sectors:
            print("unique sectors", len(set(sectors)), "min", hex(min(sectors)), "max", hex(max(sectors)))
        for l in lines[-40:]:
            if l.startswith("[thread]") or l.startswith("[sema]") or "prims" in l:
                print(l)
