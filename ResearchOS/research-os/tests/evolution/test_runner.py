"""A success exit or a caller-written PASS cannot manufacture test coverage."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evolution_runner', Path(__file__).resolve().parents[2] / 'ops/ci/evolution.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvidenceFence(unittest.TestCase):
    def row(self, **changes):
        row = dict(assertion_id='C09-01', expected=True, actual=True, status='PASS', evidence='native', scope='W16_G02_FIXTURE_ONLY')
        row.update(changes)
        return ('W16_ASSERTION ' + json.dumps(row) + '\n').encode()

    def test_exact_real_success(self):
        self.assertTrue(runner.verify(self.row(), 0, ['C09-01'])[0])

    def test_non_success_evidence_rejected(self):
        for raw, code, expected in [(b'', 0, ['C09-01']), (b'', 0, []), (self.row(), 1, ['C09-01']), (self.row() * 2, 0, ['C09-01']), (self.row(), 0, ['C10-01']), (self.row(actual=False), 0, ['C09-01']), (self.row(status='FAIL'), 0, ['C09-01']), (self.row(scope='LIVE'), 0, ['C09-01']), (b'W16_ASSERTION invalid', 0, ['C09-01'])]:
            with self.subTest(raw=raw, code=code, expected=expected):
                self.assertFalse(runner.verify(raw, code, expected)[0])


if __name__ == '__main__':
    unittest.main()
