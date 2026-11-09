"""Synthetic public directory/ENV units; no private pipe, helper, child or authority."""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import traceback
import unittest
from unittest import mock

BROKER = None
LOCAL = Path("D:/作品集/ResearchOS/research-os/.local")
TRIAL = LOCAL/"mu-sdk-isolated-project-ed84838046934329a76733a005c9b162"
FOUR = {"SystemRoot", "WINDIR", "TEMP", "TMP"}

class PublicEnvironmentBoundaryTests(unittest.TestCase):
    def setUp(self):
        if BROKER is None:
            raise RuntimeError("Root must supply and pin broker Source")
        self.temp = tempfile.TemporaryDirectory(prefix="broker-env-public-unit-", dir=LOCAL)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.system = self.root/"synthetic-system"
        self.system.mkdir()
        self.proof = self.root/"isolated-temp"
        self.proof.mkdir()
        self.env = {"SystemRoot": str(self.system), "WINDIR": str(self.system),
                    "TEMP": str(self.proof), "TMP": str(self.proof)}

    def bind_temp(self, value):
        env = dict(self.env)
        env["TEMP"] = env["TMP"] = value
        return env

    def reject(self, env):
        with self.assertRaises(ValueError):
            BROKER.require_public_environment(env)

    def test_exact_four_existing_isolated_keys(self):
        before = dict(self.env)
        self.assertIsNone(BROKER.require_public_environment(self.env))
        self.assertEqual(self.env, before)
        self.assertEqual(set(self.env), FOUR)

    def test_missing_each_public_key(self):
        for key in sorted(FOUR):
            with self.subTest(key=key):
                env = dict(self.env)
                del env[key]
                self.reject(env)

    def test_extra_secret_provider_profile_or_proof_key(self):
        for key in ("EXTRA_PUBLIC_KEY", "API_KEY", "PROVIDER_TOKEN", "USERPROFILE",
                    "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"):
            with self.subTest(key=key):
                env = dict(self.env)
                env[key] = "synthetic-public-test-value"
                self.reject(env)

    def test_old_two_key_request_is_rejected(self):
        self.reject({key: self.env[key] for key in ("SystemRoot", "WINDIR")})

    def test_environment_must_be_dictionary(self):
        for value in (None, "synthetic", ["SystemRoot", "WINDIR", "TEMP", "TMP"]):
            with self.subTest(kind=type(value).__name__):
                self.reject(value)

    def test_bad_type_empty_whitespace_or_NUL_for_each_value(self):
        for key in sorted(FOUR):
            for value in (None, 7, False, "", " \t", "synthetic\0value"):
                with self.subTest(key=key, kind=type(value).__name__, value_repr=repr(value)):
                    env = dict(self.env)
                    env[key] = value
                    self.reject(env)

    def test_temp_tmp_exact_binding_required(self):
        env = dict(self.env)
        env["TMP"] = str(self.system)
        self.reject(env)
        env["TMP"] = str(self.proof).upper()
        self.reject(env)

    def test_nonabsolute_temp(self):
        self.reject(self.bind_temp("synthetic-relative-temp"))

    def test_missing_temp_directory(self):
        self.reject(self.bind_temp(str(self.proof/"missing-directory")))

    def test_regular_file_is_not_temp_directory(self):
        public_file = self.root/"synthetic-public-file"
        public_file.write_text("synthetic public bytes", encoding="utf-8")
        self.reject(self.bind_temp(str(public_file)))

    def test_local_root_and_outside_root_rejected(self):
        self.reject(self.bind_temp(str(LOCAL)))
        self.reject(self.bind_temp(str(LOCAL.parent)))
        self.reject(self.bind_temp("Z:/synthetic-outside-researchos-local"))

    def test_alias_resolution_rejected_without_real_junction(self):
        original_resolve = Path.resolve
        def synthetic_alias(path, *args, **kwargs):
            if path == self.proof:
                return self.system
            return original_resolve(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", synthetic_alias):
            self.reject(dict(self.env))

    def test_alias_escape_resolution_rejected_without_real_junction(self):
        original_resolve = Path.resolve
        def synthetic_escape(path, *args, **kwargs):
            if path == self.proof:
                return LOCAL.parent
            return original_resolve(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", synthetic_escape):
            self.reject(dict(self.env))

    def test_noncanonical_dotdot_spelling_rejected(self):
        self.reject(self.bind_temp(str(self.proof)+"/../"+self.proof.name))

    def test_system_root_or_windir_overlap_rejected(self):
        for key in ("SystemRoot", "WINDIR"):
            for system_path in (self.proof, self.root):
                with self.subTest(key=key, relationship=str(system_path)):
                    env = dict(self.env)
                    env[key] = str(system_path)
                    self.reject(env)

    def test_system_directories_must_be_absolute_existing_canonical(self):
        for key in ("SystemRoot", "WINDIR"):
            for system_value in ("relative-system", str(self.root/"missing-system"),
                                 str(self.system)+"/../"+self.system.name):
                with self.subTest(key=key, system_value=system_value):
                    env = dict(self.env)
                    env[key] = system_value
                    self.reject(env)

    def test_trial_or_descendant_rejected_before_metadata(self):
        for path in (TRIAL, TRIAL/"synthetic-child", LOCAL):
            with self.subTest(path=str(path)):
                with mock.patch.object(Path, "resolve", side_effect=AssertionError("forbidden metadata traversal")):
                    with mock.patch.object(Path, "is_dir", side_effect=AssertionError("forbidden metadata traversal")):
                        self.reject(self.bind_temp(str(path)))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker-source", required=True)
    parser.add_argument("--broker-sha256", required=True)
    parser.add_argument("--verbosity", type=int, choices=(0, 1, 2), default=2)
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("Root Windows public boundary execution required")
    path = Path(args.broker_source)
    if not path.is_absolute() or str(path.resolve()).casefold() != str(path).casefold():
        raise ValueError("fixed absolute canonical public broker Source required")
    expected = args.broker_sha256
    if len(expected) != 64 or any(value not in "0123456789abcdef" for value in expected):
        raise ValueError("fixed bare SHA256 required")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("broker Source pin changed")
    spec = importlib.util.spec_from_file_location("root_reviewed_public_broker_env_units", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    global BROKER
    BROKER = module
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublicEnvironmentBoundaryTests)
    result = unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    code = 0
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
        code = 1
    finally:
        print("ROOT_PYTHON_EXIT="+str(code))
    sys.exit(code)
