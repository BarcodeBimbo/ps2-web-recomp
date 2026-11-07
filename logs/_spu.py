from pathlib import Path
# find sceSd export stubs / SPU2 guest libsd - LIBSD is real IRX so GetParam is guest code reading SPU2 regs
# Check what SPU2 register read returns for voice params
t=Path('runtime/src/iop/spu2.cpp').read_text(encoding='utf-8')
for i,l in enumerate(t.splitlines(),1):
    if i<80 or 'read' in l.lower() and ('reg' in l.lower() or 'voice' in l.lower() or 'param' in l.lower()) or 'case 0x' in l:
        if i<100 or 'case' in l or 'return' in l:
            pass
# print voice register read path
for i,l in enumerate(t.splitlines(),1):
    if 'voice' in l.lower() or 'PARAM' in l or 'get_reg' in l or 'read16' in l or '0x1F90' in l:
        print(f'{i}:{l.rstrip()[:150]}')
        if i>200: break
