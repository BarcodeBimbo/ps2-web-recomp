from pathlib import Path
from collections import Counter

p = Path(r"c:\PS2Recomp\logs\frames\sly-cap1800\draws.tsv")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
print("lines", len(lines))


def area(box: str):
    try:
        # boxes can be negative: "-1157.1,-523.1-1797.1,1360.3"
        import re

        m = re.match(
            r"^\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*$",
            box,
        )
        if not m:
            return 0.0, None
        x0, y0, x1, y1 = map(float, m.groups())
        return max(0.0, (x1 - x0)) * max(0.0, (y1 - y0)), (x0, y0, x1, y1)
    except Exception:
        return 0.0, None


draws = []
transfers = []
for ln in lines[1:]:
    if ln.startswith("vblank") or ln.startswith("image"):
        continue
    if ln.startswith("transfer"):
        transfers.append(ln)
        continue
    parts = ln.split("\t")
    if parts and parts[0] == "draw":
        parts = parts[1:]
    # capture flush format: [idx] prims first ctx prim frame zbuf tex0 tex1 clamp alpha test box texels
    if len(parts) >= 13 and parts[4] in ("07C", "07c", "316", "246", "006", "001", "0C1"):
        # idx present
        pass
    if len(parts) < 12:
        continue
    # Detect whether column0 is a draw index (decimal) vs prims by checking prim hex field position.
    try:
        if len(parts) >= 13 and all(c in "0123456789ABCDEFabcdef" for c in parts[4]) and len(parts[4]) <= 3:
            # idx, prims, first, ctx, prim, ...
            base = 1
        else:
            base = 0
        prims = int(parts[base + 0])
        first = int(parts[base + 1])
        ctx = int(parts[base + 2])
        prim = int(parts[base + 3], 16)
        frame = int(parts[base + 4], 16)
        zbuf = int(parts[base + 5], 16)
        tex0 = int(parts[base + 6], 16)
        tex1 = int(parts[base + 7], 16)
        clamp = int(parts[base + 8], 16)
        alpha = int(parts[base + 9], 16)
        test = int(parts[base + 10], 16)
        box = parts[base + 11]
        texels = parts[base + 12] if len(parts) > base + 12 else ""
    except Exception as e:
        print("parse fail", e, parts[:8])
        continue
    ar, bb = area(box)
    tbp = tex0 & 0x3FFF
    psm = (tex0 >> 20) & 0x3F
    tw = (tex0 >> 26) & 0xF
    th = (tex0 >> 30) & 0xF
    tcc = (tex0 >> 34) & 1
    tfx = (tex0 >> 35) & 3
    cbp = (tex0 >> 37) & 0x3FFF
    csm = (tex0 >> 55) & 1
    cld = (tex0 >> 61) & 7
    tme = (prim >> 4) & 1
    fge = (prim >> 5) & 1
    abe = (prim >> 6) & 1
    fst = (prim >> 8) & 1
    kind = prim & 7
    ate = test & 1
    atst = (test >> 1) & 7
    aref = (test >> 4) & 0xFF
    afail = (test >> 12) & 3
    draws.append(
        dict(
            prims=prims,
            first=first,
            ctx=ctx,
            prim=prim,
            kind=kind,
            tme=tme,
            fge=fge,
            abe=abe,
            fst=fst,
            area=ar,
            box=bb,
            tbp=tbp,
            psm=psm,
            tw=tw,
            th=th,
            tcc=tcc,
            tfx=tfx,
            cbp=cbp,
            csm=csm,
            cld=cld,
            alpha=alpha,
            test=test,
            ate=ate,
            atst=atst,
            aref=aref,
            afail=afail,
            tex0=tex0,
            frame=frame,
            zbuf=zbuf,
            tex1=tex1,
            clamp=clamp,
            texels=texels,
        )
    )

print("draws", len(draws), "transfers", len(transfers))
tex = [d for d in draws if d["tme"]]
print("textured", len(tex), "fst0", sum(1 for d in tex if d["fst"] == 0), "fst1", sum(1 for d in tex if d["fst"] == 1))
tex_sorted = sorted(tex, key=lambda d: -d["area"])
print("TOP textured by area:")
for d in tex_sorted[:20]:
    print(
        f"  area={d['area']:.0f} prims={d['prims']} prim={d['prim']:03X} kind={d['kind']} "
        f"FST={d['fst']} FGE={d['fge']} ABE={d['abe']} PSM={d['psm']:02X} "
        f"TBP={d['tbp']:04X} CBP={d['cbp']:04X} CLD={d['cld']} CSM={d['csm']} "
        f"TFX={d['tfx']} TCC={d['tcc']} TW={d['tw']} TH={d['th']} "
        f"alpha={d['alpha']:X} test={d['test']:X} ATST={d['atst']} AFAIL={d['afail']} "
        f"AREF={d['aref']} box={d['box']} texels={d['texels']}"
    )

print("ATST hist", Counter(d["atst"] for d in tex))
print("AFAIL hist", Counter(d["afail"] for d in tex))
print("ABE hist", Counter(d["abe"] for d in tex))
print("FGE hist", Counter(d["fge"] for d in tex))
print("PSM hist", Counter(d["psm"] for d in tex))
print("alpha hist top", Counter(d["alpha"] for d in tex).most_common(8))
print("kind hist", Counter(d["kind"] for d in tex))
big = [d for d in tex if d["area"] >= 10000]
print("area>=10k", len(big), "total area", sum(d["area"] for d in big))
print("big TBP", Counter(d["tbp"] for d in big).most_common(10))
print("big CBP", Counter(d["cbp"] for d in big).most_common(10))
print("big ATST/AFAIL/ABE/FGE", Counter((d["atst"], d["afail"], d["abe"], d["fge"]) for d in big).most_common(10))
print("big alpha", Counter(d["alpha"] for d in big).most_common(8))
print("sample transfers:")
for t in transfers[:20]:
    print(" ", t)

out = Path(r"c:\PS2Recomp\logs\workers\W-SLY-cap1800-parse-2026-11-07.txt")
# rewrite summary to file too
summary = []
summary.append(f"draws={len(draws)} textured={len(tex)} big10k={len(big)}")
summary.append(f"fst0={sum(1 for d in tex if d['fst']==0)} fst1={sum(1 for d in tex if d['fst']==1)}")
summary.append(f"ATST={Counter(d['atst'] for d in tex)}")
summary.append(f"big_keys={Counter((d['atst'],d['afail'],d['abe'],d['fge']) for d in big).most_common(10)}")
out.write_text("\n".join(summary) + "\n", encoding="utf-8")
print("wrote", out)
