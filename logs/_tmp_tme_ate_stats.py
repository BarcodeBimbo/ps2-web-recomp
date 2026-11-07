from pathlib import Path
from collections import Counter

# Prefer post-16bit capture if rich enough, else post-xyoffset
for cap in [
    Path(r"c:\PS2Recomp\logs\hitman-capture-xyoffset16-20261107\draws.tsv"),
    Path(r"c:\PS2Recomp\logs\hitman-capture-post-xyoffset-2026-11-07\draws.tsv"),
]:
    if not cap.is_file():
        continue
    lines = [l for l in cap.read_text(errors="replace").splitlines()[2:] if l and not l[0].isalpha()]
    print("===", cap.parent.name, "batches", len(lines))
    tme = ate = abe = 0
    prim_types = Counter()
    tme_ate = 0
    for line in lines:
        cols = line.split("\t")
        if len(cols) < 12:
            continue
        prim = int(cols[4], 16)
        test = int(cols[11], 16)
        prim_types[prim & 7] += 1
        if prim & 0x10:
            tme += 1
        if prim & 0x40:
            abe += 1
        if test & 1:
            ate += 1
        if (prim & 0x10) and (test & 1):
            tme_ate += 1
    print("prim_types", dict(prim_types))
    print("tme", tme, "abe", abe, "ate", ate, "tme+ate", tme_ate)
