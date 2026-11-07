import argparse
import fnmatch
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path

SECTOR = 2048
MAX_DISC_SIZE = 16 * 1024 ** 3


def export_path(destination, relative):
    """Validate host filenames only when exporting disc-named files."""
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$'} | {
        f'{kind}{number}' for kind in ('COM', 'LPT') for number in range(1, 10)
    }
    parts = relative.split('/')
    for name in parts:
        if (not name or name in ('.', '..') or name.endswith((' ', '.')) or
                name.split('.', 1)[0].upper() in reserved or
                any(ord(ch) < 32 or ch in '/\\:<>"|?*\x00' for ch in name)):
            raise ValueError('Cannot export unsafe host filename: ' + relative)
    root = Path(destination).resolve()
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Disc export path escapes its destination.')
    return target


def _copy_limited(source, destination, limit=MAX_DISC_SIZE):
    copied = 0
    while True:
        chunk = source.read(min(1 << 22, limit - copied + 1))
        if not chunk:
            return copied
        copied += len(chunk)
        if copied > limit:
            raise ValueError('The disc image exceeds the 16 GiB size limit.')
        destination.write(chunk)


class Layer:
    def __init__(self, index, base, pvd):
        self.index = index
        self.base = base
        self.volume = pvd[40:72].decode('ascii', 'replace').strip()
        self.sectors = struct.unpack_from('<I', pvd, 80)[0]
        self.root = struct.unpack_from('<I', pvd, 158)[0], struct.unpack_from('<I', pvd, 166)[0]


