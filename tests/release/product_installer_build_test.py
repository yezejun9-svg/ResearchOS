"""Focused source-side checks for static P1a payload construction."""
import importlib.util
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
