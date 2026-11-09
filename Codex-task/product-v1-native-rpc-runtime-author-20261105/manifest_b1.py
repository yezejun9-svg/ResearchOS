"""Hash the final immutable B1 archive and prove the two-token rev6 inverse."""
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
old = (root.parent / "test04-passed" / "codex_rpc_protocol_test.go").read_bytes()
new = (root / "source" / "codex_rpc_protocol_test.go").read_bytes()
inverse = new.replace(b"text_elements", b"textElements")
if new.count(b"text_elements") != 2 or inverse != old:
    raise SystemExit("rev6 fixture inverse proof failed")
sha = lambda raw: hashlib.sha256(raw).hexdigest()
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != "ARCHIVE.json":
        raw = path.read_bytes()
        files.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw), "sha256": sha(raw)})
manifest = {
    "scope": "PRODUCT_V1_NATIVE_RPC_RUNTIME",
    "base_head": "c3c7812347bb72930365fbb5db0efee8a965bc78",
    "source_manifest": "SOURCE.json",
    "rev6_fixture_inverse": {
        "path": "adapters/runtime/codex_rpc_protocol_test.go",
        "old_test04_sha256": sha(old),
        "new_sha256": sha(new),
        "exact_replacements": 2,
        "forward": "textElements -> text_elements",
        "inverse_restores_test04_bytes": True,
    },
    "receipts": {
        "test01": "CHILD_NONZERO_STOPPED (fixture assertion), preserved",
        "test02": "COMPLETED_OWNED_JOB_STOPPED",
        "test03": "COMPLETED_OWNED_JOB_STOPPED",
        "test04": "COMPLETED_OWNED_JOB_STOPPED",
    },
    "native_invocations": 0,
    "model_invocations": 0,
    "formal_increment": 0,
    "files": files,
}
(root / "ARCHIVE.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(len(files), sha((root / "ARCHIVE.json").read_bytes()))