class Image:
    def __init__(self, path):
        self.size = os.path.getsize(path)
        if self.size <= 0 or self.size > MAX_DISC_SIZE:
            raise ValueError('The disc image is empty or exceeds the 16 GiB size limit.')
        self.file = open(path, 'rb')
        try:
            self.layers = [Layer(0, 0, self.pvd(16))]
            first = self.layers[0].sectors
            for sector in range(first, min(first + 64, self.size // SECTOR)):
                descriptor = self.read(sector, 1)
                if descriptor[:7] == b'\x01CD001\x01':
                    self.layers.append(Layer(1, sector - 16, descriptor))
                    break
        except Exception:
            self.file.close()
            raise

    def read(self, sector, count):
        if sector < 0 or count < 0:
            raise ValueError('invalid ISO sector range')
        self.file.seek(sector * SECTOR)
        return self.file.read(count * SECTOR)

    def pvd(self, sector):
        data = self.read(sector, 1)
        if len(data) != SECTOR or data[:7] != b'\x01CD001\x01':
            raise ValueError('not an ISO 9660 image: no valid primary volume descriptor at sector %d' % sector)
        return data

    def files(self):
        for layer in self.layers:
            yield from self.walk(layer, layer.root[0], layer.root[1], '')

    def walk(self, layer, lba, size, prefix, parents=()):
        sector = layer.base + lba
        if sector in parents or len(parents) >= 64 or size > 32 * 1024 * 1024 or sector * SECTOR + size > self.size:
            raise ValueError('invalid ISO directory extent')
        data = self.read(sector, (size + SECTOR - 1) // SECTOR)
        if len(data) < size:
            raise ValueError('ISO directory extends beyond end of image')
        offset = 0
        while offset < size:
            length = data[offset]
            if length == 0:
                offset = min(size, (offset // SECTOR + 1) * SECTOR)
                continue
            if length < 34 or length > size - offset:
                raise ValueError('invalid ISO directory record length')
            record = data[offset:offset + length]
            offset += length
            name_length = record[32]
            if 33 + name_length > len(record):
                raise ValueError('truncated ISO directory record')
            extent = struct.unpack_from('<I', record, 2)[0]
            extent_size = struct.unpack_from('<I', record, 10)[0]
            name = record[33:33 + name_length]
            if name in (b'\x00', b'\x01'):
                continue
            name = name.decode('ascii', 'replace').split(';')[0]
            # ISO identifiers are disc paths, not Windows output filenames.
            # In particular FILE.;1 is a legal ISO name, as are identifiers
            # that happen to match a Windows device name.
            if not name or name in ('.', '..') or any(ch in '/\\\x00' for ch in name):
                raise ValueError('invalid ISO filename')
            file_sector = layer.base + extent
            if file_sector < 0 or file_sector * SECTOR + extent_size > self.size:
                raise ValueError('ISO file extent extends beyond end of image')
            path = prefix + name
            if record[25] & 2:
                yield from self.walk(layer, extent, extent_size, path + '/', (*parents, sector))
            else:
                yield path, layer, file_sector, extent_size

    def find(self, path):
        wanted = path.replace('\\', '/').strip('/').upper()
        for entry in self.files():
            if entry[0].upper() == wanted:
                return entry
        return None

    def copy(self, entry, destination):
        path, _, sector, size = entry
        os.makedirs(os.path.dirname(destination) or '.', exist_ok=True)
        self.file.seek(sector * SECTOR)
        with open(destination, 'wb') as out:
            left = size
            while left:
                chunk = self.file.read(min(left, 1 << 22))
                if not chunk:
                    raise ValueError("disc file extends beyond end of image: " + path)
                out.write(chunk)
                left -= len(chunk)


def info(image):
    for layer in image.layers:
        print('layer %d: volume %s, base sector %d, %d sectors' % (layer.index, layer.volume, layer.base, layer.sectors))
    entry = image.find('SYSTEM.CNF')
    if entry:
        image.file.seek(entry[2] * SECTOR)
        print(image.file.read(entry[3]).decode('ascii', 'replace').strip())


def listing(image):
    for path, layer, sector, size in image.files():
        print('%d %10d %12d  %s' % (layer.index, sector, size, path))


def extract(image, destination, patterns, limit):
    count = 0
    for entry in image.files():
        path, _, _, size = entry
        if patterns and not any(fnmatch.fnmatch(path.upper(), p.upper()) for p in patterns):
            continue
        if not patterns and limit and size > limit:
            print('left in the image: %s (%d MiB)' % (path, size >> 20))
            continue
        image.copy(entry, export_path(destination, path))
        count += 1
    print('%d files extracted to %s' % (count, destination))


def read_at(image, sector, offset, size):
    image.file.seek(sector * SECTOR + offset)
    return image.file.read(size)


def modules(image, destination):
    found = []
    for path, _, sector, size in image.files():
        head = read_at(image, sector, 0, 8)
        if head[:4] == b'SNR2':
            found.append((path.replace('/', '_'), sector, 0, size))
        elif head[:4] == b'xff2':
            found.append((os.path.splitext(path.replace('/', '_'))[0], sector, 0, size))
        elif len(head) == 8 and head[:4] == b'AFS\0':
            count = struct.unpack_from('<I', head, 4)[0]
            if count > min((size - 8) // 8, 1_000_000):
                continue
            table = read_at(image, sector, 8, count * 8)
            if len(table) != count * 8:
                continue
            for index in range(count):
                offset, length = struct.unpack_from('<II', table, index * 8)
                if 4 <= length <= size - offset and read_at(image, sector, offset, 4) == b'SNR2':
                    found.append(('%s_%04d' % (path.replace('/', '_'), index), sector, offset, length))
    os.makedirs(destination, exist_ok=True)
    if len(found) > 10000 or sum(item[3] for item in found) > 512 * 1024 * 1024:
        raise ValueError('Relocatable modules exceed the extraction budget.')
    for name, sector, offset, length in found:
        if length > 256 * 1024 * 1024: raise ValueError('Relocatable module exceeds 256 MiB.')
        with open(export_path(destination, name + '.snr'), 'wb') as out:
            out.write(read_at(image, sector, offset, length))
    print('%d relocatable modules extracted to %s' % (len(found), destination))


@contextmanager
def open_source(source, password=None):
    lower = str(source).lower()
    if lower.endswith('.zip'):
        archive = zipfile.ZipFile(source)
        try:
            members = archive.infolist()
            selected = None
            for ending in ('.iso', '.chd', '.bin', '.img', '.rom'):
                found = [m for m in members if m.filename.lower().endswith(ending)]
                if found:
                    selected = max(found, key=lambda m: m.file_size)
                    break
            if selected is None:
                raise ValueError('No .iso, .chd, .bin or .img disc image inside the ZIP archive.')
            if selected.file_size <= 0 or selected.file_size > MAX_DISC_SIZE:
                raise ValueError('The selected ZIP entry is empty or exceeds the 16 GiB disc-image limit.')
            pwd = password.encode('utf-8') if password else None
            try:
                with archive.open(selected, 'r', pwd=pwd) as stream:
                    yield stream
            except NotImplementedError:
                # This Python runtime cannot decode the member's compression
                # method. Let to_iso route the whole archive through 7-Zip.
                raise
            except RuntimeError as error:
                message = str(error).lower()
                if 'password' in message or 'encrypted' in message:
                    if password:
                        raise ValueError('The ZIP password is incorrect. Check it and retry.') from error
                    raise ValueError('This ZIP is password-protected. Enter its password and retry.') from error
                if 'compression' in message or 'compressor' in message or 'not supported' in message:
                    raise
                raise ValueError('The ZIP archive could not be read: ' + str(error)) from error
            except zipfile.BadZipFile as error:
                raise ValueError('The ZIP archive is damaged or has an invalid checksum.') from error
        finally:
            archive.close()
        return
    if lower.endswith('.cue'):
        cue_path = Path(source).resolve()
        base = cue_path.parent
        cue_text = cue_path.read_text(encoding='utf-8', errors='replace')
        for line in cue_text.splitlines():
            match = re.match(r'^\s*FILE\s+(?:"([^"]+)"|(.+?))\s+\S+\s*$', line, re.I)
            if not match:
                continue
            relative_name = (match.group(1) or match.group(2)).strip()
            member = (base / relative_name).resolve()
            if not member.is_relative_to(base):
                raise ValueError('The CUE sheet references a file outside its disc-image folder.')
            if not member.is_file():
                raise ValueError('The CUE sheet references a missing track file: ' + relative_name)
            with member.open('rb') as stream:
                yield stream
            return
        raise ValueError('The CUE sheet names no valid FILE track.')
    with open(source, 'rb') as stream:
        yield stream


def _is_iso(path):
    try:
        image = Image(path)
    except (OSError, ValueError, struct.error):
        return False
    else:
        image.file.close()
        return True


def _find_chdman():
    # Prefer an explicit override, then the copy installed by Setup.cmd, then
    # standard MAME locations and PATH. This works for the panel's worker
    # process even though its PATH is intentionally kept isolated.
    override = os.environ.get('CHDMAN')
    candidates = [Path(override)] if override else []
    project = Path(__file__).resolve().parents[1]
    candidates.extend((
        project / 'tools' / 'chdman' / 'chdman.exe',
        project / 'tools' / 'chdman' / 'chdman',
        project / 'tools' / 'mame' / 'chdman.exe',
        project / 'tools' / 'mame' / 'chdman',
    ))
    for variable in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)'):
        base = os.environ.get(variable)
        if base:
            candidates.extend((Path(base) / 'MAME' / 'chdman.exe',
                               Path(base) / 'MAME' / 'chdman'))
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate.resolve())
        except OSError:
            continue
    return shutil.which('chdman')


def _find_7zip():
    # Setup installs 7-Zip in MSYS2's private prefix. Search that location
    # directly instead of relying on the desktop process's inherited PATH.
    for variable in ('PS2_7ZIP', 'SEVEN_ZIP', 'SEVENZIP'):
        override = os.environ.get(variable)
        if override and Path(override).is_file():
            return str(Path(override).resolve())
    project = Path(__file__).resolve().parents[1]
    candidates = [
        project / 'tools' / 'msys64' / 'clang64' / 'bin' / '7z.exe',
        project / 'tools' / 'msys64' / 'clang64' / 'bin' / '7zz.exe',
        project / 'tools' / 'msys64' / 'usr' / 'bin' / '7z.exe',
        project / 'tools' / 'msys64' / 'usr' / 'bin' / '7zz.exe',
    ]
    for variable in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)'):
        base = os.environ.get(variable)
        if base:
            candidates.extend((Path(base) / '7-Zip' / '7z.exe',
                               Path(base) / '7-Zip' / '7zz.exe'))
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate.resolve())
        except OSError:
            continue
    return shutil.which('7z') or shutil.which('7zz')


def _chd_to_iso(source, target):
    tool = _find_chdman()
    if not tool:
        raise ValueError('CHD conversion utility is missing. Run Setup.cmd to install MAME chdman, or set CHDMAN to the full path of chdman.exe.')
    source_size = Path(source).stat().st_size
    if source_size <= 0 or source_size > MAX_DISC_SIZE:
        raise ValueError('The CHD image is empty or exceeds the 16 GiB size limit.')
    with Path(source).open('rb') as chd:
        header = chd.read(124)
    if len(header) < 16 or header[:8] != b'MComprHD':
        raise ValueError('The CHD header is invalid.')
    if struct.unpack_from('>I', header, 12)[0] == 5:
        if len(header) < 124 or struct.unpack_from('>I', header, 8)[0] != 124:
            raise ValueError('The CHD v5 header is truncated or invalid.')
        logical_size = struct.unpack_from('>Q', header, 32)[0]
        if not 0 < logical_size <= MAX_DISC_SIZE:
            raise ValueError('CHD expanded disc size exceeds the 16 GiB limit.')
    target_path = Path(target).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ps2-chd-', dir=target_path.parent) as temp_dir:
        temp = Path(temp_dir)
        dvd = temp / 'disc-dvd.iso'
        dvd_result = subprocess.run([tool, 'extractdvd', '-i', str(source), '-o', str(dvd)],
                                    capture_output=True, text=True, errors='replace', timeout=1800)
        if (dvd_result.returncode == 0 and dvd.is_file() and
                0 < dvd.stat().st_size <= MAX_DISC_SIZE and _is_iso(dvd)):
            os.replace(dvd, target_path)
            return

        cue, binary = temp / 'disc.cue', temp / 'disc.bin'
        cd_result = subprocess.run([tool, 'extractcd', '-i', str(source), '-o', str(cue), '-ob', str(binary)],
                                   capture_output=True, text=True, errors='replace', timeout=1800)
        if cd_result.returncode == 0 and cue.is_file():
            converted = temp / 'disc.iso'
            _write_iso(cue, converted)
            if converted.is_file() and converted.stat().st_size <= MAX_DISC_SIZE and _is_iso(converted):
                os.replace(converted, target_path)
                return
        details = (cd_result.stderr or cd_result.stdout or dvd_result.stderr or dvd_result.stdout).strip()
        if len(details) > 1200:
            details = details[-1200:]
        suffix = (' ' + details) if details else ''
        raise ValueError('Could not extract this CHD as a PS2 CD/DVD image. The CHD may be damaged, unsupported, or require its parent image.' + suffix)


def _write_iso(source, target, password=None):
    sync = b'\x00' + b'\xff' * 10 + b'\x00'
    with open_source(source, password) as src, open(target, 'wb') as dst:
        first = src.read(2352)
        if len(first) < 2352 or first[:12] != sync:
            dst.write(first)
            _copy_limited(src, dst, MAX_DISC_SIZE - len(first))
            if len(first) > MAX_DISC_SIZE:
                raise ValueError('The disc image exceeds the 16 GiB size limit.')
            return
        start = 16 if first[15] == 1 else 24
        sector = first
        while len(sector) == 2352:
            dst.write(sector[start:start + SECTOR])
            if dst.tell() > MAX_DISC_SIZE:
                raise ValueError('The disc image exceeds the 16 GiB size limit.')
            sector = src.read(2352)


def _seven_zip_to_iso(source, target, password=None):
    from archives import extract_archive
    extract_archive(source, target, password)


def _zip_chd_to_iso(source, target, password=None):
    with zipfile.ZipFile(source) as archive:
        selected = None
        for ending in ('.iso', '.chd', '.bin', '.img', '.rom'):
            candidates = [item for item in archive.infolist() if item.filename.lower().endswith(ending)]
            if candidates:
                selected = max(candidates, key=lambda item: item.file_size)
                break
        if selected is None or not selected.filename.lower().endswith('.chd'):
            return False
        if selected.file_size <= 0 or selected.file_size > 16 * 1024 ** 3:
            raise ValueError('The CHD entry is empty or exceeds the 16 GiB disc-image limit.')
        pwd = password.encode('utf-8') if password is not None else None
        target_path = Path(target).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.ps2-zip-chd-', dir=target_path.parent) as temp_dir:
            chd = Path(temp_dir) / 'disc.chd'
            try:
                with archive.open(selected, 'r', pwd=pwd) as source_stream, chd.open('wb') as output:
                    _copy_limited(source_stream, output, MAX_DISC_SIZE)
            except NotImplementedError:
                raise
            except RuntimeError as error:
                message = str(error).lower()
                if 'password' in message or 'encrypted' in message:
                    if password:
                        raise ValueError('The ZIP password is incorrect. Check it and retry.') from error
                    raise ValueError('This ZIP is password-protected. Enter its password and retry.') from error
                if 'compression' in message or 'compressor' in message or 'not supported' in message:
                    raise
                raise ValueError('The ZIP archive could not be read: ' + str(error)) from error
            _chd_to_iso(chd, target_path)
    return True


def to_iso(source, target, password=None):
    lower = str(source).lower()
    if lower.endswith('.chd'):
        _chd_to_iso(source, target)
        return
    if lower.endswith('.zip'):
        try:
            if _zip_chd_to_iso(source, target, password):
                return
        except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as error:
            # Python's zipfile module cannot read every AES/ZIP64 variant. Use
            # 7-Zip for those rather than failing before the normal fallback.
            try:
                _seven_zip_to_iso(source, target, password)
                return
            except ValueError as fallback_error:
                if '7-Zip is required' in str(fallback_error):
                    if isinstance(error, RuntimeError) and ('password' in str(error).lower() or 'encrypted' in str(error).lower()):
                        raise ValueError('This ZIP is password-protected. Enter its password; Setup.cmd also needs 7-Zip available.') from error
                    raise ValueError('This ZIP uses a compression or encryption method Python cannot read. Run Setup.cmd to install 7-Zip, then retry.') from error
                raise fallback_error from error
    from archives import ARCHIVE_EXTENSIONS
    if Path(source).suffix.lower() in ARCHIVE_EXTENSIONS and not lower.endswith('.zip'):
        _seven_zip_to_iso(source, target, password)
        return
    target_path = Path(target).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix='.ps2-disc-', suffix='.tmp', dir=target_path.parent)
    os.close(fd)
    try:
        try:
            _write_iso(source, temp_name, password)
        except (ValueError, NotImplementedError, RuntimeError, zipfile.BadZipFile) as error:
            if not lower.endswith('.zip'):
                raise
            try:
                _seven_zip_to_iso(source, target_path, password)
                return
            except ValueError as fallback_error:
                if '7-Zip is required' in str(fallback_error):
                    message = str(error).lower()
                    if 'password' in message or 'encrypted' in message:
                        raise error
                    raise ValueError('This ZIP uses a compression method Python cannot read. Run Setup.cmd to install 7-Zip, then retry.') from error
                raise fallback_error from error
        output_size = os.path.getsize(temp_name)
        if output_size == 0:
            raise ValueError('The selected disc image is empty.')
        if output_size > MAX_DISC_SIZE:
            raise ValueError('The disc image exceeds the 16 GiB size limit.')
        os.replace(temp_name, target_path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser(description='Read files from PS2 CD and DVD images, including both layers of a DVD9.')
    parser.add_argument('command', choices=['info', 'list', 'extract', 'modules', 'iso'])
    parser.add_argument('image')
    parser.add_argument('destination', nargs='?')
    parser.add_argument('patterns', nargs='*', help='paths or globs to extract, everything below --limit if omitted')
    parser.add_argument('--limit', type=int, default=64, help='MiB; larger files stay in the image unless named')
    parser.add_argument('--password-stdin', action='store_true', help='read an archive password from one line on stdin')
    args = parser.parse_args()
    password = sys.stdin.readline().rstrip('\r\n') if args.password_stdin else None
    if args.command == 'iso':
        if not args.destination:
            parser.error('iso needs the .iso file to write')
        to_iso(args.image, args.destination, password)
        return
    image = Image(args.image)
    if args.command == 'info':
        info(image)
    elif args.command == 'list':
        listing(image)
    elif args.command == 'modules':
        if not args.destination:
            parser.error('modules needs a destination folder')
        modules(image, args.destination)
    else:
        if not args.destination:
            parser.error('extract needs a destination folder')
        extract(image, args.destination, args.patterns, args.limit << 20)


if __name__ == '__main__':
    main()
