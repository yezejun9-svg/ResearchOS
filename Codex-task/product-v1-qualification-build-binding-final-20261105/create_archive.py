import hashlib
import json
from pathlib import Path
from shutil import copy2

C = Path(r"C:/Users/yqyyds/Documents/Codex/2026-11-04/task")
OUT = Path(__file__).parent
AUTHOR = C / "product-v1-qualification-build-binding-author-20261105-rev2"
RUNS = C / "product-v1-owned-verification-20261104"
RUN = RUNS / "runs/product-v1-qualification-build-tests-02"
SCOPE = RUNS / "scopes/product-v1-qualification-build-tests-02.json"
REG = C / "product-v1-qualification-build-tests-02-registration/REGISTRATION.json"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

source_manifest = json.loads((AUTHOR / "MANIFEST.json").read_text(encoding="utf-8"))
scope = json.loads(SCOPE.read_text(encoding="utf-8"))
result = json.loads((RUN / "RESULT.json").read_text(encoding="utf-8"))
registration = json.loads(REG.read_text(encoding="utf-8"))
assert sha(AUTHOR / "MANIFEST.json") == "78f3fca2e98997fc3aaf4f6e878adc2db9394c0f3edc146fe19f4d712f66f191"
assert sha(SCOPE) == "de3da1adfe74912e3ffbf905186919e8c2379095bf03068d515f0e1d0d1c3432"
assert registration["scope_sha256"] == sha(SCOPE) and registration["source_manifest_sha256"] == sha(AUTHOR / "MANIFEST.json")
assert result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and result["root_exit_code"] == 0
assert result["stop_proved"] and result["job_active_zero"] and not result["input_drift"] and not result["errors"]
stderr = (RUN / "stderr.raw").read_text(encoding="utf-8")
assert "Ran 8 tests" in stderr and "OK" in stderr and "FAILED" not in stderr and "skipped" not in stderr.lower()
scope_hashes = {item["sha256"] for item in scope["inputs"]}
rows = []

def copy(source, relative):
    dest = OUT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(source, dest)
    assert dest.read_bytes() == source.read_bytes()
    rows.append({"path": relative, "sha256": sha(dest)})

for item in source_manifest["files"]:
    src = AUTHOR / "source" / item["path"]
    assert sha(src) == item["source_sha256"] and item["source_sha256"] in scope_hashes
    copy(src, "source/" + item["path"])
    if item["baseline_sha256"] != "ABSENT_BEFORE":
        base = AUTHOR / "baseline" / item["path"]
        assert sha(base) == item["baseline_sha256"]
        copy(base, "baseline/" + item["path"])
for name in ("MANIFEST.json", "changes.patch", "changes.inverse.patch", "DIAGNOSTICS.json", "FROZEN.txt"):
    copy(AUTHOR / name, "rev2/" + name)
for src, name in ((SCOPE, "scope.json"), (REG, "REGISTRATION.json"),
                  (RUN / "RESULT.json", "RESULT.json"), (RUN / "CONSUMED.json", "CONSUMED.json"),
                  (RUN / "stdout.raw", "stdout.raw"), (RUN / "stderr.raw", "stderr.raw")):
    copy(src, "test02/" + name)

manifest = {
    "schema": "researchos.qualification-build-binding-final-source-fixture.v1",
    "status": "SOURCE_AND_PURE_TEST_ONLY_PENDING_INDEPENDENT_REVIEW",
    "source_manifest_sha256": sha(AUTHOR / "MANIFEST.json"),
    "test_scope_sha256": sha(SCOPE),
    "registration_sha256": sha(REG),
    "result_status": result["status"],
    "root_exit_code": result["root_exit_code"],
    "stop_proved": result["stop_proved"],
    "input_drift": result["input_drift"],
    "pure_python_tests": 8,
    "files": rows,
    "build_helper_native_model": "NOT_RUN_BY_SOURCE3_TEST02",
    "formal_acceptance": False,
    "product_acceptance": False,
}
(OUT / "MANIFEST.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
(OUT / "FROZEN.txt").write_bytes(b"Exact Source3 rev2 and original pure Python test02 receipts; source/fixture scope only.\n")
selection = {
    "schema": "researchos.review-archive-selection/1",
    "root": str(C),
    "review": OUT.name,
    "files": [{"path": (OUT / relative).relative_to(C).as_posix(), "sha256": sha(OUT / relative)}
              for relative in ["MANIFEST.json", "FROZEN.txt"] + [row["path"] for row in rows]],
}
(OUT / "archive-file-list.json").write_bytes((json.dumps(selection, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"manifest_sha256": sha(OUT / "MANIFEST.json"),
                  "archive_file_list_sha256": sha(OUT / "archive-file-list.json"), "selected_files": len(selection["files"])}, ensure_ascii=False))
