"""Pure injected-process fixtures: no real Popen, sockets, controller or Job."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("owned_model_supervisor", Path(__file__).with_name("supervise.py"))
S = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = S
SPEC.loader.exec_module(S)


class FakeProcess:
    def __init__(self, waits, *, kill_error=None):
        self.waits = list(waits)
        self.events = []
        self.kill_error = kill_error

    def wait(self, *, timeout):
        self.events.append(("wait", timeout))
        if not self.waits:
            raise AssertionError("extra confirmation/retry")
        result = self.waits.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result

    def kill(self):
        self.events.append(("kill_original_object",))
        if self.kill_error is not None:
            raise self.kill_error

    def __getattr__(self, name):
        raise AssertionError("forbidden PID/pipe/poll/rediscovery access: " + name)


def complete_result():
    process = {"pid": 7, "creation_filetime_decimal": "134000000000000001",
               "handle_held": True, "in_owned_job": True,
               "new_process_event": True, "signaled_after_cleanup": True}
    return {"status": "METADATA_VERIFIED_OWNED_JOB_CLOSED_ASSETS_UNCHANGED",
            "cleanup_proved": True, "streams_drained": True,
            "stage_a_assets_unchanged_after_stop": True,
            "controller_inference_requests": 0, "paid_provider_requests": 0,
            "old_root_writes": 0, "formal_increment": 0,
            "counter_reset": False, "resource_ready": False,
            "metadata_get_attempts": {"/api/version": 1, "/api/tags": 1},
            "kernel": {"CleanupProved": True, "Error": "",
                       "Close": {"JobClosed": True, "PrimarySignaled": True, "Errors": None},
                       "State": {"Active": 0, "Total": 1, "Complete": True,
                                 "Processes": [process], "Errors": []},
                       "Primary": copy.deepcopy(process)}}


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.real_popen = mock.patch.object(S.subprocess, "Popen", side_effect=AssertionError("real Popen forbidden"))
        self.real_popen.start()
        self.addCleanup(self.real_popen.stop)

    def invoke(self, process):
        calls = []

        def factory(argv, **kwargs):
            calls.append((argv, kwargs))
            process.events.append(("popen_return",))
            return process

        # Any filesystem/reporting action inside the active-child core fails.
        with mock.patch.object(Path, "open", side_effect=AssertionError("active-child file IO")), \
             mock.patch.object(S.os, "fsync", side_effect=AssertionError("active-child Sync")), \
             mock.patch.object(S.os, "kill", side_effect=AssertionError("PID kill forbidden")):
            outcome = S.run_child_once({"SystemRoot": "public-only"}, popen_factory=factory)
        self.assertIs(outcome.process, process)
        self.assertEqual(len(calls), 1)
        argv, options = calls[0]
        self.assertEqual(argv, [str(S.CONTROLLER), "-execute", "-scope", str(S.R4_SCOPE),
                                "-expected-scope-sha256", S.R4_SCOPE_SHA])
        self.assertEqual(options["creationflags"], S.CREATE_NO_WINDOW)
        self.assertIs(options["shell"], False)
        self.assertIs(options["close_fds"], True)
        self.assertEqual([options[key] for key in ("stdin", "stdout", "stderr")], [subprocess.DEVNULL] * 3)
        return outcome

    def test_first_blocking_action_is_bounded_wait_not_logger(self):
        process = FakeProcess([0])
        outcome = self.invoke(process)
        self.assertEqual(process.events, [("popen_return",), ("wait", 180)])
        self.assertEqual(outcome.record["controller_exit_code"], 0)
        self.assertFalse(outcome.record["resource_ready"])

    def test_hung_r4_logger_times_out_kills_only_original_handle(self):
        process = FakeProcess([subprocess.TimeoutExpired("frozen-controller", 180), 125])
        outcome = self.invoke(process)
        self.assertEqual(process.events, [("popen_return",), ("wait", 180),
                                          ("kill_original_object",), ("wait", 5)])
        self.assertEqual(outcome.record["status"], "UNKNOWN")
        self.assertTrue(outcome.record["termination_confirmed"])
        self.assertFalse(outcome.record["automatic_retry"])

    def test_timeout_never_promotes_late_complete_result(self):
        process = FakeProcess([subprocess.TimeoutExpired("frozen-controller", 180), 0])
        outcome = self.invoke(process)
        loader = mock.Mock(side_effect=AssertionError("late RESULT must not be read"))
        S.classify_after_exit(outcome, result_loader=loader)
        loader.assert_not_called()
        self.assertEqual(outcome.record["status"], "UNKNOWN")

    def test_failed_kill_has_exactly_one_bounded_confirmation(self):
        process = FakeProcess([subprocess.TimeoutExpired("controller", 180),
                               subprocess.TimeoutExpired("controller", 5)],
                              kill_error=OSError("RAW_TOKEN_MUST_NOT_APPEAR"))
        outcome = self.invoke(process)
        self.assertEqual(process.events.count(("kill_original_object",)), 1)
        self.assertEqual(process.events.count(("wait", 5)), 1)
        self.assertFalse(outcome.record["termination_confirmed"])
        self.assertNotIn("RAW_TOKEN", json.dumps(outcome.record))
        self.assertEqual(outcome.record["status"], "UNKNOWN")

    def test_wait_exception_and_keyboard_interrupt_use_owned_cleanup(self):
        for error in (OSError("token-value"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                process = FakeProcess([error, 125])
                outcome = self.invoke(process)
                self.assertEqual(process.events[-2:], [("kill_original_object",), ("wait", 5)])
                self.assertEqual(outcome.record["status"], "UNKNOWN")
                self.assertNotIn("token-value", json.dumps(outcome.record))

    def test_popen_constructor_error_is_uncertain_no_rediscovery_or_retry(self):
        factory = mock.Mock(side_effect=OSError("secret-value"))
        outcome = S.run_child_once({}, popen_factory=factory)
        factory.assert_called_once()
        self.assertIsNone(outcome.process)
        self.assertEqual(outcome.record["reason"], "POPEN_CONSTRUCTION_UNCERTAIN")
        self.assertEqual(outcome.record["status"], "UNKNOWN")
        self.assertNotIn("secret-value", json.dumps(outcome.record))

    def test_nonzero_exit_is_inconclusive_without_kill(self):
        process = FakeProcess([1])
        outcome = self.invoke(process)
        loader = mock.Mock()
        S.classify_after_exit(outcome, result_loader=loader)
        loader.assert_not_called()
        self.assertEqual(outcome.record["status"], "INCONCLUSIVE")
        self.assertNotIn(("kill_original_object",), process.events)

    def test_missing_or_unreadable_result_never_means_ready(self):
        for error in (FileNotFoundError(), ValueError("bad JSON")):
            outcome = self.invoke(FakeProcess([0]))
            S.classify_after_exit(outcome, result_loader=mock.Mock(side_effect=error))
            self.assertEqual(outcome.record["status"], "INCONCLUSIVE")
            self.assertFalse(outcome.record["reported_proof_complete"])

    def test_incomplete_or_forged_proof_is_inconclusive(self):
        cases = []
        for field in ("cleanup_proved", "streams_drained", "stage_a_assets_unchanged_after_stop"):
            value = complete_result(); value[field] = False; cases.append(value)
        value = complete_result(); value["kernel"]["Close"]["JobClosed"] = False; cases.append(value)
        value = complete_result(); value["kernel"]["State"]["Active"] = 1; cases.append(value)
        value = complete_result(); value["kernel"]["Primary"]["creation_filetime_decimal"] = "9"; cases.append(value)
        value = complete_result(); value["metadata_get_attempts"]["/api/tags"] = True; cases.append(value)
        value = complete_result(); value["resource_ready"] = True; cases.append(value)
        for value in cases:
            outcome = self.invoke(FakeProcess([0]))
            S.classify_after_exit(outcome, result_loader=lambda: value)
            self.assertEqual(outcome.record["status"], "INCONCLUSIVE")

    def test_complete_report_is_only_awaiting_root_review_not_acceptance(self):
        outcome = self.invoke(FakeProcess([0]))
        S.classify_after_exit(outcome, result_loader=complete_result)
        self.assertEqual(outcome.record["status"], "REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED")
        self.assertTrue(outcome.record["reported_proof_complete"])
        self.assertFalse(outcome.record["independent_acceptance"])
        self.assertFalse(outcome.record["resource_ready"])

    def test_environment_does_not_inherit_profile_proxy_or_token(self):
        directory = Path(__file__).resolve().parent / "virtual-only-no-directory-created"
        environment = S.child_environment(str(directory), directory / "attempt")
        self.assertEqual(set(environment), {"SystemRoot", "WINDIR", "PATH", "USERPROFILE",
                                            "LOCALAPPDATA", "APPDATA", "TEMP", "TMP"})
        self.assertFalse(any("proxy" in key.lower() or "token" in key.lower() for key in environment))
        self.assertNotEqual(environment["USERPROFILE"], str(Path.home()))

    def test_public_result_reader_rejects_duplicates_nonfinite_and_oversize(self):
        path = Path("memory-only-fixture.json")
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '[]', 'x' * 50):
            with mock.patch.object(Path, "open", return_value=io.BytesIO(text.encode("utf-8"))):
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    S.read_public_json(path, 20)

    def test_exclusive_record_cannot_overwrite_existing_consumption(self):
        path = Path("memory-only-CONSUMED.json")
        stream = mock.MagicMock()
        stream.__enter__.return_value = stream
        with mock.patch.object(Path, "open", side_effect=[stream, FileExistsError()]) as opened, \
             mock.patch.object(S.os, "fsync"):
            S.write_new(path, {"status": "consumed"})
            with self.assertRaises(FileExistsError):
                S.write_new(path, {"status": "retry"})
            self.assertEqual([call.args[0] for call in opened.call_args_list], ["x", "x"])
            self.assertEqual(stream.__enter__.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
