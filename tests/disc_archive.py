#!/usr/bin/env python3
"""Disc image parser and archive/password regressions; needs no PS2 game data."""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import disc  # noqa: E402
import archives

SECTOR = 2048


def directory_record(lba, size, name, flags=0):
    if isinstance(name, str):
        name = name.encode('ascii')
    padding = 1 if len(name) % 2 == 0 else 0
    record = bytearray(33 + len(name) + padding)
    record[0] = len(record)
    struct.pack_into('<I', record, 2, lba)
    struct.pack_into('<I', record, 10, size)
    record[25] = flags
    struct.pack_into('<H', record, 28, 1)
    record[32] = len(name)
    record[33:33 + len(name)] = name
    return record


def make_iso(path):
    raw = bytearray(20 * SECTOR)
    pvd = memoryview(raw)[16 * SECTOR:17 * SECTOR]
    pvd[0:7] = b'\x01CD001\x01'
    pvd[40:72] = b'AUDIT DISC'.ljust(32, b' ')
    struct.pack_into('<I', pvd, 80, 20)
    struct.pack_into('>I', pvd, 84, 20)
    root = directory_record(17, SECTOR, b'\x00', 2)
    pvd[156:156 + len(root)] = root
    directory = bytearray(SECTOR)
    offset = 0
    for entry in (
        directory_record(17, SECTOR, b'\x00', 2),
        directory_record(17, SECTOR, b'\x01', 2),
        directory_record(18, 34, 'SYSTEM.CNF;1'),
    ):
        directory[offset:offset + len(entry)] = entry
        offset += len(entry)
    raw[17 * SECTOR:18 * SECTOR] = directory
    raw[18 * SECTOR:18 * SECTOR + 34] = b'BOOT2 = cdrom0:\\SLUS_123.45;1\r\n'.ljust(34, b' ')
    path.write_bytes(raw)


