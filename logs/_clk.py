from pathlib import Path
import re
for path in ['runtime/src/iop/kernel.cpp','runtime/src/iop/kernel.hpp','runtime/include/ps2/clock.hpp']:
    p=Path(path)
    if not p.exists():
        continue
    t=p.read_text(encoding='utf-8')
    for i,l in enumerate(t.splitlines(),1):
        if 'usec_to_cycles' in l or 'kIopClock' in l or '36864' in l or 'IOP' in l and 'Clock' in l:
            print(f'{path}:{i}:{l.strip()}')
