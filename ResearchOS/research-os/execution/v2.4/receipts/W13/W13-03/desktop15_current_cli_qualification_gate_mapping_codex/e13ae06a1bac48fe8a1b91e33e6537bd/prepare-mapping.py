from pathlib import Path
import ast
import hashlib
import json

ROOT = Path("D:/作品集/ResearchOS/research-os").resolve()
OWN = Path(__file__).resolve().parent
P13 = ROOT / "execution/v2.4/receipts/W13/W13-03"
P05 = ROOT / "execution/v2.4/receipts/W05/W05-99"
B = P13 / "desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060"
C = P13 / "desktop_exact15_integration_preparation_revision_codex/e908291811794b64874f5f6f66507916"
Q = P05 / "cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0"
R = P05 / "integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa"
ACTOR = "codex:/root/f08_i17_binding_impl"
READS = {}
CHECKS = {}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def resolved(value):
    p = Path(value)
    return (p if p.is_absolute() else ROOT / p).resolve()

def read(value):
    p = resolved(value)
    require(p.is_relative_to(ROOT), "Only actual project frozen evidence")
    require("/execution/v2.4/receipts/" in p.as_posix(), "No mutable MAIN or live canonical read")
    raw = p.read_bytes()
    item = {"path": p.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    require(p not in READS or READS[p] == item, "Frozen input drift")
    READS[p] = item
    return raw

def ref(value):
    read(value)
    return dict(READS[resolved(value)])

def verify(item):
    raw = read(item["path"])
    require(hashlib.sha256(raw).hexdigest() == item["sha256"] and len(raw) == item["bytes"], "Original ref mismatch")
    return raw

def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def doc(value):
    return parse(verify(value) if isinstance(value, dict) else read(value))

def exact_ref(a, b):
    return resolved(a["path"]) == resolved(b["path"]) and a["sha256"] == b["sha256"] and a["bytes"] == b["bytes"]

def pin(path, digest, size):
    r = ref(path)
    require(r["sha256"] == digest and r["bytes"] == size, "Fixed source/evidence pin differs")
    return r

def check(name, value):
    require(value, "Static observed-input check failed: " + name)
    CHECKS[name] = True

def write_new(name, value, raw=False):
    p = OWN / name
    require(p.parent == OWN, "Own namespace only")
    payload = value if raw else (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with p.open("xb") as out:
        out.write(payload)
    return {"path": p.as_posix(), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}

def manifest_rows(path, required=(), root_closure=False, schema=None):
    mf = doc(path)
    if schema is not None:
        require(mf["schema"] == schema, "Actual manifest schema")
    rows = mf["members"] if root_closure else mf["entries"]
    if not root_closure:
        require(type(mf["count"]) is int and mf["count"] == len(rows), "Actual declared count")
    parent = resolved(path).parent
    seen = {}
    for item in rows:
        p = resolved(item["path"])
        require(p.is_relative_to(parent) and p not in seen, "Manifest boundary/duplicate")
        verify(item)
        seen[p] = item
    for item in required:
        require(resolved(item["path"]) in seen and exact_ref(seen[resolved(item["path"])], item), "Unsealed required member")
    return {"manifest_ref": ref(path), "schema": mf.get("schema"), "members": len(rows), "all_verified": True}

require(OWN.name == "e13ae06a1bac48fe8a1b91e33e6537bd" and OWN.parent.name == "desktop15_current_cli_qualification_gate_mapping_codex", "Owned new namespace")
# Only stdlib IO/JSON/hash/AST. Never import/exec candidate code or invoke any subprocess.
plan = json.loads((OWN / "mapping-plan.json").read_bytes())
source_refs = {name: pin(ROOT / entry["path"], entry["sha256"], entry["bytes"]) for name, entry in plan["source_baselines"].items()}
builder_handoff_ref = pin(B / "handoff.json", "b0e527ce2566145ea58abf33fad75502e6bc7abd4eb96ccd20beb6e10a004ad8", 3650)
bh = doc(builder_handoff_ref)
for item in bh["scripts"].values():
    verify(item)
metadata_builder_ref = bh["scripts"]["build-metadata-templates.py"]
metadata_engine_ref = bh["scripts"]["metadata-engine.template.py"]
verify(bh["plan_ref"])
verify(bh["spec_ref"])
controller_handoff_ref = ref(C / "handoff.json")
ch = doc(controller_handoff_ref)
scope_ref = pin(C / "scope.v3.proposed.json", "73f48cfb9aa7ffe7632a263202cda8da017f0b58e51c3f20f907f48f5ac5e227", 12694)
scope = doc(scope_ref)
check("controller_and_launcher_exact_handoff_refs", exact_ref(source_refs["controller"], ch["controller_ref"]) and exact_ref(source_refs["launcher"], ch["launcher_ref"]))
review_ref = pin(Q / "review.json", "2d50355615924976b526aae4b3932c9f3b9d491b9da277ef833c36151a4b482a", 13989)
qualification_ref = pin(Q / "qualification.json", "b4756653eaa85825f7ec0f787ae3970c9462694439dca6440ee791fb3dc93efe", 15279)
qualification_manifest_ref = pin(Q / "manifest.json", "f54787dfafdb645d8e88a866f43e020dfc6f62d8475d84cd71002ba6c7238b90", 5697)
qualification_handoff_ref = pin(Q / "handoff.json", "bb3a32c797620f3260fb28807534059c18e46d6f419cbedd55bf62cb97423327", 1754)
review, qual, qh = [doc(p) for p in [review_ref, qualification_ref, qualification_handoff_ref]]
root_completion_ref = pin(R / "root-launch.outer-completion.json", "8d2b7c842836ded1bdc50b34feb4a74acfa62364040ffe51ceff3acaf6f75f06", 10497757)
root_closed_manifest_ref = pin(R / "root-launch.closed.manifest.json", "9ea404feceb071bb707913c46830eaafbfb0a7d019d28ad47f665d29c8f21822", 3733)
completion = doc(root_completion_ref)
manifest_audits = [
    manifest_rows(B / "manifest.json", [builder_handoff_ref, *bh["scripts"].values()]),
    manifest_rows(C / "manifest.json", [controller_handoff_ref, scope_ref, source_refs["controller"], source_refs["launcher"]]),
    manifest_rows(Q / "manifest.json", [review_ref, qualification_ref, qualification_handoff_ref], schema="researchos.public-review-manifest.v1"),
    manifest_rows(R / "root-launch.closed.manifest.json", [root_completion_ref], root_closure=True, schema="researchos.root-launch-closure-manifest.v2"),
]
check("actual_four_frozen_manifest_member_sets", [manifest_audits[i]["members"] for i in [0, 2, 3]] == [16, 18, 11] and all(row["all_verified"] for row in manifest_audits))
check("actual_review_schema_decision_and_identity",
      review["schema"] == "researchos.cli43-bounded-execution-independent-review.v1"
      and review["reviewer"] == "codex:/root/w05_merge_review"
      and review["decision"] == "CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED"
      and review["non_author"] is True and review["actual_readonly_evidence_audit"] is True
      and review["actual_independent_product_execution"] is False and review["requested_changes"] == [])
check("actual_narrow_scope_preparation_permission",
      review["current43_fresh_held2_qualified"] is True and review["desktop15_new_scope_preparation_permitted"] is True
      and qual["current43_fresh_held2_qualified"] is True and qual["desktop15_new_scope_preparation_permitted"] is True)
check("qualification_schema_source_head_and_review_link",
      qual["schema"] == "researchos.cli43-bounded-execution-qualification.v1"
      and qual["reviewer"] == review["reviewer"]
      and qual["source_commit"] == review["source_commit"] == "a510dbef4a7e08fb5c428df44c39b133f3ffa856"
      and exact_ref(review["qualification_ref"], qualification_ref)
      and exact_ref(qh["review_ref"], review_ref) and exact_ref(qh["qualification_ref"], qualification_ref))
for key, item in qual["evidence_refs"].items():
    verify(item)
    check("qualification_review_evidence_link_" + key, exact_ref(item, review[key]))
check("root_completion_and_closed_manifest_exact_link",
      exact_ref(review["root_completion_ref"], root_completion_ref)
      and exact_ref(review["root_closed_manifest_ref"], root_closed_manifest_ref))
fresh_scope = doc(review["scope_ref"])
result = doc(review["result_ref"])
check("actual_run_uuid_source_and_case_scope",
      qual["run_uuid"] == fresh_scope["run_uuid"] == "c4f309c5528f5d42be5e7eeb146a20aa"
      and fresh_scope["source_commit"] == qual["source_commit"]
      and exact_ref(review["scope_ref"], completion["source_scope_ref"])
      and exact_ref(review["grant_ref"], completion["grant_ref"])
      and exact_ref(review["result_ref"], completion["executor_result_ref"])
      and exact_ref(review["executor_manifest_ref"], completion["executor_manifest_ref"]))
ids = ["real-existing-open-readonly", "real-existing-self-send"]
check("two_exact_qualified_cases_no_missing_or_skip",
      qual["qualified_case_ids"] == review["case_ids"] == ids
      and type(qual["qualified_case_count"]) is int and qual["qualified_case_count"] == 2
      and [x["case_id"] for x in qual["case_facts"]] == ids
      and all(x["state"] == "QUALIFIED" and type(x["native_test_exit"]) is int and x["native_test_exit"] == 0 for x in qual["case_facts"])
      and qual["cases_NOT_RUN"] == [] and qual["test_leaf_PASS"] == 2 and qual["test_leaf_FAIL"] == qual["test_leaf_SKIP"] == 0)
check("expected_CLI3_preserved_separate_from_test0",
      qual["CLI_exit_codes"] == [0, 3] and [x["CLI_exit"] for x in qual["case_facts"]] == [0, 3]
      and [[g["independent_exit"] for g in x["generations"]] for x in qual["case_facts"]] == [[0, 0, 0], [0, 0, 3]])
check("14_observed_native_stages_and_original_result",
      type(qual["native_calls"]) is int and qual["native_calls"] == qual["native_calls_exit0"] == completion["native_calls"] == result["native_calls"] == len(result["stages"]) == 14
      and result["first_cause"] is None and result["secondary"] == [] and result["NOT_RUN"] == []
      and [x["leaf"] for x in result["cases"]] == ids and all(x["status"] == "PASS" for x in result["cases"]))
check("actual_Root_completion_four_exit_fields_int0",
      completion["schema"] == "researchos.root-actual-launch-completion.v2" and completion["actor"] == "codex:/root"
      and all(type(completion[k]) is int and completion[k] == 0 for k in ["actual_outer_tool_exit", "actual_python_caller_exit", "actual_launcher_native_exit", "actual_inner_python_native_exit"])
      and completion["caller_error"] is None and completion["caller_secondary"] == [] and completion["underlying_local_failure_count"] == 0)
check("original_Root_unqualified_flags_not_rewritten",
      completion["caller_OS_lifecycle_qualification"] is False and completion["fresh_compile_qualification"] is False
      and completion["complete_current43_source_validation"] is False and completion["independent_qualification"] == "PENDING")
check("HTTP_observations_and_unknowns_not_global_cap",
      qual["HTTP_observed_legs"] == 28 and qual["HTTP_by_case"] == [7, 21]
      and qual["HTTP_upstream_by_case"] == [5, 12] and qual["HTTP_proxy_by_case"] == [2, 9]
      and qual["unobserved_client_outbound_attempts"] is None)
check("no_scope_or_source_or_formal_authorization",
      review["desktop15_execution_authorized"] is False and qual["desktop15_execution_authorized"] is False
      and qual["Main_integration_authorized"] is False and qual["whole43_test_suite_qualified"] is False
      and review["source_acceptance"] is False and qual["source_acceptance"] is False
      and type(review["formal_increment"]) is int and type(qual["formal_increment"]) is int
      and review["formal_increment"] == qual["formal_increment"] == 0
      and qual["SDK_MODEL_Node_external_paid_private_calls"] == 0)
old_review_ref = {"path": (P05 / "cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e/review.json").as_posix(),
                  "sha256": "fe7d4cb67d28517c4c55ca82461c0448f791635b128020faa1278b86d971fbf8", "bytes": 7818}
old_review = doc(old_review_ref)
original_source_proof_refs = {
    "cli43_completed_ref": old_review["completed_ref"], "cli43_manifest_ref": old_review["manifest_ref"],
    "cli43_post_registration_audit_ref": old_review["post_registration_audit_ref"], "cli43_execution_review_ref": old_review_ref,
}
for item in original_source_proof_refs.values():
    verify(item)
for item in qual["source_import_proof_refs"]:
    verify(item)
check("original_CLI43_review_and_post_refs_preserved",
      any(exact_ref(item, old_review_ref) for item in qual["source_import_proof_refs"])
      and any(exact_ref(item, original_source_proof_refs["cli43_post_registration_audit_ref"]) for item in qual["source_import_proof_refs"]))
check("historical_tuple_preserved_without_current_inference", qual["current_canonical_tuple"] == [331, 159, 509])
check("597_current_and_export_records_remain_narrow",
      review["counts"]["source_files_current_hashed"] == review["counts"]["export_files_current_hashed"] == 597
      and review["counts"]["remaining_failed_checks"] == 0)
exact15 = doc(scope["exact15_ref"])
check("15_source_paths_58_union_exact_original",
      len(exact15) == len({x["path"] for x in exact15}) == scope["exact_paths"] == 15
      and scope["union_paths"] == 58
      and not {x["path"] for x in exact15}.intersection(set(scope["shared38_paths"]) | set(scope["cli8_paths"]))
roster_path = P13 / "desktop_http_first_branch_revision_codex/a8e573ecbd20499c8bff9d4222dd9ffc/finite_roster.expanded.json"
roster_ref = pin(roster_path, "02b24caa6480359c2ee9a6f14ed0b9fb5cd876dc84b4985cf56a114ce0f45a29", 141929)
roster = doc(roster_ref)
check("original_finite_roster_159_plus7_preserved",
      len(roster["leaves"]) == roster["new_exact_leaf_count"] == 159
      and len(roster["regressions"]) == roster["legacy_regression_execution_units"] == 7
      and all(row["status"] == "NOT_RUN" for row in roster["leaves"] + roster["regressions"]))
original_author_ref = scope["historical_evidence_refs"][0]
original_author = doc(original_author_ref)
check("169_author_evidence_not_promoted_to_Root", original_author["current_Node"] == "159+7+3 actual0, no repeated launch" and scope["author169_inherited_as_Root_current"] is False)
check("source_only_operation_bounds_and_OPEN_gates_preserved",
      scope["apply_cap"] == scope["commit_cap"] == 1 and scope["git_step_cap"] == 80
      and scope["product_tests_HTTP_SQL_models"] == scope["formal_increment"] == 0
      and scope["source_acceptance"] is False
      and all(scope[k] is False for k in ["fresh43_validation_authorized", "fresh58_validation_authorized", "Desktop_GUI_install_NVDA_authorized"])
      and scope["old_Go3_normal_OS_gap_retained"] is True and scope["new_Go3_boundeddebug_separate"] is True)
anchors = []
for source, ranges in [("builder", [(97,119),(188,216),(365,397)]), ("controller", [(129,151),(209,256),(350,356)]), ("launcher",[(84,115)])]:
    raw = read(source_refs[source]["path"])
    parsed = ast.parse(raw)
    lines = raw.splitlines(keepends=True)
    for start, end in ranges:
        block = b"".join(lines[start-1:end])
        anchors.append({"source": source, "file_ref": source_refs[source], "start": start, "end": end,
                        "raw_byte_sha256": hashlib.sha256(block).hexdigest(), "raw_bytes": len(block),
                        "raw_text": block.decode("utf-8")})
    check("AST_parsed_only_" + source, bool(parsed.body))
source_anchor_ref = write_new("source-consumer-anchors.json", {"schema": "researchos.raw-source-consumer-anchors.v1", "actor": ACTOR, "candidate_execution": False, "anchors": anchors})
input_refs = [READS[p] for p in sorted(READS)]
before_ref = write_new("inputs.before.json", {"schema":"researchos.frozen-input-ref-snapshot.v1","refs":input_refs})
after_refs = []
for item in input_refs:
    raw = resolved(item["path"]).read_bytes()
    after_refs.append({"path": item["path"], "sha256": hashlib.sha256(raw).hexdigest(), "bytes":len(raw)})
check("all_frozen_input_bytes_unchanged_during_readonly_mapping", input_refs == after_refs)
after_ref = write_new("inputs.after.json", {"schema":"researchos.frozen-input-ref-snapshot.v1","refs":after_refs})
actual_refs = {
    "desktop_builder_handoff_ref": builder_handoff_ref, "desktop_builder_manifest_ref": ref(B / "manifest.json"),
    "desktop_controller_handoff_ref": controller_handoff_ref, "desktop_controller_manifest_ref": ref(C / "manifest.json"),
    "builder_ref": source_refs["builder"], "metadata_template_builder_ref": metadata_builder_ref, "metadata_engine_ref": metadata_engine_ref,
    "controller_ref": source_refs["controller"], "launcher_ref": source_refs["launcher"], "scope_ref": scope_ref,
    "qualification_review_ref": review_ref, "qualification_ref": qualification_ref, "qualification_manifest_ref": qualification_manifest_ref,
    "qualification_handoff_ref": qualification_handoff_ref, "root_completion_ref": root_completion_ref, "root_closed_manifest_ref": root_closed_manifest_ref,
    "original_CLI43_source_proof_refs": original_source_proof_refs, "original_exact15_ref": scope["exact15_ref"],
    "original_Node159plus7_roster_ref": roster_ref, "original_Node169_author_statement_ref": original_author_ref,
}
audit_ref = write_new("static-mapping-audit.json", {
    "schema":"researchos.desktop15-current-qualification-readonly-static-audit.v1","actor":ACTOR,
    "checks":CHECKS,"check_count":len(CHECKS),"manifest_audits":manifest_audits,
    "refs":actual_refs,"input_before_ref":before_ref,"input_after_ref":after_ref,
    "review_permission":"New scope preparation only; actual review field, not a new grant",
    "candidate_imported_or_executed":False,"original_source_or_canonical_writes":0,"actual_target_native_exit":None,
    "target_calls":{"Go":0,"SQL":0,"Node":0,"Job_helper":0,"HTTP_network":0,"SDK_MODEL_paid":0,"CAS":0,"mutable_Main_reads":0},
    "new_failed_tools":0,"new_failure_origins":[],"old_coordination_or_W05_locator_origins_recounted":False,
})
mapping = dict(plan)
mapping.update(actual_input_refs=actual_refs, source_consumer_anchors_ref=source_anchor_ref,
               qualification_review_schema=review["schema"], qualification_schema=qual["schema"],
               actual_review_decision=review["decision"], actual_qualification_original_payload=qual,
               actual_root_observation_flags={key:completion[key] for key in ["caller_OS_lifecycle_qualification","fresh_compile_qualification","complete_current43_source_validation","independent_qualification","separately_captured_outer_native_raw"]},
               original_finite_roster_caps=roster["caps"], original_scope_limits=scope["limits"],
               static_audit_ref=audit_ref, input_before_ref=before_ref, input_after_ref=after_ref,
               source_accepted=False,Root_execution_grant=False,formal_increment=0,writer_status="STOPPED_AFTER_SEAL")
mapping_ref = write_new("gate-mapping.json", mapping)
tools_path = OWN / "tool-observations.json"
tools_raw = tools_path.read_bytes()
tools_ref = {"path": tools_path.as_posix(),"sha256":hashlib.sha256(tools_raw).hexdigest(),"bytes":len(tools_raw)}
hdf = write_new("handoff.json", {
    "schema":"researchos.desktop15-current-cli-qualification-gate-mapping-handoff.v1","actor":ACTOR,
    "decision":"READONLY_GATE_MAPPING_READY_FOR_SOURCE_PREPARATION","status":"STOPPED_AFTER_SEAL",
    "gate_mapping_ref":mapping_ref,"minimal_diff_advice_path":(OWN/"minimal-diff-advice.md").as_posix(),
    "static_audit_ref":audit_ref,"raw_source_anchors_ref":source_anchor_ref,
    "input_before_ref":before_ref,"input_after_ref":after_ref,"tool_observations_ref":tools_ref,"original_input_refs":actual_refs,
    "actual_current43_held2_qualified":True,"desktop15_new_scope_preparation_permitted_by_original_review":True,
    "desktop15_execution_authorized":False,"source_acceptance":False,"formal_increment":0,
    "whole43_test_suite_qualified":False,"new_failure_origins":[],"new_failed_tools":0,
    "old_coordination_or_W05_locator_origins_recounted":False,"open_gates":plan["open_gates"],
    "candidate_imports":0,"native_target_calls":0,"source_or_canonical_writes":0,
    "own_metadata_sealer_native_exit_at_write":None,
    "manifest":{"path":(OWN/"manifest.json").as_posix(),"self_excluded":True,"scope":"All owned files including this handoff; only manifest.json excluded"},
})
members = []
for p in sorted(OWN.iterdir()):
    if p.is_file() and p.name != "manifest.json":
        raw = p.read_bytes()
        members.append({"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
mf = write_new("manifest.json", {"schema":"researchos.immutable-public-receipt-manifest.v1","members":members,"member_count":len(members),"self_excluded":True})
print(json.dumps({"status":"STOPPED_AFTER_SEAL","decision":"READONLY_GATE_MAPPING_READY_FOR_SOURCE_PREPARATION","mapping_ref":mapping_ref,"handoff_ref":hdf,"manifest_ref":mf,"manifest_members":len(members),"audit_ref":audit_ref,"check_count":len(CHECKS),"new_failed_tools":0,"target_calls":0,"source_or_canonical_writes":0},ensure_ascii=False,indent=2))

