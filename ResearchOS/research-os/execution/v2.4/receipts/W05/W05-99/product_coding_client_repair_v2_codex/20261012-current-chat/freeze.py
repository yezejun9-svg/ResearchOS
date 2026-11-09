"""Freeze the C-bound build and local test evidence without rewriting prior receipts."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
D_ROOT = HERE.parents[6]
C_ROOT = pathlib.Path(r"C:\Users\yqyyds\.codex\researchos-build-worktrees\coding-client-v2-20261012")
C_BUILD = C_ROOT / ".local/builds/product-coding-client-repair-v2-20261012"
C_LOGS = C_ROOT / ".local/builds/product-coding-client-repair-v2-20261012-logs"
RAW = HERE / "raw"
COMMIT = "b20c816ec346c1dad1534b18b02abbb4f47c4628"


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: pathlib.Path, value) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=C_ROOT, text=True, encoding="utf-8").strip()


assert git("rev-parse", "HEAD") == COMMIT
assert git("status", "--porcelain") == ""
assert pathlib.Path(git("rev-parse", "--git-common-dir")).resolve() == (D_ROOT / ".git").resolve()
source = read_json(HERE / "source-bundle.json")
assert source["candidate_commit"] == COMMIT
for entry in source["source_files"]:
    relative = pathlib.Path(entry["path"])
    assert digest(C_ROOT / relative) == digest(D_ROOT / ".local/worktrees/w05-product-coding-client-repair-v2-20261012" / relative) == entry["sha256"]

for path in C_LOGS.iterdir():
    assert path.is_file() and digest(path) == digest(RAW / "c-bound-build-logs" / path.name)
descriptor_path = C_BUILD / "apps/desktop/resources/client-wire/descriptor.json"
assert digest(descriptor_path) == digest(RAW / "c-bound-descriptor.json")
result = read_json(C_LOGS / "result.json")
descriptor = read_json(descriptor_path)
assert result["status"] == "BUILT_NOT_TESTED" and result["source_acceptance"] is False
assert result["drift"] == []
assert result["build_input_digest"] == descriptor["build_input_digest"]
assert result["binary_sha256"] == descriptor["binary_sha256"]
assert len(read_json(C_LOGS / "inputs.before.json")) == len(read_json(C_LOGS / "inputs.after.json")) == 6439
assert digest(C_BUILD / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe") == result["binary_sha256"]
module_hashes = {entry["path"]: entry["sha256"] for entry in descriptor["exact_module_source_inventory"]}
for entry in source["source_files"]:
    if entry["path"].startswith("apps/desktop/"):
        assert module_hashes[entry["path"].removeprefix("apps/desktop/")] == entry["sha256"]

test_names = ["c-bound-boundary", "c-bound-validator-quoted", "c-bound-dom-normal", "c-bound-dom-status", "c-bound-dom-retry"]
tests = []
for name in test_names:
    invocation = read_json(RAW / f"{name}.invocation.json")
    assert invocation["exit"] == 0 and pathlib.Path(invocation["cwd"]).resolve() == C_ROOT.resolve()
    assert digest(RAW / f"{name}.stdout") == invocation["stdout_sha256"]
    assert digest(RAW / f"{name}.stderr") == invocation["stderr_sha256"]
    tests.append({"name": name, "exit": 0, "invocation_sha256": digest(RAW / f"{name}.invocation.json")})
assert "ℹ pass 25" in (RAW / "c-bound-boundary.stdout").read_text(encoding="utf-8")
assert "PASS" in (RAW / "c-bound-validator-quoted.stdout").read_text(encoding="utf-8")
for name in test_names[2:]:
    assert '"actual_model_calls":0' in (RAW / f"{name}.stdout").read_text(encoding="utf-8")

scope = D_ROOT / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp429/coding-client-c-build-scope.json"
binding = {
    "schema": "researchos.w05.desktop-coding-client-repair-v2-c-build-binding/1",
    "source_bundle_sha256": digest(HERE / "source-bundle.json"),
    "scope_sha256": digest(scope),
    "source_worktree": str(D_ROOT / ".local/worktrees/w05-product-coding-client-repair-v2-20261012"),
    "build_worktree": str(C_ROOT),
    "git_common_dir": str((D_ROOT / ".git").resolve()),
    "candidate_commit": COMMIT,
    "registered_source_files_verified": len(source["source_files"]),
    "build_input_count": 6439,
    "build_input_digest": result["build_input_digest"],
    "build_input_drift": result["drift"],
    "binary_sha256": result["binary_sha256"],
    "descriptor_sha256": digest(descriptor_path),
    "descriptor": str(descriptor_path),
    "build_result_sha256": digest(C_LOGS / "result.json"),
    "build_logs": str(C_LOGS),
    "tests": tests,
    "diagnostic_only": {"name": "c-bound-validator", "cause": "PowerShell split unquoted -test.v", "exit": 2},
    "evidence_class": "SOURCE_BOUND_BUILD_AND_LOCAL_FIXTURE_TESTS",
    "live_provider_qualification": False,
    "independent_review": "PENDING",
    "formal_acceptance_delta": 0,
    "parent_acceptance_delta": 0,
}
write_new(HERE / "c-build-binding.json", binding)

readme = """# Coding client repair v2 candidate

