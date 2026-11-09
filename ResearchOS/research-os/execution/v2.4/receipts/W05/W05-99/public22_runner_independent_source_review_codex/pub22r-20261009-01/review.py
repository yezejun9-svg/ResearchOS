"""Independent, read-only Source review of the W05 public schema22 runner."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import types

R = Path(r"D:\作品集\ResearchOS\research-os")
N = Path(__file__).resolve().parent
S = R / "execution/v2.4/receipts/W05/W05-99/genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01"
C = R / "execution/v2.4"
EXPECTED = {
    "HDF.json": ("24aebe7f5c32582c914968e84f9cf8f5daa56cb5ef757123b313b6834fb866a3", 3257),
    "MF.json": ("c344fdc8fb89f992146065c50545a5d61c3303f1da84e6b5a20e3f3da634d9f9", 3781),
    "public22_runner.py": ("f78c695e4b47620c9e8d7a8f455a6229896b1139874e0f85653b5b0e98b0381d", 22530),
    "contract.json": ("a4f77d32acca9f286c25eac7024701ea5fd98ec10b4ae2c17b2f818a734a959d", 10703),
}


def require(value, code):
    if not value:
        raise AssertionError(code)


def pin(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def read(ref):
    actual = pin(ref["path"])
    require(actual["sha256"] == ref["sha256"] and actual["bytes"] == ref["bytes"],
            "SOURCE_REF_CHANGED")
    return Path(actual["path"]).read_bytes()


def write(name, value):
    path = N / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
    return pin(path)


def main():
    exact = {name: pin(S / name) for name in EXPECTED}
    for name, expected in EXPECTED.items():
        require((exact[name]["sha256"], exact[name]["bytes"]) == expected,
                "SEALED_SOURCE_INPUT_CHANGED")
    handoff = json.loads(read(exact["HDF.json"]))
    manifest = json.loads(read(exact["MF.json"]))
    require(handoff["manifest_ref"]["sha256"] == exact["MF.json"]["sha256"]
            and handoff["runner_ref"]["sha256"] == exact["public22_runner.py"]["sha256"]
            and handoff["contract_ref"]["sha256"] == exact["contract.json"]["sha256"]
            and type(manifest.get("members")) is list
            and len(manifest["members"]) == manifest["member_count"],
            "SOURCE_HANDOFF_MEMBER_BINDING")
    for member in manifest["members"]:
        read(member)
    contract = json.loads(read(exact["contract.json"]))
    source_inputs_ref = handoff["source_inputs_ref"]
    source_inputs = json.loads(read(source_inputs_ref))
    require(len(source_inputs["references"]) == source_inputs["count"] == 549,
            "SOURCE_INPUT_COUNT")
    sourceguard_ref = contract["source_guard"]
    require(pin(sourceguard_ref["path"])["sha256"] == sourceguard_ref["sha256"],
            "GUARD_SOURCE_CHANGED")
    guard_module = types.ModuleType("review_pinned_source_guard")
    exec(compile(read(sourceguard_ref), sourceguard_ref["path"], "exec"),
         guard_module.__dict__)
    canons = [pin(C / (name + ".json")) for name in
              ("checkpoint", "path_ownership", "step_state", "commands")]
    resources = [*exact.values(), *manifest["members"], *source_inputs["references"],
                 *canons, source_inputs_ref, sourceguard_ref]
    unique = {}
    for ref in resources:
        read(ref)
        key = str(Path(ref["path"]).resolve()).casefold()
        require(key not in unique or (unique[key]["sha256"], unique[key]["bytes"]) ==
                (ref["sha256"], ref["bytes"]), "CONFLICTING_RESOURCE_PINS")
        unique[key] = pin(ref["path"])
    guard = guard_module.SourceReadGuard(per_file_cap=512*1024*1024,
                                        total_cap=2*1024*1024*1024)
    guard.acquire(list(unique.values()))
    checks = []
    def passed(name): checks.append({"id": name, "passed": True})
    try:
        module = runpy.run_path(exact["public22_runner.py"]["path"],
                                run_name="independent_source_review")
        project = module["compile_case"](contract, {"case_id":"a"*32,
            "output_root":str(Path(contract["output_parent"]) / ("schema22-public-" + "a"*32)),
            "end_version":22})
        require([p["id"] for p in project["phases"]] ==
                ["bootstrap22", "keygen22", "backup22", "verify22"],
                "PUBLIC22_PHASE_PROJECTION")
        passed("actual_old22_public_four_phase_projection")
        require(all(pin(contract[name]["path"])["sha256"] == contract[name]["sha256"]
                    for name in ("old22_control", "old22_backup")),
                "OLD22_PROGRAMME_DRIFT")
        passed("old22_public_binaries_exact")
        require(all(pin(ref["path"])["sha256"] == ref["sha256"]
                    for ref in contract["current_main_source_refs"]),
                "CURRENT_MAIN_SOURCE_CHANGED")
        require(contract["main23_candidate_drift"][0]["matches_prior_main_vector"] is False,
                "UNREBOUND_MAIN23_DRIFT_NOT_DISCLOSED")
        passed("current_main_five_refs_and_prior23_candidate_drift")
        try:
            module["compile_case"](contract,{"case_id":"a"*32,
                "output_root":project["paths"]["root"],"end_version":24})
        except module["BoundaryError"] as exc:
            require(str(exc) == "MAIN_PUBLIC_23_TO_24_NOT_ADOPTED", "WRONG_24_REJECTION")
        else:
            raise AssertionError("END24_UNEXPECTEDLY_ACCEPTED")
        require(not (R / "internal/domain/backup_prepared_abandonment_upgrade.go").exists()
                and not (R / "migrations/sqlite/0024_prepared_run_abandonment.sql").exists(),
                "PUBLIC24_MAIN_UNEXPECTEDLY_PRESENT")
        passed("end24_refusal_and_missing_main_source_sql")
        empty = {"versions":list(range(1,23)), "integrity":["ok"],
                 "foreign_key_violations":0,
                 "tables":{"client_sessions":{"count":0},
                           "client_command_queue":{"count":0},
                           "auth_principals":{"count":0},
                           "domain_objects":{"count":0}}}
        require(module["validate_ledger"](empty,22) is True,
                "DROPPED_OWNER_COUNTEREXAMPLE_DID_NOT_REPRODUCE")
        passed("counterexample_verify22_dropped_owner_passes_ledger")
        nonempty = json.loads(json.dumps(empty))
        nonempty["tables"]["client_command_queue"]["count"] = 1
        try:
            module["validate_ledger"](nonempty,22)
        except module["BoundaryError"] as exc:
            require(str(exc) == "BOOTSTRAP_ONLY_TYPED_EMPTY_SCOPE_REQUIRED",
                    "TYPED_EMPTY_WRONG_REJECTION")
        else:
            raise AssertionError("NONEMPTY_QUEUE_ACCEPTED")
        passed("nonempty_queue_rejected_by_typed_empty_boundary")
        cp = json.loads(read(canons[0])); ow = json.loads(read(canons[1]))
        public_workers = [w for w in cp.get("workers", []) if
                          "PUBLIC22" in str(w.get("slice_id", "")).upper()]
        subtasks = ow.get("card_path_bindings", {}).get("W05-99", {}).get("subtasks", {})
        public_subtasks = [key for key in subtasks if "public22" in key.lower()]
        require(not public_workers and not public_subtasks,
                "PUBLIC22_ACTUAL_REGISTRATION_STATE_CHANGED")
        passed("current_canon_has_no_public22_root_scope_owner_worker_lease")
        controls = json.loads(read(handoff["controls_ref"]))
        require(controls["pass"] == controls["count"] == 49
                and controls["fail"] == 0 and controls["runtime_verified"] is False
                and controls["process_calls"] == controls["database_calls"] ==
                    controls["native_calls"] == 0, "SOURCE_CONTROLS_NOT_PURE")
        passed("source49_controls_only_synthetic_non_authoritative")
        source_guard = json.loads(read(handoff["sourceguard_ref"]))
        require(source_guard["verification"] == "PASSED"
                and source_guard["closed"] is True
                and source_guard["retained_handles_count"] == 0
                and source_guard["errors"] == [], "AUTHOR_SOURCE_GUARD_UNCLOSED")
        passed("author_source_guard_closed_and_pinned")
    finally:
        cleanup = guard.close()
    require(cleanup["verification"] == "PASSED" and cleanup["closed"] is True
            and cleanup["retained_handles_count"] == 0 and cleanup["errors"] == [],
            "REVIEW_SOURCE_GUARD_UNCLOSED")
    guard_ref = write("sourceguard.closed.json", cleanup)
    result_ref = write("independent-controls.json", {
        "schema":"researchos.w05-public22-independent-source-controls.v1",
        "checks":checks,"passed":len(checks),"failed":0,"read_pins":len(unique),
        "guard_closed":True,"guard_ref":guard_ref,"product_processes":0,
        "product_database_calls":0,"SyntheticNonAuthoritative":True,
        "current_canonical_refs":canons})
    print(json.dumps({"controls_ref":result_ref,"guard_ref":guard_ref,
                      "checks":len(checks),"held_refs":len(unique)},ensure_ascii=False))


if __name__ == "__main__": main()
