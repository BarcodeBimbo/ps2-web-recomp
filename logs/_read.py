from pathlib import Path
# find CLI options and how gob5 was run
for p in ['games/b49f2e769315347e8bda839feb705744/smoke.log','logs/cnk-igfileio-gob5.log','logs/rebuild-cnk-igfileio.log']:
    print('====', p)
    print(Path(p).read_text(encoding='utf-8', errors='replace')[:1500])
