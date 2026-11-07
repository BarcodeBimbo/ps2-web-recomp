from pathlib import Path
import os
# find ELF / SLUS / recompiled sources for CNK
root=Path('.')
hits=[]
for p in root.rglob('*'):
    if not p.is_file(): continue
    n=p.name.lower()
    if 'b49f' in n or n.startswith('slus') or 'cnk' in n and p.suffix in ('.elf','.bin','.o','.cpp','.txt'):
        if p.stat().st_size < 200_000_000:
            hits.append((str(p), p.stat().st_size))
for h in sorted(hits)[:60]:
    print(h)
print('--- entries ---')
print(Path('games/b49f2e769315347e8bda839feb705744/entries.txt').read_text()[:2000])
print('--- how to run ---')
for p in Path('scripts').glob('*.py') if Path('scripts').exists() else []:
    t=p.read_text(encoding='utf-8',errors='replace')
    if 'ps2run' in t or 'b49f' in t:
        print(p)
