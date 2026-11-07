from pathlib import Path
# use disc index via a tiny probe with existing tools, or parse ISO
import sys
sys.path.insert(0,'.')
# quick ISO path search using runtime isn't available; scan with pycdlib or raw
iso=Path('games/b49f2e769315347e8bda839feb705744/disc.iso')
# use previously known disc.py via a small C++? or python ISO9660
# simple: search for MUSIC directory name in path table / directory records
data=iso.read_bytes()[:512*2048]  # first 512 sectors
# find MUSIC as dir name
import re
for m in re.finditer(rb'MUSIC', data):
    ctx=data[max(0,m.start()-16):m.start()+24]
    print(hex(m.start()), ctx)
# also list via running a small helper if list_cnk exists
print('---')
print(Path('logs/list_cnk_assets.py').read_text()[:500])
