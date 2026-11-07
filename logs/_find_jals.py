from pathlib import Path
import struct

p = Path(r"C:\PS2Recomp\logs\vvaa.irx").read_bytes()
BASE = 0xB9400
load_ofs = 0xB0
targets = {
    0x22D0: "SystemOpen",
    0x22FC: "Precache",
    0x223C: "SysClose",
    0x2738: "FileRead",
    0x2640: "FileClose",
    0x2650: "FileSeek",
    0x2848: "FileOpen",
}
for off in range(load_ofs, load_ofs + 0x2800, 4):
    w = struct.unpack_from("<I", p, off)[0]
    op = (w >> 26) & 0x3F
    if op != 3:
        continue
    rel = (w & 0x3FFFFFF) << 2
    if rel in targets or (0x22C0 <= rel <= 0x2900):
        addr = BASE + off - load_ofs
        print(f"{addr:08X}: jal {rel:#x} {targets.get(rel, '')}")
