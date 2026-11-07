from pathlib import Path
# find wgpu dll and a typical run command from windows_port
text=Path('scripts/windows_port.py').read_text(encoding='utf-8')
# extract relevant run snippet
for i,l in enumerate(text.splitlines()):
    if 'wgpu' in l.lower() or 'ps2run' in l or 'trace_iop' in l or '--frames' in l or 'WGPU' in l:
        if i<200 or 'ps2run' in l or 'PATH' in l or 'frames' in l:
            print(f'{i+1}:{l}')
