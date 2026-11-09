import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-routing-20261104')

FILES = {}
FILES['tests/runtime/check/legacy.go'] = r'''package main

// Exact selectors keep development suites, accepted legacy fixtures, and v2.4 LIVE
// requirements separate. An unknown selector must never borrow another suite's assertions.
import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
)

type runtimeRoute string

const (
    runtimeServed runtimeRoute = "served"
    runtimeFixture runtimeRoute = "legacy-fixture"
    runtimeV24Live runtimeRoute = "v24-live-preflight"
)

func selectRuntimeRoute(task, check, caseID string) (runtimeRoute, error) {
    if (check == "") == (caseID == "") {
        return "", fmt.Errorf("exactly one check_id or case_id is required")
    }
    if task == "W12" && check == "" && caseID == "C11" {
        return runtimeFixture, nil
    }
    if task != "W05" {
        return "", fmt.Errorf("unsupported test.runtime task/selector combination")
    }
    if caseID == "A04" {
        return runtimeV24Live, nil
    }
    switch check {
    case "W05-01", "W05-02":
        return runtimeServed, nil
    case "W05-G01":
        return runtimeFixture, nil
    case "W05-G02", "W05-H08", "W05-P01", "W05-U02":
        return runtimeV24Live, nil
    }
    return "", fmt.Errorf("unsupported test.runtime task/selector combination")
}

// Resolve the interpreter from the project lock on every invocation. Neither PATH
// nor an unverified environment override can select a different Python binary.
func lockedPython(root string) (string, error) {
    raw, err := os.ReadFile(filepath.Join(root, "execution", "toolchains", "locked.json"))
    if err != nil { return "", fmt.Errorf("read Python tool lock: %w", err) }
    var lock struct { Tools map[string]struct { Path string `json:"path"`; SHA256 string `json:"sha256"` } `json:"tools"` }
    if err = json.Unmarshal(raw, &lock); err != nil { return "", fmt.Errorf("parse Python tool lock: %w", err) }
    tool, exists := lock.Tools["python"]
    digest, hashErr := hex.DecodeString(tool.SHA256)
    if !exists || !filepath.IsAbs(tool.Path) || hashErr != nil || len(digest) != sha256.Size {
        return "", fmt.Errorf("Python lock requires an absolute path and SHA256")
    }
    info, err := os.Stat(tool.Path)
    if err != nil || !info.Mode().IsRegular() { return "", fmt.Errorf("locked Python is not a regular file") }
    binary, err := os.ReadFile(tool.Path)
    if err != nil { return "", fmt.Errorf("read locked Python: %w", err) }
    actual := sha256.Sum256(binary)
    if !strings.EqualFold(hex.EncodeToString(actual[:]), tool.SHA256) {
        return "", fmt.Errorf("locked Python SHA256 mismatch")
    }
    return tool.Path, nil
}

func runtimePythonCommand(root, script, mode string) (*exec.Cmd, error) {
    python, err := lockedPython(root)
    if err != nil { return nil, err }
    cmd := exec.Command(python, "-X", "utf8", filepath.Join(root, filepath.FromSlash(script)), "--mode", mode)
    cmd.Dir = root
    cmd.Env = os.Environ()
    return cmd, nil
}

func runtimeRoutingBlocked(reason, detail string) {
    _ = json.NewEncoder(os.Stdout).Encode(map[string]any{
        "status": "BLOCKED", "reason_code": reason, "reason": detail,
        "assertion_ids": []string{}, "passed_assertion_ids": []string{}, "passed": false,
    })
}

// Keep this entry point for main.go and the served W05-01/02 suites.
func routeLegacy() (int, bool) {
    route, err := selectRuntimeRoute(os.Getenv("RESEARCHOS_TASK_ID"), os.Getenv("RESEARCHOS_CHECK_ID"), os.Getenv("RESEARCHOS_CASE_ID"))
    if err != nil { runtimeRoutingBlocked("INVALID_SELECTOR", err.Error()); return 2, true }
    if route == runtimeServed { return 0, false }
    script, mode := "ops/ci/runtime.py", "fixture"
    if route == runtimeV24Live { script, mode = "ops/ci/runtime_v24.py", "live" }
    cmd, err := runtimePythonCommand(repoRoot(), script, mode)
    if err != nil { runtimeRoutingBlocked("TOOLCHAIN_ERROR", err.Error()); return 3, true }
    cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
    if err = cmd.Run(); err != nil {
        if exit, isExit := err.(*exec.ExitError); isExit { return exit.ExitCode(), true }
        runtimeRoutingBlocked("TOOLCHAIN_ERROR", err.Error())
        return 3, true
    }
    return 0, true
}

type runtimeRouteRow struct { task, check, caseID string; want runtimeRoute; valid bool }

func runtimeRouteRows() []runtimeRouteRow {
    return []runtimeRouteRow{
        {"W05", "W05-01", "", runtimeServed, true},
        {"W05", "W05-02", "", runtimeServed, true},
        {"W05", "W05-G01", "", runtimeFixture, true},
        {"W12", "", "C11", runtimeFixture, true},
        {"W05", "W05-G02", "", runtimeV24Live, true},
        {"W05", "W05-H08", "", runtimeV24Live, true},
        {"W05", "W05-P01", "", runtimeV24Live, true},
        {"W05", "W05-U02", "", runtimeV24Live, true},
        {"W05", "", "A04", runtimeV24Live, true},
        {"W12", "W05-G01", "", "", false},
        {"W12", "", "A04", "", false},
        {"W05", "", "C11", "", false},
        {"W05", "W05-01", "A04", "", false},
        {"W05", "W05-G02", "A04", "", false},
        {"W05", "W99-DOES-NOT-EXIST", "", "", false},
        {"W12", "", "", "", false},
        {"W05", "", "", "", false},
        {"", "", "A04", "", false},
        {"", "W05-01", "", "", false},
        {"", "", "", "", false},
    }
}

func runtimeRoutingMismatches() []string {
    bad := []string{}
    for _, row := range runtimeRouteRows() {
        got, err := selectRuntimeRoute(row.task, row.check, row.caseID)
        if (err == nil) != row.valid || got != row.want {
            bad = append(bad, fmt.Sprintf("%s/%s/%s: got %s error=%v, want %s valid=%t", row.task, row.check, row.caseID, got, err, row.want, row.valid))
        }
    }
    return bad
}

func routingTruthTableOK() {
    bad := runtimeRoutingMismatches()
    ok("W0501-ROUTING-TRUTH-TABLE", len(bad) == 0, bad)
}
'''

