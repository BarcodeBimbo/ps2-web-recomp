#!/usr/bin/env python3
"""Analyze CNK live RAM dump for asset/draw gate blockers."""
from pathlib import Path
import struct

ram = Path(r"C:\PS2Recomp\logs\cnk-live.ram").read_bytes()
EE = ram[:0x2000000]
IOP = ram[0x2000000:0x2000000 + 0x200000]
print("sizes", len(ram), len(EE), len(IOP))

def u32(a, mem=EE):
    return struct.unpack_from("<I", mem, a)[0]

def u64(a, mem=EE):
    return struct.unpack_from("<Q", mem, a)[0]

def dump(a, n=8, mem=EE, label=""):
    words = [u32(a + i * 4, mem) for i in range(n)]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in mem[a : a + n * 4])
    print(f"{label}{a:08X}: " + " ".join(f"{w:08X}" for w in words) + f" |{asc}|")

addrs = [
    (0x702BA0, "skip"),
    (0x705BE0, "ready_be0"),
    (0x705BF0, "flag_bf0"),
    (0x705C00, "ctr_5c00"),
    (0x705C10, "sema47_id"),
    (0x705C18, "sema45_id"),
    (0x705C20, "finish_ctr"),
    (0x705DF8, "tim_df8"),
    (0x705F10, "tim_f10"),
    (0x654290, "finish_flag"),
    (0x6542A0, "tgt_42a0"),
    (0x6542D8, "off_42d8"),
    (0x7430C0, "igfile_ctx"),
    (0x7504C0, "gfc_buf"),
    (0x782800, "gob_buf"),
]
for a, lab in addrs:
    dump(a, 8, label=lab + " ")

be0 = u32(0x705BE0)
print("follow 705BE0 ->", hex(be0))
if be0 < len(EE):
    dump(be0, 16, label="*be0 ")

# GFC signature?
sig = EE[0x7504C0:0x7504C0+16]
print("GFC head", sig[:16].hex(), sig[:8])
if len(sig) >= 16:
    print(" be32s", [struct.unpack(">I", sig[i:i+4])[0] for i in range(0,16,4)])

# Search for ASSETS / MUSIC / .TGA strings in EE RAM
for s in [b"ASSETS", b"MUSIC", b"LEGENG", b"TITLE", b"igFile", b"FileIO", b"siid", b".GFC", b".GOB", b"POOLS"]:
    hits = []
    start = 0
    while len(hits) < 8:
        i = EE.find(s, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    print(s, [hex(h) for h in hits], [EE[h:h+32] for h in hits[:3]])

# Check igfile ctx structure - dump more
print("\n=== igfile ctx region ===")
dump(0x7430C0, 32)
# look for function pointers in ctx (code range)
ctx = EE[0x7430C0:0x7430C0+0x200]
ptrs = []
for i in range(0, len(ctx), 4):
    w = struct.unpack_from("<I", ctx, i)[0]
    if 0x00100000 <= w < 0x00620000 and (w & 3) == 0:
        ptrs.append((0x7430C0 + i, w))
print("code ptrs in ctx", [(hex(a), hex(v)) for a, v in ptrs[:40]])

# SIID client buffer area from logs ~0x155F100
print("\n=== SIID EE buffers ===")
for a in (0x155F100, 0x155F140, 0x70D090, 0x70D140, 0x1856B58):
    if a < len(EE):
        dump(a, 12, label="siid ")

# Look at IOP VVAA module data around stream status (base 0xB9400)
print("\n=== IOP VVAA region ===")
for a in (0xB9400, 0xB97C4, 0xBEBC0, 0xBF000, 0xBA31C):
    dump(a, 8, mem=IOP, label="iop ")

# Search IOP for 0x500C status words
hits = []
for a in range(0, len(IOP) - 4, 4):
    if struct.unpack_from("<I", IOP, a)[0] == 0x500C:
        hits.append(a)
print("IOP 0x500C hits", len(hits), [hex(h) for h in hits[:20]])

# Count non-zero / non-EE in GFC buffer
gfc = EE[0x7504C0:0x7504C0 + 0x40000]
nonzero = sum(1 for b in gfc if b not in (0, 0xEE))
print("GFC buffer nonzero bytes", nonzero, "of", len(gfc))
print("GFC unique sample", gfc[:64].hex())

gob = EE[0x782800:0x782800 + 0x8000]
print("GOB buffer nonzero", sum(1 for b in gob if b not in (0, 0xEE)), gob[:64].hex())

# Disassemble around 0x423500-0x423700 for SignalSema path (from prior notes)
print("\n=== code near 0x4235C0 ===")
for a in range(0x423500, 0x423700, 4):
    w = u32(a)
    # print only calls / interesting
    op = (w >> 26) & 0x3F
    if op == 3 or (op == 0 and (w & 0x3F) in (8, 9, 0xC)):
        print(f"{a:08X}: {w:08X}")
