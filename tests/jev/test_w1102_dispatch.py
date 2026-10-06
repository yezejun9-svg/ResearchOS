"""Instrumented wrapper fixtures only; never executes the legacy admission."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('w1102_handler', Path(__file__).with_name('w1102_check.py'))
handler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handler)
LEGACY = (handler.ROOT/'tests/jev/admit_frozen_live.py').read_bytes()
CHILD_OUT = '{"status":"PASS","measurement_mode":"READ_ONLY_ADMISSION_OF_PAST_LIVE"}\n旧输出\n'
CHILD_ERR = 'preserved child stderr\n'


class DispatchFixtures(unittest.TestCase):
    def run_fixture(self, name, selector, extra=(), forward=True, tamper=None):
        with tempfile.TemporaryDirectory(prefix='w1102-dispatch-fixture-') as folder:
            root = Path(folder)
            legacy = root/'tests/jev/admit_frozen_live.py'
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(LEGACY if tamper != 'before' else b'changed fixture')
            env = {'PRESERVE_ENV_VALUE': 'fixture-only'}
            env.update(selector)
            calls = []

            def instrumented_child(argv, **kwargs):
                calls.append((argv, kwargs))
                print(CHILD_OUT, end='')
                print(CHILD_ERR, end='', file=handler.sys.stderr)
                if tamper == 'after':
                    legacy.write_bytes(b'changed fixture after forwarding')
                return SimpleNamespace(returncode=7)

            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(handler, 'ROOT', root), patch.dict(os.environ, env, clear=True), \
                 patch.object(handler.sys, 'argv', ['w1102_check.py', *extra]), \
                 patch.object(handler.subprocess, 'run', instrumented_child), \
                 contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = handler.main()
            if forward:
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0], [handler.sys.executable, '-X', 'utf8',
                                              'tests/jev/admit_frozen_live.py', *extra])
                self.assertEqual(calls[0][1], {'cwd': root, 'env': env})
                self.assertEqual(stdout.getvalue(), CHILD_OUT)
                self.assertEqual(code, 1 if tamper == 'after' else 7)
                if tamper != 'after':
                    self.assertEqual(stderr.getvalue(), CHILD_ERR)
                reports = list(root.glob('execution/v2.4/receipts/W11/W11-02/legacy-forward/*/report.json'))
                self.assertEqual(len(reports), 1)
                record = json.loads(reports[0].read_text())
                self.assertEqual(record['legacy_sha256_before'], handler.LEGACY_SHA256)
                self.assertEqual(record['source_unchanged'], tamper != 'after')
                self.assertEqual(record['child_exit_code'], 7)
            else:
                self.assertEqual(calls, [])
                self.assertEqual(code, 1)
                self.assertEqual(stdout.getvalue(), '')
                self.assertTrue(stderr.getvalue())
            print('W1102_DISPATCH_ASSERTION ' + json.dumps(dict(assertion_id=name,
                expected='routing/argv/env/streams/exit/hash invariants preserved',
                actual='routing/argv/env/streams/exit/hash invariants preserved',
                status='PASS', mode='FIXTURE_INSTRUMENTED_SUBPROCESS', real_child_executed=False)))

    def test_legacy_selectors(self):
        for check in ('W11-G02', 'W11-G03', 'W11-G04'):
            self.run_fixture('FORWARD-'+check, dict(RESEARCHOS_TASK_ID='W11',
                             RESEARCHOS_CHECK_ID=check, RESEARCHOS_CASE_ID=''))
        self.run_fixture('FORWARD-A08', dict(RESEARCHOS_TASK_ID='W11',
                         RESEARCHOS_CHECK_ID='', RESEARCHOS_CASE_ID='A08'))
        self.run_fixture('FORWARD-DEFAULT', {})
        self.run_fixture('FORWARD-ARGV', dict(RESEARCHOS_TASK_ID='W11',
                         RESEARCHOS_CHECK_ID='W11-G02'), ('--evidence-root', 'fixture path with 空格'))

    def test_refused_selectors(self):
        for name, check, case, extra in (
            ('REJECT-NEW-MIXED', 'W11-02', 'A08', ()),
            ('REJECT-OLD-MIXED', 'W11-G02', 'A08', ()),
            ('REJECT-UNKNOWN', 'W11-unknown', '', ()),
            ('REJECT-NEW-ARGS', 'W11-02', '', ('--evidence-root', 'unused')),
        ):
            self.run_fixture(name, dict(RESEARCHOS_TASK_ID='W11',
                             RESEARCHOS_CHECK_ID=check, RESEARCHOS_CASE_ID=case), extra, forward=False)

    def test_pinned_legacy_before_and_after(self):
        selector = dict(RESEARCHOS_TASK_ID='W11', RESEARCHOS_CHECK_ID='W11-G02')
        self.run_fixture('REJECT-LEGACY-HASH-BEFORE', selector, forward=False, tamper='before')
        self.run_fixture('REJECT-LEGACY-HASH-AFTER', selector, tamper='after')


if __name__ == '__main__':
    unittest.main()
