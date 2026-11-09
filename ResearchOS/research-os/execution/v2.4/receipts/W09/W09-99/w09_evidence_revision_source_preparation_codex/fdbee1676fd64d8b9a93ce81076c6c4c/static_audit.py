"""Pure IO and AST audit for this source proposal; never imports candidates."""
import ast
import difflib
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OLD = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_evidence_implementation_source_proposal_codex/9bc40daa1dba4b628892ebb7188b70b4"
REVIEW = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_evidence_implementation_independent_source_review_codex/c18ea962f1048f32363faae671d89f05/review.json"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def emit(name, value):
    (HERE / name).write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())


def diff(old, new, a, b):
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        fromfile=a, tofile=b, n=3))


rows = []
mapping = [
    ("domain_test.proposed.go", "internal/domain/domain_test.go", "domain_test.proposed.go"),
    ("retrieval_test.proposed.go", "internal/domain/retrieval_test.go", "retrieval_test.proposed.go"),
    ("retrieval.proposed.py", "ops/ci/retrieval.py", "retrieval.proposed.py"),
    ("w09_evidence_export_test.proposed.go", "internal/domain/w09_evidence_export_test.go", "w09_evidence_export_test.proposed.go"),
    ("w09_formal_router.v4.proposed.py", "ops/ci/w09_formal_router.py", "w09_formal_router.v3.proposed.py"),
    ("w09_evidence_closure.py", "ops/ci/w09_evidence_closure.py", None),
]
for candidate, target, previous in mapping:
    current = HERE / candidate
    target_path = ROOT / target
    basis = target_path if target_path.is_file() else None
    old = basis.read_text(encoding="utf-8") if basis else ""
    new = current.read_text(encoding="utf-8")
    basis_copy = None
    if basis:
        basis_copy = HERE / "basis" / target
        basis_copy.parent.mkdir(parents=True, exist_ok=True)
        if basis_copy.exists():
            assert basis_copy.read_bytes() == basis.read_bytes(), "BASIS_MAIN_DRIFT"
        else:
            basis_copy.write_bytes(basis.read_bytes())
    forward = diff(old, new, str(basis.relative_to(ROOT)) if basis else "/dev/null", target)
    inverse = diff(new, old, target, str(basis.relative_to(ROOT)) if basis else "/dev/null")
    (HERE / (candidate + ".forward.diff")).write_text(forward, encoding="utf-8")
    (HERE / (candidate + ".inverse.diff")).write_text(inverse, encoding="utf-8")
    if candidate.endswith(".py"):
        tree = ast.parse(new, filename=str(current))
        compile(tree, str(current), "exec", dont_inherit=True)
    previous_path = OLD / previous if previous else None
    previous_delta = None
    if previous_path and previous_path.is_file():
        previous_delta_path = HERE / (candidate + ".v3-to-v4.diff")
        previous_delta_path.write_text(diff(previous_path.read_text(encoding="utf-8"), new,
                                           str(previous_path.relative_to(ROOT)), target), encoding="utf-8")
        previous_delta = pin(previous_delta_path)
    rows.append({"candidate": pin(current), "target_path": target, "basis": pin(basis) if basis else None,
                 "frozen_basis_copy": pin(basis_copy) if basis_copy else None,
                 "prior_v3_candidate": pin(previous_path) if previous_path and previous_path.is_file() else None,
                 "v3_to_v4_diff": previous_delta,
                 "forward_diff": pin(HERE / (candidate + ".forward.diff")),
                 "inverse_diff": pin(HERE / (candidate + ".inverse.diff")),
                 "same_as_basis": old == new})

review = pin(REVIEW)
assert review["sha256"] == "2de40ba6334959f6d7c641cbe7b970ce3da1e58dbea6d274f74b8d9c349c76ac"
emit("static_audit.json", {"schema": "researchos.w09-v4-static-audit.v1", "status": "SOURCE_ONLY_AST_PASS",
                           "python_imported": False, "go_executed": False, "native_executed": False,
                           "candidate_executed": False, "formal_accepted_delta": 0,
                           "prior_v3_review": review, "files": rows})
print(json.dumps({"status": "SOURCE_ONLY_AST_PASS", "file_count": len(rows),
                  "review_sha256": review["sha256"]}, ensure_ascii=False))
