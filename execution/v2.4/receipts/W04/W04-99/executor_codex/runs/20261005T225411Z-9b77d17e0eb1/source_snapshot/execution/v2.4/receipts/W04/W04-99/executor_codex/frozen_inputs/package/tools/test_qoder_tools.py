"""Small stdlib checks. Uses fake Qoder only; never submits a model request."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
import probe_qoder as probe


class QoderToolsChecks(unittest.TestCase):
    def test_probe_inputs_and_disabled_tools(self):
        with tempfile.TemporaryDirectory(prefix='researchos-inputs-') as temp:
            root = Path(temp)
            for name in probe.INPUTS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('test specification', encoding='utf-8')
            argv = probe.build_argv(Path(sys.executable), root)
            self.assertEqual(argv[argv.index('--model') + 1], 'Qwen3.8-Flash')
            self.assertEqual(argv.count('--attachment'), 3)
            self.assertIn('--tools=', argv)
            self.assertIn('--strict-mcp-config', argv)
            self.assertIn('--no-session-persistence', argv)
            self.assertEqual(argv[argv.index('--max-model-request-retries') + 1], '0')
            (root / probe.INPUTS[-1]).unlink()
            with self.assertRaises(ValueError):
                probe.build_argv(Path(sys.executable), root)
        dummy = 'sk-' + 'a' * 20
        self.assertNotIn(dummy, probe.redact('api_key=' + dummy))
        self.assertNotIn('example-token', probe.redact('Bearer example-token'))

    def test_bounded_process_output(self):
        code, out, err, timed_out = probe.run_bounded(
            [sys.executable, '-c', "print('probe fixture')"], Path.cwd(), 5)
        self.assertEqual((code, out.strip(), err, timed_out), (0, 'probe fixture', '', False))

    def test_timeout_kills_own_descendant_and_preserves_unrelated_process(self):
        with tempfile.TemporaryDirectory(prefix='researchos-tree-check-') as temp:
            root = Path(temp)
            marker = root / 'child-must-not-survive.txt'
            child = "import time; from pathlib import Path; time.sleep(1.5); Path(" + repr(str(marker)) + ").write_text('escaped')"
            parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); print('spawned',flush=True); time.sleep(20)"
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])
            try:
                code, out, _, timed_out = probe.run_bounded([sys.executable, '-c', parent], root, 0.8)
                self.assertEqual(code, 124)
                self.assertTrue(timed_out)
                self.assertIn('spawned', out)
                time.sleep(1)
                self.assertFalse(marker.exists(), 'Timed-out probe left a child process running')
                self.assertIsNone(unrelated.poll(), 'Probe cleanup affected an unrelated process')
            finally:
                unrelated.terminate()
                unrelated.wait(timeout=5)

    def test_launcher_print_check_and_missing_model(self):
        shell = shutil.which('pwsh') or shutil.which('powershell.exe')
        if not shell:
            self.skipTest('PowerShell is unavailable')
        with tempfile.TemporaryDirectory(prefix='researchos-launcher-check-') as temp:
            base = Path(temp)
            root = base / 'spec'
            tools = root / 'tools'
            tools.mkdir(parents=True)
            (base / 'research-os').mkdir()
            launcher = tools / 'start_qoder.ps1'
            shutil.copyfile(Path(__file__).with_name('start_qoder.ps1'), launcher)
            (tools / 'validate_package.py').write_text("print('FIXTURE_VALIDATOR_OK')\n", encoding='utf-8')
            (root / 'GOAL_START.txt').write_text('/goal fixture only\n', encoding='utf-8')
            fake = base / 'fake-qoder.ps1'
            command = [shell, '-NoProfile', '-File', str(launcher), '-QoderCli', str(fake),
                       '-PythonExecutable', sys.executable]
            fake.write_text("throw 'PrintOnly must not execute this fixture'\n", encoding='utf-8')
            shown = subprocess.run(command + ['-PrintOnly'], capture_output=True, text=True, timeout=15)
            self.assertEqual(shown.returncode, 0, shown.stderr)
            shown_args = json.loads(shown.stdout)['argv']
            self.assertEqual(shown_args[shown_args.index('--model') + 1], 'Qwen3.8-Flash')
            for model, expected_code in [('   Qwen3.8-Flash   ', 0), ('Qwen3.8-Max', 1)]:
                fake.write_text(
                    "if ($args[0] -eq '--version') { 'fixture-version'; exit 0 }\n"
                    "if ($args[0] -eq '--list-models') { 'MODEL'; '" + model + "'; exit 0 }\n"
                    "throw 'CheckOnly must not start a TUI or submit a prompt'\n", encoding='utf-8')
                checked = subprocess.run(command + ['-CheckOnly'], capture_output=True, text=True, timeout=15)
                self.assertEqual(checked.returncode, expected_code, checked.stdout + checked.stderr)
                self.assertIn('CHECK_ONLY' if expected_code == 0 else 'No model was substituted', checked.stdout + checked.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