class DiscArchiveTests(unittest.TestCase):
    def test_valid_iso_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'disc.iso'
            make_iso(path)
            image = disc.Image(path)
            try:
                self.assertIn('SYSTEM.CNF', {entry[0] for entry in image.files()})
            finally:
                image.file.close()

    def test_malformed_directory_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.iso'
            make_iso(path)
            with path.open('r+b') as source:
                source.seek(17 * SECTOR)
                source.write(b'\x01')
            image = disc.Image(path)
            try:
                with self.assertRaisesRegex(ValueError, 'directory record'):
                    list(image.files())
            finally:
                image.file.close()


    def test_oversized_sparse_image_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'oversized.iso'
            with path.open('wb') as source:
                source.truncate(disc.MAX_DISC_SIZE + 1)
            with self.assertRaisesRegex(ValueError, '16 GiB'):
                disc.Image(path)

    def test_windows_device_name_can_be_read_but_not_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'unsafe.iso'
            make_iso(path)
            unsafe = directory_record(18, 34, 'NUL.txt')
            with path.open('r+b') as source:
                source.seek(17 * SECTOR + len(directory_record(17, SECTOR, b'\x00', 2)) +
                            len(directory_record(17, SECTOR, b'\x01', 2)))
                source.write(unsafe + bytes(SECTOR - 2 * len(directory_record(17, SECTOR, b'\x00', 2)) - len(unsafe)))
            image = disc.Image(path)
            try:
                self.assertIsNotNone(image.find('NUL.txt'))
                self.assertIsNone(image.find('CORE.GT4'))
                image.copy(image.find('NUL.txt'), Path(tmp) / 'safe-name.bin')
                with self.assertRaisesRegex(ValueError, 'unsafe host filename'):
                    disc.extract(image, Path(tmp) / 'export', [], 0)
            finally:
                image.file.close()

    def test_iso_trailing_period_is_readable_during_optional_core_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'normal.iso'
            make_iso(path)
            record = directory_record(18, 34, 'DATA.;1')
            with path.open('r+b') as source:
                source.seek(17 * SECTOR + 2 * len(directory_record(17, SECTOR, b'\x00', 2)))
                source.write(record + bytes(SECTOR - 2 * len(directory_record(17, SECTOR, b'\x00', 2)) - len(record)))
            image = disc.Image(path)
            try:
                self.assertIsNotNone(image.find('DATA.'))
                self.assertIsNone(image.find('CORE.GT4'))
            finally:
                image.file.close()

    def test_cue_cannot_escape_its_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cue = root / 'disc.cue'
            cue.write_text('FILE "../outside.bin" BINARY\n', encoding='ascii')
            (root.parent / 'outside.bin').write_bytes(b'data')
            with self.assertRaisesRegex(ValueError, 'outside'):
                with disc.open_source(cue):
                    pass
            (root.parent / 'outside.bin').unlink(missing_ok=True)

    def test_password_protected_zip_and_wrong_password(self):
        zip_tool = shutil.which('zip')
        if not zip_tool:
            self.skipTest('zip utility is not installed for creating ZipCrypto test fixtures')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso = root / 'source.iso'
            archive = root / 'protected.zip'
            output = root / 'roundtrip.iso'
            make_iso(iso)
            subprocess.run([zip_tool, '-q', '-P', 'unit-test-secret', str(archive), str(iso)], check=True)
            disc.to_iso(archive, output, 'unit-test-secret')
            self.assertEqual(output.read_bytes(), iso.read_bytes())
            with self.assertRaisesRegex(ValueError, 'password'):
                disc.to_iso(archive, root / 'wrong.iso', 'incorrect')


    def test_project_managed_7zip_is_discovered_without_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            fake_script = project / 'scripts' / 'disc.py'
            fake_script.parent.mkdir()
            fake_script.write_text('# test path')
            binary = project / 'tools' / 'msys64' / 'clang64' / 'bin' / '7z.exe'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'fake exe')
            with patch.object(disc, '__file__', str(fake_script)), \
                    patch('disc.shutil.which', return_value=None):
                self.assertEqual(disc._find_7zip(), str(binary.resolve()))

    def archive_fixture(self, password=None, unsupported=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.zip';image=root/'disc.iso';output=root/'out.iso'
            make_iso(image)
            with zipfile.ZipFile(source,'w') as bundle:bundle.write(image,'disc.iso')
            if unsupported:
                data=bytearray(source.read_bytes())
                struct.pack_into('<H',data,data.index(b'PK\x03\x04')+8,99)
                struct.pack_into('<H',data,data.index(b'PK\x01\x02')+10,99);source.write_bytes(data)
            calls=[]
            def bounded(command,limit,destination=None,timeout=1800):
                calls.append(command)
                if command[1]=='l':
                    listing=f'Path = disc.iso\nSize = {image.stat().st_size}\nEncrypted = {"+" if password else "-"}\n'
                    return 0,listing.encode(),''
                destination.write(image.read_bytes());return 0,b'', ''
            with patch('disc._find_7zip',return_value='7z'),patch('archives._run_bounded',side_effect=bounded):
                if unsupported:disc.to_iso(source,output,password)
                else:disc._seven_zip_to_iso(source,output,password)
            self.assertEqual(output.read_bytes(),image.read_bytes())
            self.assertEqual([c[1] for c in calls],['l','x'])
            self.assertIn('-so',calls[1]);self.assertIn('-spd',calls[1])
            return calls

    def test_seven_zip_does_not_prompt_for_an_optional_password(self):
        calls=self.archive_fixture()
        self.assertTrue(all(not any(arg.startswith('-p') for arg in c) for c in calls))

    def test_seven_zip_password_is_sent_only_when_supplied(self):
        calls=self.archive_fixture('known password')
        self.assertTrue(all('-pknown password' in c for c in calls))

    def test_unsupported_zip_compression_falls_back_to_seven_zip(self):
        self.archive_fixture(unsupported=True)

    def test_chd_and_seven_zip_dependencies_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop('CHDMAN', None)
                with patch('disc.shutil.which', return_value=None):
                    with self.assertRaisesRegex(ValueError, 'chdman'):
                        disc.to_iso(root / 'missing.chd', root / 'output.iso')
                    with self.assertRaisesRegex(ValueError, '7-Zip'):
                        disc.to_iso(root / 'missing.7z', root / 'output.iso')


if __name__ == '__main__':
    unittest.main(verbosity=2)
