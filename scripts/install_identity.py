"""Content identity of normalized PS2 discs, serialized across build workers."""
from contextlib import contextmanager
import hashlib
import json
import os
import re
from pathlib import Path
import time


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def identity_lock(games):
    with (games/'.identity.lock').open('a+b') as stream:
        if os.name=='nt':
            import msvcrt
            stream.seek(0);stream.write(b'0');stream.flush()
            for attempt in range(1800):
                try: stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError: time.sleep(.1)
            else: raise ValueError('Timed out waiting for disc identity verification.')
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX)
        try: yield
        finally:
            if os.name=='nt': stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(stream,fcntl.LOCK_UN)


def claim_disc(root, game_id, disc):
    games=Path(root)/'games';digest=sha256(disc)
    with identity_lock(games):
        index_path=games/'.disc-index.json'
        try: index=json.loads(index_path.read_text())
        except (OSError,ValueError):index={}
        if not isinstance(index,dict):index={}
        owner=index.get(digest)
        if isinstance(owner,str) and re.fullmatch(r'[a-f0-9]{32}',owner) and owner!=game_id and (games/owner/'disc.iso').is_file():
            try: state=json.loads((games/owner/'library.json').read_text()).get('status')
            except (OSError,ValueError):state=None
            if state not in ('duplicate','deleting',None):return digest,owner
        for folder in games.iterdir():
            if not folder.is_dir() or folder.name==game_id: continue
            manifest=folder/'library.json';other=folder/'disc.iso'
            if not manifest.is_file() or not other.is_file():continue
            try: data=json.loads(manifest.read_text(encoding='utf-8'))
            except (ValueError,OSError):continue
            if not isinstance(data,dict) or data.get('status')!='ready':continue
            known=data.get('disc_sha256') or sha256(other)
            if known==digest:
                index[digest]=folder.name
                temporary=index_path.with_suffix('.tmp');temporary.write_text(json.dumps(index));temporary.replace(index_path)
                return digest,folder.name
        index[digest]=game_id
        temporary=index_path.with_suffix('.tmp');temporary.write_text(json.dumps(index));temporary.replace(index_path)
        return digest,None
