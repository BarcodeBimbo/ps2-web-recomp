from pathlib import Path
# find run wrappers
for p in Path('.').glob('*.ps1'):
    print('ps1', p)
for p in Path('scripts').rglob('*') if Path('scripts').exists() else []:
    if p.suffix in ('.py','.ps1','.cmd','.bat') and any(k in p.read_text(encoding='utf-8',errors='replace').lower() for k in ['ps2run','frames','b49f']):
        print(p)
for p in Path('tools').rglob('*.py') if Path('tools').exists() else []:
    t=p.read_text(encoding='utf-8',errors='replace')
    if 'ps2run' in t:
        print('tools', p)
