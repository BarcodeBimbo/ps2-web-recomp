#!/usr/bin/env python3
import json, re
from pathlib import Path

for name in [
    "1afe3ac8-48f0-4c8e-996a-1adbd28b1315",
    "d3042714-c511-48f1-b984-a244e305ecb0",
]:
    p = Path(rf"C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts\{name}\{name}.jsonl")
    if not p.exists():
        continue
    print("====", name)
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if "forced ready" not in line and "0x500C" not in line and "siid cmd4" not in line:
                if "STBLz" not in line and "inflate" not in line.lower():
                    continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            msg = o.get("message", {}).get("content")
            if not isinstance(msg, list):
                continue
            for c in msg:
                if isinstance(c, dict) and c.get("type") == "text":
                    t = c.get("text", "")
                    if any(k in t for k in ("forced ready", "500C", "STBLz", "inflate", "prims")):
                        print(f"L{i} text:", t[:2000])
                        print("---")
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    path = str(inp.get("path", ""))
                    if "sif.cpp" in path or "spu2" in path:
                        print(f"L{i} edit {path}")
                        ns = inp.get("new_string") or inp.get("contents") or ""
                        if "siid" in ns.lower() or "500C" in ns or "STBL" in ns:
                            print(ns[:1500])
                            print("---")
