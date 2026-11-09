"""Independent offline review only; never execute supervise.main with real factories."""
import contextlib
import dis
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
blocked_attempts = []

def forbid_process(*args, **kwargs):
    blocked_attempts.append("forbidden-process-entry")
    raise AssertionError("real process construction forbidden in independent review")

def audit(event, args):
    if event.startswith(("subprocess.Popen", "_winapi.CreateProcess", "os.system",
                         "os.spawn", "os.exec", "socket.connect", "socket.bind",
                         "socket.getaddrinfo")):
        blocked_attempts.append(event)
        raise AssertionError("native child/network audit event forbidden: " + event)

sys.addaudithook(audit)
subprocess.Popen = forbid_process
spec = importlib.util.spec_from_file_location("supervisor_author_fixtures", ROOT / "test_supervise.py")
T = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = T
spec.loader.exec_module(T)
S = T.S

class GateTests(unittest.TestCase):
    def setUp(self):
        self.auth_path = S.AUTHORIZATION_ROOT / "independent-memory-auth.json"
        self.auth = {
            "schema": "researchos.root-model-supervisor-authorization.v1",
            "actor": "codex:/root", "project_id": S.PROJECT_ID,
            "controller_sha256": S.CONTROLLER_SHA,
            "controller_scope_sha256": S.R4_SCOPE_SHA,
            "supervisor_manifest_sha256": "manifest-pin",
            "supervisor_scope_sha256": "scope-pin", "endpoint": S.ENDPOINT,
            "max_controller_launches": 1, "inference_limit": 0,
            "attempt_directory": str(S.ATTEMPT),
            "status": "ROOT_AUTHORIZED_ONCE_AFTER_REVIEW",
            "checkpoint_revision": 594, "checkpoint_sha256": "checkpoint-pin"}
        self.checkpoint = {"revision": 594, "project_id": S.PROJECT_ID}
        self.manifest = {"files": [{"relative": "supervise.py", "sha256": "source-pin"}]}
        self.hashes = {str(S.PYTHON): S.PYTHON_SHA, str(S.ROOT / "MANIFEST.json"): "manifest-pin",
                       str(S.ROOT / "supervise.py"): "source-pin",
                       str(S.CONTROLLER): S.CONTROLLER_SHA, str(S.R4_SCOPE): S.R4_SCOPE_SHA,
                       str(S.REVIEW): S.REVIEW_SHA, str(S.ROOT / "SCOPE.json"): "scope-pin",
                       str(self.auth_path): "root-scope-pin", str(S.CHECKPOINT): "checkpoint-pin"}
        self.existing = set()

    def verify(self, auth_path=None):
        def read(path, *args):
            if path == S.ROOT / "MANIFEST.json": return copy.deepcopy(self.manifest)
            if path == self.auth_path: return copy.deepcopy(self.auth)
            if path == S.CHECKPOINT: return copy.deepcopy(self.checkpoint)
            raise AssertionError("unexpected record read")
        with mock.patch.object(S, "sha256", side_effect=lambda p: self.hashes.get(str(p), "bad-pin")), \
             mock.patch.object(S, "read_public_json", side_effect=read), \
             mock.patch.object(Path, "resolve", lambda p, *a, **k: Path(os.path.normpath(str(p)))), \
             mock.patch.object(Path, "exists", lambda p: str(p) in self.existing):
            return S.verify_prelaunch("manifest-pin", auth_path or self.auth_path, "root-scope-pin")

    def test_exact_current_checkpoint_and_public_scope_bind(self):
        result = self.verify()
        self.assertEqual(result["checkpoint_revision"], 594)
        self.assertEqual(result["checkpoint_sha256"], "checkpoint-pin")

    def test_stale_or_wrong_project_checkpoint_rejects(self):
        mutations = [("revision", 593), ("revision", True), ("project_id", "other-project")]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                old = self.checkpoint[key]; self.checkpoint[key] = value
                with self.assertRaises(ValueError): self.verify()
                self.checkpoint[key] = old
        self.hashes[str(S.CHECKPOINT)] = "newer-checkpoint-hash"
        with self.assertRaises(ValueError): self.verify()

    def test_template_old_revision_and_boolean_limits_reject(self):
        for key, value in [("status", "TEMPLATE_NOT_AUTHORIZATION"),
                           ("checkpoint_revision", 591), ("checkpoint_revision", True),
                           ("max_controller_launches", True), ("inference_limit", False)]:
            with self.subTest(key=key):
                old = self.auth[key]; self.auth[key] = value
                with self.assertRaises(ValueError): self.verify()
                self.auth[key] = old

    def test_nonpublic_scope_or_bad_source_pin_rejects(self):
        with self.assertRaises(ValueError):
            self.verify(S.ROOT / "private-or-unapproved-scope.json")
        self.hashes[str(S.ROOT / "supervise.py")] = "changed-source"
        with self.assertRaises(ValueError): self.verify()

    def test_manifest_traversal_rejects(self):
        self.manifest["files"][0]["relative"] = "../outside.py"
        with self.assertRaises(ValueError): self.verify()

    def test_attempt_and_r4_run_each_block_replay(self):
        for path in (S.ATTEMPT, S.R4_RUN):
            with self.subTest(path=str(path)):
                self.existing = {str(path)}
                with self.assertRaises(ValueError): self.verify()

