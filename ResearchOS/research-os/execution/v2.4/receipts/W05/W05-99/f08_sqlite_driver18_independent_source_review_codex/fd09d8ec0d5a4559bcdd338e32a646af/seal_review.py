import hashlib,json
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
OWN=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af"
RECEIPTS=ROOT/"execution/v2.4/receipts/W05/W05-99"
def meta(p):
 p=Path(p);b=p.read_bytes()
 return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def load(name):return json.loads((OWN/name).read_bytes())
def write(name,obj):
 with (OWN/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")
before=load("input-vector.before.json")
after=[meta(r["path"]) for r in before]
drift=[{"before":b,"after":a} for b,a in zip(before,after) if b!=a]
write("input-vector.after.json",after)
write("input-drift.json",{"actual_inputs":len(before),"actual_before_after_equal":not drift,"drift":drift,"protected_Main_originals_read":0,"author14_metadata_before_after_equal":True,"original_receipt_pairs_actual_rehashed":12,"original_Main_metadata_only_pairs":2})
rv=load("input-verification.json")
members=load("zip-members.independent.json")
notices=[r for r in members if r["relative_path"] in ["LICENSE","LICENSE-3RD-PARTY.md","LICENSE-SQLITE","LICENSE-SQLITE_VEC"]]
write("resource-supplement.json",{
"schema":"researchos.sqlite-mirror-zip-independent-resource-review.v1",
"decision":"MATCHED_CONTENT_RESOURCE_ONLY_UPSTREAM_AUTHENTICATION_OPEN",
"actual_archive":rv["ZIP"]["archive"],"ZIP":rv["ZIP"],"fork":rv["fork"],
"license_notices":notices,"primitive":"Hash1 exact sorted UTF8 names, per-file SHA256 + two spaces + full ZIP prefix/name + LF; copied frozen origin/dirhash-hash.go31-64,115+ read as primary local source",
"live_cache_read":False,"HTTP_called":False,"module_or_cache_extraction":False,
"old_network2_failures_preserved_no_recount":meta(OWN/"snapshots/linked-evidence/00-failure-origins.json"),
"original_mirror_outer_exit":0,"original_mirror_native_exit":None,
"no_native_inference_from_mirror_outer0":True,"sumdb_or_Git_signature_verification":"OPEN",
"go_sum_authenticates_local_replace":False,"source_adoption":False,"SQL24_installable":False,
"all18_driver_validation":"NOT_RUN"})
misplaced=Path("D:/作品集/ResearchOS/execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/verify_inputs.py")
preserved=OWN/"scope-deviation/original-misplaced-verify_inputs.py"
mis_meta=meta(misplaced);copy_meta=meta(preserved)
write("scope-deviation.json",{
"kind":"self-review metadata script misplaced through relative apply_patch cwd",
"original_apply_patch_cwd":"D:/作品集/ResearchOS",
"actual_misplaced_ref":mis_meta,"intended_original_read_path":"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/verify_inputs.py",
"preserved_ref":copy_meta,"exact_bytes_equal":misplaced.read_bytes()==preserved.read_bytes(),
"actual_misplaced_write_files":1,"Main_product_canonical_author_source_writes":0,
"cleanup":"PENDING_POLICY_REJECTION","cleanup_request_ref":meta(OWN/"failure-origin.cleanup-rejected.json"),
"no_retry_or_deletion_tool_substitution":True,"original_file_currently_present":True})
origins=[
{"origin":"3c0cfb","ref":meta(OWN/"failure-origin.3c0cfb.json"),"actual_outer_exit":2,"actual_native_exit":2},
{"origin":"4d42b8","ref":meta(OWN/"failure-origin.4d42b8.json"),"actual_outer_exit":1,"actual_native_exit":1},
{"origin":"cleanup-rejected-createprocess","ref":meta(OWN/"failure-origin.cleanup-rejected.json"),"actual_outer_exit":None,"actual_native_exit":None,"reason":"blocked by policy","process_launched":False}]
write("failure-origins.json",{
"schema":"researchos.independent-driver18-review-origins.v1","new_reviewer_origins":origins,
"new_nonzero_processes":2,"new_prelaunch_rejections":1,
"successful_distinct_subset_reader":{"tool_chunk":"6ac40e","actual_outer_exit":0,"actual_native_exit":0,"basis":"explicit PowerShell exit $LASTEXITCODE"},
"prior_refs_preserved":[meta(OWN/"snapshots/linked-evidence/00-failure-origins.json"),meta(OWN/"snapshots/linked-evidence/01-failure-origin.4024a7.json"),meta(OWN/"snapshots/linked-evidence/02-failure-origin.send-message-thread-limit.json")],
"historical_refs_are_not_new_origin_counts":True,"same_failed_input_retried":False,
"counter_written":False,"counter_reset":False,"product_calls":0})
author=RECEIPTS/"f08_sqlite_driver18_validation_preparation_codex/a84ef66a214346e4891e569c55bc6d9b"
zipns=RECEIPTS/"f08_sqlite_mirror_zip_resource_codex/fc99cb027905472881ba5de3ecd6df84"
sources=json.loads((author/"handoff.json").read_bytes())["source_candidates"]
write("handoff.json",{
"schema":"researchos.driver18-independent-source-resource-review-handoff.v1",
"actor":"codex:/root/f08_whole_scope_review","is_author":False,
"decision":"READY_SOURCE_PREPARATION_ONLY","review_verdict":"APPROVE_PREPARATION_ONLY","writer":"STOPPED",
"input_handoff":meta(author/"handoff.json"),"input_manifest":meta(author/"manifest.json"),
"mirror_input_handoff":meta(zipns/"handoff.json"),"mirror_input_manifest":meta(zipns/"manifest.json"),
"review_ref":meta(OWN/"REVIEW.md"),"source_review_ref":meta(OWN/"source-review.json"),
"resource_supplement_ref":meta(OWN/"resource-supplement.json"),
"actual_candidate_refs":sources,
"input_verification_ref":meta(OWN/"input-verification.json"),
"input_before_ref":meta(OWN/"input-vector.before.json"),
"input_after_ref":meta(OWN/"input-vector.after.json"),
"input_drift_ref":meta(OWN/"input-drift.json"),
"commands_ref":meta(OWN/"command-records.json"),"origins_ref":meta(OWN/"failure-origins.json"),
"scope_deviation_ref":meta(OWN/"scope-deviation.json"),
"actual_frozen_inputs":len(before),"actual_input_drift":len(drift),
"all18":"NOT_RUN","Go_AST_compile_gofmt_SQL_driver_HTTP":"NOT_RUN",
"I17":"FATAL_OPEN_NO_ACTUAL_COMPLETE_CALLBACK_NAMES_RAW_VECTORS",
"I16":"OPEN_FUTURE_ROOT_THREE_STAGE_EXECUTION_PROVENANCE",
"future_I18_budget_observation":"original two1000x200ms loops approximately400 seconds plus remaining original work; preserve body",
"next_allowed_boundary":"Exact reviewed candidates and content-matched ZIP may be inputs to new Root-controlled resource/source preparation only. Separate finite scope/module closure/actual builds/owned execution and non-author acceptance required.",
"new_reviewer_origins":origins,"original_failed_input_retry":False,
"old_driver_peer_REQUEST_734ee_unchanged":True,"source_adoption":False,"original_driver_acceptance_changed":False,
"SQL24_installable":False,"three_callbacks_complete":False,"formal_case_increment":0,
"counter_written":False,"Main_cache_module_canonical_author_old_review_writes":0,
"self_metadata_scope_exception":"one misplaced own review script outside project, preserved exactly; cleanup PENDING after policy rejection, no workaround",
"manifest":"manifest.json self excluded; includes handoff; final actual SHA/bytes reported separately"})
write("manifest.json",{"schema":"researchos.independent-review-manifest.v1",
"files":[meta(p) for p in sorted(OWN.rglob("*"),key=lambda p:p.as_posix()) if p.is_file() and p.name!="manifest.json"],
"self_excluded":True})
mf=load("manifest.json")
own_mismatches=[r for r in mf["files"] if meta(r["path"])!=r]
print(json.dumps({"decision":"READY_SOURCE_PREPARATION_ONLY","writer":"STOPPED","actual_frozen_inputs":len(before),"input_drift":drift,"own_manifest_members":len(mf["files"]),"own_member_mismatches":own_mismatches,"terminal_refs":[meta(OWN/n) for n in ["REVIEW.md","source-review.json","resource-supplement.json","handoff.json","manifest.json","failure-origins.json","scope-deviation.json"]],"new_reviewer_origins":origins,"cleanup":"PENDING_POLICY_REJECTION","source_adoption":False,"all18":"NOT_RUN"},ensure_ascii=False))

