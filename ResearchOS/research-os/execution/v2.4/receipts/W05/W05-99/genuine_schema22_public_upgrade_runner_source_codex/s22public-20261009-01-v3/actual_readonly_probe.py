"""Read-only diagnostic of already-existing original1025 public artifacts."""
import hashlib
import importlib.util
import json
from pathlib import Path

N = Path(__file__).resolve().parent
B = N.parent.parent
HDF = B / "public22_actual_independent_review_codex" / "actual-01a1210b" / "HDF.resolved.json"
spec = importlib.util.spec_from_file_location("public22_source_v3", N / "public22_runner.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def checked(ref):
    assert pin(ref["path"])["sha256"] == ref["sha256"] and pin(ref["path"])["bytes"] == ref["bytes"]
    return Path(ref["path"])

def main():
    hdf = json.loads(HDF.read_bytes())
    proof = json.loads(checked(hdf["root_cause_ref"]).read_bytes())
    refs = proof["source_refs"]
    assert len(refs) >= 11
    assert all(checked(ref).is_file() for ref in refs[:11])
    source = module.readonly_database_observation(refs[0]["path"])
    restored = module.readonly_database_observation(refs[1]["path"])
    manifest = json.loads(Path(refs[2]["path"]).read_bytes())
    report = json.loads(Path(refs[3]["path"]).read_bytes())
    trigger = module.expected_restore_trigger_sql(Path(refs[7]["path"]).read_text(encoding="utf-8"))
    assert json.loads(Path(refs[4]["path"]).read_bytes()) == manifest
    assert json.loads(Path(refs[5]["path"]).read_bytes()) == report
    assert report["status"] == module.RESTORED and report["recovery"]["credentials"] == "REVOKED_REPROVISION_LOCALLY"
    assert report["backup_id"] == manifest["id"] and report["before"] == report["after"] == manifest["inventory"]
    assert module.validate_restore22(restored, source, manifest, trigger) is True
    result = {
        "schema": "researchos.public22-source-v3-existing-artifact-readonly-diagnostic.v1",
        "scope": "ALREADY_EXISTING_ORIGINAL1025_ARTIFACTS_ONLY",
        "original_actual_outcome": "FAILED_VERIFY22_PUBLIC_RESTORE_SCHEMA_MISMATCH_RETAINED",
        "new_process_calls": 0, "new_native_calls": 0, "database_mode": "ro,immutable,query_only",
        "source_tables": len(source["tables"]), "restored_tables": len(restored["tables"]),
        "source_schema_sha256": source["schema_sha256"], "restored_schema_sha256": restored["schema_sha256"],
        "filtered_restored_schema_matches_manifest": True,
        "auth_credentials_full_row_expected_digest_matches_restored": True,
        "raw_data_rows_emitted": False, "formal_acceptance": False, "execution_grant": False,
        "prior_review_hdf_ref": pin(HDF), "prior_delta_proof_ref": hdf["root_cause_ref"],
        "source_runner_ref": pin(N / "public22_runner.py"),
    }
    path = N / "actual-readonly-diagnostic.final.json"
    with path.open("x", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"result_ref": pin(path), "tables": len(source["tables"]), "original1025_reclassified": False}, ensure_ascii=False))

if __name__ == "__main__":
    main()
