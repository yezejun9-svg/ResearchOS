"""Inert standard-library tests for the optional first synthetic build binding."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "apps/desktop/build-development.py"
SPEC = importlib.util.spec_from_file_location("researchos_desktop_build_development", SCRIPT)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class QualificationBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "合成来源"
        self.root.mkdir()
        self.helper = self.base / "qualification-helper.exe"
        self.helper_bytes = b"inert test helper, never executed"
        self.helper.write_bytes(self.helper_bytes)
        self.expected = digest(self.helper_bytes)
        for name, value in (("QUALIFICATION_FIRST_HELPER_SHA256", self.expected),
                            ("QUALIFICATION_FIRST_HELPER_BYTES", len(self.helper_bytes))):
            patch = mock.patch.object(builder, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def args(self, **overrides):
        values = {"qualification_root": str(self.root), "qualification_helper": str(self.helper),
                  "qualification_helper_sha256": self.expected}
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_default_closed_and_all_three_required(self):
        self.assertEqual(builder.qualification_inputs(argparse.Namespace()),
                         {"enabled": False, "status": "CLOSED_NO_QUALIFICATION_LINK"})
        for changes in ({"qualification_root": None}, {"qualification_helper": None},
                        {"qualification_helper_sha256": None}, {"qualification_root": ""},
                        {"qualification_helper_sha256": "SHA256:" + self.expected},
                        {"qualification_helper_sha256": self.expected.upper()},
                        {"qualification_helper_sha256": "0" * 64}):
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                builder.qualification_inputs(self.args(**changes))

    def test_unicode_source_and_exact_core_only_linker(self):
        binding = builder.qualification_inputs(self.args())
        self.assertTrue(binding["enabled"])
        self.assertEqual(binding["source_validation"], "DERIVED_NOT_PRESENT_NOT_VALIDATED")
        self.assertEqual(binding["source_derived"], str(self.root / "S"))
        self.assertFalse((self.root / "S").exists())
        control = self.base / "output/apps/desktop/resources/control"
        core = [str(item) for item in builder.core_build_argv(Path("C:/Go/bin/go.exe"), control, binding)]
        self.assertEqual(core[0:4], ["C:\\Go\\bin\\go.exe", "build", "-mod=readonly", "-trimpath"])
        self.assertEqual(core[4], "-ldflags")
        self.assertEqual(core[5], f"-X {builder.QUALIFICATION_ROOT_SYMBOL}={self.root} -X {builder.QUALIFICATION_HELPER_SYMBOL}=sha256:{self.expected}")
        self.assertEqual(core[5].split().count("-X"), 2)
        self.assertEqual(core[-1], "./apps/control")
        disabled = builder.qualification_inputs(argparse.Namespace())
        self.assertNotIn("-ldflags", [str(item) for item in builder.core_build_argv(Path("C:/Go/bin/go.exe"), control, disabled)])
        verifier = [str(item) for item in builder.verifier_build_argv(Path("C:/Go/bin/go.exe"), control)]
        self.assertNotIn("-ldflags", verifier)
        self.assertEqual(verifier[-1], "./apps/runtime-verifier")

    def test_ambient_goflags_are_cleared_for_shared_child_environment(self):
        env = builder.child_environment({"GOFLAGS": "-ldflags=-X=evil", "KEEP": "public"},
                                        {"go": Path("C:/Go/bin/go.exe")}, self.base / "mod", self.base / "cache",
                                        self.base / "tmp", self.base / "temp")
        self.assertEqual(env["GOFLAGS"], "")
        self.assertEqual(env["KEEP"], "public")
        self.assertEqual(env["GOPROXY"], "off")

    def test_original_spelling_rejects_injection_aliases_and_reparse(self):
        for value in (r"C:relative", r"\\server\share\root", r"\\?\C:\root", r"C:\root\..\other",
                      r"C:\root\a:b", r"C:\root;evil", 'C:\\root" -X evil', r"C:/root"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                builder.qualification_windows_path(value, linker_value=True)
        with self.assertRaises(RuntimeError):
            builder.qualification_windows_path(str(self.root) + " with space", linker_value=True)
        original = Path.lstat
        def flagged(path):
            info = original(path)
            if path == self.root:
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=builder.REPARSE)
            return info
        with mock.patch.object(Path, "lstat", flagged), self.assertRaises(RuntimeError):
            builder.qualification_no_reparse(self.helper if self.helper == self.root else self.root)

    def test_helper_copy_hash_collision_and_mutation(self):
        binding = builder.qualification_inputs(self.args())
        output = self.base / "output"
        (output / "apps/desktop/resources/control").mkdir(parents=True)
        copied = builder.qualification_copy_helper(binding, output)
        self.assertEqual(copied.read_bytes(), self.helper_bytes)
        self.assertEqual(self.helper.read_bytes(), self.helper_bytes)
        with self.assertRaises(RuntimeError):
            builder.qualification_copy_helper(binding, output)
        self.helper.write_bytes(b"mutated")
        other = self.base / "other"
        (other / "apps/desktop/resources/control").mkdir(parents=True)
        with self.assertRaises(RuntimeError):
            builder.qualification_copy_helper(binding, other)

    def test_protected_root_overlap_rejects_before_any_build_or_failure_write(self):
        cases = [
            (self.root / "S", self.base / "safe-receipts", self.root),
            (self.base / "bundle", self.root / "receipts", self.root),
        ]
        scratch_root = self.base / "bundle-go-cache"
        scratch_root.mkdir()
        cases.append((self.base / "bundle", self.base / "safe-receipts", scratch_root))
        for output, receipts, root in cases:
            with self.subTest(output=output, receipts=receipts):
                args = self.args(qualification_root=str(root))
                args.output, args.receipts = str(output), str(receipts)
                with mock.patch.object(builder, "run_command") as run, mock.patch.object(builder, "git") as git:
                    with self.assertRaises(RuntimeError):
                        builder.build(args)
                    run.assert_not_called()
                    git.assert_not_called()
                self.assertFalse((root / "S").exists())
                self.assertFalse((root / "receipts").exists())
                self.assertFalse((receipts / "failed.json").exists())
        builder.write_owned_failure(None, self.root, RuntimeError("preflight rejection"))
        self.assertFalse((self.root / "failed.json").exists())

    def test_prebuilt_receipt_is_distinct_from_current_go_list(self):
        build_root = self.base / "product-v1-native-helper-build01"
        helper = build_root / "buildout/qualification-helper.exe"
        helper.parent.mkdir(parents=True)
        helper.write_bytes(self.helper_bytes)
        binding = builder.qualification_inputs(self.args(qualification_helper=str(helper)))
        main = self.base / "main"
        receipt = main / builder.QUALIFICATION_HELPER_BUILD_RECEIPT
        receipt.mkdir(parents=True)
        selected = {"cmd/researchos-qualification-helper/main_windows.go": "a" * 64,
                    "internal/qualificationprobe/plan.go": "b" * 64, "go.mod": "c" * 64, "go.sum": "d" * 64}
        snapshot = {"files": [{"path": path, "sha256": sha} for path, sha in selected.items()]}
        go = self.base / "go.exe"
        controller = self.base / "owned_run.py"
        b3 = self.base / "product-v1-native-qualification-producer-author-20261105-rev4/MANIFEST.json"
        argv = ["build", "-trimpath", "-buildvcs=false", "-o", str(helper), "./cmd/researchos-qualification-helper"]
        prepared = {"schema": "researchos.native-qualification-helper-build-manifest/1", "source_head": "synthetic",
                    "source_binding": "HELPER_ONLY_SELECTED_GO_FILES_NOT_WHOLE_APPLICATION",
                    "argv": argv, "cwd": str(build_root / "source"), "controller_sha256": "f" * 64,
                    "go_sdk_sha256": "e" * 64, "approved_b3_manifest_sha256": "7" * 64,
                    "files": [{"path": "source/" + path, "sha256": sha} for path, sha in selected.items()]}
        (receipt / "MANIFEST.json").write_bytes(json.dumps(prepared).encode())
        inputs = ([{"path": str(build_root / "source" / path), "sha256": sha} for path, sha in selected.items()] +
                  [{"path": str(build_root / "MANIFEST.json"), "sha256": builder.sha256(receipt / "MANIFEST.json")},
                   {"path": str(go), "sha256": "e" * 64}, {"path": str(controller), "sha256": "f" * 64},
                   {"path": str(b3), "sha256": "7" * 64}])
        scope = {"schema": "researchos.owned-windows-run/1", "scope_id": builder.QUALIFICATION_HELPER_SCOPE_ID,
                 "purpose": "build", "authorization": "ROOT_REVIEWED_EXACT_COMMAND", "argv": argv,
                 "cwd": str(build_root / "source"), "controller_sha256": "f" * 64,
                 "executable": str(go), "executable_sha256": "e" * 64, "inputs": inputs}
        result = {"status": "COMPLETED_OWNED_JOB_STOPPED", "root_exit_code": 0, "scope_id": builder.QUALIFICATION_HELPER_SCOPE_ID,
                  "stop_proved": True, "job_active_zero": True, "input_drift": False, "errors": [],
                  "automatic_retry": False, "terminate_job_attempts": 0, "terminate_original_root_attempts": 0,
                  "job_total_processes": 3}
        post = {"status": "BUILT_NOT_EXECUTED_NOT_NATIVE_QUALIFIED", "stop_proved": True,
                "forced": False, "model_native_helper_execution": False, "job_processes": 3,
                "sha256": self.expected, "bytes": len(self.helper_bytes), "path": str(helper)}
        def save():
            (receipt / "scope.json").write_bytes(json.dumps(scope).encode())
            current = builder.sha256(receipt / "scope.json")
            result["scope_sha256"] = current
            post["scope_sha256"] = current
            (receipt / "RESULT.json").write_bytes(json.dumps(result).encode())
            (receipt / "POSTCHECK.json").write_bytes(json.dumps(post).encode())
        save()
        provenance = builder.qualification_original_build(main, binding, snapshot)
        self.assertEqual(provenance["provenance"], "PREBUILT_ORIGINAL_OWNED_BUILD_RECEIPT_NOT_CURRENT_GO_LIST")
        baseline_scope = json.loads(json.dumps(scope))
        baseline_result = json.loads(json.dumps(result))
        baseline_prepared = json.loads(json.dumps(prepared))
        for name in ("wrong_result_scope", "scope_input_swap", "wrong_target_argv", "detached_prepared_manifest", "contradictory_stop", "duplicate_input"):
            with self.subTest(name=name):
                scope = json.loads(json.dumps(baseline_scope))
                result = json.loads(json.dumps(baseline_result))
                prepared = json.loads(json.dumps(baseline_prepared))
                local_snapshot = json.loads(json.dumps(snapshot))
                if name == "wrong_result_scope":
                    save()
                    result["scope_sha256"] = "0" * 64
                    (receipt / "RESULT.json").write_bytes(json.dumps(result).encode())
                else:
                    if name == "scope_input_swap": scope["inputs"][0]["sha256"] = "0" * 64
                    if name == "wrong_target_argv": scope["argv"][0] = "test"
                    if name == "detached_prepared_manifest":
                        prepared["files"][0]["sha256"] = "0" * 64
                        local_snapshot["files"][0]["sha256"] = "0" * 64
                        (receipt / "MANIFEST.json").write_bytes(json.dumps(prepared).encode())
                        scope["inputs"][4]["sha256"] = builder.sha256(receipt / "MANIFEST.json")
                    if name == "contradictory_stop": result["job_active_zero"] = False
                    if name == "duplicate_input": scope["inputs"].append(dict(scope["inputs"][0]))
                    save()
                with self.assertRaises(RuntimeError):
                    builder.qualification_original_build(main, binding, local_snapshot)
                (receipt / "MANIFEST.json").write_bytes(json.dumps(baseline_prepared).encode())

    def test_helper_sources_and_new_test_are_snapshot_inputs(self):
        self.assertIn("cmd/researchos-qualification-helper/", builder.SOURCE_PREFIXES)
        self.assertIn("tests/desktop/test_qualification_build.py", builder.ALLOWLIST)


if __name__ == "__main__":
    unittest.main()
