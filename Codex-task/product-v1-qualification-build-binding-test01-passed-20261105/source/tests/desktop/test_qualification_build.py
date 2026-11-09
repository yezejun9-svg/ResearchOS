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

    def test_prebuilt_receipt_is_distinct_from_current_go_list(self):
        binding = builder.qualification_inputs(self.args())
        main = self.base / "main"
        receipt = main / builder.QUALIFICATION_HELPER_BUILD_RECEIPT
        receipt.mkdir(parents=True)
        (receipt / "scope.json").write_text("{}\n", encoding="utf-8")
        selected = {"cmd/researchos-qualification-helper/main_windows.go": "a" * 64,
                    "internal/qualificationprobe/plan.go": "b" * 64, "go.mod": "c" * 64, "go.sum": "d" * 64}
        snapshot = {"files": [{"path": path, "sha256": sha} for path, sha in selected.items()]}
        prepared = {"source_head": "synthetic", "files": [{"path": "source/" + path, "sha256": sha} for path, sha in selected.items()]}
        result = {"status": "COMPLETED_OWNED_JOB_STOPPED", "root_exit_code": 0,
                  "stop_proved": True, "input_drift": False, "errors": []}
        post = {"status": "BUILT_NOT_EXECUTED_NOT_NATIVE_QUALIFIED", "stop_proved": True,
                "model_native_helper_execution": False, "scope_sha256": builder.sha256(receipt / "scope.json"),
                "sha256": self.expected, "bytes": len(self.helper_bytes), "path": str(self.helper)}
        for name, value in (("MANIFEST.json", prepared), ("RESULT.json", result), ("POSTCHECK.json", post)):
            (receipt / name).write_text(json.dumps(value), encoding="utf-8")
        provenance = builder.qualification_original_build(main, binding, snapshot)
        self.assertEqual(provenance["provenance"], "PREBUILT_ORIGINAL_OWNED_BUILD_RECEIPT_NOT_CURRENT_GO_LIST")
        snapshot["files"][0]["sha256"] = "e" * 64
        with self.assertRaises(RuntimeError):
            builder.qualification_original_build(main, binding, snapshot)

    def test_helper_sources_and_new_test_are_snapshot_inputs(self):
        self.assertIn("cmd/researchos-qualification-helper/", builder.SOURCE_PREFIXES)
        self.assertIn("tests/desktop/test_qualification_build.py", builder.ALLOWLIST)


if __name__ == "__main__":
    unittest.main()
