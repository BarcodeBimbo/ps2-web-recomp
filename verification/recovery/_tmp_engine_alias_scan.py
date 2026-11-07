import re

games = {
    "Hitman": r"c:\PS2Recomp\games\a2116d2ac08a7be4db4e8455ad58d2e5\disc\boot.elf",
    "NFS": r"c:\PS2Recomp\games\60c82f4a111da300ac23bbec85272788\disc\boot.elf",
    "CNK": r"c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf",
}
needles = [
    b"Intrinsic Alchemy",
    b"ALCHEMY",
    b"Alchemy",
    b"alchemy",
    b"igFileIO",
    b"igIGB",
    b"igObject",
    b"Velocity",
    b"Glacier",
    b"EAGL",
    b"RenderWare",
    b"Renderware",
    b"rwcore",
    b"Criterion",
    b"iaAlchemy",
    b"Alchemy3D",
    b"Alchemy3",
    b"Vicarious",
    b"Intrinsic",
    b"sgFinalizer",
    b"Insight",
    b"IG_ROOT",
    b"igPsx2",
    b"Fast IGB",
    b".igb",
    b"STBL",
    b"ASSETS.GOB",
    b"Speed",
]
for name, path in games.items():
    data = open(path, "rb").read()
    print("====", name, "====")
    for n in needles:
        c = data.count(n)
        if c:
            print(" ", n.decode(errors="replace"), c)
    print("  -- Velocity contexts --")
    for m in re.finditer(rb".{0,24}Velocity.{0,48}", data):
        s = m.group().decode("latin1", "replace").replace("\n", " ")
        print("  ", s[:110])
    print("  -- EAGL contexts --")
    for m in list(re.finditer(rb".{0,24}EAGL.{0,48}", data))[:8]:
        print("  ", m.group().decode("latin1", "replace").replace("\n", " ")[:110])
    print("  -- Glacier contexts --")
    for m in list(re.finditer(rb".{0,24}Glacier.{0,48}", data))[:8]:
        print("  ", m.group().decode("latin1", "replace").replace("\n", " ")[:110])
    print("  -- Alchemy/Intrinsic contexts --")
    for pat in [rb".{0,20}Alchemy.{0,60}", rb".{0,20}Intrinsic.{0,60}", rb".{0,20}iaAlchemy.{0,40}", rb".{0,20}Alchemy3D.{0,40}"]:
        for m in list(re.finditer(pat, data))[:6]:
            print("  ", m.group().decode("latin1", "replace").replace("\n", " ")[:120])
