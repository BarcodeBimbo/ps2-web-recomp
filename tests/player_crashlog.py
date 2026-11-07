"""Player shell: automatic crash logs, no debug-only chrome."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / 'web' / 'shell.html').read_text(encoding='utf-8')


class PlayerCrashLog(unittest.TestCase):
    def test_shell_has_required_markers(self):
        self.assertEqual(SHELL.count('{{{ SCRIPT }}}'), 1)
        self.assertIn('class="control-settings"', SHELL)

    def test_auto_crash_log_helpers(self):
        self.assertIn('async function saveCrashLog', SHELL)
        self.assertIn("saveCrashLog(reason || 'halt'", SHELL)
        self.assertIn('no-drawing-after-1800-frames', SHELL)
        self.assertIn('frame-callback-stall-30s', SHELL)
        self.assertIn('frame-callback-stall-120s', SHELL)
        self.assertIn('frameStallLimitMs', SHELL)
        self.assertIn('discWaiting', SHELL)
        self.assertIn('cyberarcade-crash-', SHELL)

    def test_debug_chrome_removed(self):
        self.assertNotIn('id="capture-prompt"', SHELL)
        self.assertNotIn('id="stats-toggle"', SHELL)
        # Crash logs save automatically on halt/stall; no manual debug button.
        self.assertIn('crash log was saved automatically', SHELL)
        self.assertIn('saveCrashLog', SHELL)


if __name__ == '__main__':
    unittest.main(verbosity=2)
