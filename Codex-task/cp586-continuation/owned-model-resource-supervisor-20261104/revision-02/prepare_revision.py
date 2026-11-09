"""Offline one-use revision preparation; never imports/runs supervisor main."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = json.loads((BASE / "MANIFEST.json").read_bytes())
assert digest(BASE / "MANIFEST.json") == "1b8004fc8f11fd11dc49ad0793f688f25cc69c581166b3a156293f1a996e1fe9"
for item in manifest["files"]:
    assert digest(BASE / item["relative"]) == item["sha256"], item["relative"]
assert not (BASE / "attempt-01").exists()
assert not (BASE.parent / "owned-model-resource-stage-b" / "revision-04" / "run-01").exists()
assert not (HERE / "supervise.py").exists()
assert not (HERE / "test_supervise.py").exists()

source = (BASE / "supervise.py").read_text(encoding="utf-8")
old_root = 'ROOT = Path(r"C:\\Users\\yqyyds\\Documents\\Codex\\2026-11-04\\task\\cp586-continuation\\owned-model-resource-supervisor-20261104")\nR4 = ROOT.parent / "owned-model-resource-stage-b" / "revision-04"'
new_root = 'BASE = Path(r"C:\\Users\\yqyyds\\Documents\\Codex\\2026-11-04\\task\\cp586-continuation\\owned-model-resource-supervisor-20261104")\nROOT = BASE / "revision-02"\nR4 = BASE.parent / "owned-model-resource-stage-b" / "revision-04"'
assert source.count(old_root) == 1
source = source.replace(old_root, new_root)
assert source.count('ATTEMPT = ROOT / "attempt-01"') == 1
source = source.replace('ATTEMPT = ROOT / "attempt-01"', 'ATTEMPT = BASE / "attempt-01"')
start = source.index('    try:\n        process = popen_factory', source.index('def run_child_once('))
end = source.index('    return ManagedOutcome({"status": "CONTROLLER_EXITED_REQUIRES_RESULT_REVIEW",', start)
source = source[:start] + '''    process = None
    try:
        process = popen_factory(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, shell=False, close_fds=True,
                                creationflags=CREATE_NO_WINDOW, cwd=str(ROOT), env=env)
        # Handle acquisition and FIRST potentially blocking wait share this
        # protected region, including cancellation before wait begins.
        code = process.wait(timeout=OUTER_WAIT_SECONDS)
    except BaseException as error:
        if process is None:
            # No returned handle: outcome is uncertain. Never rediscover or retry.
            return ManagedOutcome({"status": "UNKNOWN", "reason": "POPEN_CONSTRUCTION_UNCERTAIN",
                                   "launch_error": error_kind(error), "automatic_retry": False,
                                   "resource_ready": False, "reported_proof_complete": False})
        reason = ("OUTER_TIMEOUT" if isinstance(error, subprocess.TimeoutExpired)
                  else "WAIT_EXCEPTION_OR_CANCELLATION")
        return bounded_stop(process, reason, error)
''' + source[end:]
tests = (BASE / "test_supervise.py").read_text(encoding="utf-8")
marker = '    def test_popen_constructor_error_is_uncertain_no_rediscovery_or_retry(self):'
assert tests.count(marker) == 1
regression = '''    def test_cancel_immediately_after_handle_assignment_is_owned_and_bounded(self):
        # Inject on the first line AND first opcode after the fake handle has
        # been assigned. This tests the actual boundary, not a moved line number.
        for injection_event in ("line", "opcode"):
            with self.subTest(event=injection_event):
                process = FakeProcess([125])
                calls = []
                fired = []

                def factory(*args, **kwargs):
                    calls.append(1)
                    process.events.append(("popen_return",))
                    return process

                def trace(frame, event, arg):
                    if frame.f_code is S.run_child_once.__code__:
                        frame.f_trace_opcodes = True
                        if (event == injection_event and not fired
                                and frame.f_locals.get("process") is process):
                            fired.append(frame.f_lasti)
                            process.events.append(("cancel_before_wait", injection_event))
                            raise KeyboardInterrupt()
                    return trace

                previous_trace = sys.gettrace()
                try:
                    with mock.patch.object(Path, "open", side_effect=AssertionError("active-child file IO")), \\
                         mock.patch.object(S.os, "fsync", side_effect=AssertionError("active-child Sync")), \\
                         mock.patch.object(S.os, "kill", side_effect=AssertionError("PID kill forbidden")):
                        sys.settrace(trace)
                        outcome = S.run_child_once({}, popen_factory=factory)
                finally:
                    sys.settrace(previous_trace)
                self.assertEqual(len(fired), 1)
                self.assertEqual(calls, [1])
                self.assertIs(outcome.process, process)
                self.assertEqual(process.events, [("popen_return",),
                                 ("cancel_before_wait", injection_event),
                                 ("kill_original_object",), ("wait", 5)])
                self.assertEqual(outcome.record["status"], "UNKNOWN")
                self.assertEqual(outcome.record["reason"], "WAIT_EXCEPTION_OR_CANCELLATION")
                self.assertTrue(outcome.record["termination_confirmed"])
                self.assertFalse(outcome.record["automatic_retry"])
                self.assertFalse(outcome.record["resource_ready"])

    def test_revision_does_not_create_another_attempt_or_change_r4_target(self):
        self.assertEqual(S.ROOT, S.BASE / "revision-02")
        self.assertEqual(S.ATTEMPT, S.BASE / "attempt-01")
        self.assertEqual(S.R4, S.BASE.parent / "owned-model-resource-stage-b" / "revision-04")
        self.assertEqual(S.R4_RUN, S.R4 / "run-01")
        self.assertEqual(S.ENDPOINT, "http://127.0.0.1:43861")
        self.assertEqual(S.CONTROLLER_SHA, "332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297")
        self.assertEqual(S.R4_SCOPE_SHA, "49a78cf270e40f4e76131bd9a1cd98e929548f39d36e9e1d203507f6ab67bdab")

'''
tests = tests.replace(marker, regression + marker)
for name, text in (("supervise.py", source), ("test_supervise.py", tests)):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
print(json.dumps({"status": "REVISION02_SOURCE_CREATED_OFFLINE", "old_pins_checked": len(manifest["files"]),
                  "source_sha256": digest(HERE / "supervise.py"), "tests_sha256": digest(HERE / "test_supervise.py"),
                  "actual_child_launches": 0, "old_pins_changed": 0}))
