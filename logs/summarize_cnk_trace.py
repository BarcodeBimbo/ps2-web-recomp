from collections import Counter
from pathlib import Path

path = Path(r"games/b49f2e769315347e8bda839feb705744/trace_sys.txt")
if not path.exists():
    # also try explore-style merged log
    print("missing", path)
    raise SystemExit(1)
lines = path.read_text(errors="ignore").splitlines()
print("lines", len(lines))
for pat in [
    "WaitSema",
    "SignalSema",
    "unhandled",
    "cannot read",
    "missing",
    "halted",
    "primitives",
    "SetGsCrt",
    "CreateSema",
]:
    hits = [l for l in lines if pat in l]
    print(pat, len(hits))
    for l in hits[-8:]:
        print(" ", l[:180])
syscalls = Counter()
for l in lines:
    if "[sys]" in l:
        parts = l.split()
        # find token with (
        token = next((p for p in parts if "(" in p), parts[1] if len(parts) > 1 else "?")
        syscalls[token] += 1
print("top syscalls")
for k, v in syscalls.most_common(30):
    print(f"  {v:5d} {k}")
