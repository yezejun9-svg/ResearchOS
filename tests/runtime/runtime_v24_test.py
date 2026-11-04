"""Development tests only: no runtime/provider or formal acceptance execution."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("runtime_v24", ROOT / "ops/ci/runtime_v24.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class RuntimeV24PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec_root = os.environ["RESEARCHOS_V24_SPEC_ROOT"]

    def env(self, check="", case="", task="W05", root=None):
        return {"RESEARCHOS_TASK_ID": task, "RESEARCHOS_CHECK_ID": check,
                "RESEARCHOS_CASE_ID": case, "RESEARCHOS_V24_SPEC_ROOT": self.spec_root if root is None else root}

    def assert_blocked(self, report, code, reason):
        self.assertNotEqual(code, 0)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["reason_code"], reason)
        self.assertEqual(report["assertion_ids"], [])
        self.assertEqual(report["passed_assertion_ids"], [])
        self.assertEqual(report["passed_count"], 0)
        self.assertFalse(report["native_executed"])
        self.assertFalse(report["provider_executed"])
        self.assertNotIn('"PASS"', json.dumps(report))

    def test_frozen_live_checks_are_not_run(self):
        for check, mode in runtime.LIVE_CHECK_MODES.items():
            with self.subTest(check=check):
                report, code = runtime.preflight(["--mode", "live"], self.env(check=check))
                self.assert_blocked(report, code, "IMPLEMENTATION_GAP")
                self.assertEqual(report["required_mode"], mode)
                self.assertEqual(report["expected_assertion_ids"], [check])
                self.assertEqual(report["assertions"][0]["status"], "NOT_RUN")
                self.assertTrue(report["assertions"][0]["reason"])

    def test_a04_exact_six_frozen_ids(self):
        report, code = runtime.preflight(["--mode", "live"], self.env(case="A04"))
        self.assert_blocked(report, code, "IMPLEMENTATION_GAP")
        self.assertEqual(report["expected_assertion_ids"], ["A04-01", "A04-02", "A04-03", "A04-04", "A04-05", "A04-06"])
        self.assertEqual([row["assertion_id"] for row in report["assertions"]], report["expected_assertion_ids"])
        self.assertTrue(all(row["status"] == "NOT_RUN" and row["reason"] for row in report["assertions"]))

    def test_mixed_unknown_cross_task_and_fixture_rejected(self):
        for env in [self.env(check="W05-G02", case="A04"), self.env(case="A04", task="W12"),
                    self.env(check="W05-G01"), self.env(check="W05-01"), self.env(check="W05-UNKNOWN"),
                    self.env(case="C11"), self.env(), self.env(case="A04", task="")]:
            with self.subTest(env=env):
                self.assert_blocked(*runtime.preflight(["--mode", "live"], env), "INVALID_SELECTOR")
        self.assert_blocked(*runtime.preflight(["--mode", "fixture"], self.env(case="A04")), "INVALID_MODE")

    def test_missing_relative_and_drifting_spec_rejected(self):
        for root in ["", "spec/v2.0", str(Path(self.spec_root)/"absent")]:
            with self.subTest(root=root):
                self.assert_blocked(*runtime.preflight(["--mode", "live"], self.env(case="A04", root=root)), "SPEC_RESOURCE_MISSING")
        with tempfile.TemporaryDirectory() as tmp:
            for relative in runtime.SPEC_PINS:
                target = Path(tmp)/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(self.spec_root)/relative, target)
            for relative in runtime.SPEC_PINS:
                target = Path(tmp)/relative
                original = target.read_bytes()
                target.write_bytes(original+b" ")
                self.assert_blocked(*runtime.preflight(["--mode", "live"], self.env(case="A04", root=tmp)), "SPEC_HASH_MISMATCH")
                target.write_bytes(original)

    def test_contract_mode_and_roster_drift_rejected(self):
        docs = runtime.load_spec(self.spec_root)
        with patch.object(runtime, "load_spec", return_value=docs):
            case = next(row for row in docs["contracts/acceptance.json"]["cases"] if row["id"]=="A04")
            case["assertions"] = case["assertions"][:-1]
            self.assert_blocked(*runtime.preflight(["--mode", "live"], self.env(case="A04")), "SPEC_CONTRACT_MISMATCH")
        docs = runtime.load_spec(self.spec_root)
        with patch.object(runtime, "load_spec", return_value=docs):
            task = next(row for row in docs["contracts/tasks.json"]["tasks"] if row["task_id"]=="W05")
            next(row for row in task["task_gate_checks"] if row["check_id"]=="W05-G02")["mode"]="FIXTURE"
            self.assert_blocked(*runtime.preflight(["--mode", "live"], self.env(check="W05-G02")), "SPEC_CONTRACT_MISMATCH")

    def test_arbitrary_command_or_pass_file_not_supported(self):
        for extra in [["--command", "anything"], ["--pass-file", "anything.json"]]:
            self.assert_blocked(*runtime.preflight(["--mode", "live"]+extra, self.env(case="A04")), "INVALID_ARGUMENT")

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in ['{"a":1,"a":2}', '{"a":NaN}']:
            with self.assertRaises(ValueError): runtime._json(raw)

    def test_cli_is_nonzero_and_has_no_pass(self):
        lock = json.loads((ROOT/"execution/toolchains/locked.json").read_bytes())["tools"]["python"]
        python = Path(lock["path"])
        self.assertTrue(python.is_absolute())
        self.assertEqual(hashlib.sha256(python.read_bytes()).hexdigest(), lock["sha256"])
        env = dict(os.environ, **self.env(case="A04"))
        result = subprocess.run([str(python), "-X", "utf8", str(ROOT/"ops/ci/runtime_v24.py"), "--mode", "live"],
                                cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assert_blocked(json.loads(result.stdout), result.returncode, "IMPLEMENTATION_GAP")

if __name__ == "__main__":
    unittest.main(verbosity=2)
