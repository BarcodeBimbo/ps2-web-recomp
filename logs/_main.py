from pathlib import Path
for p in list(Path('.').glob('**/main.cpp'))+list(Path('.').glob('**/ps2run*.cpp'))+list(Path('native').glob('**/*') if Path('native').exists() else []):
    if p.is_file() and p.suffix=='.cpp':
        print(p)
# search for max_frames assignment
for p in Path('.').rglob('*.cpp'):
    try:
        t=p.read_text(encoding='utf-8',errors='replace')
    except Exception:
        continue
    if 'max_frames' in t and ('argv' in t or '--frames' in t or 'argparse' in t or 'strcmp' in t):
        print('HIT', p)
        for i,l in enumerate(t.splitlines(),1):
            if 'frames' in l.lower() and ('--' in l or 'max_frames' in l or 'opt' in l):
                print(f'  {i}:{l.strip()[:160]}')
