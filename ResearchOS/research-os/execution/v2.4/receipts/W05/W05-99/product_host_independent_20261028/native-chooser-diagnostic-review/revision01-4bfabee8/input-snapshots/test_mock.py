"""Pure mock checks. Never starts Electron, Core, or a real named pipe."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).with_name("diagnose_once.py")
spec = importlib.util.spec_from_file_location("chooser_diagnosis_revision01", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeProcess:
    pid = 31415
    returncode = None

    def poll(self):
        return self.returncode


class FakeStream:
    def close(self):
        raise OSError("stream close failed")


class GuardrailTests(unittest.TestCase):
    def setUp(self):
        module.OWNED_HANDLES.clear()

    def tearDown(self):
        module.OWNED_HANDLES.clear()

    def test_popen_handle_registered_before_receipt_failure(self):
        process = FakeProcess()
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw)
            fake_startup = type("Startup", (), {"dwFlags": 0, "wShowWindow": 0})
            with mock.patch.object(module.subprocess, "STARTUPINFO", return_value=fake_startup), \
                    mock.patch.object(module.subprocess, "STARTF_USESHOWWINDOW", 1, create=True), \
                    mock.patch.object(module.subprocess, "Popen", return_value=process), \
                    mock.patch.object(module, "save", side_effect=OSError("receipt write failed")):
                with self.assertRaisesRegex(OSError, "receipt write failed"):
                    module.launch(out / "fake.exe", [], out, {}, out, "electron")
        self.assertEqual([row["process"] for row in module.OWNED_HANDLES], [process])

    def test_popen_handle_registered_before_stream_close_failure(self):
        process = FakeProcess()
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw)
            fake_startup = type("Startup", (), {"dwFlags": 0, "wShowWindow": 0})
            with mock.patch.object(module.subprocess, "STARTUPINFO", return_value=fake_startup), \
                    mock.patch.object(module.subprocess, "STARTF_USESHOWWINDOW", 1, create=True), \
                    mock.patch.object(module.subprocess, "Popen", return_value=process), \
                    mock.patch("builtins.open", return_value=FakeStream()):
                with self.assertRaisesRegex(OSError, "stream close failed"):
                    module.launch(out / "fake.exe", [], out, {}, out, "electron")
        self.assertEqual([row["process"] for row in module.OWNED_HANDLES], [process])

    def test_known_pid_reuse_and_exact_bundle_image_block_release(self):
        known = [{"pid": 11, "image": module.normpath("C:/owned/electron.exe"),
                  "created_ns": "123", "role": "electron"}]
        image = module.normpath("C:/owned/electron.exe")
        rows = [{"pid": 11, "image": "C:/other/not-electron.exe", "created_ns": "999", "read_error": None},
                {"pid": 12, "image": "C:/owned/electron.exe", "created_ns": "234", "read_error": None}]
        blocked = module.scan_blockers({"status": "OBSERVED", "rows": rows}, [image], known)
        self.assertIn("KNOWN_PID_REUSED_OR_UNKNOWN:11", blocked)
        self.assertIn("EXACT_BUNDLE_IMAGE_STILL_RUNNING:12", blocked)

    def test_release_nonce_and_scope_binding(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ROOT-RELEASE.json"
            waiting = {"scope_sha256": "scope", "controller_pid": 77,
                       "release_nonce": "unique", "known_identities": [],
                       "at": "2026-10-28T00:00:00+00:00"}
            value = {"schema": "researchos.native-chooser-root-release.v1", "actor": "codex:/root",
                     "scope_sha256": "scope", "controller_pid": 77, "release_nonce": "unique",
                     "known_identities": [], "root_confirmed_identity_absence": True,
                     "confirmed_absent_at": "2026-10-28T00:00:01+00:00"}
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(len(module.validate_root_release(path, waiting)), 64)
            value["release_nonce"] = "wrong"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ROOT_RELEASE_BINDING_MISMATCH"):
                module.validate_root_release(path, waiting)

    def test_hold_survives_logging_print_and_interrupt_then_requires_two_scans(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw)
            actual_save = module.save
            actual_append = module.safe_append
            scans = []
            sleeps = []
            appends = []

            def flaky_save(folder, name, value):
                if name == "UNRESOLVED.json":
                    raise OSError("receipt unavailable")
                actual_save(folder, name, value)
                if name == "WAITING_FOR_ROOT.json":
                    release = {"schema": "researchos.native-chooser-root-release.v1",
                               "actor": "codex:/root", "scope_sha256": value["scope_sha256"],
                               "controller_pid": value["controller_pid"],
                               "release_nonce": value["release_nonce"],
                               "known_identities": value["known_identities"],
                               "root_confirmed_identity_absence": True,
                               "confirmed_absent_at": "2099-01-01T00:00:00+00:00"}
                    (out / "ROOT-RELEASE.json").write_text(json.dumps(release), encoding="utf-8")

            def fake_scan(*_args):
                scans.append(1)
                return {"status": "OBSERVED", "rows": []}

            def fake_sleep(_seconds):
                sleeps.append(1)
                if len(sleeps) == 1:
                    raise KeyboardInterrupt

            def flaky_append(path, value):
                appends.append(1)
                if len(appends) == 1:
                    return False  # Failed observation logging must reset the release count.
                return actual_append(path, value)

            with mock.patch.object(module, "save", side_effect=flaky_save), \
                    mock.patch.object(module, "known_identities", return_value=[]), \
                    mock.patch.object(module, "bundle_images", return_value=[]), \
                    mock.patch.object(module, "scan_once", side_effect=fake_scan), \
                    mock.patch.object(module, "safe_append", side_effect=flaky_append), \
                    mock.patch.object(module.time, "sleep", side_effect=fake_sleep), \
                    mock.patch.object(module.signal, "signal"), \
                    mock.patch("builtins.print", side_effect=BrokenPipeError("console closed")):
                result = module.hold(out, "mock failure", out, {}, out, "scope", None, out / "no-witness")
            self.assertEqual(result, 1)
            self.assertGreaterEqual(len(scans), 3)  # log failure and interruption each reset a scan
            self.assertTrue((out / "ROOT-RELEASED.json").exists())


if __name__ == "__main__":
    unittest.main()
