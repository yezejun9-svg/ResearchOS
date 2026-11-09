"""Copy the completed development build's unique evidence into canonical receipts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
recipe = json.loads((HERE / "build-invocation.pre.json").read_bytes())
worktree = Path(recipe["cwd"])
argv = recipe["argv"]
output = Path(argv[argv.index("--output") + 1])
internal = Path(argv[argv.index("--receipts") + 1])
result = json.loads((internal / "result.json").read_bytes())
descriptor = json.loads(Path(result["descriptor"]).read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert (HERE / "builder.native-exit.txt").read_text(encoding="ascii").strip() == "0"
assert result["status"] == "BUILT_NOT_TESTED" and not result["source_acceptance"] and result["drift"] == []
assert result["build_input_digest"] == descriptor["build_input_digest"]
assert len(result["invocations"]) == 9 and all(item["exit"] == 0 for item in result["invocations"])
before = json.loads((internal / "inputs.before.json").read_bytes())
after = json.loads((internal / "inputs.after.json").read_bytes())
assert len(before) == len(after)
assert all(item["sha256"] == item["current_sha256"] for item in after)
assert subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=worktree, capture_output=True, check=True).stdout == b""

copied = []


def copy(source, relative):
    destination = HERE / "copied" / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists()
    shutil.copy2(source, destination)
    assert digest(source) == digest(destination)
    copied.append({"origin": str(source), "canonical": str(destination), "sha256": digest(source), "bytes": source.stat().st_size})


for source in sorted(internal.iterdir()):
    assert source.is_file() and not source.is_symlink()
    copy(source, Path("internal-builder-receipts") / source.name)

client = output / "apps/desktop/resources/client-wire"
copy(client / "descriptor.json", Path("artifacts/client-wire/descriptor.json"))
binary = client / "researchos-client-wire-validator.exe"
assert digest(binary) == descriptor["binary_sha256"] and binary.stat().st_size == descriptor["binary_bytes"]
copy(binary, Path("artifacts/client-wire") / binary.name)
for item in descriptor["compiled_React_asset_inventory"]:
    source = output / "apps/web/dist" / item["path"]
    assert digest(source) == item["sha256"] and source.stat().st_size == item["bytes"]
    copy(source, Path("artifacts/web-dist") / item["path"])
for relative in ["validator.test.exe", "fixtures/negative-child.go", "fixtures/negative-child.exe"]:
    copy(output / relative, Path("artifacts/auxiliary") / relative)

manifest = {
    "schema": "researchos.desktop-main7d-development-build-evidence.v1",
    "source_head": recipe["expected_head"],
    "source_tree": recipe["expected_tree"],
    "source_worktree_tracked_clean": True,
    "builder_native_exit": 0,
    "builder_result_status": result["status"],
    "source_acceptance": result["source_acceptance"],
    "input_count": len(before),
    "input_drift_count": 0,
    "subinvocations": len(result["invocations"]),
    "subinvocation_nonzero_count": 0,
    "build_input_digest": result["build_input_digest"],
    "binary_sha256": descriptor["binary_sha256"],
    "react_asset_count": len(descriptor["compiled_React_asset_inventory"]),
    "tools": descriptor["tools"],
    "output_root": str(output),
    "internal_receipt_root": str(internal),
    "copies": copied,
}
(HERE / "build-evidence-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({key: manifest[key] for key in ["input_count", "input_drift_count", "subinvocations", "react_asset_count", "binary_sha256", "source_worktree_tracked_clean"]}, ensure_ascii=False))
