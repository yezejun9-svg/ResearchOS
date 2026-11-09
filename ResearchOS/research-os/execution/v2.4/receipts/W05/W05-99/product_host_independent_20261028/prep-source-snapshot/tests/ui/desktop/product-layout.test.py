"""Pure builder checks. This test never launches Electron, Core, or a CLI."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("product_builder", ROOT / "apps/desktop/build-product-layout.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class ProductLayoutBuilderTest(unittest.TestCase):
    def test_installation_id_changes_with_control_or_cli(self):
        binaries = {key: {"sha256": str(i) * 64} for i, key in
                    enumerate(("cli", "control", "electron", "verifier", "validator"), 1)}
        original = BUILDER.install_id("C:/product-A", "a" * 40, "b" * 64, "c" * 64,
                                      "2.4.0", "researchos-client/2", 24, binaries)
        self.assertEqual(len(original), 64)
        binaries["cli"]["sha256"] = "9" * 64
        self.assertNotEqual(original, BUILDER.install_id(
            "C:/product-A", "a" * 40, "b" * 64, "c" * 64,
            "2.4.0", "researchos-client/2", 24, binaries))
        self.assertNotEqual(original, BUILDER.install_id(
            "C:/product-B", "a" * 40, "b" * 64, "c" * 64,
            "2.4.0", "researchos-client/2", 24, {key: {"sha256": str(i) * 64}
            for i, key in enumerate(("cli", "control", "electron", "verifier", "validator"), 1)}))

    def test_build_refuses_output_outside_worktree_before_creating_receipts(self):
        with tempfile.TemporaryDirectory(prefix="researchos-product-test-") as tmp:
            output = Path(tmp) / "product"
            receipts = Path(tmp) / "receipts"
            args = SimpleNamespace(output=str(output), receipts=str(receipts))
            with self.assertRaisesRegex(RuntimeError, "product output must be new"):
                BUILDER.build(args)
            self.assertFalse(output.exists())
            self.assertFalse(receipts.exists())


if __name__ == "__main__":
    unittest.main()
