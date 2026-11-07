"""Real 7-Zip integration tests with synthetic discs, no game data."""
from pathlib import Path
import os
import subprocess
import sys
import tarfile
import struct
import zlib
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from archives import inspect_archive, extract_archive, PasswordRequired
from disc_archive import make_iso
from disc import to_iso

TOOL=os.environ.get('PS2_7ZIP')

@unittest.skipUnless(TOOL,'Set PS2_7ZIP to a real 7z/7zz executable')
class ArchiveIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.iso=self.root/'disc.iso';make_iso(self.iso)
    def tearDown(self):self.temp.cleanup()
    def create(self,format,password=None,header=False):
        archive=self.root/('source.'+format)
        args=[TOOL,'a','-y','-t'+format,str(archive),str(self.iso)]
        if password:args.append('-p'+password)
        if header:args.append('-mhe=on')
        subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=30)
        return archive
    def check(self,archive,password=None):
        output=self.root/'out.iso';extract_archive(archive,output,password)
        self.assertEqual(output.read_bytes(),self.iso.read_bytes())
    def test_plain_zip_and_sevenzip(self):
        for fmt in ['zip','7z']:
            with self.subTest(fmt=fmt):
                archive=self.create(fmt);self.assertFalse(inspect_archive(archive)['needs_password']);self.check(archive)
    def test_encrypted_zip_and_sevenzip(self):
        for fmt in ['zip','7z']:
            with self.subTest(fmt=fmt):
                archive=self.create(fmt,'known password')
                self.assertTrue(inspect_archive(archive)['needs_password'])
                with self.assertRaises(PasswordRequired):self.check(archive)
                with self.assertRaises(PasswordRequired):self.check(archive,'wrong')
                self.check(archive,'known password')
    def test_encrypted_headers(self):
        archive=self.create('7z','secret',True)
        self.assertTrue(inspect_archive(archive)['needs_password']);self.check(archive,'secret')

    def test_aes_zip_import_uses_sevenzip_fallback(self):
        archive = self.root / 'aes.zip'
        subprocess.run([TOOL, 'a', '-y', '-tzip', '-mem=AES256', '-promsfun.com',
                        str(archive), str(self.iso)], check=True, stdout=subprocess.DEVNULL, timeout=30)
        self.assertTrue(inspect_archive(archive)['needs_password'])
        output = self.root / 'aes-disc.iso'
        to_iso(archive, output, 'romsfun.com')
        self.assertEqual(output.read_bytes(), self.iso.read_bytes())
        with self.assertRaisesRegex(ValueError, 'password'):
            to_iso(archive, self.root / 'wrong.iso', 'incorrect')
    def test_tar_and_tar_gz(self):
        for name,mode in [('game.tar','w'),('game.tar.gz','w:gz')]:
            archive=self.root/name
            with tarfile.open(archive,mode) as tar:tar.add(self.iso,arcname='folder/disc.iso')
            self.check(archive)
    def test_ignores_unsafe_unrelated_members(self):
        archive=self.root/'game.tar'
        other=self.root/'ignored.txt';other.write_text('not a game')
        with tarfile.open(archive,'w') as tar:
            tar.add(self.iso,arcname='../../disc.iso')
            tar.add(other,arcname='../../outside.txt')
        self.check(archive)
        self.assertFalse((self.root.parent/'outside.txt').exists())
    def test_rar_stored_member(self):
        body=self.iso.read_bytes();name=b'disc.iso'
        def header(kind,flags,extra):
            data=struct.pack('<BHH',kind,flags,7+len(extra))+extra
            return struct.pack('<H',zlib.crc32(data)&65535)+data
        archive=self.root/'source.rar'
        archive.write_bytes(b'Rar!\x1a\x07\x00'+header(0x73,0,b'\0'*6)+header(0x74,0x8000,
            struct.pack('<IIBIIBBHI',len(body),len(body),3,zlib.crc32(body),0,20,0x30,len(name),0x20)+name)+body+header(0x7b,0,b''))
        self.check(archive)

    def test_multiple_discs_require_selection(self):
        archive=self.root/'multi.tar'
        with tarfile.open(archive,'w') as tar:
            tar.add(self.iso,arcname='first.iso');tar.add(self.iso,arcname='second.iso')
        with self.assertRaisesRegex(ValueError,'multiple'):self.check(archive)

if __name__=='__main__':unittest.main(verbosity=2)
