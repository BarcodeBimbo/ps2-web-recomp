"""CHD DVD/CD round trips using real MAME tools and synthetic disc sectors."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from disc import to_iso
from disc_archive import make_iso
TOOL=os.environ.get('CHDMAN')

@unittest.skipUnless(TOOL,'Set CHDMAN to a real chdman executable')
class ChdIntegration(unittest.TestCase):
    def test_dvd_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'input.iso';make_iso(source)
            packed=root/'input.chd';output=root/'output.iso'
            subprocess.run([TOOL,'createdvd','-i',str(source),'-o',str(packed)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            to_iso(packed,output);self.assertEqual(source.read_bytes(),output.read_bytes())
    def test_cd_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'input.iso';make_iso(source)
            cue=root/'input.cue';cue.write_text('FILE "input.iso" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
            packed=root/'input.chd';output=root/'output.iso'
            subprocess.run([TOOL,'createcd','-i',str(cue),'-o',str(packed)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            to_iso(packed,output);self.assertEqual(source.read_bytes(),output.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
