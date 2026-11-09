"""Fail-closed controls for evidence validation (no product/provider/GUI calls)."""
import json
from pathlib import Path
import tempfile
import unittest

from parent_gates import Gate, digest, parse_go, save, strict_results, source_delta
from dispatch_parent import main as dispatch, select, PARENT_CHECKS, ROOT
from contextlib import redirect_stdout
import io
import sys


class EvidenceNegatives(unittest.TestCase):
    def test_only_exact_additive_integration_delta_allowed(self):
        old = {"client.go": "aa", "host.go": "bb"}
        allowed = {"descriptive.go": "cc"}
        self.assertTrue(source_delta(old, old | allowed, allowed)["ok"])
        for current in ({"client.go": "aa"}, old | {"client.go": "changed"},
                        old | {"unexpected.go": "cc"}, old | {"descriptive.go": "wrong"}):
            self.assertFalse(source_delta(old, current, allowed)["ok"])

    def test_selector_bridge_preserves_all_six_legacy_tuples(self):
        for task in ("W01", "W02", "W06"):
            for case in ("", "A02"):
                calls = []
                env = {"RESEARCHOS_TASK_ID": task, "RESEARCHOS_CASE_ID": case, "KEEP_MARKER": "unchanged"}
                def fake(argv, **kwargs):
                    calls.append((argv, kwargs))
                    return 37
                self.assertEqual(dispatch(env, fake), 37)
                self.assertEqual(calls, [([sys.executable, "-X", "utf8", str(ROOT / "ops/ci/core_evidence.py")],
                                         {"cwd": ROOT, "env": env})])

    def test_selector_bridge_omitted_task_and_case_forward_legacy(self):
        env = {"KEEP_MARKER": "unchanged"}
        calls = []
        def fake(argv, **kwargs):
            calls.append((argv, kwargs))
            return 37
        self.assertEqual(dispatch(env, fake), 37)
        self.assertEqual(calls, [([sys.executable, "-X", "utf8", str(ROOT / "ops/ci/core_evidence.py")],
                                 {"cwd": ROOT, "env": env})])

    def test_selector_bridge_omitted_task_with_a02_forward_legacy(self):
        env = {"RESEARCHOS_CASE_ID": "A02", "KEEP_MARKER": "unchanged"}
        calls = []
        def fake(argv, **kwargs):
            calls.append((argv, kwargs))
            return 37
        self.assertEqual(dispatch(env, fake), 37)
        self.assertEqual(calls, [([sys.executable, "-X", "utf8", str(ROOT / "ops/ci/core_evidence.py")],
                                 {"cwd": ROOT, "env": env})])

    def test_selector_bridge_refuses_mixed_unknown_before_child(self):
        for task, check, case in (("W02", "W01-G01", ""), ("W01", "W01-G01", "A02"),
                                 ("W06", "W01-G02", ""), ("W01", "W01-G05", ""),
                                 ("W02", "W02-G01", ""), ("W01", "", "C04"), ("UNKNOWN", "", ""),
                                 ("", "W01-G01", "")):
            calls = []
            env = dict(zip(("RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"), (task, check, case)))
            with redirect_stdout(io.StringIO()) as output:
                code = dispatch(env, lambda *args, **kwargs: calls.append(args))
            self.assertEqual((code, calls), (2, []))
            self.assertEqual(json.loads(output.getvalue())["assertion_ids"], [])

    def test_selector_bridge_exact_four_parent_commands(self):
        for check in PARENT_CHECKS:
            self.assertEqual(select("W01", check, ""), [sys.executable, "-B", "-X", "utf8",
                            str(ROOT / "qualification/v2.4/qualify.py"), "--check-id", check])

    def test_boolean_and_inventory_fail_closed(self):
        required = ["same_session", "cancel", "self_verify_refused"]
        good = [{"id": name, "ok": True} for name in required]
        self.assertTrue(strict_results(good, required))
        for bad in ([], good[:-1], good + [good[0]],
                    [dict(row, ok="true") for row in good],
                    [dict(row, ok=1) for row in good],
                    [dict(row, ok=False) if row["id"] == "cancel" else row for row in good],
                    [None], [{"ok": True}]):
            with self.subTest(bad=bad):
                self.assertFalse(strict_results(bad, required))

    def test_go_zero_assertion_skip_and_failure_never_pass(self):
        good = [{"Action": "pass", "Test": "TestCancel"}, {"Action": "pass"}]
        encode = lambda rows: "\n".join(json.dumps(row) for row in rows)
        self.assertTrue(parse_go(encode(good), ["TestCancel"])["ok"])
        for rows in ([], [{"Action": "pass"}], good + [good[0]],
                     [{"Action": "skip", "Test": "TestCancel"}, {"Action": "pass"}],
                     good + [{"Action": "fail", "Test": "TestCancel/subcase"}]):
            with self.subTest(rows=rows):
                self.assertFalse(parse_go(encode(rows), ["TestCancel"])["ok"])

    def test_go_split_raw_assertions_preserve_true_result(self):
        assertion = "W06_ASSERTION " + json.dumps({"assertion_id": "refused", "status": "PASS", "actual": "no write"}) + "\n"
        events = [{"Action": "output", "Test": "TestCancel", "Output": assertion[:38]},
                  {"Action": "output", "Test": "TestCancel", "Output": assertion[38:]},
                  {"Action": "pass", "Test": "TestCancel"}, {"Action": "pass"}]
        raw = "\n".join(map(json.dumps, events))
        result = parse_go(raw, ["TestCancel"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["assertions"], [{"assertion_id": "refused", "status": "PASS", "actual": "no write"}])
        self.assertFalse(parse_go(raw.replace("PASS", "FAIL"), ["TestCancel"])["ok"])

    def test_empty_or_truncated_assertion_is_not_success(self):
        raw = "\n".join(map(json.dumps, [{"Action": "output", "Test": "TestX", "Output": 'W06_ASSERTION {"status":'},
                                        {"Action": "pass", "Test": "TestX"}, {"Action": "pass"}]))
        self.assertFalse(parse_go(raw, ["TestX"])["ok"])

    def test_raw_input_change_and_missing_input_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            evidence = root / "raw.json"
            evidence.write_text('{"critical_fail":0,"assertions":[]}', encoding="utf-8")
            expected = digest(evidence)
            gate = Gate.__new__(Gate)
            gate.inputs = {}
            self.assertEqual(gate.input("raw.json", expected, root), evidence)
            evidence.write_text('{"critical_fail":0,"assertions":[{"pass":true}]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "INPUT_HASH_DRIFT"):
                gate.input("raw.json", expected, root)
            with self.assertRaises(FileNotFoundError):
                gate.input("missing.json", expected, root)

    def test_immutable_record_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.json"
            save(path, {"status": "BLOCKED"})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                save(path, {"status": "PASS"})
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
