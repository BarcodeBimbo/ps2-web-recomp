import json, re
from pathlib import Path

p = Path(
    r"C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts"
    r"\d3042714-c511-48f1-b984-a244e305ecb0\d3042714-c511-48f1-b984-a244e305ecb0.jsonl"
)

# Pull assistant text around lines that mention 47 / FINISH / 705C10 / 423690
want = re.compile(
    r"iSignalSema\(47\)|0000002F|705C10|423690|FINISH|thread.?3|post-vsync|"
    r"drain_deferred|write\(0x61\)|422D10|hypothesis|one behind|6542A0",
    re.I,
)

with open(p, encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        if i not in range(100, 148) and i not in (27, 35, 67, 107, 109, 110, 142, 143, 147):
            # also scan any with key terms
            if "47" not in line and "705C10" not in line and "423690" not in line and "FINISH" not in line:
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
                    texts.append(c.get("text", ""))
                # capture shell command strings that mention 47
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    cmd = inp.get("command") or inp.get("final_summary") or ""
                    if isinstance(cmd, str) and want.search(cmd):
                        texts.append(f"[tool {c.get('name')}] {cmd[:1500]}")
                    fs = inp.get("final_summary")
                    if fs:
                        texts.append(f"[final_summary] {fs}")
        text = "\n".join(texts)
        if not text or not want.search(text):
            continue
        print(f"===== L{i} {role} =====")
        print(text[:4000])
        print()

# Also check if disasm scripts or FIX_REPORT have 47
for path in [
    Path(r"C:\PS2Recomp\FIX_REPORT.md"),
    Path(r"C:\PS2Recomp\UPDATE_NOTES.md"),
]:
    if not path.exists():
        continue
    t = path.read_text(encoding="utf-8", errors="replace")
    if "CNK" in t or "WaitSema" in t or "705C" in t:
        print("====", path.name)
        for m in re.finditer(r".{0,80}(WaitSema|705C|sema 4|FINISH|Timrman|VVAA).{0,120}", t, re.I):
            print(m.group(0).replace("\n", " ")[:220])
            print("---")
