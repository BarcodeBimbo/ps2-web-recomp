from pathlib import Path
# libsd GetSwitch HLE
text=Path('runtime/src/iop/spu2.cpp').read_text(encoding='utf-8',errors='replace') if Path('runtime/src/iop/spu2.cpp').exists() else ''
for p in Path('runtime/src/iop').glob('*.cpp'):
    t=p.read_text(encoding='utf-8',errors='replace')
    if 'sceSdGetSwitch' in t or 'GetSwitch' in t or 'libsd' in t and 'def(' in t:
        print('====', p)
        for i,l in enumerate(t.splitlines(),1):
            if 'GetSwitch' in l or 'libsd' in l or 'SdInit' in l or 'VoiceTrans' in l:
                print(f'{i}:{l.strip()[:140]}')