class MainConsumptionTests(unittest.TestCase):
    def exercise(self, fail_at=None):
        events = []
        binding = {"checkpoint_revision": 594, "checkpoint_sha256": "cp",
                   "root_scope_sha256": "scope"}
        def mkdir(path, *args, **kwargs):
            events.append(("mkdir", str(path)))
            if fail_at == "mkdir" and path == S.ATTEMPT: raise FileExistsError()
        def write(path, record):
            events.append(("write", path.name))
            if fail_at == "consume" and path.name == "CONSUMED.json": raise OSError("fixture")
        def launch(env, *, popen_factory):
            events.append(("launch",))
            return S.ManagedOutcome({"status": "UNKNOWN", "automatic_retry": False,
                                     "resource_ready": False, "reported_proof_complete": False})
        args = ["supervise.py", "--execute", "--root-scope", str(S.AUTHORIZATION_ROOT / "memory.json")]
        with mock.patch.object(sys, "argv", args), \
             mock.patch.object(S, "verify_prelaunch", return_value=binding), \
             mock.patch.object(Path, "mkdir", mkdir), \
             mock.patch.object(S, "child_environment", return_value={"SystemRoot": "public"}), \
             mock.patch.object(S, "write_new", side_effect=write), \
             mock.patch.object(S, "run_child_once", side_effect=launch) as called, \
             contextlib.redirect_stdout(io.StringIO()):
            code = S.main()
        return code, events, called.call_count

    def test_consumption_is_flushed_before_single_launch(self):
        code, events, calls = self.exercise()
        self.assertEqual(code, 1)
        self.assertEqual(calls, 1)
        self.assertLess(events.index(("write", "CONSUMED.json")), events.index(("launch",)))
        self.assertEqual(events[-1], ("write", "SUPERVISOR-RESULT.json"))

    def test_failed_consumption_never_launches(self):
        for failure in ("mkdir", "consume"):
            with self.subTest(failure=failure):
                code, events, calls = self.exercise(failure)
                self.assertEqual(code, 2)
                self.assertEqual(calls, 0)
                self.assertNotIn(("launch",), events)