FILES['tests/runtime/check/routing_test.go'] = r'''package main

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"
    "testing"
)

// These tests never call main, boot, a provider, or the old suite's scratch cleanup.
func TestRuntimeExactRoutes(t *testing.T) {
    for _, row := range runtimeRouteRows() {
        t.Run(row.task+"/"+row.check+"/"+row.caseID, func(t *testing.T) {
            got, err := selectRuntimeRoute(row.task, row.check, row.caseID)
            if (err == nil) != row.valid || got != row.want { t.Fatalf("route=%s err=%v; want=%s valid=%t", got, err, row.want, row.valid) }
        })
    }
}

func TestRuntimeLockedPython(t *testing.T) {
    root := t.TempDir()
    lockDir := filepath.Join(root, "execution", "toolchains")
    if err := os.MkdirAll(lockDir, 0700); err != nil { t.Fatal(err) }
    tool := filepath.Join(root, "python.exe")
    content := []byte("inert test bytes; never executed")
    if err := os.WriteFile(tool, content, 0600); err != nil { t.Fatal(err) }
    sum := sha256.Sum256(content)
    digest := hex.EncodeToString(sum[:])
    writeLock := func(value any) {
        t.Helper()
        raw, err := json.Marshal(value); if err != nil { t.Fatal(err) }
        if err = os.WriteFile(filepath.Join(lockDir, "locked.json"), raw, 0600); err != nil { t.Fatal(err) }
    }
    pythonLock := func(path, hash string) any { return map[string]any{"tools": map[string]any{"python": map[string]string{"path":path,"sha256":hash}}} }
    for _, tc := range []struct{name string; value any; good bool}{
        {"valid", pythonLock(tool,digest), true},
        {"missing-tool", map[string]any{"tools":map[string]any{}}, false},
        {"relative-path", pythonLock("python.exe",digest), false},
        {"missing-binary", pythonLock(filepath.Join(root,"absent.exe"),digest), false},
        {"directory", pythonLock(root,digest), false},
        {"bad-digest", pythonLock(tool,"bad"), false},
        {"mismatched-digest", pythonLock(tool,string(make([]byte,64))), false},
        {"wrong-digest", pythonLock(tool,"0000000000000000000000000000000000000000000000000000000000000000"), false},
    } {
        t.Run(tc.name,func(t *testing.T){writeLock(tc.value); got,err:=lockedPython(root); if (err==nil)!=tc.good {t.Fatalf("got=%q err=%v",got,err)}; if tc.good && got!=tool {t.Fatalf("unlocked tool %q",got)} })
    }
    writeLock(pythonLock(tool,digest))
    t.Setenv("RESEARCHOS_PYTHON",filepath.Join(root,"untrusted.exe"))
    cmd, err := runtimePythonCommand(root,"ops/ci/runtime_v24.py","live")
    if err != nil { t.Fatal(err) }
    if cmd.Path != tool || cmd.Dir != root || len(cmd.Args)!=6 || cmd.Args[3]!=filepath.Join(root,"ops","ci","runtime_v24.py") || cmd.Args[5]!="live" {t.Fatalf("incorrect locked command: %#v",cmd)}
    if err := os.Remove(filepath.Join(lockDir,"locked.json")); err != nil {t.Fatal(err)}
    if _,err = lockedPython(root);err==nil {t.Fatal("missing lock accepted")}
}
'''

