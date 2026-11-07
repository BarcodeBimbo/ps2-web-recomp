import json, re
from pathlib import Path

paths = [
    Path(r"C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts\d3042714-c511-48f1-b984-a244e305ecb0\d3042714-c511-48f1-b984-a244e305ecb0.jsonl"),
    Path(r"C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts\1afe3ac8-48f0-4c8e-996a-1adbd28b1315\1afe3ac8-48f0-4c8e-996a-1adbd28b1315.jsonl"),
]
# Also scan agent store notes
store = Path(r"C:\Users\joshy\AppData\Local\Cursor\AgentStores\cursor_agent_stores\6a53ee0b-7ff6-4557-b922-2741a43ad132\files")
pat = re.compile(
    r"WaitSema\(47\)|SignalSema\(47\)|iSignalSema\(47\)|sema.?47|705C10|Thread.?3|"
    r"0x423690|422D10|drain_deferred|FINISH|705C00|cmake --build|--frames|"
    r"press|6542A0|post-vsync|draw thread",
    re.I,
)

for p in paths:
    print("====", p.parent.name)
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            try:
                o = json.loads(line)
            except Exception:
                continue
            msg = o.get("message", {}).get("content")
            chunks = []
            if isinstance(msg, list):
                for c in msg:
                    if isinstance(c, dict) and c.get("type") == "text":
                        chunks.append(c.get("text", ""))
                    # also mine shell command outputs? skip
            text = "\n".join(chunks)
            if not pat.search(text):
                continue
            if o.get("role") != "assistant":
                continue
            # Prefer final-ish text messages
            if "Changed files" in text or "Gate status" in text or "WaitSema(47)" in text or "705C10" in text:
                print(f"--- L{i} ---")
                print(text[:3500])
                print()
            elif "cmake --build" in text or "--frames" in text:
                # extract rebuild cmds
                for m in re.finditer(r".{0,40}cmake --build.{0,120}", text):
                    print(f"L{i} CMD:", m.group(0).replace("\n", " "))
                for m in re.finditer(r".{0,40}ps2run\.exe.{0,200}", text):
                    print(f"L{i} RUN:", m.group(0).replace("\n", " ")[:240])

print("==== store files ====")
if store.exists():
    for f in sorted(store.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:40]:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if pat.search(t) or "CNK" in t or "WaitSema" in t:
            print(f.name, f.stat().st_size)
            for m in pat.finditer(t):
                s = max(0, m.start() - 100)
                e = min(len(t), m.end() + 160)
                print(" ", t[s:e].replace("\n", " ")[:280])
