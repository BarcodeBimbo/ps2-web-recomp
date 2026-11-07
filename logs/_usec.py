from pathlib import Path
import re
text=Path('runtime/src/iop/libs.cpp').read_text(encoding='utf-8')
for m in re.finditer(r'USec2SysClock|SysClock2USec|GetSystemTime|def\("thbase"', text):
    start=max(0, m.start()-50); end=min(len(text), m.end()+200)
    # find line
    line=text.count('\n',0,m.start())+1
    print(f'--- {line} ---')
    print(text[text.rfind('\n',0,m.start())+1:text.find('\n',m.end())+1])
# print thbase section around USec
lines=text.splitlines()
for i,l in enumerate(lines):
    if 'USec2SysClock' in l or 'SysClock2USec' in l or 'GetSystemTime' in l:
        for j in range(max(0,i-1), min(len(lines), i+8)):
            print(f'{j+1}:{lines[j]}')
        print()
