# -*- coding: utf-8 -*-
p = r"games/b49f2e769315347e8bda839feb705744/disc/boot.elf"
data = open(p, "rb").read()
i = data.find(b"igFileIO.irx")
print("igFileIO at", hex(i))
print(data[i : i + 256])
for s in [
    b"failed to load",
    b"LoadModule",
    b"igFileIO",
    b"cannot open",
    b"STBL",
    b"error creating",
    b"SifBindRpc",
]:
    idx = 0
    n = 0
    while n < 3:
        j = data.find(s, idx)
        if j < 0:
            break
        print(hex(j), s, data[max(0, j - 16) : j + 48])
        idx = j + 1
        n += 1
