from pathlib import Path
import hashlib

def h(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]

base = Path("games/c0c4527037b6168660829a0eb13df1a3/shots")
gp = Path("logs/sly-gameplay")
qf = Path("logs/sly-gameplay-qfix")
for f in range(300, 3900, 300):
    name = f"frame_{f:05d}.ppm"
    parts = []
    for label, root in [("ex", base), ("gp", gp), ("qf", qf)]:
        p = root / name
        parts.append(f"{label}={h(p) if p.exists() else '-'}")
    print(f"{f}: {' '.join(parts)}")
print("cycles old", 8848466619, "new", 8848466112, "delta", 8848466619 - 8848466112)
print("prims old", 4061228, "new", 2126927)
