# Extract more of the VVAA cmd1 call from cnk-ig11 - maybe args continue on next lines
from pathlib import Path
lines=Path('logs/cnk-ig11.log').read_text(encoding='utf-8',errors='replace').splitlines()
for i,l in enumerate(lines):
    if '0x73696964 fn 0 send 188' in l:
        for j in range(i, min(i+15,len(lines))):
            print(f'{j+1}:{lines[j]}')
        break
print('==== looking at sif call logging format ====')
for i,l in enumerate(lines):
    if 'call server 0x00012114' in l or 'call server 0x12114' in l:
        for j in range(i, min(i+10,len(lines))):
            print(f'{j+1}:{lines[j]}')
        break
