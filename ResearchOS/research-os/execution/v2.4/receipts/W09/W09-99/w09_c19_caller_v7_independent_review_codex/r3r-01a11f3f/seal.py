import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
r=json.loads((N/"result.json").read_bytes());checks=json.loads((N/"checks.json").read_bytes());refs=json.loads((N/"input-pins.json").read_bytes())
assert checks["all_passed"] and checks["count"]==196 and len(refs)==90
guards=[]
for name in ("source-guard.cleanup.json","source-guard.fixed.cleanup.json"):
 g=json.loads((N/name).read_bytes())
 assert g["closed"] and not g["errors"] and g["retained_handles_count"]==0 and len(g["entries"])==90
 assert all(v["closed"] and v["verified"] and v["final_path_match"] for v in g["entries"])
 guards.append(pin(N/name))
origin=pin(N/"failure-origin.935.original-tool-io.json")
failure=json.loads(Path(origin["path"]).read_bytes())
assert failure["ordinal"]==935 and failure["result"]["chunk_id"]=="339c9e" and failure["result"]["exit_code"]==1 and failure["qualification"]["python_exit"]==1
save("failure-disposition.json",dict(reviewer_original_failures=[dict(ordinal=935,origin_ref=origin,script_ref=pin(N/"review.py"),cleanup_ref=guards[0])],author_original_failures_preserved=[933,934],successful_followup_original_io_ref=pin(N/"r3_run_fixed.original-tool-io.json"),successful_control_run_result_ref=pin(N/"result.json"),successful_control_run_new_failure_count=0,overall_reviewer_new_original_failure_count=1,failures_not_overwritten_or_split=True,candidate_Source_unchanged=True,automatic_product_retry=False))
for v in refs:assert pin(Path(v["path"]))==v
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
save("MF.json",dict(schema="researchos.independent-source-review-manifest.v1",members=members,member_count=len(members)))
save("HDF.json",dict(schema="researchos.w09-c19-r3-independent-source-review.v1",status=r["status"],source_resource_gate=r["source_resource_gate"],actual_resource_gate="NOT_RUN",manifest_ref=pin(N/"MF.json"),report_ref=pin(N/"REPORT.md"),successful_control_run_result_ref=pin(N/"result.json"),checks_ref=pin(N/"checks.json"),input_pins_ref=pin(N/"input-pins.json"),independent_inverse_ref=pin(N/"independent-inverse.json"),actual_guard_cleanup_refs=guards,failure_disposition_ref=pin(N/"failure-disposition.json"),candidate_HDF=r["candidate_HDF"],candidate_MF=r["candidate_MF"],prepare_ref=r["prepare_ref"],producer_ref=r["producer_ref"],choice_ref=r["choice_ref"],calling_contract_ref=r["calling_contract_ref"],checks=196,inputs=90,all_other_r2_caller_bytes_and_AST_unchanged=True,Source21_closure_only_changed=True,author_controls_retained128_new13=True,new_producer_packet_and_ModeDecision_required=True,current_canonical_read_or_held=False,five_future_paths_absent=True,Root_scope_registration_and_explicit_same_fresh_vector_required=True,actual_Git_Go_SQL_Native_API_model_consumer=False,formal_consumers="NOT_RUN_REGISTRY_UNBOUND",formal_acceptance=False,execution_grant=False,actual_source_guards_closed=True,retained_handles=0,author_original_failures_preserved=[933,934],reviewer_original_failures=[dict(ordinal=935,origin_ref=origin)],new_product_failures=[],STOP_FINAL=True))
for v in members+refs:assert pin(Path(v["path"]))==v
save("postseal.json",dict(status="PASS_POSTSEAL",HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),members=len(members),inputs=len(refs),all_pins_unchanged=True))
print(json.dumps(dict(HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),postseal=pin(N/"postseal.json"),failure935=origin),ensure_ascii=False))
