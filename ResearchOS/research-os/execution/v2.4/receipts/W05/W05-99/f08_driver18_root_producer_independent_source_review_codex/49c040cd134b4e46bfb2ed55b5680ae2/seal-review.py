import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve().parent

def read(name):
    return json.loads((OWN / name).read_text(encoding="utf-8"))

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write_new(name, value):
    with (OWN / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

before = read("input-pins.before.json")
review = read("review.json")
origins = read("failure-origins.json")
assert len(before["refs"]) == 46
assert review["decision"] == "REQUEST_CHANGES"
assert len(review["critical"]) == 0 and len(review["important"]) == 3
assert origins["new_origin_count"] == 0
checks = []
for expected in before["refs"]:
    actual = pin(expected["path"])
    checks.append({"expected": expected, "actual": actual, "equal": actual == expected})
drift = [row for row in checks if not row["equal"]]
after = {
    "schema": "researchos.driver18-root-producer-review-input-pins-after.v1",
    "refs": [row["actual"] for row in checks],
    "checks": checks,
    "frozen_ref_count": len(checks),
    "drift_count": len(drift),
    "whole_frozen_files_rehashed": True,
    "canonical_or_target_access": False
}
write_new("input-pins.after.json", after)
names = [
    "review.json", "REVIEW.md", "coverage.json", "counterexamples.NOT_RUN.json",
    "input-pins.before.json", "input-pins.after.json",
    "author-pin-checks.original.json", "readonly-io.original.json", "failure-origins.json"
]
handoff = {
    "schema": "researchos.driver18-root-producer-independent-source-review-handoff.v1",
    "reviewer": "codex:/root/f08_whole_scope_review",
    "non_author": True,
    "status": "STOPPED",
    "decision": "REQUEST_CHANGES",
    "critical_count": 0,
    "important_count": 3,
    "required_fix_ids": ["R01", "R02", "R03"],
    "review_ref": pin(OWN / "review.json"),
    "readable_review_ref": pin(OWN / "REVIEW.md"),
    "evidence_refs": {name: pin(OWN / name) for name in names if name not in ("review.json", "REVIEW.md")},
    "source_ref": review["source_ref"],
    "author_handoff_ref": review["author_handoff_ref"],
    "author_manifest_ref": review["author_manifest_ref"],
    "author_annex_ref": review["author_annex_ref"],
    "A01_A07_mapping_ref": review["mapping_ref"],
    "frozen_consumers": review["frozen_consumers"],
    "frozen_ref_count": len(checks),
    "frozen_input_drift_count": len(drift),
    "source_AST_parse_only": True,
    "counterexamples": "Ten explicit logical NOT_RUN controls; no target execution.",
    "original_metadata_IO_calls": 7,
    "original_metadata_IO_outer_native": "All seven captured reads 0/0 via explicit exit $LASTEXITCODE. Final pure-IO seal response is external original tool evidence.",
    "new_failure_origins": [],
    "new_origin_count": 0,
    "old_failure_counters_untouched": True,
    "author_original_outer0_nativeNULL_unchanged": True,
    "actual_Root_tuple_catalog_reviews_prepared_proof": "OPEN",
    "actual_A01_A07_execution": "NOT_RUN",
    "actual_registration": False,
    "actual_grant": False,
    "actual_prepare": False,
    "actual_driver_execution": False,
    "source_acceptance": False,
    "driver_scope": "Partial17 I01-I16,I18 only; I17 FATAL_OPEN; full18 not qualified.",
    "formal_increment": 0,
    "SQL24_adoption": False,
    "full_callbacks": "OPEN",
    "canonical_reads": 0,
    "canonical_writes": 0,
    "author_and_other_original_namespaces_written": 0,
    "Main_module_cache_or_private_input_access": False,
    "CLI331_qualification_not_used_as_F08_authority": True,
    "manifest_path": str(OWN / "manifest.json"),
    "manifest_self_excluded": True
}
write_new("handoff.json", handoff)
members = [pin(path) for path in sorted(OWN.iterdir(), key=lambda item: item.name) if path.is_file() and path.name != "manifest.json"]
assert len(members) == 11
write_new("manifest.json", {
    "schema": "researchos.driver18-root-producer-independent-source-review-manifest.v1",
    "namespace": str(OWN),
    "self_excluded": True,
    "member_count": len(members),
    "members": members
})
manifest = read("manifest.json")
assert all(pin(row["path"]) == row for row in manifest["members"])
print(json.dumps({
    "status": "STOPPED",
    "decision": "REQUEST_CHANGES",
    "frozen_ref_count": len(checks),
    "frozen_input_drift_count": len(drift),
    "manifest_member_count": len(members),
    "critical_count": 0,
    "important_count": 3,
    "new_origin_count": 0,
    "refs": {name: pin(OWN / name) for name in ("review.json", "REVIEW.md", "handoff.json", "manifest.json", "failure-origins.json", "input-pins.after.json")}
}, ensure_ascii=False))

