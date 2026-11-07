"""Real child output capture, command failures/timeouts and stage reports."""
from pathlib import Path
import contextlib,io,json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import setup_progress as progress
class Reporting(unittest.TestCase):
 def test_output_failure_timeout_and_report(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(progress,'ROOT',Path(temp)):
   progress.REPORT.clear();output=io.StringIO()
   with contextlib.redirect_stdout(output):
    progress.phase('Fixture install',lambda:progress.run_command([sys.executable,'-u','-c','print("download done; extracting")'],cwd=temp,timeout=3))
    with self.assertRaises(subprocess.CalledProcessError):progress.run_command([sys.executable,'-c','raise SystemExit(3)'],cwd=temp,timeout=3)
    with self.assertRaises(TimeoutError):progress.run_command([sys.executable,'-c','import time;time.sleep(10)'],cwd=temp,timeout=.2)
   with self.assertRaises(TimeoutError):progress.run_command([sys.executable,'-c','import time;time.sleep(10)'],cwd=temp,timeout=3,idle_timeout=.2)
   self.assertIn('download done; extracting',output.getvalue())
   report=json.loads((Path(temp)/'tools/setup-report.json').read_text());self.assertEqual(report[0]['status'],'complete')
   self.assertIn('download done; extracting',(Path(temp)/'tools/setup.log').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
