"""Inspect a prompt/GS capture without executing game code."""
import argparse
from collections import Counter
import json
from pathlib import Path


def inspect(path):
    with Path(path).open('rb') as stream:
        raw=stream.readline(4096)
        if not raw.endswith(b'\n'):raise ValueError('Invalid capture header.')
        header=json.loads(raw)
        if (not isinstance(header,dict) or header.get('format') != 'ps2-prompt-capture-v1' or
            type(header.get('drawsBytes')) is not int or not 0 <= header['drawsBytes'] <= 16*1024*1024 or
            header.get('vramBytes') != 4194304):raise ValueError('Unsupported capture layout.')
        draws=stream.read(header['drawsBytes'])
        vram=stream.read(header['vramBytes'])
        if len(draws)!=header['drawsBytes'] or len(vram)!=header['vramBytes'] or stream.read(1):raise ValueError('Truncated or oversized capture.')
    rows=[]
    for line in draws.decode('utf-8').splitlines():
        row=line.split('\t')
        if row[0].isdigit():
            if len(row)!=14:raise ValueError('Malformed draw row.')
            rows.append(row)
    kinds=Counter(int(row[4],16)&7 for row in rows)
    names=['point','line','line strip','triangle','triangle strip','triangle fan','sprite','reserved']
    return {'boot':header.get('boot'),'drawBatches':len(rows),'primitives':sum(int(row[1]) for row in rows),
            'texturedBatches':sum(bool(int(row[4],16)&16) for row in rows),
            'primitiveKinds':{names[k]:n for k,n in sorted(kinds.items())},
            'vramBytes':len(vram),
            'limits':'Batches and end-of-frame VRAM do not include the EE/VU instruction trace or every vertex. This capture cannot prove correct geometry or identify a rendering cause by itself.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('capture',nargs='+');args=parser.parse_args()
    try:
        for path in args.capture:print(json.dumps({'file':Path(path).name,**inspect(path)},indent=2))
    except (ValueError,OSError,UnicodeError) as error: parser.exit(1,str(error)+'\n')
