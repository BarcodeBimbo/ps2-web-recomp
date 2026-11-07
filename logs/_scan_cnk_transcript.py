import json
from pathlib import Path

p = Path(r"C:/Users/joshy/.cursor/projects/c-PS2Recomp/agent-transcripts/1afe3ac8-48f0-4c8e-996a-1adbd28b1315")
keys = ("WaitSema", "iSignal", "4235", "VVAA", "MUSIC", "timrman", "prims", "usec", "gate", "SIID", "siid", "SignalSema")
for f in p.rglob("*.jsonl"):
    for i, line in enumerate(open(f, encoding="utf-8", errors="replace")):
        try:
            o = json.loads(line)
        except Exception:
            continue
        msg = o.get("message", {})
        role = o.get("role")
        content = msg.get("content") if isinstance(msg, dict) else None
        texts = []
        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text":
                    texts.append(c.get("text", ""))
                elif c.get("type") == "tool_use" and c.get("name") in ("Write", "StrReplace"):
                    inp = c.get("input", {})
                    texts.append(f"TOOL {c['name']} path={inp.get('path', '')}")
                    if "old_string" in inp:
                        texts.append(inp.get("old_string", "")[:200])
                    if "new_string" in inp:
                        texts.append(inp.get("new_string", "")[:400])
                    if "contents" in inp:
                        texts.append(inp.get("contents", "")[:400])
        elif isinstance(content, str):
            texts.append(content)
        t = "\n".join(texts)
        if any(k in t for k in keys):
            snippet = " ".join(t.split())[:700]
            print(f"--- {f.name}:{i} {role} ---")
            print(snippet)
            print()
