import hashlib
import json
from pathlib import Path

p = Path(__file__).resolve().parent
names = [
    "B-author-report.md",
    "B-diagnostic-ledger.md",
    "B-evidence-manifest.json",
    "B-whole-source.patch",
    "b91-commit.command.json",
    "b91-commit.result.json",
    "b91-commit.stdout.raw",
    "b91-commit.stderr.raw",
    "b78-final-focused.result.json",
    "b78-final-focused.stdout.raw",
    "b105-existing-regression.result.json",
    "b105-existing-regression.stdout.raw",
    "b92-head.result.json",
    "b93-status.result.json",
    "b94-commit-check.result.json",
    "b97-tree.result.json",
    "b106-final-status.result.json",
]
files = {}
for name in names:
    raw = (p / name).read_bytes()
    files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
final = {
    "schema": "researchos.qualification-failure-B-source-final-index.v1",
    "status": "AUTHOR_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW",
    "base_commit": "f48fca0e4013bda19913a34d91da0cd23157a08b",
    "candidate_commit": "75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603",
    "candidate_tree": "ba3f9d4c101df39ab17856158d5fc72a9f0600ce",
    "clean_worktree": "b106-final-status.result.json",
    "source_scope_paths": 9,
    "formal_increment": 0,
    "files": files,
}
out = p / "FINAL.json"
out.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
raw = out.read_bytes()
print("FINAL.json sha256=" + hashlib.sha256(raw).hexdigest() + " bytes=" + str(len(raw)))