FILES['ops/ci/runtime_v24.py'] = r'''"""Fail-closed v2.4 runtime LIVE routing preflight; not a formal runtime driver.

No provider, native process, external command, or caller-supplied result is run/read.
The dispatcher captures this report. Zero assertions pass until a real driver exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

SPEC_PINS = {
    "PACKAGE_MANIFEST.json": "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964",
    "contracts/execution.plan.json": "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17",
    "contracts/tasks.json": "37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4",
    "contracts/acceptance.json": "ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66",
}
LIVE_CHECK_MODES = {
    "W05-G02": "LIVE_WINDOWS_AND_SERVICE",
    "W05-H08": "LIVE_WINDOWS", "W05-P01": "LIVE_WINDOWS", "W05-U02": "LIVE_WINDOWS",
}
A04_IDS = [f"A04-{i:02d}" for i in range(1, 7)]
GAP = "The current Mu runtime has no v2.4 formal LIVE driver for this selector. Native/provider execution and independent acceptance were not run."

class PreflightError(ValueError):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PreflightError("INVALID_ARGUMENT", message)

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def _json(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")))

def _one(rows, predicate, label):
    found = [row for row in rows if predicate(row)]
    if len(found) != 1:
        raise PreflightError("SPEC_CONTRACT_MISMATCH", f"expected one {label}")
    return found[0]

def load_spec(root_value):
    if not root_value or not Path(root_value).is_absolute():
        raise PreflightError("SPEC_RESOURCE_MISSING", "RESEARCHOS_V24_SPEC_ROOT must be the registry-bound absolute frozen v2.4 root; no fallback is allowed")
    root = Path(root_value)
    docs = {}
    for relative, expected in SPEC_PINS.items():
        try:
            raw = (root / relative).read_bytes()
        except OSError as error:
            raise PreflightError("SPEC_RESOURCE_MISSING", f"cannot read frozen {relative}: {error.strerror}") from error
        if hashlib.sha256(raw).hexdigest() != expected:
            raise PreflightError("SPEC_HASH_MISMATCH", f"frozen hash mismatch: {relative}")
        try:
            docs[relative] = _json(raw)
        except (ValueError, UnicodeError) as error:
            raise PreflightError("SPEC_CONTRACT_MISMATCH", f"invalid frozen JSON: {relative}") from error
    manifest = docs["PACKAGE_MANIFEST.json"]
    if manifest.get("package_id") != "researchos-implementation-spec" or manifest.get("package_version") != "2.4.0":
        raise PreflightError("SPEC_CONTRACT_MISMATCH", "expected ResearchOS specification 2.4.0")
    for relative in SPEC_PINS:
        if relative == "PACKAGE_MANIFEST.json":
            continue
        entry = _one(manifest["files"], lambda row: row.get("path") == relative, relative+" manifest entry")
        if entry.get("sha256") != SPEC_PINS[relative] or entry.get("size_bytes") != (root / relative).stat().st_size:
            raise PreflightError("SPEC_CONTRACT_MISMATCH", f"manifest binding mismatch: {relative}")
    return docs

def frozen_selection(docs, task_id, check_id, case_id):
    tasks = docs["contracts/tasks.json"]
    task = _one(tasks["tasks"], lambda row: row.get("task_id") == task_id, "W05 task")
    selection = tasks["verification_command_selection"]
    if check_id:
        gate = _one(task["task_gate_checks"], lambda row: row.get("check_id") == check_id, "runtime check")
        binding = _one(selection["parent_check_bindings"], lambda row: row.get("task_id") == task_id and row.get("check_id") == check_id, "runtime check binding")
        if gate.get("mode") != LIVE_CHECK_MODES[check_id] or binding.get("expected_assertion_ids") != [check_id] or binding.get("key") != "test.runtime":
            raise PreflightError("SPEC_CONTRACT_MISMATCH", "runtime check mode/assertion binding mismatch")
        return gate["mode"], [{"id": check_id, "check": gate["check"], "expected": gate["expected"]}]
    case = _one(docs["contracts/acceptance.json"]["cases"], lambda row: row.get("id") == case_id, "A04 case")
    binding = _one(selection["formal_case_bindings"], lambda row: row.get("task_id") == task_id and row.get("case_id") == case_id, "A04 formal binding")
    if (case.get("mode") != "LIVE_WINDOWS" or [row.get("id") for row in case["assertions"]] != A04_IDS
            or binding.get("expected_assertion_ids") != A04_IDS or binding.get("key") != "test.runtime"
            or case_id not in task["owned_acceptance_ids"]):
        raise PreflightError("SPEC_CONTRACT_MISMATCH", "A04 requires exactly its six frozen LIVE assertions")
    return case["mode"], case["assertions"]

def preflight(argv=None, environ=None):
    env = os.environ if environ is None else environ
    report = {"command": "test.runtime", "driver": "v24-live-gap-preflight", "status": "BLOCKED",
              "passed": False, "assertion_ids": [], "passed_assertion_ids": [],
              "assertions": [], "expected_assertion_ids": [], "passed_count": 0,
              "native_executed": False, "provider_executed": False, "independent_acceptance": "NOT_RUN"}
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--mode", required=True)
        args = parser.parse_args(argv)
        task, check, case = (env.get(name, "") for name in ("RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"))
        report.update(task_id=task, check_id=check, case_id=case, requested_mode=args.mode)
        if task != "W05" or (bool(check) == bool(case)) or (check and check not in LIVE_CHECK_MODES) or (case and case != "A04"):
            raise PreflightError("INVALID_SELECTOR", "require exact W05 plus one of G02/H08/P01/U02 or case A04; mixed/unknown selectors are rejected")
        if args.mode != "live":
            raise PreflightError("INVALID_MODE", "v2.4 LIVE requirements cannot run or pass in fixture mode")
        docs = load_spec(env.get("RESEARCHOS_V24_SPEC_ROOT", ""))
        required_mode, assertions = frozen_selection(docs, task, check, case)
        report.update(required_mode=required_mode, spec_version="2.4.0", spec_root=str(Path(env["RESEARCHOS_V24_SPEC_ROOT"]).resolve()), spec_sha256=dict(SPEC_PINS),
                      expected_assertion_ids=[row["id"] for row in assertions],
                      assertions=[{"assertion_id": row["id"], "check": row["check"], "expected": row["expected"], "status": "NOT_RUN", "reason": GAP} for row in assertions],
                      reason_code="IMPLEMENTATION_GAP", reason=GAP)
        return report, 1
    except PreflightError as error:
        report.update(reason_code=error.code, reason=str(error))
        return report, 2
    except (KeyError, TypeError, ValueError, OSError) as error:
        report.update(reason_code="SPEC_CONTRACT_MISMATCH", reason=f"invalid frozen contract structure: {type(error).__name__}")
        return report, 2

def main():
    report, code = preflight()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code

if __name__ == "__main__":
    sys.exit(main())
'''

