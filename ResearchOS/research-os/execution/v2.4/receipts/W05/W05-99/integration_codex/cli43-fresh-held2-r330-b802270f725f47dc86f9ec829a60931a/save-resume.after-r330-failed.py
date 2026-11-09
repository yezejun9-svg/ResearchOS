"""Durable additive resume after r330 failure and r331 source preparation; metadata only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def doc(p):return json.loads(p.read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
cp=doc(ROOT/"execution/v2.4/checkpoint.json");ow=doc(ROOT/"execution/v2.4/path_ownership.json")
assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[330,158,502]
closed=doc(OUT/"root-launch.outer-completion.json")
for r in closed["canonical_refs_at_completion"]:assert pin(Path(r["path"]))==r
names={
"actual_failed_root_completion":OUT/"root-launch.outer-completion.json",
"actual_failed_root_closed_manifest":OUT/"root-launch.closed.manifest.json",
"failed_execution_independent_review":BASE/"cli43_failed_execution_independent_review_codex/b33d80b428a247539130e8585e85f3c7/review.json",
"failed_execution_review_manifest":BASE/"cli43_failed_execution_independent_review_codex/b33d80b428a247539130e8585e85f3c7/manifest.json",
"legacy_schema_source_preparation":BASE/"cli43_legacy_entity_schema_preparation_codex/26c182c39c734501ac4f85cf6c978a86/handoff.json",
"legacy_schema_independent_review":BASE/"cli43_legacy_entity_schema_independent_review_codex/7dd9e18c009e45b4a6a205fb06ddfb70/review.json",
"fixed_seven_origin_cut":OUT/"late-origins.capture.for-r331.v2.json",
"new_stage_source_preparation":OUT/"stage-r331.source-preparation.json",
"F08_terminal_pairing_source":BASE/"f08_driver18_root_binding_terminal_pairing_preparation_codex/f38b92cdbd4844529ce3da03d08630ad/handoff.json",
"F08_terminal_pairing_independent_review":BASE/"f08_driver18_terminal_pairing_independent_source_review_codex/5ee0bc895e324d94852e95e383292cfd/review.json",
"W09_controller_independent_REQUEST":ROOT/"execution/v2.4/receipts/W09/W09-99/f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505/review.json"}
refs={k:pin(p) for k,p in names.items()}
cut=doc(names["fixed_seven_origin_cut"]);assert cut["before"]==[330,158,502] and cut["after"]==[331,159,509] and len(cut["origins"])==7
snapshot={"schema":"researchos.additive-point-in-time-resume.v1","actor":"codex:/root","canonical_tuple":[330,158,502],"known_observed_failure_origins":509,"known_unregistered_distinct_origins":7,"failure_cut_ref":refs["fixed_seven_origin_cut"],"canonical_refs":closed["canonical_refs_at_completion"],"protected_Main_head":"a510dbef4a7e08fb5c428df44c39b133f3ffa856","prior_index_empty_and_11_tracked_D_preserved":True,"refs":refs,"r330":{"actual_outer_and_Python":1,"case00":"QUALIFIED","case01":"FAILED_WRONG_ORACLE_SCHEMA_SOURCE","expected_CLI_native_exit":3,"one_underlying_failure_origin":True,"all_three_generations_exited":True,"job_idle_zero_processes":True,"remaining_owned_handles":0,"qualification":"WITHHELD","Desktop15":"HOLD"},"r331":{"UUID":"c4f309c5528f5d42be5e7eeb146a20aa","namespace":"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa","source_change":"only strict Goal/Task schema path and hash match unchanged fixture legacy b114; POST and original assertions untouched","source_only_independent_decision":"READY_FOR_ROOT_NEW_SCOPE_PREPARATION","stage_initial_tool_chunk":"87ab79","stage_actual_session_id":47883,"stage_final_exit_at_snapshot":None,"actual_registration_or_grant_at_snapshot":False,"requires":["closed metadata stage","independent bound scope review","Root prepare","independent registration draft review","Root CAS seal and grant","independent caller review","new fresh compilation and execution","independent actual evidence qualification"]},"F08":"TERMINAL_PAIR_STATIC_READY; Root capture/sealer/A01-A07/I17/SQL24 OPEN","W09":"SIX_SOURCE_REQUESTS_UNDER_REVISION; candidate target not run","current_formal_acceptance":"0/42; all22parents effective acceptance incomplete","old_cleanup_rejection":{"path":"outside-repo fd09 verify_inputs.py","automatic_approval_review":"CreateProcess policy rejected","status":"PRESERVED; no alternate deletion"},"source_or_formal_acceptance_increment":0,"SDK_MODEL_paid_calls_in_current_scopes":0,"counter_reset":False,"prior_immutable_snapshots_rewritten":False,"native_NULL_preserved":True}
save("RESUME.after-r330.failed.snapshot.json",snapshot)
save("RESUME.after-r330.failed.snapshot.manifest.json",{"self_excluded":True,"entries":[pin(OUT/"RESUME.after-r330.failed.snapshot.json"),pin(Path(__file__).absolute())]})
print(json.dumps({"snapshot_ref":pin(OUT/"RESUME.after-r330.failed.snapshot.json"),"manifest_ref":pin(OUT/"RESUME.after-r330.failed.snapshot.manifest.json"),"canonical_tuple":[330,158,502],"known_observed":509,"formal_increment":0},ensure_ascii=False))
