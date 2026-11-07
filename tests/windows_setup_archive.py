#!/usr/bin/env python3
"""Security regressions for downloaded Windows toolchain archives."""
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import windows_setup  # noqa: E402


class SafeZipExtractionTests(unittest.TestCase):
    def test_extracts_normal_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'tools.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('tool/bin/compiler.exe', b'tool')
                bundle.writestr('tool/include/header.h', b'header')
            destination = root / 'dest'
            windows_setup.safe_extract_zip(archive, destination)
            self.assertEqual((destination / 'tool/bin/compiler.exe').read_bytes(), b'tool')
            self.assertEqual((destination / 'tool/include/header.h').read_bytes(), b'header')

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('../escape.txt', b'no')
            with self.assertRaisesRegex(RuntimeError, 'unsafe path'):
                windows_setup.safe_extract_zip(archive, root / 'dest')
            self.assertFalse((root / 'escape.txt').exists())

    def test_rejects_windows_drive_and_alternate_stream_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('C:/Windows/escape.txt', 'folder/payload.txt:stream'):
                archive = root / ('bad-' + str(len(name)) + '.zip')
                with zipfile.ZipFile(archive, 'w') as bundle:
                    bundle.writestr(name, b'no')
                with self.assertRaisesRegex(RuntimeError, 'unsafe path'):
                    windows_setup.safe_extract_zip(archive, root / ('dest-' + str(len(name))))

    def test_rejects_symbolic_link_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'link.zip'
            info = zipfile.ZipInfo('tool/link')
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr(info, '../outside')
            with self.assertRaisesRegex(RuntimeError, 'symbolic link'):
                windows_setup.safe_extract_zip(archive, root / 'dest')


    def test_rejects_windows_reserved_device_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('NUL.txt', 'CON', 'COM1.bin', 'LPT9.dll', 'CONIN$.txt'):
                archive = root / ('device-' + str(len(name)) + '.zip')
                with zipfile.ZipFile(archive, 'w') as bundle:
                    bundle.writestr(name, b'no')
                with self.assertRaisesRegex(RuntimeError, 'unsafe path'):
                    windows_setup.safe_extract_zip(archive, root / ('dest-' + str(len(name))))

    def test_enforces_uncompressed_size_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'large.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('large.bin', b'x' * 100)
            with self.assertRaisesRegex(RuntimeError, 'size limit'):
                windows_setup.safe_extract_zip(archive, root / 'dest', max_uncompressed=50)



    def test_chdman_installer_pins_hash_and_runs_silent_mame_installer(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'stage'
            stage.mkdir()
            tool_dir = root / 'tools' / 'chdman'
            tool_exe = tool_dir / 'chdman.exe'
            calls = []

            def fake_download(url, path):
                calls.append(('download', url))
                path.write_bytes(b'verified fixture')

            def fake_run(command, **kwargs):
                calls.append(('run', command))
                tool_dir.mkdir(parents=True, exist_ok=True)
                tool_exe.write_bytes(b'chdman fixture')
                return windows_setup.subprocess.CompletedProcess(command, 0, '', '')

            with patch.object(windows_setup, 'CHDMAN_DIR', tool_dir), \
                    patch.object(windows_setup, 'CHDMAN_EXE', tool_exe), \
                    patch.object(windows_setup, 'download', side_effect=fake_download), \
                    patch.object(windows_setup, 'verify_sha256') as verify, \
                    patch.object(windows_setup.subprocess, 'run', side_effect=fake_run), \
                    patch.object(windows_setup.shutil, 'which', return_value=None), \
                    patch.dict(windows_setup.os.environ, {}, clear=True):
                windows_setup.install_chdman(stage)

            self.assertTrue(tool_exe.is_file())
            self.assertEqual(calls[0], ('download', windows_setup.MAME_URL))
            verify.assert_called_once_with(stage / f'mame{windows_setup.MAME_VERSION.replace(".", "")}_x64.exe',
                                           windows_setup.MAME_SHA256)
            install_args = calls[1][1]
            self.assertIn('-y', install_args)
            self.assertIn(f'-o{tool_dir}', install_args)


class EmsdkBootstrapPinTests(unittest.TestCase):
    def test_bootstrap_uses_immutable_revision_not_moving_main(self):
        self.assertRegex(windows_setup.EMSDK_BOOTSTRAP_REVISION, r'^[0-9a-f]{7,40}$')
        self.assertNotIn('refs/heads/main',
                         f'https://codeload.github.com/emscripten-core/emsdk/zip/{windows_setup.EMSDK_BOOTSTRAP_REVISION}')

    def test_install_emsdk_extracts_pinned_bootstrap_and_installs_pinned_sdk(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'stage'
            stage.mkdir()
            emsdk = root / 'tools' / 'emsdk'
            calls = []

            def fake_download(url, path):
                calls.append(url)
                path.write_bytes(b'fixture')

            def fake_extract(archive, destination):
                extracted = destination / f'emsdk-{windows_setup.EMSDK_BOOTSTRAP_REVISION}'
                extracted.mkdir()
                (extracted / 'emsdk.py').write_text('# pinned fixture')

            def fake_run(*args, **kwargs):
                calls.append(args)

            with patch.object(windows_setup, 'EMSDK', emsdk), \
                    patch.object(windows_setup, 'download', side_effect=fake_download), \
                    patch.object(windows_setup, 'safe_extract_zip', side_effect=fake_extract), \
                    patch.object(windows_setup, 'verify_sha256') as verify, \
                    patch.object(windows_setup, 'run', side_effect=fake_run), \
                    patch.object(windows_setup, 'tools_env', return_value={}):
                windows_setup.install_emsdk(stage)

            verify.assert_called_once_with(stage / 'emsdk.zip', windows_setup.EMSDK_BOOTSTRAP_SHA256)
            self.assertTrue((emsdk / 'emsdk.py').is_file())
            self.assertIn(windows_setup.EMSDK_BOOTSTRAP_REVISION, calls[0])
            self.assertNotIn('refs/heads/main', calls[0])
            self.assertEqual(len(calls), 3)  # download, install, activate
            self.assertIn(windows_setup.EM_VERSION, calls[1])
            self.assertIn('activate', calls[2])

if __name__ == '__main__':
    unittest.main(verbosity=2)
