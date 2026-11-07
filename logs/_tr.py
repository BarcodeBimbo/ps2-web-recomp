from pathlib import Path
# skim latest agent transcripts for CNK/VVAA/GFC conclusions
import os
d=Path(r'C:\Users\joshy\.cursor\projects\c-PS2Recomp\agent-transcripts')
files=sorted(d.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
for f in files:
    print('====', f.name, f.stat().st_mtime)
    text=f.read_text(encoding='utf-8', errors='replace')
    for key in ['VVAA','siid','GFC','igfileio','WaitSema','prim','DiIop','cmd 4','0x73696964']:
        if key.lower() in text.lower():
            print(' has', key)
    # print last user/assistant snippets mentioning CNK blockers
    lines=[ln for ln in text.splitlines() if '2 prim' in ln or 'VVAA' in ln or 'siid' in ln or 'near_zero' in ln or 'post-CDVD' in ln]
    for ln in lines[-8:]:
        print(ln[:200])
