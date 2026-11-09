"""Seal the current seven-file Desktop candidate without rewriting r2 records."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-main7d-native-20261025")
spec = importlib.util.spec_from_file_location("build_development", ROOT / "apps/desktop/build-development.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(name, value):
    with (HERE / name).open("xb") as out:
        out.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


freeze = read(HERE / "SOURCE-FREEZE-03.json")
source = builder.source_snapshot()
assert source["digest"] == freeze["source_snapshot_digest"]
assert set(source["candidate_delta"]) == builder.ALLOWLIST
assert digest(HERE / "SOURCE-FREEZE-03.patch") == freeze["patch"]["sha256"]
for row in source["files"]:
    if row["path"] in builder.ALLOWLIST:
        assert row["sha256"] == freeze["seven_file_hashes"][row["path"]]["sha256"]
build = read(HERE / "build-02/result.json")
manifest = read(HERE / "build-02/development-manifest.json")
assert build["status"] == "BUILT_NOT_NATIVE_TESTED"
assert not build["source_drift"] and not build["public_vendor_drift"]
assert build["manifest_sha256"] == digest(HERE / "build-02/development-manifest.json")
assert manifest["source"]["digest"] == freeze["source_snapshot_digest"]
assert manifest["source"]["seven_scoped_source_sha256"] == {
    path: row["sha256"] for path, row in freeze["seven_file_hashes"].items()
}
for stem in ["source", "mu-vendor-5083", "mu-compiled-inputs", "core-verifier-go-inputs"]:
    assert read(HERE / f"build-02/{stem}.before.json") == read(HERE / f"build-02/{stem}.after.json")
for folder in (HERE / "build-02/commands").iterdir():
    if folder.is_dir():
        assert read(folder / "result.json")["native_exit"] == 0
checks = [
    "focused-03.pre-python-bundle-tests", "focused-04.pre-launcher-check",
    "focused-04.pre-launcher-smoke-tests", "build-02.pre-build",
    "postbuild-03.pre-python-built-bundle", "postbuild-03.pre-node-sealed-dryrun",
    "postbuild-03.pre-nearest-desktop-tests", "resources-02.pre-installed-resources",
    "precommit-02.pre-init-temp-index", "precommit-02.pre-patch-apply-cached-check",
]
for stem in checks:
    assert (HERE / f"{stem}.native-exit.txt").read_text(encoding="ascii").strip() == "0", stem
assert Path(build["output"]).joinpath("development-manifest.json").read_bytes() == \
    (HERE / "build-02/development-manifest.json").read_bytes()
assert not (ROOT / ".local/desktop-state-dryrun-20261025-02").exists()
status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=no"],
                        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8", "replace").splitlines()
assert all(line[3:].replace("\\", "/") in builder.ALLOWLIST for line in status), status
prior = read(HERE / "diagnostics.json")
diagnostics = {
    "schema": "researchos.desktop-complete-tree-diagnostics-r3.v1",
    "previous_diagnostics_sha256": digest(HERE / "diagnostics.json"),
    "previous_precommit_sha256": digest(HERE / "PRECOMMIT-MANIFEST.json"),
    "attempts": [
        {"id": "r2-self-review", "status": "SUPERSEDED", "reason": "stdout UTF-8 chunks could split a Chinese renderer title; original r2 build remains historical"},
        {"id": "focused-04", "status": "PASSED", "native_exits": [0, 0], "coverage": "split Chinese codepoint, no newline, incomplete UTF-8 tail"},
        {"id": "freeze-03", "status": "FROZEN", "manifest": "SOURCE-FREEZE-03.json"},
        {"id": "build-02", "status": "BUILT_NOT_NATIVE_TESTED", "native_exit": 0},
        {"id": "postbuild-03", "status": "PASSED_WITH_SKIP", "native_exits": [0, 0, 0]},
        {"id": "resources-02", "status": "PURE_STATIC_PASS", "native_exit": 0},
        {"id": "precommit-02", "status": "PATCH_CHECK_PASS", "native_exits": [0, 0]},
        {"id": "seal-02", "status": "FAILED", "native_exit": 1, "reason": "receipt-only seal script incorrectly assumed staged added files were absent from tracked porcelain; corrected allowlist check in seal-03"},
    ],
    "formal_increment": 0,
    "native_GUI_Core_started": False,
    "original_data_or_credentials_accessed": False,
}
put("diagnostics-r3.json", diagnostics)
precommit = {
    "schema": "researchos.desktop-complete-tree-precommit-r3.v1",
    "base_commit": freeze["base_commit"], "base_tree": freeze["base_tree"],
    "scope_sha256": freeze["scope_sha256"],
    "seven_file_source_hashes": freeze["seven_file_hashes"],
    "source_snapshot_digest": freeze["source_snapshot_digest"],
    "patch_sha256": freeze["patch"]["sha256"],
    "build_result_sha256": digest(HERE / "build-02/result.json"),
    "development_manifest_sha256": build["manifest_sha256"],
    "go_compiled_input_manifest_sha256": digest(HERE / "build-02/core-verifier-go-inputs.before.json"),
    "mu_vendor_5083_manifest_sha256": digest(HERE / "build-02/mu-vendor-5083.before.json"),
    "mu_compiled_input_manifest_sha256": digest(HERE / "build-02/mu-compiled-inputs.before.json"),
    "checked_runtime_resources_sha256": digest(HERE / "resources-02.pre-installed-resources.stdout.raw"),
    "dry_run_sha256": digest(HERE / "postbuild-03.pre-node-sealed-dryrun.stdout.raw"),
    "diagnostics_sha256": digest(HERE / "diagnostics-r3.json"),
    "git_apply_cached_check_exit": 0,
    "source_worktree_tracked_dirty": status,
    "status": "CANDIDATE_PRECOMMIT_NO_NATIVE_ACCEPTANCE",
}
put("PRECOMMIT-MANIFEST-r3.json", precommit)
print(json.dumps({"precommit_sha256": digest(HERE / "PRECOMMIT-MANIFEST-r3.json"),
                  "diagnostics_sha256": precommit["diagnostics_sha256"],
                  "source_snapshot_digest": source["digest"],
                  "files": len(freeze["seven_file_hashes"])}, ensure_ascii=False))