FILES['tests/runtime/runtime_v24_test.py'] = r'''"""Development tests only: no runtime/provider or formal acceptance execution."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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
        env = dict(os.environ, **self.env(case="A04"))
        result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT/"ops/ci/runtime_v24.py"), "--mode", "live"],
                                cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assert_blocked(json.loads(result.stdout), result.returncode, "IMPLEMENTATION_GAP")

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

for name, content in FILES.items():
    target = ROOT/name
    if name in ('ops/ci/runtime_v24.py','tests/runtime/check/routing_test.go','tests/runtime/runtime_v24_test.py') and target.exists():
        raise SystemExit(f'new target already exists: {target}')

for name, content in FILES.items():
    target = ROOT/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content,encoding='utf-8',newline='\n')

target=ROOT/'tests/runtime/check/w0502.go'
text=target.read_text(encoding='utf-8')
start=text.index('// routingW0502OK asserts')
end=text.index('// cancelCascadeW0502',start)
text=text[:start]+'''// Share the exact selector truth table with W05-01, including rejected combinations.
func routingW0502OK() {
    bad := runtimeRoutingMismatches()
    ok("W0502-SELECTOR-ROUTING-IS-DATA-NOT-ACCIDENT", len(bad) == 0, bad)
}

'''+text[end:]
target.write_text(text,encoding='utf-8',newline='\n')

target=ROOT/'tests/runtime/check/w0501.go'
text=target.read_text(encoding='utf-8')
start=text.index('\tliveGate := exec.Command("python"')
end=text.index('\n\texecutionRecord :=',start)
text=text[:start]+'''\t// The v2.4 route is a non-executing gap preflight, never the old Codex LIVE harness.
    liveGate, gateErr := runtimePythonCommand(repoRoot(), "ops/ci/runtime_v24.py", "live")
    gateText := fmt.Sprint(gateErr)
    if gateErr == nil {
        liveGate.Env = append(os.Environ(), "RESEARCHOS_TASK_ID=W05", "RESEARCHOS_CHECK_ID=W05-G02",
            "RESEARCHOS_CASE_ID=", "PYTHONUTF8=1")
        out, runErr := liveGate.CombinedOutput()
        gateErr, gateText = runErr, string(out)
    }
    ok("W0501-LIVE-GATE-REFUSES-WITHOUT-EXPLICIT-OPT-IN",
        gateErr != nil && strings.Contains(gateText, `"status": "BLOCKED"`) &&
            strings.Contains(gateText, `"assertion_ids": []`) && !strings.Contains(gateText, `"status": "PASS"`), gateText)
'''+text[end:]
target.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'written':list(FILES)+['tests/runtime/check/w0501.go','tests/runtime/check/w0502.go']},ensure_ascii=False))
