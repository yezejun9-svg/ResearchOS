import hashlib
import json
from pathlib import Path
from shutil import copy2

C = Path(r"C:/Users/yqyyds/Documents/Codex/2026-11-04/task")
OUT = Path(__file__).parent
AUTHOR = C / "product-v1-qualification-build-binding-author-20261105"
RUNS = C / "product-v1-owned-verification-20261104"
RUN = RUNS / "runs/product-v1-qualification-build-tests-01"
SCOPE = RUNS / "scopes/product-v1-qualification-build-tests-01.json"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

candidate = json.loads((AUTHOR / "MANIFEST.json").read_text(encoding="utf-8"))
scope = json.loads(SCOPE.read_text(encoding="utf-8"))
result = json.loads((RUN / "RESULT.json").read_text(encoding="utf-8"))
assert sha(SCOPE) == "949c489086b4400ca8d6541788335987654cd1c051c13f393cdb8720a4364ae0"
assert result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and result["root_exit_code"] == 0
assert result["stop_proved"] and result["job_active_zero"] and not result["input_drift"] and not result["errors"]
stderr = (RUN / "stderr.raw").read_text(encoding="utf-8")
assert "Ran 7 tests" in stderr and "OK" in stderr and "FAILED" not in stderr and "skipped" not in stderr.lower()
scope_inputs = {row["sha256"] for row in scope["inputs"]}
files = []
for item in candidate["files"]:
    src = AUTHOR / "source" / item["path"]
    assert sha(src) == item["source_sha256"] and item["source_sha256"] in scope_inputs
    dest = OUT / "source" / item["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(src, dest)
    files.append({"path": dest.relative_to(OUT).as_posix(), "sha256": sha(dest)})
for source, relative in [
    (AUTHOR / "MANIFEST.json", "candidate/MANIFEST.json"),
    (AUTHOR / "changes.patch", "candidate/changes.patch"),
    (AUTHOR / "changes.inverse.patch", "candidate/changes.inverse.patch"),
    (AUTHOR / "DIAGNOSTICS.json", "candidate/DIAGNOSTICS.json"),
    (SCOPE, "test01/scope.json"),
    (RUN / "RESULT.json", "test01/RESULT.json"),
    (RUN / "CONSUMED.json", "test01/CONSUMED.json"),
    (RUN / "stdout.raw", "test01/stdout.raw"),
    (RUN / "stderr.raw", "test01/stderr.raw"),
]:
    dest = OUT / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(source, dest)
    files.append({"path": relative, "sha256": sha(dest)})
manifest = {
    "schema": "researchos.qualification-build-binding-test01-archive.v1",
    "status": "PURE_PYTHON_TEST01_PASS_SOURCE_REVIEW_BLOCKED_SUPERSEDED_BY_REV2",
    "candidate_manifest_sha256": sha(AUTHOR / "MANIFEST.json"),
    "test_scope_sha256": sha(SCOPE),
    "result_status": result["status"],
    "exit_code": result["root_exit_code"],
    "stop_proved": result["stop_proved"],
    "input_drift": result["input_drift"],
    "pure_python_tests": 7,
    "files": files,
    "build_helper_native_model": "NOT_RUN_BY_TEST01",
    "formal_acceptance": False,
    "product_acceptance": False,
}
(OUT / "MANIFEST.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(sha(OUT / "MANIFEST.json"))
