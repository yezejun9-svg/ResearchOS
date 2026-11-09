"""Independent, read-only Source review of the W05 public schema22 runner."""
import hashlib
import json
import ast
import copy
from pathlib import Path
import runpy
import sys
import types

R = Path(r"D:\作品集\ResearchOS\research-os")
N = Path(__file__).resolve().parent
S = R / "execution/v2.4/receipts/W05/W05-99/genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2"
C = R / "execution/v2.4"
EXPECTED = {
    "HDF.json": ("6f2ec5e3eeb6c06a343ab9fc2fdfb1462e0e740da72986f5c8b7639fab31187e", 3494),
    "MF.json": ("cca5a67720a616832d8503158c2c7b2c2933638bcdfc5da2b3eb69dcd1e78ca5", 9010),
    "public22_runner.py": ("c157e0a213406267d56d3f24ee07092413c26bb3c6bafaf9ac5469fbf4829da7", 24984),
    "contract.json": ("24d24cf6535b79355ad0a4e9a9ef518b93039f4c67bd01ad74cae5d66a127976", 10863),
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
            and len(manifest["members"]) > 0
            and manifest.get("excludes") == ["MF.json", "HDF.json"],
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
        def rejected(call, code):
            try: call()
            except module["BoundaryError"] as exc:
                require(str(exc) == code, "WRONG_REJECTION_" + code)
            else: raise AssertionError("UNEXPECTED_ACCEPT_" + code)
        zero = {"count": 0, "rows_sha256": "0"*64}
        sealed = {"versions":list(range(1,23)), "integrity":["ok"],
            "foreign_key_violations":0, "schema_sha256":"a"*64,
            "tables":{"client_sessions":copy.deepcopy(zero),
                      "client_command_queue":copy.deepcopy(zero),
                      "auth_principals":{"count":1,"rows_sha256":"b"*64},
                      "domain_objects":{"count":1,"rows_sha256":"c"*64}}}
        require(module["validate_restore22"](copy.deepcopy(sealed),sealed) is True,
                "VALID_EXACT_RESTORE_REJECTED")
        passed("F1_exact_22_logical_restore_accepted")
        dropped = copy.deepcopy(sealed)
        dropped["tables"]["auth_principals"]["count"] = 0
        require(module["validate_ledger"](dropped,22) is True,
                "LEGACY_DROPPED_OWNER_COUNTEREXAMPLE_NOT_REPRODUCED")
        rejected(lambda:module["validate_restore22"](dropped,sealed),
                 "PUBLIC_RESTORE_OWNER_ROW_REQUIRED")
        passed("F1_dropped_owner_counterexample_rejected")
        cases = [
            ("owner_row", lambda d:d["tables"]["auth_principals"].update(rows_sha256="d"*64), "PUBLIC_RESTORE_TABLE_STATE_MISMATCH"),
            ("domain_row", lambda d:d["tables"]["domain_objects"].update(rows_sha256="d"*64), "PUBLIC_RESTORE_TABLE_STATE_MISMATCH"),
            ("schema_digest", lambda d:d.update(schema_sha256="d"*64), "PUBLIC_RESTORE_SCHEMA_MISMATCH"),
            ("missing_digest", lambda d:d.pop("schema_sha256"), "PUBLIC_RESTORE_SCHEMA_DIGEST_REQUIRED"),
            ("missing_table", lambda d:d["tables"].pop("domain_objects"), "PUBLIC_RESTORE_TABLE_STATE_MISMATCH"),
            ("extra_table", lambda d:d["tables"].update(unexpected=copy.deepcopy(zero)), "PUBLIC_RESTORE_TABLE_STATE_MISMATCH"),
        ]
        for label, change, error in cases:
            altered = copy.deepcopy(sealed); change(altered)
            rejected(lambda altered=altered:module["validate_restore22"](altered,sealed), error)
            passed("F1_reject_" + label)
        tree = ast.parse(read(exact["public22_runner.py"]))
        arm = [n for n in ast.walk(tree) if isinstance(n,ast.If)
               and ast.unparse(n.test) == "phase['id'] == 'verify22'"]
        require(len(arm)==1 and any(isinstance(n,ast.Call)
                and isinstance(n.func,ast.Name) and n.func.id == "validate_restore22"
                for n in ast.walk(arm[0])), "VERIFY22_NOT_WIRED_TO_STRONG_VALIDATOR")
        passed("F1_verify22_production_branch_wired_to_validator")
        # Exercise the actual orchestration function with an in-memory Path and
        # deny all downstream source guard, Native, process, and SQLite entrypoints.
        def prepare_failure(name, close_fails=False):
            target = module["regular_absolute"](project["paths"][name])
            rootkey = module["regular_absolute"](project["paths"]["root"])
            created, attempted, saved, loaded = set(), [], [], []
            class MemPath:
                def __init__(self, path): self.path=str(path)
                def __str__(self): return self.path
                def __truediv__(self, part): return MemPath(module["ntpath"].join(self.path,part))
                def mkdir(self):
                    key=module["regular_absolute"](self.path); attempted.append(key)
                    if key == target: raise OSError("INDEPENDENT_MKDIR_FAILURE:" + name)
                    created.add(key)
                def exists(self): return module["regular_absolute"](self.path) in created
                def is_dir(self): return self.exists()
                def is_file(self): return False
            class Scope:
                def require_registered(self,*args,**kwargs): return None
                def require_phase(self,phase,*args): require(phase=="prepare","LATE_PHASE_REACHED")
                def receipt_context(self): return {"synthetic_review":True}
                def qualified_current_main23(self,*args): raise AssertionError("MAIN_BINDING_REACHED")
            c_ref={"path":"D:/Unopened/review-contract.json","sha256":"1"*64,"bytes":1}
            q_ref={"path":"D:/Unopened/review-request.json","sha256":"2"*64,"bytes":1}
            def saved_new(path,value):
                if close_fails: raise OSError("INDEPENDENT_CLOSE_FAILURE")
                saved.append((str(path),copy.deepcopy(value)))
                return {"path":str(path),"sha256":"3"*64,"bytes":1}
            def denied_load(*args):
                loaded.append(args); raise AssertionError("PRODUCT_LOAD_REACHED")
            namespace=module["run_registered_case"].__globals__
            names=["Path","read_exact","save_new","_assert_output_ancestors","_load_pinned_module"]
            old={key:namespace[key] for key in names}
            try:
                namespace.update(Path=MemPath,
                    read_exact=lambda ref:json.dumps(contract if ref==c_ref else
                        {"case_id":"a"*32,"output_root":project["paths"]["root"],"end_version":22}).encode(),
                    save_new=saved_new, _assert_output_ancestors=lambda path:None,
                    _load_pinned_module=denied_load)
                result=module["run_registered_case"](c_ref,q_ref,Scope())
            finally: namespace.update(old)
            failure=result["first_failure"]
            require(failure["phase"]=="prepare" and failure["type"]=="OSError"
                    and failure["message"]=="INDEPENDENT_MKDIR_FAILURE:"+name
                    and failure["original_ordinal"] is None and failure["last_child_exit"] is None,
                    "F2_FIRST_FAILURE_LOST_"+name)
            require(result["calls"]==[] and not loaded and attempted[-1]==target
                    and len(attempted)==len(set(attempted))
                    and result["recoverability"]["automatic_retry_or_recovery_performed"] is False,
                    "F2_SIDE_EFFECT_OR_RETRY_"+name)
            require(set(map(module["regular_absolute"],result["preparation"]["created_directories"]))==created
                    and module["regular_absolute"](result["preparation"]["attempted_path"])==target
                    and result["publication"]["root"]==(rootkey in created),
                    "F2_PARTIAL_PREP_INCORRECT_"+name)
            if name=="root":
                require(not saved and result["closed_receipt"]["status"]==
                        "ROOT_NOT_CREATED_ROOT_MUST_PERSIST_RETURNED_STATE", "F2_ROOT_UNCREATED_RESULT")
            elif close_fails:
                require(not saved and result["status"]=="STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED"
                        and result["closed_receipt"]["status"]=="FAILED_ROOT_MUST_PERSIST_RETURNED_STATE"
                        and result["closed_receipt"]["error"]["message"]=="INDEPENDENT_CLOSE_FAILURE",
                        "F2_CLOSE_FAILURE_RESULT")
            else:
                require(len(saved)==1 and saved[0][0].endswith("case.closed.json")
                        and saved[0][1]["first_failure"]==failure
                        and saved[0][1]["publication"]==result["publication"]
                        and result["closed_receipt"]["status"]=="PUBLISHED", "F2_RECEIPT_RESULT")
            passed("F2_prepare_"+name+("_close_failure" if close_fails else ""))
        for name in ["root","private","raw","tmp","work22"]: prepare_failure(name)
        prepare_failure("raw",True)
        cp = json.loads(read(canons[0])); ow = json.loads(read(canons[1]))
        public_workers = [w for w in cp.get("workers", []) if
                          "PUBLIC22" in str(w.get("slice_id", "")).upper()]
        subtasks = ow.get("card_path_bindings", {}).get("W05-99", {}).get("subtasks", {})
        public_subtasks = [key for key in subtasks if "public22" in key.lower()]
        require(not public_workers and not public_subtasks,
                "PUBLIC22_ACTUAL_REGISTRATION_STATE_CHANGED")
        passed("current_canon_has_no_public22_root_scope_owner_worker_lease")
        controls = json.loads(read(handoff["controls_ref"]))
        require(controls["pass"] == controls["count"] == 85
                and controls["fail"] == 0 and controls["runtime_verified"] is False
                and controls["process_calls"] == controls["database_calls"] ==
                    controls["native_calls"] == 0, "SOURCE_CONTROLS_NOT_PURE")
        passed("source85_controls_only_synthetic_non_authoritative")
        delivery = json.loads(read(handoff["source_delivery_ref"]))
        require(delivery["source_read_guard_this_revision"] ==
                "NOT_EXECUTED; SOURCE_ONLY_FILE_HASH_CHECKS" and
                delivery["actual_product_processes"] == 0 and
                delivery["actual_SQLite_calls"] == 0 and
                delivery["actual_native_API_calls"] == 0,
                "AUTHOR_RUNTIME_SCOPE_MISSTATED")
        passed("author_revision_source_only_scope_explicit")
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
