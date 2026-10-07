"""Validator mutation tests; synthetic events never count as product assertions."""
import contextlib
import copy
import io
import json
import os
import unittest
from unittest.mock import patch

import w1702


def valid_events():
    rows = [{"assertion_id": key, "status": "PASS", "expected": True, "actual": True}
            for key in sorted(w1702.INCREMENT_IDS)]
    return [{"Action": "pass"},
            *[{"Action": "pass", "Test": name} for name in w1702.TESTS],
            {"Action": "output", "Output": "".join("W1702_ASSERTION " + json.dumps(row) + "\n" for row in rows)}]


class HandlerTests(unittest.TestCase):
    def test_valid_inventory(self):
        self.assertEqual(len(w1702.validate_increment(valid_events())), 17)

    def test_zero_assertions_rejected(self):
        with self.assertRaises(ValueError):
            w1702.validate_increment(valid_events()[:-1])

    def test_duplicate_assertion_rejected(self):
        events = valid_events()
        lines = events[-1]["Output"].splitlines()
        lines[-1] = lines[0]
        events[-1]["Output"] = "\n".join(lines)
        with self.assertRaises(ValueError):
            w1702.validate_increment(events)

    def test_failed_skipped_missing_or_wrong_test_rejected(self):
        for event in ({"Action": "fail", "Test": w1702.TESTS[0]},
                      {"Action": "skip", "Test": w1702.TESTS[0]},
                      {"Action": "pass", "Test": "Unrelated"}):
            with self.subTest(event=event), self.assertRaises(ValueError):
                w1702.validate_increment(valid_events() + [event])
        with self.assertRaises(ValueError):
            w1702.validate_increment(valid_events()[1:])

    def test_forged_pass_with_mismatched_value_rejected(self):
        events = valid_events()
        events[-1]["Output"] = events[-1]["Output"].replace('"actual": true', '"actual": false', 1)
        with self.assertRaises(ValueError):
            w1702.validate_increment(events)

    def test_wrong_selectors_and_live_rejected_before_execution(self):
        good = {"RESEARCHOS_TASK_ID": "W17", "RESEARCHOS_CHECK_ID": "W17-02"}
        variants = [{}, dict(good, RESEARCHOS_TASK_ID="W11"), dict(good, RESEARCHOS_CHECK_ID="W17-G03"),
                    dict(good, RESEARCHOS_CASE_ID="C22"), dict(good, RESEARCHOS_MODE="LIVE")]
        for env in variants:
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), patch.object(w1702.sys, "argv", ["w1702.py"]), \
                 patch.object(w1702.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(w1702.main(), 1)
                self.assertEqual(json.loads(output.getvalue())["assertions"], 0)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
