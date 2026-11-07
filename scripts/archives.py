"""Bounded, single-member archive import. Archive paths are never extracted."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import zipfile

from malware_guard import assert_safe_import, HOST_EXECUTABLE_EXTENSIONS

ARCHIVE_EXTENSIONS = {'.zip', '.zipx', '.7z', '.7zip', '.rar', '.tar', '.gz', '.gzip',
                      '.tgz', '.bz2', '.tbz', '.tbz2', '.xz', '.txz', '.zst', '.lzma',
                      '.cab', '.arj', '.lzh', '.lha', '.cpio', '.xar', '.z'}
DISC_EXTENSIONS = ('.iso', '.chd', '.bin', '.img', '.rom')
MAX_LIST = 8 * 1024 * 1024
MAX_MEMBERS = 100000

class PasswordRequired(ValueError):
    pass


def password_error(password):
    return PasswordRequired('Incorrect archive password.' if password else 'This archive needs a password.')


def _run_bounded(command, limit, output=None, timeout=1800):
    # No shell, inherited stdin, unbounded capture_output or archive-named paths.
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errors)
        timed_out = threading.Event()
        def terminate():
            timed_out.set()
            try: process.kill()
            except ProcessLookupError: pass
        timer = threading.Timer(timeout, terminate)
        timer.daemon = True
        timer.start()
        data = bytearray()
        count = 0
        try:
            while chunk := process.stdout.read(65536):
                count += len(chunk)
                if count > limit:
                    process.kill()
                    raise ValueError('Archive output exceeds its allowed size.')
                if output is None: data.extend(chunk)
                else: output.write(chunk)
            status = process.wait()
            if timed_out.is_set(): raise ValueError('Archive operation timed out.')
            errors.seek(0)
            detail = errors.read(8192).decode('utf-8', 'replace')
            return status, bytes(data), detail
        finally:
            timer.cancel()
            if process.poll() is None: process.kill()
            process.wait()
            process.stdout.close()


def _listed(source, password=None):
    from disc import _find_7zip
    tool = _find_7zip()
    if not tool: raise ValueError('7-Zip is required for this archive. Run Setup.cmd or install 7-Zip.')
    args = [f'-p{password}'] if password else []
    status, raw, errors = _run_bounded([tool, 'l', '-slt', '-ba', '-sccUTF-8', *args, '--', str(Path(source).resolve())], MAX_LIST, timeout=60)
    text = raw.decode('utf-8', 'replace')
    if status:
        if any(word in (text + errors).lower() for word in ('password', 'encrypted', 'decrypt')):
            raise password_error(password)
        raise ValueError('Archive listing failed. Check its format, integrity, and multipart files.')
    entries = []
    for block in re.split(r'\r?\n\s*\r?\n', text.strip()):
        fields = dict(line.split(' = ', 1) for line in block.splitlines() if ' = ' in line)
        if 'Path' not in fields: continue
        try: size = int(fields.get('Size', '0'))
        except ValueError: raise ValueError('Archive has an invalid member size.') from None
        entries.append({'name': fields['Path'], 'size': size,
                        'encrypted': fields.get('Encrypted') == '+',
                        'file': fields.get('Folder') != '+' and not any(fields.get(k) for k in ('Symbolic Link', 'Hard Link'))})
        if len(entries) > MAX_MEMBERS: raise ValueError('Too many archive members.')
    return tool, entries


def _choose(entries, allow_container=False):
    from disc import MAX_DISC_SIZE
    for ext in DISC_EXTENSIONS:
        candidates = [e for e in entries if e['file'] and e['name'].lower().endswith(ext)]
        if candidates:
            if len(candidates) != 1:
                raise ValueError('Archive contains multiple disc images. Extract and choose one disc first.')
            entry = candidates[0]
            if not 0 < entry['size'] <= MAX_DISC_SIZE: raise ValueError('Disc member is empty or exceeds 16 GiB.')
            # Only the disc member is streamed out; host programs are never launched.
            if Path(entry['name']).suffix.lower() in HOST_EXECUTABLE_EXTENSIONS:
                raise ValueError('Refusing to extract a host program from the archive.')
            return entry
    if allow_container:
        files = [e for e in entries if e['file']]
        if len(files) == 1 and Path(files[0]['name']).suffix.lower() in ARCHIVE_EXTENSIONS:
            if Path(files[0]['name']).suffix.lower() in HOST_EXECUTABLE_EXTENSIONS:
                raise ValueError('Refusing to extract a host program from the archive.')
            if not 0 < files[0]['size'] <= MAX_DISC_SIZE: raise ValueError('Nested archive exceeds 16 GiB.')
            return files[0]
    # Prefer a clear malware refusal when the archive is only host programs.
    host_only = [e for e in entries if e.get('file') and Path(e['name']).suffix.lower() in HOST_EXECUTABLE_EXTENSIONS]
    if host_only and not any(e.get('file') and e['name'].lower().endswith(DISC_EXTENSIONS) for e in entries):
        raise ValueError('Archive contains host programs but no PS2 disc image. Refusing to extract or run them.')
    raise ValueError('Archive contains no supported PS2 disc image.')


def inspect_archive(source, password=None):
    """Inspect headers only. Passwords are requested only for encrypted content."""
    source = Path(source)
    if source.suffix.lower() not in ARCHIVE_EXTENSIONS: return {'archive': False, 'needs_password': False}
    if source.suffix.lower() == '.zip':
        try:
            with zipfile.ZipFile(source) as archive:
                members = archive.infolist()
                if len(members) > MAX_MEMBERS: raise ValueError('Too many archive members.')
                entries = [{'name': m.filename, 'size': m.file_size, 'encrypted': bool(m.flag_bits & 1), 'file': not m.is_dir()} for m in members]
                entry = _choose(entries, True)
                return {'archive': True, 'needs_password': entry['encrypted'], 'member': entry['name']}
        except zipfile.BadZipFile:
            pass
    try:
        _, entries = _listed(source, password)
        entry = _choose(entries, True)
        return {'archive': True, 'needs_password': entry['encrypted'], 'member': entry['name']}
    except PasswordRequired:
        return {'archive': True, 'needs_password': True}


def extract_archive(source, target, password=None, depth=0):
    from disc import MAX_DISC_SIZE, to_iso
    if depth > 2: raise ValueError('Archive nesting is too deep. Extract the disc first.')
    if password is not None and (not isinstance(password, str) or len(password) > 1024 or any(c in password for c in '\x00\r\n')):
        raise ValueError('Invalid archive password.')
    source = Path(source)
    if depth == 0:
        assert_safe_import(source)
    tool, entries = _listed(source, password)
    entry = _choose(entries, True)
    if entry['encrypted'] and not password: raise password_error(password)
    target = Path(target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ps2-archive-', dir=target.parent) as work:
        # Fixed local name prevents path traversal, links, ADS and device files.
        # Extraction streams to a file; the member is never executed.
        member = Path(work) / ('disc' + Path(entry['name']).suffix.lower())
        args = [f'-p{password}'] if password else []
        with member.open('wb') as output:
            status, _, errors = _run_bounded([tool, 'x', '-so', '-y', '-spd', '-sccUTF-8', *args, '--',
                                               str(Path(source).resolve()), entry['name']], min(entry['size'], MAX_DISC_SIZE), output)
        if status:
            if any(word in errors.lower() for word in ('password', 'encrypted', 'decrypt', 'data error')) and entry['encrypted']:
                raise password_error(password)
            raise ValueError('Disc extraction failed. Check the archive or multipart volumes.')
        if member.stat().st_size != entry['size']: raise ValueError('Extracted member size does not match its archive header.')
        assert_safe_import(member, scan=True)
        if member.suffix.lower() in ARCHIVE_EXTENSIONS:
            extract_archive(member, target, password, depth + 1)
        else:
            to_iso(member, target, password)
