"""Additive actual execution resume; preserves independently pending qualification."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
ROOT=Path(r"D:\作品集\ResearchOS\research-os");OUT=Path(__file__).absolute().parent
BASE=ROOT/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 p=Path(p).absolute();b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
closed=read(OUT/"root-launch.outer-completion.json")
assert pin(OUT/"root-launch.outer-completion.json")["sha256"]=="8d2b7c842836ded1bdc50b34feb4a74acfa62364040ffe51ceff3acaf6f75f06"
assert closed["actual_outer_tool_exit"]==closed["actual_python_caller_exit"]==closed["actual_launcher_native_exit"]==closed["actual_inner_python_native_exit"]==0
assert closed["underlying_local_failure_count"]==0 and closed["first_origin_ref"] is None and closed["native_calls"]==14 and closed["SDK_MODEL_external_paid"]==0
assert len(closed["actual_case_results_original_payload"])==2 and all(r["status"]=="PASS" for r in closed["actual_case_results_original_payload"]) and not closed["actual_NOT_RUN_original_payload"]
for r in closed["canonical_refs_at_completion"]:assert pin(r["path"])==r
cp=read(ROOT/"execution/v2.4/checkpoint.json");ow=read(ROOT/"execution/v2.4/path_ownership.json")
assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[331,159,509]
names={
"Root_actual_completion":OUT/"root-launch.outer-completion.json",
"Root_closed_manifest":OUT/"root-launch.closed.manifest.json",
"Root_authorized_before_caller_snapshot":OUT/"RESUME.authorized.before-caller.snapshot.json",
"CLI_caller_independent_review":BASE/"cli43_root_caller_static_independent_review_codex/aebdd56f135c4063a6b0ad4679707822/review.json",
"W09_source_revision_independent_review":ROOT/"execution/v2.4/receipts/W09/W09-99/w09_controller_revision_independent_review_codex/bd6b0994244f4676a3c3a2be8ef3661a/review.json",
"W09_late_coordination_origin":ROOT/"execution/v2.4/receipts/W09/W09-99/w09_controller_revision_independent_review_codex/bd6b0994244f4676a3c3a2be8ef3661a/coordination-failure-origin.json",
"F08_Root_producer_preparation_handoff":BASE/"f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/handoff.json",
"F08_Root_producer_contract_mapping":BASE/"f08_driver18_root_producer_contract_mapping_codex/172e0c45ad4a4b25b19e1da1822804f2/contract-map.json"}
refs={n:pin(p) for n,p in names.items()}
assert refs["W09_late_coordination_origin"]["sha256"]=="21eb69a5dcc61a1f6ea23ca7ef9075a4e9f3b928ea409643671b263ea713161f"
snapshot={"schema":"researchos.additive-actual-execution-resume.v1","actor":"codex:/root","canonical_tuple":[331,159,509],"known_observed_origins_at_snapshot":510,"known_unregistered_distinct_origins":1,"original_native_NULLs_and_fixed_cut_preserved":True,"counter_reset":False,"canonical_refs":closed["canonical_refs_at_completion"],"protected_Main_head":"a510dbef4a7e08fb5c428df44c39b133f3ffa856","actual_scope_ref":closed["source_scope_ref"],"actual_grant_ref":closed["grant_ref"],"refs":refs,"actual_execution":{"outer_Python_launcher_inner_native_exits":[0,0,0,0],"native_calls":14,"SDK_MODEL_external_paid":0,"underlying_new_failure_count":0,"case_results":closed["actual_case_results_original_payload"],"NOT_RUN":closed["actual_NOT_RUN_original_payload"],"independent_actual_qualification":"PENDING","complete_current43_source_validation":False,"source_acceptance":False,"formal_increment":0},"next_actions":["W05 non-author actual bounded held2 evidence qualification (running; no rerun)","Desktop15 machine-gate mapping preserves old43 sourceimport proof and adds actual qualification (readonly running)","F08 Root producer source-only non-author review (running; actual A01-A07/I17/SQL24 OPEN)","W09 actual Root capsule producer and v2/v3 composition remain OPEN"],"W09_source_review":"READY_PREPARATION_ONLY; C01/C02/C03/C04/C06 source fixes; C05 actual Root proof OPEN","Desktop15":"HOLD_PENDING_CLI_ACTUAL_INDEPENDENT_QUALIFICATION","effective_parent_acceptance":"all22 incomplete","current_formal_acceptance":"0/42","original_failure_receipts_or_historical_snapshots_modified":False,"old_outside_repo_cleanup_policy_rejection":"PRESERVED; no alternate deletion"}
save("RESUME.actual-execution.snapshot.json",snapshot)
save("RESUME.actual-execution.snapshot.manifest.json",{"self_excluded":True,"entries":[pin(OUT/"RESUME.actual-execution.snapshot.json"),pin(__file__)]})
print(json.dumps({"snapshot_ref":pin(OUT/"RESUME.actual-execution.snapshot.json"),"manifest_ref":pin(OUT/"RESUME.actual-execution.snapshot.manifest.json"),"tuple":[331,159,509],"known_observed":510,"independent_qualification":"PENDING","formal_increment":0},ensure_ascii=False))
