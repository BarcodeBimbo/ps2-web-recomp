from pathlib import Path
# inspect EE code around RA 0x423004 in explore_ram if it looks like EE RAM dump
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
print('ram size', len(ram))
# disassemble a few words at 0x423000
import struct
for addr in range(0x422fe0, 0x423040, 4):
    w=struct.unpack_from('<I', ram, addr)[0]
    print(f'{addr:08X}: {w:08X}')
print('--- stack frames strings near 0x00108EC0 ---')
for addr in [0x00108EC0,0x00108EE0,0x001090AC,0x0010999C,0x0010A044,0x00118FE0,0x001AFB2C]:
    # look at function prologues backwards? print nearby as words
    print(hex(addr), ram[addr:addr+16].hex())
