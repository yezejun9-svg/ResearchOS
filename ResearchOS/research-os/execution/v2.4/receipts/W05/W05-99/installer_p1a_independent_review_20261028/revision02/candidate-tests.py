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
                                   receipts=str(occupied), go="unused", scope="unused",
                                   scope_sha256="unused")
            before = {path.name: path.read_bytes() for path in occupied.iterdir()}
            with self.assertRaisesRegex(ValueError, "create-new") as raised:
                builder.build(args, authorized_roots=(str(artifacts), str(receipts)))
            self.assertFalse(builder.write_owned_failure(args, raised.exception))
            self.assertEqual(before, {path.name: path.read_bytes() for path in occupied.iterdir()})
            self.assertFalse((artifacts / "new").exists())

    def test_explicit_pin_accepts_new_scope_path_and_new_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first_art, first_receipt, second_art, second_receipt = (
                base / name for name in ("artifacts-a", "receipts-a", "artifacts-b", "receipts-b"))
            for root in (first_art, first_receipt, second_art, second_receipt):
                root.mkdir()
            def scope_for(artifact, receipt, schema):
                return {"schema": schema, "owner": builder.SCOPE_OWNER,
                        "worktree": str(builder.ROOT), "artifact_root": str(artifact),
                        "receipt_root": str(receipt)}
            first = builder.encode(scope_for(first_art, first_receipt,
                "researchos.installer-p1a-exact4-revision-scope.v1"))
            first_path, copy_path, new_path = (base / name for name in
                                               ("scope-a.json", "scope-copy.json", "scope-new.json"))
            first_path.write_bytes(first)
            copy_path.write_bytes(first)
            pin = builder.digest(first)
            self.assertEqual(builder.bound_roots(str(first_path), pin),
                             (str(first_art), str(first_receipt)))
            self.assertEqual(builder.bound_roots(str(copy_path), pin),
                             (str(first_art), str(first_receipt)))
            second = builder.encode(scope_for(second_art, second_receipt,
                "researchos.installer-p1a-exact2-scope-admission-revision.v1"))
            new_path.write_bytes(second)
            self.assertEqual(builder.bound_roots(str(new_path), builder.digest(second)),
                             (str(second_art), str(second_receipt)))

    def test_wrong_pin_and_scope_shape_refuse_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, artifact, receipts = (base / name for name in ("source", "artifact", "receipts"))
            for root in (source, artifact, receipts):
                root.mkdir()
            scope = {"schema": "researchos.installer-p1a-exact2-scope-admission-revision.v1",
                     "owner": builder.SCOPE_OWNER, "worktree": str(builder.ROOT),
                     "artifact_root": str(artifact), "receipt_root": str(receipts)}
            path = base / "scope.json"
            raw = builder.encode(scope)
            path.write_bytes(raw)
            output, receipt = artifact / "candidate", receipts / "run"
            args = SimpleNamespace(scope=str(path), scope_sha256="0" * 64,
                                   candidate=str(source), output=str(output),
                                   receipts=str(receipt), go="unused")
            for bad_pin in ("", "not-a-digest", "0" * 64):
                args.scope_sha256 = bad_pin
                with self.assertRaises(ValueError):
                    builder.build(args)
                self.assertFalse(output.exists())
                self.assertFalse(receipt.exists())
            for changed in ({**scope, "schema": "unrecognized"},
                            {**scope, "owner": "other"},
                            {**scope, "artifact_root": str(artifact / ".." / "escape")},
                            {**scope, "receipt_root": str(artifact)}):
                payload = builder.encode(changed)
                path.write_bytes(payload)
                args.scope_sha256 = builder.digest(payload)
                with self.assertRaises(ValueError):
                    builder.build(args)
                self.assertFalse(output.exists())
                self.assertFalse(receipt.exists())
            path.write_bytes(raw + b" ")
            args.scope_sha256 = builder.digest(raw)
            with self.assertRaises(ValueError):
                builder.build(args)
            self.assertFalse(output.exists())
            self.assertFalse(receipt.exists())


if __name__ == "__main__":
    unittest.main()
