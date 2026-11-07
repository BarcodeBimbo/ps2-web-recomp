import json, re
from pathlib import Path

root = Path(r"C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts")
pat = re.compile(r"SIID|siid|0x1211|igfileio|PRIM|prims|Alchemy|draw gate|PATH1|asset|0x12114", re.I)

for d in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
    f = next(d.glob("*.jsonl"), None)
    if not f:
        continue
    print("====", d.name)
    hits = 0
    with open(f, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if not pat.search(line):
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            role = o.get("role")
            msg = o.get("message", {}).get("content")
            texts = []
            if isinstance(msg, list):
                for c in msg:
                    if isinstance(c, dict) and c.get("type") == "text":
                        texts.append(c.get("text", "")[:3000])
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        inp = c.get("input") or {}
                        for k in ("command", "final_summary", "current_step", "query"):
                            v = inp.get(k)
                            if isinstance(v, str) and pat.search(v):
                                texts.append(f"[{c.get('name')} {k}] " + v[:1000])
            text = "\n".join(texts)
            if not text or not pat.search(text):
                continue
            hits += 1
            if hits <= 10:
                print(f"-- L{i} {role} --")
                for m in pat.finditer(text):
                    s = max(0, m.start() - 100)
                    e = min(len(text), m.end() + 160)
                    print(text[s:e].replace("\n", " ")[:300])
                    print("---")
    print("hits", hits)
