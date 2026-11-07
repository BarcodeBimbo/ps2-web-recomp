from pathlib import Path
import sys
sys.path.insert(0,'scripts')
from disc import Image
img=Image(Path('games/b49f2e769315347e8bda839feb705744/disc.iso'))
for path, sector, _, size in img.files():
    u=path.upper()
    if 'MUSIC' in u or u.endswith('/MUSIC') or u=='MUSIC' or '\\MUSIC' in u or u.startswith('MUSIC'):
        print(f'{path} sector={sector} size={size}')
print('--- sample root ---')
n=0
for path, sector, isdir, size in img.files():
    if path.count('/')<=1 and n<40:
        print(f'{"DIR" if isdir else "FILE"} {path} sec={sector} size={size}'); n+=1
