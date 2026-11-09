import hashlib
import json
from pathlib import Path

OWN = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505")
ACTOR = "codex:/root/f08_i17_binding_impl"

def pin(p):
    raw = p.read_bytes()
    return {"path": p.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def create(name, value):
    p = OWN / name
    if p.exists():
        raise ValueError("No sealed artifact overwrite")
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    return pin(p)

audit = json.loads((OWN / "static-source-audit.json").read_bytes())
after = json.loads((OWN / "source-read-after.json").read_bytes())
origins = json.loads((OWN / "failure-origins.json").read_bytes())
rpath = OWN / "review.json"
review = json.loads(rpath.read_bytes())
assert review["decision"] == "REQUEST_CHANGES" and len(review["requested_changes"]) == 6
assert all(audit["checks"].values()) and after["unchanged"] is True
assert origins["new_failed_tool_invocations"] == review["new_failed_tool_invocations"] == 1
assert origins["origin_records"][0]["actual_native_exit"] is None
# Only the new own review metadata is completed before sealing.
review["static_source_audit_ref"] = pin(OWN / "static-source-audit.json")
review["source_input_before_ref"] = pin(OWN / "source-read-before.json")
review["source_input_after_ref"] = pin(OWN / "source-read-after.json")
review["tool_observations_ref"] = pin(OWN / "tool-observations.json")
review["delegated_job_source_review_ref"] = pin(OWN / "delegated-job-source-review.json")
review["new_failure_origins_ref"] = pin(OWN / "failure-origins.json")
review["original_input_ref_checks"] = audit["original_ref_checks"]
rpath.write_bytes((json.dumps(review, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
refs = {key: pin(OWN / name) for key,name in [
 ("review_ref","review.json"),("static_source_audit_ref","static-source-audit.json"),
 ("source_before_ref","source-read-before.json"),("source_after_ref","source-read-after.json"),
 ("failure_origins_ref","failure-origins.json"),("tool_observations_ref","tool-observations.json"),
 ("delegated_job_source_review_ref","delegated-job-source-review.json")]}
hdf = {
 "schema":"researchos.w09.finite-controller-independent-review-handoff.v1",
 "reviewer":ACTOR,"author":"codex:/root/sources_parent_impl","writer_status":"STOPPED_AFTER_SEAL",
 "decision":"REQUEST_CHANGES","requested_change_ids":[v["id"] for v in review["requested_changes"]],
 "refs":refs,"original_bundle_refs":{v["observed_ref"]["path"]:v["observed_ref"] for v in audit["original_ref_checks"]},
 "companion_whole_manifest_path":(OWN/"manifest.json").as_posix(),
 "manifest_rule":"All own receipt files including this handoff, manifest itself excluded; caller pins manifest after creation.",
 "static_confirmations":review["static_confirmations"],"all_actual_target_calls":"NOT_RUN",
 "new_failed_tool_invocations":1,
 "new_failure_origin_keys":[x["origin_key"] for x in origins["origin_records"]],
 "local_review_metadata_failed_invocations":0,"delegated_metadata_failed_invocations":1,
 "metadata_sealer_actual_native_exit_at_write":None,
 "NULL_policy":"os206 was rejected before native process creation; actual_native_exit NULL remains NULL, never inferred from outer script failure.",
 "successful_delegated_stdout_policy":"Exact successful stdout not transferred; actual metadata only, held in child's original history. This reviewer independently reads same fixed source bytes.",
 "static_checker_origin_scope":"static-source-audit.new_failure_origins=[] concerns that successful own source-checker only; delegated failure is separately preserved above.",
 "source_acceptance":False,"controller_execution_ready":False,"parent_accepted":False,"formal_acceptance_increment":0,
 "no_go_SQL_HTTP_SDK_MODEL_helper_controller_or_CAS_execution":True,
 "mutable_Main_state_read":False,"canonical_or_source_writes":0,
 "historical_failure_counter_modified":False,"old_I17_and_ad2dc_seals_modified":False,
 "next_action":"Author prepares a new UUID controller candidate addressing six exact source paths; original2098f823 stays sealed. Then another nonauthor review and immutable actual Root grant/resources/source lease are still required before any execution.",
 "no_self_acceptance":True
}
hdf_ref = create("handoff.json",hdf)
members = [pin(p) for p in sorted(OWN.rglob("*")) if p.is_file() and p.name!="manifest.json"]
manifest_ref = create("manifest.json",{
 "schema":"researchos.w09.controller-review-whole-manifest.v1","reviewer":ACTOR,
 "member_count":len(members),"member_bytes":sum(x["bytes"] for x in members),
 "self_excluded":True,"handoff_included":True,"members":members,
 "product_acceptance":False
})
assert all(pin(Path(x["path"]))==x for x in members)
print(json.dumps({"decision":"REQUEST_CHANGES","handoff":hdf_ref,"whole_manifest":manifest_ref,"review":pin(rpath),
 "static_audit":pin(OWN/"static-source-audit.json"),"failure_origins":pin(OWN/"failure-origins.json"),
 "member_count":len(members),"new_failed_tool_invocations":1,"writer_status":"STOPPED"},ensure_ascii=False))

