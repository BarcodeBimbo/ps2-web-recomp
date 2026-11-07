from pathlib import Path
import os
# read windows_setup for cmake path
for name in ['scripts/windows_setup.py','windows_setup.py','Setup.cmd']:
    p=Path(name)
    if p.exists():
        t=p.read_text(encoding='utf-8',errors='replace')
        print('====', name)
        for i,l in enumerate(t.splitlines(),1):
            if 'cmake' in l.lower() or 'BIN' in l or 'PATH' in l:
                print(f'{i}:{l[:160]}')
