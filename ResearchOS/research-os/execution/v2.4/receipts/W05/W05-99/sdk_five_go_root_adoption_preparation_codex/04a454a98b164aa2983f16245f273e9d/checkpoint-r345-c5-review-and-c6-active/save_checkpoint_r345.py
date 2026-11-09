import sys
sys.dont_write_bytecode=True
import json,hashlib,os,uuid
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os"); O=Path(__file__).resolve().parent; P=O.parent
B=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 b=p.read_bytes(); return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(p,value):
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json"; old=cp.read_bytes()
assert hashlib.sha256(old).hexdigest()=="ddc7de2afa1131036506e073a9086620ad06d240f10bbe6f7306c81927380539"
c=json.loads(old); assert c["revision"]==344 and len(c["failure_counters"])==702
assert c["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and c["current_step_id"]=="W05-99"
other=[R/"execution/v2.4"/(n+".json") for n in ("path_ownership","step_state","commands")]; ob=[p.read_bytes() for p in other]
main={"internal/host/vault.go":("5bcf6aed6515bd991e5e7222999994e3d9192a6bd8f5a32b4669d4c67c0a6b50",12082),"internal/host/host.go":("6387df33f531be14d32c439095f9ebcf079fb7ae2c27697c98cdc9a554fb5dc7",8703),"apps/control/main.go":("9a519be38a1c09a819864073eedf0eaf9941c4c75f95ded0c3e89143012da9b1",12674),"internal/domain/runtime_qualification.go":("420aaec664f877806af079d47cf5e5a0cc4950f2cdc42b8ae1dc16ef7a4c5c54",16400),"apps/cli/cli_stream.go":("87bfbd69972e674ae5255455ed26ce82ece167d8bb67155beed0cd52c05b9e6f",30399)}
mb={n:(R/n).read_bytes() for n in main}
for n,b in mb.items(): assert (hashlib.sha256(b).hexdigest(),len(b))==main[n]
review=B/"mu_sdk_controller_v5_independent_review_codex/ca1965e9f0b449b786c4e6925d7018fb/independent-source-review.json"
assert pin(review)["sha256"]=="757f59c32d7a48de95f1b0c7b1fc7b3d219547ae92c20304da123ca905c62df2"
rd=json.loads(review.read_bytes());assert rd["decision"]=="REQUEST_CHANGES" and rd["distinct_findings"]==2
save(O/"checkpoint.before.json",c)
c["expected_previous_revision"]=344;c["revision"]=345;c["updated_at"]=datetime.now(timezone.utc).isoformat();c["updated_by"]="codex:/root"
w=c["work_in_progress"];w.update({
"mu_sdk_controller_v5_independent_review_ref":pin(review),
"mu_sdk_controller_review_state":"C5_REQUEST_CHANGES_TWO_P1_C6_O4_SOURCE_CONSTRUCTION_ACTIVE",
"mu_sdk_live_trial_state":"SOURCE_FIX_AND_ROOT_CALLER_INTEGRATION_NO_LIVE_GRANT",
"mu_sdk_controller_open":["C5-R01 actual current Source authors must be excluded by both controller and observer","C5-R02 fresh cleanup must originate from reviewed pinned producer over retained actual Job/process handles","Root resident caller, actual canonical pair, same-PID observer and callback watchdog lifecycle","Trusted Host READY/GO/EOF under whole300s aggregate3-request authority"],
"mu_sdk_source_authors_active":["codex:/root/live_resource_lookup: immutable C6 controller and cleanup producer","codex:/root/w05_merge_review: immutable O4 author provenance gate"],
"mu_sdk_source_readonly_reviewers_active":["codex:/root/command_queue_impl: read-only minimal Root caller integration inputs"],
"mu_sdk_next_action":"Seal C6 and O4; true nonauthor source review; verify actual no-provider Job/watchdog/observer lifecycle and Root resident caller; prepare isolated CLI draft and trusted Host; then bounded3-request real SDK trial.",
"r345_registered_failure_count":702,"r345_observed_failure_count":702,
"mu_sdk_original_699_702_outer_js_projection_gap":"Stored commandExecution records and prior fileChange records are preserved; outer functions.exec JS wrappers were not recoverable. Existing failure counts unchanged.",
"mu_sdk_active_run_uuid":None,"mu_sdk_live_execution_grant_issued":False,"mu_sdk_runtime_qualification":False,"mu_sdk_actual_external_provider_requests_current_trial":0})
c["note"]="Root resumed exact identity/Git/selector at W05-99; Main five Go bytes unchanged, old13 tracked dirty paths preserved. C5 actual independent review REQUEST_CHANGES on current author acceptance and unbound cleanup callback; new C6+O4 scoped Source writers active. Actual private Windows guard component remains independent PASS,22 local tests reused; six parents/zero42 current cases, no provider calls or grant. All702 failures unchanged and projection gaps explicit. No completion claimed."
assert c["failure_counters"]==json.loads(old)["failure_counters"]
new=(json.dumps(c,ensure_ascii=False,indent=2)+"\n").encode()
with (O/"checkpoint.after.proposed.json").open("xb") as f:f.write(new)
save(O/"prepared.json",{"before":pin(O/"checkpoint.before.json"),"proposed":pin(O/"checkpoint.after.proposed.json"),"main_refs":[pin(R/n) for n in main],"other_refs":[pin(p) for p in other],"review":pin(review),"provider_calls":0,"formal_acceptance":False})
assert cp.read_bytes()==old and [p.read_bytes() for p in other]==ob
temp=cp.with_name(cp.name+"."+uuid.uuid4().hex)
with temp.open("xb") as f:f.write(new);f.flush();os.fsync(f.fileno())
assert cp.read_bytes()==old
os.replace(temp,cp)
assert cp.read_bytes()==new and [p.read_bytes() for p in other]==ob and {n:(R/n).read_bytes() for n in main}==mb
closed=save(O/"checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":345,"ownership_revision":168,"registered_failures":702,"observed_failures":702,"old702_unchanged":True,"other_canonical_unchanged":True,"main_five_unchanged":True,"provider_calls":0,"formal_acceptance":False})
resume={"schema":"researchos.root-resume-sdk-controller-host-v2","project_id":c["project_id"],"repository_root":str(R),"head":c["head"],"checkpoint_ref":pin(cp),"checkpoint_revision":345,"ownership_revision":168,"current_card":"W05-99","accepted_parents":6,"current_formal_accepted":0,"formal_cases_total":42,"local_tests_top_level":22,"historical_failures_preserved":702,"observed_failures":702,"old_tracked_git_dirty_count":13,"runtime_qualification":False,"live_execution_grant":False,"external_provider_requests_current_trial":0,"controller_v5_independent_review":pin(review),"source_fix_constructors":w["mu_sdk_source_authors_active"],"read_only_reviewer":w["mu_sdk_source_readonly_reviewers_active"],"actual_private_guard_status":w["mu_sdk_guard_component_actual_status"],"original_io_gaps":w["mu_sdk_original_699_702_outer_js_projection_gap"],"retained_handle_scope":"sys-anchored same-parent memory only; no cross-process persistence or active Root residency claimed","next_action":w["mu_sdk_next_action"],"completion_asserted":False,"closed_ref":closed}
rr=save(P/"RESUME.r345.c5-review-c6-o4-active.original.json",resume)
print(json.dumps({"checkpoint_ref":pin(cp),"closed_ref":closed,"resume_ref":rr,"failures":702,"model_requests":0}),flush=True)

