"""Mock/source checks for the complete Desktop development builder.

The real build and its manifest are checked separately. These tests never
start Electron, Core or a provider.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import types
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "apps/desktop/build-development.py"
spec = importlib.util.spec_from_file_location("desktop_build_development", SOURCE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DevelopmentBundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="ros-desktop-development-mock-"))

    def tearDown(self):
        target = self.temp.resolve()
        base = Path(tempfile.gettempdir()).resolve()
        self.assertTrue(target.is_relative_to(base) and target.name.startswith("ros-desktop-development-mock-"))
        def writable_then_remove(operation, name, error):
            if not isinstance(error, PermissionError):
                raise error
            os.chmod(name, stat.S_IWRITE)
            operation(name)
        shutil.rmtree(target, onexc=writable_then_remove)

    def test_sqlite_closure_rejects_gap_and_missing_next(self):
        migrations = self.temp / "migrations/sqlite"
        migrations.mkdir(parents=True)
        (migrations / "0001_bootstrap.sql").write_text("SELECT 1;", encoding="utf-8")
        (migrations / "0003_other.sql").write_text("SELECT 3;", encoding="utf-8")
        (migrations / "next_v24_sessions.sql").write_text("SELECT 4;", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "continuous numbered"):
            builder.validate_migrations(self.temp)
        (migrations / "0002_domain.sql").write_text("SELECT 2;", encoding="utf-8")
        self.assertEqual(len(builder.validate_migrations(self.temp)), 4)
        (migrations / "next_v24_sessions.sql").unlink()
        with self.assertRaisesRegex(RuntimeError, "continuous numbered"):
            builder.validate_migrations(self.temp)

    def test_exact_copy_and_tree_refuse_redirected_source(self):
        source = self.temp / "source"
        source.mkdir()
        (source / "file.txt").write_bytes(b"one")
        self.assertEqual(builder.copy_tree(source, self.temp / "output"), 1)
        self.assertEqual((self.temp / "output/file.txt").read_bytes(), b"one")
        with self.assertRaisesRegex(RuntimeError, "output collision"):
            builder.copy_tree(source, self.temp / "output")
        alias = source / "alias.txt"
        try:
            os.symlink(source / "file.txt", alias)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Windows symlink fixture unavailable: {error}")
        with self.assertRaisesRegex(RuntimeError, "redirected"):
            builder.copy_tree(source, self.temp / "other")

    def test_source_snapshot_covers_new_delta_and_refuses_outside_scope(self):
        repo = self.temp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        for relative in builder.ALLOWLIST:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        subprocess.run(["git", "-C", str(repo), "add", "apps/desktop/main/main.js"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "fixture"], check=True, capture_output=True)
        prior = builder.ROOT
        try:
            builder.ROOT = repo
            snapshot = builder.source_snapshot()
            self.assertEqual(len(snapshot["candidate_delta"]), 6)
            self.assertEqual(len(snapshot["files"]), 7)
            (repo / "apps/desktop/launch-development.mjs").write_bytes(b"changed")
            self.assertNotEqual(builder.source_snapshot()["digest"], snapshot["digest"])
            (repo / "outside.txt").write_bytes(b"unauthorized")
            with self.assertRaisesRegex(RuntimeError, "outside frozen scope"):
                builder.source_snapshot()
        finally:
            builder.ROOT = prior

    def test_wrong_locked_tool_fails_before_output_creation(self):
        fake = self.temp / "wrong-go.exe"
        fake.write_bytes(b"wrong")
        args = types.SimpleNamespace(go=str(fake), node=r"C:\nvm4w\nodejs\node.exe",
            electron_dist=str(ROOT / "apps/desktop/node_modules/electron/dist"),
            module_cache=str(ROOT / ".local/tools/gopath/pkg/mod"), web_modules=str(ROOT / "apps/web/node_modules"),
            mu_common=str(ROOT), output=str(ROOT / ".local/wrong-tool-should-not-exist"),
            receipts=str(self.temp / "receipts"))
        with self.assertRaisesRegex(RuntimeError, "locked go"):
            builder.build(args)
        self.assertFalse((self.temp / "receipts").exists())

    def test_actual_build_manifest_when_explicitly_supplied(self):
        directory = os.environ.get("RESEARCHOS_DEVELOPMENT_BUNDLE")
        if not directory:
            self.skipTest("real builder outcome is checked after creation")
        bundle = Path(directory)
        manifest = json.loads((bundle / "development-manifest.json").read_bytes())
        self.assertEqual(manifest["schema"], builder.SCHEMA)
        self.assertEqual(manifest["source"]["head"], "7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e")
        self.assertEqual(manifest["core"]["migration_count"], 25)
        self.assertEqual(manifest["mu"]["vendored_files_verified"], 5083)
        self.assertGreaterEqual(manifest["electron"]["file_count"], 75)
        self.assertEqual(manifest["files"], builder.inventory(bundle))


if __name__ == "__main__":
    unittest.main()
