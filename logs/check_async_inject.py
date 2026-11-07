import sys
from pathlib import Path
sys.path.insert(0, 'scripts')
import panel

for gid in ['60c82f4a111da300ac23bbec85272788', 'c0671389c296be6afe9e5224c97d30df']:
    print(gid, panel.resolve_async_mode(gid))
shell = Path('web/shell.html').read_text(encoding='utf-8')
body = shell.replace('__PS2_ASYNC_MODE__', panel.resolve_async_mode('60c82f4a111da300ac23bbec85272788'))
assert "const browserAsyncMode='asyncify'" in body
print('MW shell inject OK')
