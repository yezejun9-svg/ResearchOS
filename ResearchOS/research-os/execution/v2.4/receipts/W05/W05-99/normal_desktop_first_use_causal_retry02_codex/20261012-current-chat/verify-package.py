"""Read-only byte and scope verification of the CP430 assembled package."""
import hashlib
import json
import pathlib

RECEIPT = pathlib.Path(__file__).resolve().parent
composition = json.loads((RECEIPT / "composition.json").read_text(encoding="utf-8"))
root = pathlib.Path(composition["package_root"])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = composition["package_files"]
expected = {row["path"]: row for row in rows}
actual = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
if set(actual) != set(expected) or len(actual) != 58:
    raise SystemExit(f"package inventory mismatch: expected={len(expected)} actual={len(actual)}")
for relative, file in actual.items():
    row = expected[relative]
    if file.is_symlink() or sha(file) != row["sha256"] or file.stat().st_size != row["bytes"]:
        raise SystemExit(f"package file drift: {relative}")
descriptor = json.loads((root / "apps/desktop/resources/client-wire/descriptor.json").read_text(encoding="utf-8"))
if descriptor["build_input_digest"] != composition["desktop_full_input_digest"]:
    raise SystemExit("full input binding drift")
for row in descriptor["exact_module_source_inventory"]:
    file = root / "apps/desktop" / row["path"]
    if sha(file) != row["sha256"]:
        raise SystemExit(f"module descriptor drift: {row['path']}")
for row in descriptor["compiled_React_asset_inventory"]:
    file = root / "apps/web/dist" / row["path"]
    if sha(file) != row["sha256"] or file.stat().st_size != row["bytes"]:
        raise SystemExit(f"React descriptor drift: {row['path']}")
manifest = root / "apps/desktop/resources/control/runtime-verifier-installation.json"
config = json.loads(manifest.read_text(encoding="utf-8"))
verifier = root / "apps/desktop/resources/control/runtime-verifier.exe"
if config["executable"] != str(verifier) or config["executable_hash"] != "sha256:" + sha(verifier):
    raise SystemExit("absolute verifier installation binding drift")
acl = json.loads((RECEIPT / "manifest-acl.json").read_text(encoding="utf-8"))
if not acl["protected"] or acl["rule_count"] != 1 or acl["file_sha256"] != sha(manifest):
    raise SystemExit("installation manifest ACL evidence mismatch")
out = {
    "schema": "researchos.cp430-package-readonly-verification.v1",
    "status": "COMPONENTS_HASHED_NOT_LAUNCHED",
    "package_root": str(root),
    "package_file_count": len(actual),
    "desktop_module_count": len(descriptor["exact_module_source_inventory"]),
    "react_asset_count": len(descriptor["compiled_React_asset_inventory"]),
    "public_host_asset_count": len(composition["public_host_assets"]),
    "full_input_digest": descriptor["build_input_digest"],
    "validator_sha256": descriptor["binary_sha256"],
    "installation_manifest_sha256": sha(manifest),
    "acl_protected_current_sid_single_ace": True,
    "model_calls": 0,
    "activation": "NOT_STARTED",
}
with (RECEIPT / "verification.json").open("x", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(json.dumps(out, ensure_ascii=False))
