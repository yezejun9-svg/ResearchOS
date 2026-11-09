import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "FINAL-manifest.json").read_text(encoding="utf-8"))
matrix = json.loads((root / "claim-test-matrix.json").read_text(encoding="utf-8"))
index = json.loads((root / "command-index.json").read_text(encoding="utf-8"))
source = Path(manifest["worktree"])
assert manifest["commit"] == "1d3cc504da79df5bf0f69755011738d5adb827b0"
assert len(manifest["source_allowlist"]) == 5
assert len(manifest["combined_source_paths"]) == 9
assert len(index["commands"]) == index["count"]
assert len({row["tag"] for row in index["commands"]}) == index["count"]
for item, info in manifest["patches"].items():
    raw = (root / info["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == info["sha256"], item
    assert len(raw) == info["bytes"], item
    assert raw.count(b"diff --git ") == len(info["source_paths"]), item
for path, info in manifest["source_hashes"].items():
    raw = (source / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == info["sha256"], path
    assert len(raw) == info["bytes"], path
indexed = {row["tag"]: row for row in index["commands"]}
for tag in manifest["passing_native_exit_zero"]:
    assert indexed[tag]["native_exit"] == 0, tag
for claim in matrix["claims"]:
    for tag in claim["evidence"]:
        assert tag in indexed, (claim["id"], tag)
assert matrix["formal_increment"] == manifest["formal_increment"] == 0
assert matrix["actual_authority"] is manifest["actual_authority"] is False
assert matrix["self_acceptance"] is manifest["self_acceptance"] is False
print(json.dumps({"verified": True, "indexed_commands": index["count"], "patch_path_counts": [5, 9], "source_sha256_count": len(manifest["source_hashes"]), "claim_count": len(matrix["claims"])}))
