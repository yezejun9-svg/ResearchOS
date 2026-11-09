from pathlib import Path
import hashlib
import json
import re
import shutil

root = Path(r"C:\Users\yqyyds\Documents\Codex\2026-11-04\task")
source = root / "native-normal-home-binding-20261105"
review = root / "native-normal-home-binding-independent-review-20261105"
run = root / "product-v1-owned-verification-20261104" / "runs" / "product-v1-native-normal-home-tests-01"
scope = root / "product-v1-owned-verification-20261104" / "scopes" / "product-v1-native-normal-home-tests-01.json"
registration = root / "product-v1-native-normal-home-tests-01-registration" / "REGISTRATION.json"
archive = root / "native-normal-home-binding-final-evidence-20261105"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert not archive.exists(), f"new archive already exists: {archive}"
assert sha(source / "manifest.json") == "2a9376dd6c91d20344abeecd48153d2d5f16ca53f8a4c147a9d96f3078b197e6"
assert sha(review / "REVIEW.json") == "fafb5dd1a74f1b24b27ba53d924cb992777c74fac47d03279aa51ccf18b78f97"
assert sha(scope) == "5ec98d727ccd8329e400f187a36bb998c8a7b7894026b454389368fce234461a"

source_manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
for rel, expected in source_manifest["files"].items():
    assert sha(source / rel) == expected, rel

result = json.loads((run / "RESULT.json").read_text(encoding="utf-8"))
assert result["status"] == "COMPLETED_OWNED_JOB_STOPPED"
assert result["scope_sha256"] == sha(scope)
assert result["root_exit_code"] == 0 and result["job_active_zero"] and result["stop_proved"]
assert not result["timed_out"] and not result["input_drift"] and result["terminate_job_attempts"] == 0
for item in result["raw"]:
    assert sha(run / item["file"]) == item["sha256"]

stdout = (run / "stdout.raw").read_text(encoding="utf-8")
top_pass = len(re.findall(r"(?m)^--- PASS:", stdout))
sub_pass = len(re.findall(r"(?m)^    --- PASS:", stdout))
assert top_pass == 6 and sub_pass == 35
assert not re.search(r"(?m)^(--- FAIL:|    --- FAIL:|--- SKIP:|    --- SKIP:|FAIL$)", stdout)

copies = {}
for name in ("codex_qualification_windows.go", "codex_qualification_capture_windows.go",
             "codex_qualification_windows_test.go", "codex_qualification_capture_windows_test.go"):
    copies[f"source/baseline/{name}"] = source / "baseline" / name
    copies[f"source/candidate/{name}"] = source / "candidate" / name
for name in ("forward.patch", "inverse.patch", "diagnostics.json", "scope.json", "contract.json", "manifest.json", "archive-file-list.json"):
    copies[f"source/{name}"] = source / name
for name in ("REVIEW.json", "hash-evidence.json", "archive-file-list.json", "author-source-map.json", "author-scope.json", "author-manifest.json", "author-forward.patch", "author-diagnostics.json"):
    copies[f"review/{name}"] = review / name
copies.update({
    "test/scope.json": scope,
    "test/REGISTRATION.json": registration,
    "test/CONSUMED.json": run / "CONSUMED.json",
    "test/RESULT.json": run / "RESULT.json",
    "test/stdout.raw": run / "stdout.raw",
    "test/stderr.raw": run / "stderr.raw",
})

archive.mkdir()
for rel, original in copies.items():
    target = archive / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, target)
    assert sha(target) == sha(original), rel

source_map = {
    "schema": "researchos.native-normal-home-binding-source-map.v1",
    "source_head": "998fc6330ba735056cd31f8ebf68dd50a8251c1b",
    "original_candidate_manifest_sha256": sha(source / "manifest.json"),
    "exact_source_files": [
        {"repo_path": rel, "baseline_archive_path": f"source/baseline/{Path(rel).name}",
         "candidate_archive_path": f"source/candidate/{Path(rel).name}",
         "baseline_sha256": sha(source / "baseline" / Path(rel).name),
         "candidate_sha256": sha(source / "candidate" / Path(rel).name)}
        for rel in (
            "adapters/runtime/codex_qualification_windows.go",
            "adapters/runtime/codex_qualification_capture_windows.go",
            "adapters/runtime/codex_qualification_windows_test.go",
            "adapters/runtime/codex_qualification_capture_windows_test.go",
        )
    ],
}
(archive / "source-mapping.json").write_text(json.dumps(source_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

diagnostics = {
    "schema": "researchos.native-normal-home-binding-final-evidence.v1",
    "source_candidate": "four exact leased files, preserved from original candidate manifest 2a9376dd",
    "static_review": "APPROVED_SOURCE_FIXTURE_ONLY, REVIEW.json SHA256 fafb5dd1a74f1b24b27ba53d924cb992777c74fac47d03279aa51ccf18b78f97",
    "test_scope_sha256": sha(scope),
    "test_observation": {"top_level_pass": top_pass, "subtest_pass": sub_pass, "fail": 0, "skip": 0,
                         "root_exit_code": result["root_exit_code"], "job_total_processes": result["job_total_processes"],
                         "job_active_zero": result["job_active_zero"], "stop_proved": result["stop_proved"],
                         "timed_out": result["timed_out"], "input_drift": result["input_drift"],
                         "terminate_job_attempts": result["terminate_job_attempts"]},
    "historical_markers": "REGISTRATION and CONSUMED retain their original prelaunch status text; RESULT and raw stdout preserve the later completed outcome.",
    "limits": "Go fixture PASS and static source approval do not establish formal product acceptance, real HOME alias safety, or live Native qualification. Original flow01 remains consumed and failed.",
    "new_execution": "none; archive operation copied and hashed C-workspace evidence only",
}
(archive / "diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

payload = {p.relative_to(archive).as_posix(): sha(p) for p in sorted(archive.rglob("*")) if p.is_file()}
manifest = {"schema": "researchos.native-normal-home-binding-final-archive.v1", "root": str(root),
            "archive": archive.relative_to(root).as_posix(), "files": payload}
(archive / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# This root-form selection is for Root's C-workspace tools. It deliberately
# contains only paths beneath root; repo-relative source paths live in the
# separate source-mapping.json file above.
selected = {"root": str(root), "files": [
    {"path": (archive.relative_to(root) / rel).as_posix(), "sha256": digest}
    for rel, digest in sorted({**payload, "manifest.json": sha(archive / "manifest.json")}.items())
]}
(archive / "archive-file-list.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for item in selected["files"]:
    path = root / item["path"]
    assert path.is_file() and path.resolve().is_relative_to(root.resolve())
    assert sha(path) == item["sha256"]
assert len(selected["files"]) == len(payload) + 1
print(json.dumps({"archive": str(archive), "payload_files": len(payload), "selected_files": len(selected["files"]),
                  "manifest_sha256": sha(archive / "manifest.json"), "selection_sha256": sha(archive / "archive-file-list.json"),
                  "test_top_pass": top_pass, "test_sub_pass": sub_pass}, ensure_ascii=False))
