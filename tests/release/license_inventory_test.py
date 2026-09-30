#!/usr/bin/env python3
"""Small stdlib self-check for npm lock and installed license inventory."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.release.build import npm_licenses


def package(root, name, metadata, documents=()):
    directory = root / "apps/web/node_modules" / name
    directory.mkdir(parents=True)
    (directory / "package.json").write_text(json.dumps(metadata), encoding="utf-8")
    for filename, content in documents:
        (directory / filename).write_bytes(content)


def demo():
    with tempfile.TemporaryDirectory(prefix="researchos-license-inventory-") as temporary:
        root = Path(temporary)
        lock_packages = {
            "": {"name": "fixture"},
            "node_modules/rolldown": {"version": "1.2.11", "license": "MIT"},
            "node_modules/@rolldown/binding-win32-x64-msvc": {
                "version": "1.2.11", "license": "MIT", "optional": True,
                "os": ["win32"], "cpu": ["x64"]},
            "node_modules/@rolldown/binding-linux-x64-gnu": {
                "version": "1.2.11", "license": "MIT", "optional": True,
                "os": ["linux"], "cpu": ["x64"]},
            "node_modules/required-missing": {"version": "2.0.0", "license": "MIT"},
            "node_modules/mismatch": {"version": "1.0.0", "license": "MIT"},
        }
        lock = root / "apps/web/package-lock.json"
        lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({"packages": lock_packages}), encoding="utf-8")
        package(root, "rolldown", {"name": "rolldown", "version": "1.2.11", "license": "MIT"},
                (("LICENSE", b"parent license"), ("THIRD-PARTY-LICENSE", b"third-party license")))
        package(root, "@rolldown/binding-win32-x64-msvc", {
            "name": "@rolldown/binding-win32-x64-msvc", "version": "1.2.11", "license": "MIT"})
        package(root, "mismatch", {"name": "mismatch", "version": "2.0.0", "license": "Apache-2.0"},
                (("LICENSE", b"wrong-version license"),))

        files = {}
        modules, gaps = npm_licenses(root, files)
        by_name = {module["name"]: module for module in modules}
        optional = by_name["@rolldown/binding-linux-x64-gnu"]
        assert optional["installation_status"] == "OPTIONAL_NOT_INSTALLED"
        assert not any(optional["name"] in gap for gap in gaps)

        parent = by_name["rolldown"]["license_texts"]
        assert [entry["source_file"] for entry in parent] == ["LICENSE", "THIRD-PARTY-LICENSE"]
        assert all(hashlib.sha256(files[entry["file"]]).hexdigest() == entry["sha256"] for entry in parent)

        binding = by_name["@rolldown/binding-win32-x64-msvc"]
        assert binding["declared_license"] == "MIT"
        assert binding["license_texts"] == []
        assert any(binding["name"] in gap and "license text unavailable" in gap for gap in gaps)

        mismatch = by_name["mismatch"]
        assert mismatch["installation_status"] == "VERSION_MISMATCH"
        assert mismatch["declared_license"] == "MIT"
        assert mismatch["license_texts"] == []
        assert any("required-missing" in gap for gap in gaps)


if __name__ == "__main__":
    demo()
    print("license inventory self-check: PASS")
