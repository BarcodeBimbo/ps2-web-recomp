from pathlib import Path
from collections import Counter

lines = Path("logs/sly-cap1800/draws.tsv").read_text().strip().splitlines()
print("lines", len(lines))
psm_c = Counter()
cpsm_c = Counter()
tcc_c = Counter()
tfx_c = Counter()
ate_c = Counter()
atst_c = Counter()
wms_c = Counter()
mmag_c = Counter()
big = []
psm_names = {
    0x00: "CT32",
    0x01: "CT24",
    0x02: "CT16",
    0x0A: "CT16S",
    0x13: "T8",
    0x14: "T4",
    0x1B: "T8H",
    0x24: "T4HL",
    0x2C: "T4HH",
}
for line in lines[1:]:
    if not line or line.startswith(("vblank", "image", "transfer")):
        continue
    f = line.split("\t")
    if len(f) < 12:
        continue
    try:
        tex0 = int(f[7], 16)
        test = int(f[11], 16)
        clamp = int(f[9], 16)
        tex1 = int(f[8], 16)
        prims = int(f[1])
    except ValueError:
        continue
    psm = (tex0 >> 20) & 0x3F
    cp = (tex0 >> 51) & 0xF
    tcc = (tex0 >> 34) & 1
    tfx = (tex0 >> 35) & 3
    ate = test & 1
    atst = (test >> 1) & 7
    aref = (test >> 4) & 0xFF
    afail = (test >> 12) & 3
    wms = clamp & 3
    wmt = (clamp >> 2) & 3
    mmag = (tex1 >> 5) & 1
    psm_c[psm] += prims
    cpsm_c[cp] += prims
    tcc_c[tcc] += prims
    tfx_c[tfx] += prims
    ate_c[ate] += prims
    atst_c[(ate, atst, aref, afail)] += prims
    wms_c[(wms, wmt)] += prims
    mmag_c[mmag] += prims
    if prims > 40:
        big.append((prims, psm_names.get(psm, hex(psm)), cp, tcc, tfx, ate, atst, aref, afail, wms, wmt, mmag, f[12] if len(f) > 12 else "", f[13] if len(f) > 13 else ""))

print("psm", [(psm_names.get(k, hex(k)), v) for k, v in psm_c.most_common(10)])
print("cpsm", cpsm_c.most_common(8))
print("tcc", dict(tcc_c))
print("tfx", dict(tfx_c))
print("ate", dict(ate_c))
print("mmag", dict(mmag_c))
print("wrap", wms_c.most_common(8))
print("atst top", atst_c.most_common(12))
print("biggest draws:")
for b in sorted(big, reverse=True)[:20]:
    print(b)