# Independently scan every opcode from original-object assignment to the first
# wait call, plus the old source-line129 probe. Only memory fake objects exist.
boundary_cases = []
class CancellationBoundaryTests(unittest.TestCase):
    def test_every_acquired_before_wait_opcode_is_owned_and_bounded(self):
        instructions = list(dis.get_instructions(S.run_child_once))
        stores = [i for i, ins in enumerate(instructions)
                  if ins.opname == "STORE_FAST" and ins.argval == "process"]
        self.assertEqual(len(stores), 2)
        start = stores[1] + 1
        end = next(i for i in range(start, len(instructions))
                   if instructions[i].opname.startswith("CALL"))
        offsets = [ins.offset for ins in instructions[start:end + 1]]
        for target in offsets:
            with self.subTest(offset=target):
                process = T.FakeProcess([125])
                calls = []
                fired = []
                def factory(*args, **kwargs):
                    calls.append(1)
                    return process
                def trace(frame, event, arg):
                    if frame.f_code is S.run_child_once.__code__:
                        frame.f_trace_opcodes = True
                        if (event == "opcode" and not fired and frame.f_lasti == target
                                and frame.f_locals.get("process") is process):
                            fired.append(target)
                            raise KeyboardInterrupt()
                    return trace
                previous = sys.gettrace()
                try:
                    with mock.patch.object(Path, "open", side_effect=AssertionError("active-child IO")), \
                         mock.patch.object(S.os, "fsync", side_effect=AssertionError("active-child Sync")), \
                         mock.patch.object(S.os, "kill", side_effect=AssertionError("PID kill")):
                        sys.settrace(trace)
                        outcome = S.run_child_once({}, popen_factory=factory)
                finally:
                    sys.settrace(previous)
                self.assertEqual(fired, [target])
                self.assertEqual(calls, [1])
                self.assertIs(outcome.process, process)
                self.assertEqual(process.events, [("kill_original_object",), ("wait", 5)])
                self.assertEqual(outcome.record["status"], "UNKNOWN")
                loader = mock.Mock(side_effect=AssertionError("late RESULT"))
                S.classify_after_exit(outcome, result_loader=loader)
                loader.assert_not_called()
                boundary_cases.append({"opcode_offset": target,
                                       "opname": next(i.opname for i in instructions if i.offset == target),
                                       "events": process.events, "status": outcome.record["status"]})

def cancellation_gap_probe():
    process = T.FakeProcess([125])
    fired = []
    def trace(frame, event, arg):
        if (frame.f_code is S.run_child_once.__code__ and event == "line"
                and frame.f_lineno == 129 and not fired):
            fired.append(frame.f_lasti)
            raise KeyboardInterrupt()
        return trace
    previous = sys.gettrace()
    escaped = False
    outcome = None
    try:
        sys.settrace(trace)
        outcome = S.run_child_once({}, popen_factory=lambda *a, **k: process)
    except KeyboardInterrupt:
        escaped = True
    finally:
        sys.settrace(previous)
    return {"old_counterexample_source_line": 129, "injection_fired": bool(fired),
            "keyboard_interrupt_escaped": escaped, "fake_process_events": process.events,
            "status": outcome.record["status"] if outcome else None,
            "same_original_object": outcome.process is process if outcome else False,
            "real_processes_created": 0}

suite = unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(T))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(GateTests))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(MainConsumptionTests))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CancellationBoundaryTests))
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
(OUT / "pure-mock-tests.log").write_text(log.getvalue(), encoding="utf-8")
compile_artifacts = []
for name in ("supervise", "test_supervise"):
    target = OUT / (name + ".review.pyc")
    py_compile.compile(str(ROOT / (name + ".py")), cfile=str(target), doraise=True,
                       invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
    compile_artifacts.append({"relative": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
summary = {"schema": "researchos.supervisor-independent-offline-checks.v1",
           "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
           "author_tests": 15, "independent_gate_main_tests": 8,
           "independent_cancellation_scan_tests": 1,
           "py_compile_exit": 0, "compile_artifacts": compile_artifacts,
           "blocked_real_process_or_network_attempts": blocked_attempts,
           "real_Popen_calls": 0, "controller_runs": 0, "native_backend_runs": 0,
           "HTTP": 0, "D_writes": 0, "formal_increment": 0,
           "cancellation_gap_probe": cancellation_gap_probe(),
           "acquired_before_wait_opcode_scan": boundary_cases}
(OUT / "offline-checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
probe = summary["cancellation_gap_probe"]
probe_ok = (probe["injection_fired"] and not probe["keyboard_interrupt_escaped"]
            and probe["same_original_object"] and probe["status"] == "UNKNOWN"
            and probe["fake_process_events"] == [("kill_original_object",), ("wait", 5)])
raise SystemExit(0 if result.wasSuccessful() and not blocked_attempts and probe_ok else 1)



