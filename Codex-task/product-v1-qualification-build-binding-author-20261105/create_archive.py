from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/作品集/ResearchOS/research-os")
WORKTREE = ROOT / ".local/worktrees/product-v1-qualification-build-binding-20261105"
OUT = Path(__file__).parent
FILES = [
    "apps/desktop/build-development.py",
    "tests/desktop/test_qualification_build.py",
    "docs/installation/desktop-development.md",
]
BASELINE = {
    "apps/desktop/build-development.py": "f571ef6b73b8e7e2ce94113c6749b0aac0a5e1851f59dc7fbb2eafd213690032",
    "tests/desktop/test_qualification_build.py": "ABSENT_BEFORE",
    "docs/installation/desktop-development.md": "d58c3842e922abe2b480779853119203029b5809816f9fd761044269bd4d6a6b",
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def diff(path: str, old: bytes, new: bytes) -> str:
    old_lines = old.decode("utf-8").splitlines(keepends=True)
    new_lines = new.decode("utf-8").splitlines(keepends=True)
    assert not old or old.endswith(b"\n")
    assert not new or new.endswith(b"\n")
    assert b"\r" not in old and b"\r" not in new
    header = [f"diff --git a/{path} b/{path}\n"]
    if not old:
        header.append("new file mode 100644\n")
    if not new:
        header.append("deleted file mode 100644\n")
    left = "/dev/null" if not old else f"a/{path}"
    right = "/dev/null" if not new else f"b/{path}"
    return "".join(header + list(difflib.unified_diff(old_lines, new_lines, fromfile=left, tofile=right)))


entries = []
forward = []
inverse = []
for rel in FILES:
    old = b"" if BASELINE[rel] == "ABSENT_BEFORE" else (ROOT / rel).read_bytes()
    raw = (WORKTREE / rel).read_bytes()
    if BASELINE[rel] != "ABSENT_BEFORE":
        assert digest(old) == BASELINE[rel]
        write(OUT / "baseline" / rel, old)
    write(OUT / "source" / rel, raw)
    entries.append({"path": rel, "baseline_sha256": BASELINE[rel], "source_sha256": digest(raw)})
    forward.append(diff(rel, old, raw))
    inverse.append(diff(rel, raw, old))
write(OUT / "changes.patch", "".join(forward).encode("utf-8"))
write(OUT / "changes.inverse.patch", "".join(inverse).encode("utf-8"))

scope = ROOT / "execution/product-v1/receipts/single-harness-20261104/qualification-build-binding/scope.json"
contracts = {
    rel: digest((ROOT / rel).read_bytes())
    for rel in (
        "execution/product-v1/contracts/native-qualification-build.v1.md",
        "execution/product-v1/contracts/native-qualification-build-review.v1.json",
    )
}
diagnostics = {
    "schema": "researchos.qualification-build-binding-author-diagnostics.v1",
    "author_checks": ["Python ast.parse on both scoped Python files: PASS", "Baseline SHA256 readback: PASS"],
    "author_executions": {"python_unit": 0, "build": 0, "go": 0, "helper": 0, "native": 0, "model": 0},
    "worktree_git_access": "Managed sandbox git reported bare/unavailable and console rendered Unicode replacement characters. Root separately reported escalated read-only Git verified inside-work-tree=true, exact worktree top-level, and raw .git UTF-8 without replacement characters. No Git metadata repair or config change was made by author.",
    "helper_original_build_receipt_source": "Validated required --mu-common public Main, then read-only execution/product-v1/receipts/single-harness-20261104/native-helper-build01/{RESULT,POSTCHECK,scope,MANIFEST}.json; never assumed those receipts are present in the clean source worktree.",
    "remaining": ["Root-supervised standard-library Python unit test", "Independent exact-three-file source review", "Root-owned full development build", "Native qualification and model execution remain separately closed"],
}
write(OUT / "DIAGNOSTICS.json", (json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
manifest = {
    "schema": "researchos.qualification-build-binding-source-candidate.v1",
    "status": "FROZEN_SOURCE_AST_ONLY_PENDING_ROOT_PURE_TEST_AND_REVIEW",
    "base_head": "61fe2d6a9f9ecbdd8a9de597ffbb6757e49de667",
    "worktree": str(WORKTREE),
    "scope_sha256": digest(scope.read_bytes()),
    "contract_sha256": contracts,
    "files": entries,
    "forward_patch_sha256": digest((OUT / "changes.patch").read_bytes()),
    "inverse_patch_sha256": digest((OUT / "changes.inverse.patch").read_bytes()),
    "diagnostics_sha256": digest((OUT / "DIAGNOSTICS.json").read_bytes()),
    "prebuilt_helper_expected_sha256": "4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef",
    "prebuilt_helper_expected_bytes": 5335552,
    "proposed_pure_test_argv": ["python.exe", "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests/desktop", "-p", "test_qualification_build.py", "-v"],
    "python_unit": "NOT_RUN_BY_AUTHOR",
    "build_helper_native_model": "NOT_RUN_BY_AUTHOR",
    "formal_acceptance": False,
    "product_acceptance": False,
}
write(OUT / "MANIFEST.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
write(OUT / "FROZEN.txt", b"Exact-three-file qualification build-binding candidate frozen. AST-only author check; no unit/build/Native/model execution.\n")
print(digest((OUT / "MANIFEST.json").read_bytes()))
