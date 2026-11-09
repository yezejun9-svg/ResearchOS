from pathlib import Path
import hashlib
import json
import subprocess

QA = Path(__file__).resolve().parent
WT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-path-entry-20261105")
BASE = "71396f932d0ccc7035f3fdb4896e3c7ecc8f6343"
FILES = ["internal/host/native_folder_windows.go", "internal/host/native_folder_windows_test.go"]
GIT = ["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false", "--no-optional-locks"]

def git(*args):
    result = subprocess.run(GIT + list(args), cwd=WT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    assert not result.stderr, result.stderr.decode("utf-8", errors="replace")
    return result.stdout

assert git("rev-parse", "HEAD").decode().strip() == BASE
status = git("status", "--porcelain=v1", "--untracked-files=all")
expected_status = {" M " + rel for rel in FILES}
assert set(status.decode("utf-8").splitlines()) == expected_status, status
assert set(git("diff", "--name-only").decode().splitlines()) == set(FILES)
git("diff", "--check")
checks = json.loads((QA / "checks.json").read_text(encoding="utf-8"))
assert [x["stage"] for x in checks["checks"]] == ["focused-test", "vet", "final-compile", "final-vet"]
assert all(x["exit_code"] == 0 for x in checks["checks"])

freeze = QA / "freeze"
freeze.mkdir(exist_ok=False)
hashes = {}
for rel in FILES:
    data = (WT / rel).read_bytes()
    hashes[rel] = hashlib.sha256(data).hexdigest()
    dest = freeze / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
patch = git("diff", "--binary", "HEAD", "--", *FILES)
(freeze / "candidate.diff").write_bytes(patch)
(freeze / "status.raw.txt").write_bytes(status)
events = [json.loads(line) for line in (QA / "focused-test.stdout.log").read_text(encoding="utf-8").splitlines() if line.startswith("{")]
passed = sorted({e["Test"] for e in events if e.get("Action") == "pass" and e.get("Test")})
assert passed and not any(e.get("Action") in ("fail", "skip") for e in events), events[-3:]
manifest = {
    "status": "FROZEN_SOURCE_NOT_INDEPENDENTLY_ACCEPTED",
    "scope_id": "PRODUCT_V1_NATIVE_PATH_ENTRY",
    "owner": "codex:/root/native_picker_path_entry",
    "base_head": BASE,
    "worktree": str(WT),
    "files_sha256": hashes,
    "patch_sha256": hashlib.sha256(patch).hexdigest(),
    "checks": checks["checks"],
    "final_warning": checks["final_warning"],
    "passed_top_level_tests": [x for x in passed if "/" not in x],
    "passed_subtests": [x for x in passed if "/" in x],
    "gui_runs": 0, "model_runs": 0, "formal_increment": 0, "product_acceptance_increment": 0,
    "limitations": ["Fake UI effects prove callback dispatch, not real Shell path-entry UX.", "Root independent source review, fresh build and owned GUI validation remain pending."],
}
for rel, digest in hashes.items():
    assert hashlib.sha256((WT / rel).read_bytes()).hexdigest() == digest
(freeze / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"freeze": str(freeze), "sha256": hashes, "top_level_tests": len(manifest["passed_top_level_tests"]), "subtests": len(manifest["passed_subtests"]), "status": manifest["status"]}, ensure_ascii=False))
