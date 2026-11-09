"""Seal v3 Source handoff; no Canon, product, SQLite or child execution."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

N = Path(__file__).resolve().parent
B = N.parent.parent
V2 = N.parent / "s22public-20261009-01-v2"
REVIEW = B / "public22_actual_independent_review_codex" / "actual-01a1210b"
AUTHOR = "codex:/root/w09_formal_profile_source_impl"

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def same(left, right):
    return Path(left["path"]) == Path(right["path"]) and left["sha256"] == right["sha256"] and left["bytes"] == right["bytes"]

def checked(ref):
    assert same(ref, pin(ref["path"])), ref["path"]
    return Path(ref["path"])

def read(path):
    return json.loads(Path(path).read_bytes())

def write_new(name, value):
    path = N / name
    with path.open("xb") as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return pin(path)

def verify_pair(binding_path):
    binding_ref = pin(binding_path)
    binding = read(binding_path)
    capture_path = checked(binding["capture_ref"])
    lines = capture_path.read_bytes().splitlines(keepends=True)
    assert len(lines) == 4
    assert [hashlib.sha256(line).hexdigest() for line in lines] == binding["original_line_sha256"]
    assert [len(line) for line in lines] == binding["source_line_bytes"]
    rows = [json.loads(line) for line in lines]
    assert [row["ordinal"] for row in rows] == binding["source_ordinals"]
    assert rows[0]["type"] == "session_meta" and rows[0]["payload"]["id"] == binding["source_session_id"]
    assert rows[1]["payload"]["call_id"] == rows[3]["payload"]["call_id"] == binding["original_call_id"]
    assert rows[2]["payload"]["item"]["exit_code"] == binding["actual_exit_code"]
    return {"capture_ref": pin(capture_path), "binding_ref": binding_ref, "actual_exit_code": binding["actual_exit_code"], "source_ordinals": binding["source_ordinals"]}

def main():
    contract = read(N / "contract.json")
    inputs = read(N / "source-inputs.json")
    controls = read(N / "source-controls.json")
    diagnostic = read(N / "actual-readonly-diagnostic.final.json")
    assert contract["source_author"] == AUTHOR and contract["source_namespace"] == N.as_posix()
    assert same(contract["source_runner_ref"], pin(N / "public22_runner.py"))
    assert same(contract["source_inputs_ref"], pin(N / "source-inputs.json"))
    assert controls["count"] == controls["pass"] == 100 and controls["fail"] == 0
    assert controls["native_calls"] == controls["process_calls"] == controls["database_calls"] == 0
    assert diagnostic["original_actual_outcome"] == "FAILED_VERIFY22_PUBLIC_RESTORE_SCHEMA_MISMATCH_RETAINED"
    assert diagnostic["new_native_calls"] == 0 and diagnostic["database_mode"] == "ro,immutable,query_only"
    assert same(diagnostic["source_runner_ref"], contract["source_runner_ref"])
    for role in ("old22_recovery_source", "old22_backup_source", "old22_canonical_source"):
        checked(contract[role]); assert contract[role] in inputs["references"]
    prior = pin(V2 / "HDF.json")
    assert prior["sha256"] == "6f2ec5e3eeb6c06a343ab9fc2fdfb1462e0e740da72986f5c8b7639fab31187e"
    prior_doc = read(prior["path"])
    assert prior_doc["author"] == "codex:/root/native_temp_independent_review"
    checked(prior_doc["manifest_ref"]); checked(prior_doc["runner_ref"]); checked(prior_doc["contract_ref"])
    review_hdf = pin(REVIEW / "HDF.resolved.json")
    assert review_hdf["sha256"] == "e3f85d17d12dabae183ad9e2dde96253ba4319310ab94e2e530bf0932ad152d5"
    review = read(review_hdf["path"])
    for key in ("decision_ref", "manifest_ref", "root_cause_ref", "original_assignment_ref", "returned_state_ref"):
        checked(review[key])
    assignment = read(review["original_assignment_ref"]["path"])
    assert assignment["ordinal"] == 1025 and assignment["successful_native_children"] == 4
    assert assignment["first_failure"]["message"] == "PUBLIC_RESTORE_SCHEMA_MISMATCH"
    assert assignment["actual_outer_exit"] == assignment["actual_python_exit"] == assignment["actual_native_exit"] == 0
    assert assignment["formal_acceptance"] is False
    true_io = {
        "source_controls": verify_pair(N / "v3-source-controls.actual-fullhostpair.binding.json"),
        "existing_readonly": verify_pair(N / "v3-existing-readonly.actual-fullhostpair.binding.json"),
    }
    assert all(item["actual_exit_code"] == 0 for item in true_io.values())
    failures = [verify_pair(N / f"v3-review-failure-actual-call-{ordinal}.binding.json") for ordinal in (6794, 6801, 6815, 6829)]
    assert all(item["actual_exit_code"] == 1 for item in failures)
    revision = {
        "schema": "researchos.schema22-public-runner-v3-source-revision.v1",
        "scope": "SOURCE_ONLY_FINITE_PUBLIC22_RESTORE_ORACLE",
        "prior_v2_hdf_ref": prior,
        "prior_v2_source_author": prior_doc["author"],
        "v3_source_author": AUTHOR,
        "actual_independent_review_hdf_ref": review_hdf,
        "actual_root_cause_ref": review["root_cause_ref"],
        "original1025_assignment_ref": review["original_assignment_ref"],
        "changes": [
            "Mirror frozen Go backupSchema over all sqlite_master rows and bind the source digest to the original backup manifest.",
            "Require exactly the frozen backup_require_fresh_observation trigger on restore; reject missing, altered, or extra schema entries.",
            "Compare all 83 table counts and row digests; derive auth_credentials expected digest by changing only revoked 0 to 1 across full rows and fixed PK layout.",
            "Require public backup/restore stdout equality and status/credentials/inventory report consistency; retain Owner, ledger, baseline, guard and Job controls.",
            "Provide a separate Root-gated read-only existing-artifact recheck method; original1025 remains failed and no child is replayed."
        ],
        "preliminary_diagnostic_ref": pin(N / "actual-readonly-diagnostic.json"),
        "final_diagnostic_ref": pin(N / "actual-readonly-diagnostic.final.json"),
        "controls_ref": pin(N / "source-controls.json"),
        "successful_true_io": true_io,
        "reviewer_side_failures": failures,
        "new_product_executions": 0,
        "new_native_calls": 0,
        "Canon_modified": False,
        "original_case_modified": False,
        "original1025_reclassified": False,
        "independent_source_review": "PENDING_NONAUTHOR",
        "formal_acceptance": False,
    }
    revision_ref = write_new("revision-changes.json", revision)
    delivery = {
        "schema": "researchos.schema22-public-runner-v3-source-delivery.v1",
        "status": "SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_NEW_ROOT_REGISTRATION",
        "source_author": AUTHOR,
        "prior_v2_source_author": prior_doc["author"],
        "prior_v2_hdf_ref": prior,
        "runner_ref": pin(N / "public22_runner.py"),
        "contract_ref": pin(N / "contract.json"),
        "source_inputs_ref": pin(N / "source-inputs.json"),
        "controls_ref": pin(N / "source-controls.json"),
        "revision_ref": revision_ref,
        "actual_readonly_diagnostic_ref": pin(N / "actual-readonly-diagnostic.final.json"),
        "actual_review_hdf_ref": review_hdf,
        "actual_review_decision_ref": review["decision_ref"],
        "original1025_assignment_ref": review["original_assignment_ref"],
        "original1025_status": "FAILED_VERIFY22_PUBLIC_RESTORE_SCHEMA_MISMATCH_RETAINED",
        "actual_successful_old_native_children": 4,
        "new_native_children": 0,
        "source_controls_passed": 100,
        "new_root_scope_required_for_existing_recheck": True,
        "new_root_registration_required_for_any_new_execution": True,
        "independent_non_author_source_review_required": True,
        "execution_grant": False,
        "formal_acceptance": False,
        "schema21": "OPEN",
        "full20to24": "OPEN",
    }
    delivery_ref = write_new("source-delivery.json", delivery)
    members = [pin(path) for path in N.iterdir() if path.is_file() and path.name not in ("HDF.json", "MF.json")]
    members.sort(key=lambda item: item["path"].lower())
    manifest_ref = write_new("MF.json", {"schema": "researchos.schema22-public-runner-v3-source-manifest.v1", "members": members, "complete_namespace_members_excluding_hdf_mf": True, "formal_acceptance": False})
    hdf_ref = write_new("HDF.json", {
        "schema": "researchos.schema22-public-runner-v3-source-handoff.v1",
        "status": delivery["status"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_author": AUTHOR,
        "prior_v2_source_author": prior_doc["author"],
        "prior_v2_hdf_ref": prior,
        "manifest_ref": manifest_ref,
        "source_delivery_ref": delivery_ref,
        "runner_ref": delivery["runner_ref"],
        "contract_ref": delivery["contract_ref"],
        "source_inputs_ref": delivery["source_inputs_ref"],
        "controls_ref": delivery["controls_ref"],
        "revision_ref": revision_ref,
        "actual_readonly_diagnostic_ref": delivery["actual_readonly_diagnostic_ref"],
        "actual_review_hdf_ref": review_hdf,
        "original1025_assignment_ref": review["original_assignment_ref"],
        "actual_successful_old_native_children": 4,
        "new_native_children": 0,
        "source_controls_passed": 100,
        "new_root_scope_required_for_existing_recheck": True,
        "independent_non_author_source_review_required": True,
        "execution_grant": False,
        "formal_acceptance": False,
        "original1025_reclassified": False,
        "Canon_modified": False,
        "old_v2_source_modified": False,
        "STOP": True,
    })
    assert all(same(member, pin(member["path"])) for member in read(manifest_ref["path"])["members"])
    assert len([path for path in N.iterdir() if path.is_file()]) == len(members) + 2
    print(json.dumps({"HDF": hdf_ref, "MF": manifest_ref, "delivery": delivery_ref, "revision": revision_ref, "members": len(members), "controls": 100}, ensure_ascii=False))

if __name__ == "__main__":
    main()
