import re
from pathlib import Path
for path in Path('runtime/src/iop').glob('*.cpp'):
    text = path.read_text(encoding='utf-8', errors='replace').splitlines()
    for i,l in enumerate(text,1):
        if re.search(r'timr|HardTimer|SetTimer|AllocHard|StartHard|register_hle_library', l, re.I):
            print(f'{path.name}:{i}:{l.strip()}')
