"""Focused source-side checks for static P1a payload construction."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

MODULE = Path(__file__).resolve().parents[2] / "ops/release/product_installer/build.py"
spec = importlib.util.spec_from_file_location("product_installer_build", MODULE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildValidationTests(unittest.TestCase):
    def test_canonical_bytes_are_location_independent(self):
        left = {"files": [{"path": "中文 a", "bytes": 1}], "schema": "x"}
        right = {"schema": "x", "files": [{"bytes": 1, "path": "中文 a"}]}
        self.assertEqual(builder.encode(left), builder.encode(right))
        self.assertEqual(builder.digest(builder.encode(left)), builder.digest(builder.encode(right)))

    def test_rejects_unsafe_inventory_paths(self):
        good = {"path": "payload/good.txt", "sha256": "a" * 64, "bytes": 0}
        builder.validate_row(good)
        for name in ("../escape", "payload/../escape", "payload\\alias", "payload//alias",
                     "payload/file. ", "/absolute", "C:/absolute", "payload:stream"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.validate_row({**good, "path": name})

    def test_dotdot_escape_and_overlapping_roots_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, artifacts, receipts = (base / name for name in ("source", "artifacts", "receipts"))
            for path in (source, artifacts, receipts):
                path.mkdir()
            with self.assertRaisesRegex(ValueError, "noncanonical"):
                builder.validate_destinations(str(source), str(artifacts / ".." / "escape"),
                                              str(receipts / "run"), str(artifacts), str(receipts))
            with self.assertRaisesRegex(ValueError, "overlap"):
                builder.validate_destinations(str(source), str(source / "output"),
                                              str(receipts / "run"), str(source), str(receipts))

    def test_junction_ancestor_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, actual, link, receipts = (base / name for name in
                                              ("source", "actual-artifacts", "link-artifacts", "receipts"))
            for path in (source, actual, receipts):
                path.mkdir()
            setup = subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(link), str(actual)],
                                   capture_output=True)
            self.assertEqual(setup.returncode, 0, setup.stderr)
            with self.assertRaisesRegex(ValueError, "reparse"):
                builder.validate_destinations(str(source), str(link / "output"),
                                              str(receipts / "run"), str(link), str(receipts))

    def test_preexisting_receipts_remain_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, artifacts, receipts = (base / name for name in ("source", "artifacts", "receipts"))
            for path in (source, artifacts, receipts):
                path.mkdir()
            occupied = receipts / "run"
            occupied.mkdir()
            sentinel = occupied / "sentinel.txt"
            sentinel.write_bytes(b"do not touch")
            args = SimpleNamespace(candidate=str(source), output=str(artifacts / "new"),
                                   receipts=str(occupied), go="unused", scope="unused")
            before = {path.name: path.read_bytes() for path in occupied.iterdir()}
            with self.assertRaisesRegex(ValueError, "create-new") as raised:
                builder.build(args, authorized_roots=(str(artifacts), str(receipts)))
            self.assertFalse(builder.write_owned_failure(args, raised.exception))
            self.assertEqual(before, {path.name: path.read_bytes() for path in occupied.iterdir()})
            self.assertFalse((artifacts / "new").exists())


if __name__ == "__main__":
    unittest.main()
