"""Reject malicious ELF segments and symbol tables before memory access."""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

parser=argparse.ArgumentParser()
parser.add_argument('--recompiler',type=Path,required=True)
args=parser.parse_args()

def base():
    data=bytearray(0x300)
    data[:7]=b'\x7fELF\x01\x01\x01'
    struct.pack_into('<HHIIIIIHHHHHH',data,16,2,8,1,0x100000,52,0,0,52,32,1,40,0,0)
    struct.pack_into('<8I',data,52,1,0x100,0x100000,0,8,16,5,4)
    struct.pack_into('<2I',data,0x100,0x03e00008,0)
    return data

cases=[]
for label,offset,value in [('filesz exceeds memsz',68,100),('offset wrap',56,0xfffffffc),('unbounded memsz',72,0xffffffff),('bad phoff',28,0xfffffff0)]:
    data=base();struct.pack_into('<I',data,offset,value);cases.append((label,data))
data=base();struct.pack_into('<H',data,42,8);cases.append(('short program header',data))
for name,stroff,strsize,symname,termination in [('bad string offset',0xfffffffc,16,0,True),('bad symbol name',0x280,8,16,True),('unterminated name',0x280,8,0,False)]:
    data=base();struct.pack_into('<I',data,32,0x180);struct.pack_into('<HHH',data,46,40,3,0)
    struct.pack_into('<10I',data,0x180+40,0,2,0,0,0x260,16,2,0,4,16)
    struct.pack_into('<10I',data,0x180+80,0,3,0,0,stroff,strsize,0,0,1,0)
    struct.pack_into('<IIIBBH',data,0x260,symname,0x100000,0,2,0,1)
    if not termination:data[0x280:0x288]=b'xxxxxxxx'
    cases.append((name,data))
with tempfile.TemporaryDirectory() as folder:
    work=Path(folder)
    for name,data in cases:
        source=work/'input.elf';source.write_bytes(data)
        run=subprocess.run([str(args.recompiler.resolve()),str(source),'--out',str(work/'generated')],capture_output=True,text=True,timeout=10)
        assert run.returncode != 0,(name,'accepted malformed ELF')
        assert run.returncode > 0 and 'AddressSanitizer' not in run.stderr and 'runtime error:' not in run.stderr,(name,run.stderr)
print(f'PASS: {len(cases)} malformed ELF bounds and string fixtures')
