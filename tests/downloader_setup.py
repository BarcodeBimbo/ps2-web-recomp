"""Unified Windows setup sequencing, caching and failure handling (mocked installs)."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import windows_setup as setup
import downloader_runtime as runtime

class DownloaderSetup(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.msys=self.root/'tools/msys64';self.bin=self.msys/'clang64/bin'
  self.folder=self.root/'downloader';self.folder.mkdir()
  for name in ['package.json','package-lock.json']: (self.folder/name).write_text('{}')
  self.browser=False;self.commands=[];self.fail_npm=False
  for obj,name,value in [(setup,'ROOT',self.root),(setup,'MSYS',self.msys),(setup,'BIN',self.bin),(runtime,'ROOT',self.root)]:
   mock=patch.object(obj,name,value);mock.start();self.addCleanup(mock.stop)
  mock=patch.object(setup.subprocess,'run',side_effect=self.invoke);mock.start();self.addCleanup(mock.stop)
  mock=patch.object(setup,'run_command',side_effect=self.invoke);mock.start();self.addCleanup(mock.stop)
 def touch(self,p):p.parent.mkdir(parents=True,exist_ok=True);p.touch()
 def invoke(self,command,**kwargs):
  command=list(map(str,command));self.commands.append(command)
  if command[0].endswith('bash.exe'):
   self.touch(self.bin/'node.exe');self.touch(self.bin.parent/'lib/node_modules/npm/bin/npm-cli.js')
  elif 'ci' in command:
   if self.fail_npm:raise subprocess.CalledProcessError(1,command)
   self.touch(self.folder/'node_modules/phantomwright-driver/cli.js')
  elif 'install' in command:self.browser=True
  elif command[-1].endswith('check-browser.mjs'):
   if not self.browser and kwargs.get('check'):raise subprocess.CalledProcessError(1,command)
   return SimpleNamespace(returncode=0 if self.browser else 1)
  return SimpleNamespace(returncode=0)
 def test_first_start_installs_everything_then_reuses(self):
  setup.install_downloader()
  self.assertTrue(any(c[0].endswith('bash.exe') for c in self.commands))
  self.assertTrue(any('ci' in c for c in self.commands));self.assertTrue(self.browser)
  chosen=(runtime.node_executable() or '').lower()
  self.assertTrue(chosen.endswith('node.exe') or chosen.endswith('/node') or chosen.endswith('\\node'))
  self.assertEqual(runtime.runtime_env()['PLAYWRIGHT_BROWSERS_PATH'],str(self.root/'tools/downloader-browsers'))
  self.commands.clear();setup.install_downloader()
  self.assertFalse(any('ci' in c or 'install' in c or c[0].endswith('bash.exe') for c in self.commands))
 def test_missing_browser_is_repaired_without_npm_reinstall(self):
  setup.install_downloader();self.browser=False;self.commands.clear();setup.install_downloader()
  self.assertTrue(self.browser);self.assertFalse(any('ci' in c for c in self.commands))
 def test_changed_lockfile_reinstalls_dependencies(self):
  setup.install_downloader();self.commands.clear();(self.folder/'package-lock.json').write_text('{"changed":true}')
  setup.install_downloader();self.assertTrue(any('ci' in c for c in self.commands))
 def test_failed_install_is_not_stamped(self):
  self.fail_npm=True
  with self.assertRaises(subprocess.CalledProcessError):setup.install_downloader()
  self.assertFalse((self.folder/'.installed-dependencies').exists())

class StartupFallback(unittest.TestCase):
 def test_browser_install_timeout_still_starts_the_host(self):
  import panel
  import setup_progress
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);tools=root/'tools';tools.mkdir()
   fake=SimpleNamespace(locking=lambda *args:None,LK_NBLCK=1)
   with patch.dict(sys.modules,{'msvcrt':fake}),patch.object(setup,'TOOLS',tools),patch.object(setup_progress,'ROOT',root),patch.object(setup,'install_msys'),patch.object(setup,'install_emsdk'),patch.object(setup,'install_wgpu'),patch.object(setup,'install_chdman'),patch.object(setup,'install_downloader',side_effect=TimeoutError('fixture browser timeout')),patch.object(panel,'main') as host:
    setup_progress.REPORT.clear();setup.main();host.assert_called_once_with(open_browser=True)
    self.assertTrue(any(item['status']=='failed' and 'Store' in item['stage'] for item in setup_progress.REPORT))

if __name__=='__main__':unittest.main(verbosity=2)
