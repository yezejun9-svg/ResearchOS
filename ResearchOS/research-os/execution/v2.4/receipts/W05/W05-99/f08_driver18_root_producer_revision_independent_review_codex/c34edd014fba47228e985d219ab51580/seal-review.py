import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve().parent

def read(name):
    return json.loads((OWN / name).read_text(encoding="utf-8"))

def pin(path):
    p = Path(path)
    raw = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def save_new(name, value):
    with (OWN / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

review = read("review.json")
before = read("input-pins.before.json")
assert len(before["refs"]) == 32
assert review["decision"] == "REQUEST_CHANGES"
assert len(review["critical"]) == 1 and len(review["important"]) == 2
checks = []
for expected in before["refs"]:
    actual = pin(expected["path"])
    checks.append({
        "expected": expected, "actual": actual,
        "sha_bytes_equal": expected["sha256"] == actual["sha256"] and expected["bytes"] == actual["bytes"],
        "path_string_equal": expected["path"] == actual["path"]
    })
drift = sum(not x["sha_bytes_equal"] for x in checks)
save_new("input-pins.after.json", {
    "schema": "researchos.driver18-root-producer-revision-review-input-pins-after.v1",
    "frozen_ref_count": len(checks), "sha_or_bytes_drift_count": drift,
    "path_dictionary_inequality_count": sum(not x["path_string_equal"] for x in checks),
    "checks": checks, "target_execution": 0, "live_canonical_reads": 0
})
names = ["REVIEW.md", "counterexamples.NOT_RUN.json", "input-pins.before.json", "input-pins.after.json",
         "byte-AST-inverse.original.json", "readonly-IO.original.json", "failure-origins.json"]
handoff = {
    "schema": "researchos.driver18-root-producer-revision-independent-review-handoff.v1",
    "reviewer": "codex:/root/f08_whole_scope_review", "non_author": True,
    "status": "STOPPED", "decision": "REQUEST_CHANGES",
    "critical_count": 1, "important_count": 2,
    "required_fix_ids": ["R01-REV", "R02-REV", "R03-REV"],
    "review_ref": pin(OWN / "review.json"),
    "readable_review_ref": pin(OWN / "REVIEW.md"),
    "evidence_refs": {name: pin(OWN / name) for name in names},
    "source_ref": review["source_ref"],
    "author_handoff_ref": review["author_handoff_ref"],
    "author_manifest_ref": review["author_manifest_ref"],
    "prior_REQUEST_ref": review["prior_REQUEST_ref"],
    "prior_request_unchanged": True,
    "required_new_inputs_ref": review["required_new_inputs_ref"],
    "input_count": len(checks), "sha_or_bytes_drift_count": drift,
    "Python_AST_only": True, "source_inverse_hunks": 17,
    "original_function_AST_unchanged": 24,
    "author_13_controls": "NOT_RUN", "independent_8_controls": "NOT_RUN",
    "original_metadata_IO_calls": 7,
    "original_metadata_IO_exits": "outer0/Python0 via explicit exit $LASTEXITCODE; pure IO seal final result is separate original tool evidence.",
    "new_failure_origins": [], "new_origin_count": 0,
    "author_original_native_NULL_preserved": True, "old_failure_counters_untouched": True,
    "actual_Root_tuple_catalog_review_capture_prepare_proof": "OPEN",
    "actual_A01_A07": "NOT_RUN", "actual_registration": False, "actual_grant": False,
    "actual_driver_execution": False, "target_Go_SQL_Job_CAS_network_calls": 0,
    "I17": "OPEN_NOT_AUTHORIZED", "full18": "NOT_QUALIFIED", "full_callbacks": "OPEN",
    "SQL24_adoption": False, "source_acceptance": False, "formal_increment": 0,
    "live_canonical_reads": 0, "canonical_writes": 0, "other_namespace_writes": 0,
    "manifest_path": str(OWN / "manifest.json"), "manifest_self_excluded": True
}
save_new("handoff.json", handoff)
members = [pin(p) for p in sorted(OWN.iterdir(), key=lambda p: p.name) if p.is_file() and p.name != "manifest.json"]
assert len(members) == 10
save_new("manifest.json", {
    "schema": "researchos.driver18-root-producer-revision-independent-review-manifest.v1",
    "namespace": str(OWN), "self_excluded": True, "member_count": len(members), "members": members
})
assert all(pin(x["path"]) == x for x in read("manifest.json")["members"])
print(json.dumps({
    "status": "STOPPED", "decision": "REQUEST_CHANGES",
    "critical_count": 1, "important_count": 2,
    "frozen_ref_count": len(checks), "sha_or_bytes_drift_count": drift,
    "manifest_member_count": len(members), "new_origin_count": 0,
    "refs": {name: pin(OWN / name) for name in ("review.json", "REVIEW.md", "handoff.json", "manifest.json", "failure-origins.json", "input-pins.after.json")}
}, ensure_ascii=False))

