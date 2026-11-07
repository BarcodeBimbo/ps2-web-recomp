from pathlib import Path
# find option parsing for frames/disc
for p in Path('runtime/src').glob('*.cpp'):
    t=p.read_text(encoding='utf-8',errors='replace')
    if '--frames' in t or 'trace_iop' in t:
        print(p)
        for i,l in enumerate(t.splitlines(),1):
            if '--frames' in l or 'trace_iop' in l or 'g_options' in l and 'frames' in l:
                print(f'  {i}:{l.strip()[:140]}')