Commit `b20c816ec346c1dad1534b18b02abbb4f47c4628` fixes the reviewed desktop coding authorization races in seven authorized source/test paths. The original source bundle remains frozen. `c-build-binding.json` binds its eight registered files to the C build-only worktree, the shared Git object store, the 6,439 build inputs, the native binary, the descriptor, and the captured tests. The full build logs and descriptor are copied under `raw/`.

The source-bound build finished with zero input drift. Local tests passed: 25/25 desktop boundary assertions, compiled Go validator tests, and Chromium normal, STATUS recovery, and refresh-retry scenarios. Each browser run recorded zero actual model calls. The first compiled Go test invocation failed because PowerShell split the unquoted `-test.v` flag; its raw stderr and invocation are retained. The quoted retry passed.

These are source-bound local and synthetic UI results. The candidate has not been integrated into Main, installed into a managed Core, qualified against a live provider, independently reviewed, or formally accepted. Formal and parent acceptance deltas remain zero.
"""
with (HERE / "README.md").open("x", encoding="utf-8", newline="\n") as stream:
    stream.write(readme)

raw_entries = []
for path in sorted(RAW.rglob("*")):
    if path.is_file():
        raw_entries.append({"path": path.relative_to(HERE).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size})
raw_census = hashlib.sha256("".join(f"{e['path']}\t{e['sha256']}\t{e['bytes']}\n" for e in raw_entries).encode()).hexdigest()
manifest = {
    "schema": "researchos.w05.desktop-coding-client-repair-v2-receipt/1",
    "candidate_commit": COMMIT,
    "source_bundle_sha256": digest(HERE / "source-bundle.json"),
    "c_build_binding_sha256": digest(HERE / "c-build-binding.json"),
    "readme_sha256": digest(HERE / "README.md"),
    "raw_census_sha256": raw_census,
    "raw_files": len(raw_entries),
    "raw_bytes": sum(e["bytes"] for e in raw_entries),
    "build_input_digest": result["build_input_digest"],
    "binary_sha256": result["binary_sha256"],
    "tests": "25/25 boundary; Go validator pass; 3 Chromium synthetic scenarios pass",
    "actual_model_calls": 0,
    "claim": "Source-bound local candidate only; independent review and Main integration pending; formal acceptance delta 0",
}
write_new(HERE / "manifest.json", manifest)
print(json.dumps({"manifest_sha256": digest(HERE / "manifest.json"), "raw_files": len(raw_entries), "raw_bytes": manifest["raw_bytes"]}))
