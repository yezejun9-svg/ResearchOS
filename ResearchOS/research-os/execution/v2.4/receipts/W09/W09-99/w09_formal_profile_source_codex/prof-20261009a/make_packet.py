"""Seal this Source-only packet. Run with locked Python; never adopts targets."""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
R = P.parents[6]


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write_json(name, value):
    (P / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


before = P / "formal_case_index.before.py"
after = P / "formal_case_index.after.py"
profile = P / "formal_profile_w09.after.py"
assert before.read_bytes() == (R / "execution/v2.4/formal_case_index.py").read_bytes()
assert not (R / "execution/v2.4/formal_profile_w09.py").exists()
assert before.read_bytes()[:51719] == after.read_bytes()[:51719]

left = before.read_text(encoding="utf-8").splitlines(keepends=True)
right = after.read_text(encoding="utf-8").splitlines(keepends=True)
(P / "formal_case_index.forward.diff").write_text(
    "".join(difflib.unified_diff(left, right, fromfile="formal_case_index.before.py",
                                  tofile="formal_case_index.after.py")), encoding="utf-8")
(P / "formal_case_index.inverse.diff").write_text(
    "".join(difflib.unified_diff(right, left, fromfile="formal_case_index.after.py",
                                  tofile="formal_case_index.before.py")), encoding="utf-8")

artifacts = ["formal_case_index.before.py", "formal_case_index.after.py",
             "formal_profile_w09.after.py", "formal_case_index.forward.diff",
             "formal_case_index.inverse.diff", "source_controls.py", "source-controls.json",
             "source-contract.json", "REPORT.md", "failure-origin-958.txt",
             "failure-origin-unassigned-native-report-read.txt", "failure-origin-964-mapping.json",
             "make_packet.py"]
manifest = {
    "schema": "researchos.w09-formal-profile-source-manifest.v1",
    "scope": "SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ADOPTION",
    "packet": str(P),
    "target_before": {
        "execution/v2.4/formal_case_index.py": pin(R / "execution/v2.4/formal_case_index.py"),
        "execution/v2.4/formal_profile_w09.py": {"state": "ABSENT"},
    },
    "proposed_after": {"execution/v2.4/formal_case_index.py": pin(after),
                       "execution/v2.4/formal_profile_w09.py": pin(profile)},
    "complete_byte_inverse": pin(before),
    "w07_compat_prefix": {"bytes": 51719,
                          "sha256": hashlib.sha256(after.read_bytes()[:51719]).hexdigest()},
    "artifacts": [pin(P / name) for name in artifacts],
    "source_controls": "SYNTHETIC_NONAUTHORITATIVE",
    "source_proof_guards_open": 0,
    "actual_native_executions": 0,
    "formal_acceptance": False,
    "canonical_writes": False,
}
write_json("MF.json", manifest)
handoff = {
    "schema": "researchos.w09-formal-profile-source-handoff.v1",
    "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "manifest_ref": pin(P / "MF.json"),
    "report_ref": pin(P / "REPORT.md"),
    "contract_ref": pin(P / "source-contract.json"),
    "candidate_refs": [pin(after), pin(profile)],
    "original_index_ref": pin(before),
    "failure_origin_refs": [pin(P / "failure-origin-958.txt"),
                            pin(P / "failure-origin-unassigned-native-report-read.txt"),
                            pin(P / "failure-origin-964-mapping.json")],
    "only_source_namespace_written": True,
    "root_adoption_required": True,
    "formal_acceptance": False,
    "STOP": True,
    "FINAL": True,
}
write_json("HDF.json", handoff)
print(json.dumps({"status": "SOURCE_SEALED_NOT_ADOPTED", "manifest": pin(P / "MF.json"),
                  "handoff": pin(P / "HDF.json")}, ensure_ascii=False))
