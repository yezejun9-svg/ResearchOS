"""Pure fault-injection tests. They never launch the helper or open native UI."""

import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("native_folder_env_controller", Path(__file__).with_name("controller.py"))
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class FakeChild:
    pid = 73331

    def __init__(self):
        self.alive = True
        self.waited = False

    def poll(self):
        return None if self.alive else 0

    def wait(self, timeout=None):
        self.waited = True
        return 0


class HoldReached(BaseException):
    pass


class ControllerMockTests(unittest.TestCase):
    def test_first_postspawn_receipt_failure_enters_hold_with_same_handle(self):
        child = FakeChild()
        original_save = controller.save
        held = []

        def fail_spawn_record(out, name, value):
            if name == "spawn.json":
                raise OSError("fault injected: first postspawn receipt")
            return original_save(out, name, value)

        def mark_hold(out, scope_hash, owned, nonce, exc):
            held.append((owned, nonce, repr(exc)))
            raise HoldReached()

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(controller.subprocess, "Popen", return_value=child), \
                 mock.patch.object(controller, "process_identity", return_value=(child.pid, 123)), \
                 mock.patch.object(controller, "save", side_effect=fail_spawn_record), \
                 mock.patch.object(controller, "unresolved_hold", side_effect=mark_hold):
                with self.assertRaises(HoldReached):
                    controller.run_case("A", Path("helper.exe"), Path("项目 空间"), {}, Path(temporary), "scope")
            self.assertTrue((Path(temporary) / "A" / "hold-contract.json").exists())
        self.assertEqual(len(held), 1)
        self.assertIs(held[0][0], child)
        self.assertEqual(len(held[0][1]), 32)

    def test_hold_survives_receipt_error_nested_errorwrite_sleep_interrupt_and_rejects_stale_release(self):
        child = FakeChild()
        failures = {"record": 0, "append": 0, "sleep": 0}
        failed_names = set()
        original_safe_record = controller.safe_record

        def flaky_record(out, name, value):
            if name in ("UNRESOLVED.json", "WAITING_FOR_ROOT.json") and name not in failed_names:
                failed_names.add(name)
                failures["record"] += 1
                raise OSError("fault injected: hold entry receipt")
            return original_safe_record(out, name, value)

        def flaky_append(path, value):
            failures["append"] += 1
            raise OSError("fault injected: nested error write")

        def flaky_sleep(seconds):
            failures["sleep"] += 1
            if failures["sleep"] == 1:
                raise KeyboardInterrupt()
            if failures["sleep"] == 2:
                raise OSError("fault injected: nested sleep")
            threading.Event().wait(0.005)

        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            failures_in_thread = []

            def exercise():
                try:
                    controller.unresolved_hold(out, "scope", child, "nonce", RuntimeError("original"))
                except BaseException as exc:
                    failures_in_thread.append(repr(exc))

            with mock.patch.object(controller, "ignore_interrupts", return_value=None), \
                 mock.patch.object(controller, "safe_record", side_effect=flaky_record), \
                 mock.patch.object(controller, "safe_append", side_effect=flaky_append), \
                 mock.patch.object(controller.time, "sleep", side_effect=flaky_sleep):
                thread = threading.Thread(target=exercise, daemon=True)
                thread.start()
                waiting_path = out / "WAITING_FOR_ROOT.json"
                for _ in range(200):
                    if waiting_path.exists():
                        break
                    threading.Event().wait(0.01)
                self.assertTrue(waiting_path.exists())
                waiting = json.loads(waiting_path.read_text(encoding="utf-8"))
                release_path = out / "ROOT-RELEASE.json"
                release = {"schema": "researchos.native-folder-environment-root-release.v1",
                           "actor": "codex:/root", "scope_sha256": "scope",
                           "controller_pid": waiting["controller_pid"], "helper_pid": child.pid,
                           "release_nonce": "stale", "root_confirmed_identity_absence": True,
                           "confirmed_absent_at": controller.datetime.datetime.now(controller.datetime.timezone.utc).isoformat()}
                child.alive = False
                release_path.write_text(json.dumps(release), encoding="utf-8")
                threading.Event().wait(0.1)
                self.assertTrue(thread.is_alive(), "stale release must not discard the held child")
                release["release_nonce"] = waiting["release_nonce"]
                release_path.write_text(json.dumps(release), encoding="utf-8")
                thread.join(2)
                self.assertFalse(thread.is_alive(), "matching Root release and absent child should end hold")
            self.assertFalse(failures_in_thread)
            self.assertTrue(child.waited)
            self.assertGreaterEqual(failures["record"], 2)
            self.assertEqual(failed_names, {"UNRESOLVED.json", "WAITING_FOR_ROOT.json"})
            self.assertGreaterEqual(failures["append"], 1)
            self.assertGreaterEqual(failures["sleep"], 2)
            self.assertTrue((out / "ROOT-RELEASED.json").exists())


if __name__ == "__main__":
    unittest.main()
