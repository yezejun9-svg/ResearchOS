import sys
sys.dont_write_bytecode=True
import hashlib,json,types,os
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent;ST=B/"integration_codex/staged-runtime-prepare-root-59ef355458e14c0082ae8f82d98"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";old=[p.read_bytes() for p in (cp,ow)];refs=[pin(cp),pin(ow)]
assert refs[0]["sha256"]=="2a6dc37c0b2a8718bcec30f94f49d286892c26c6ad8bc910d946429fa68caf60" and refs[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
c=json.loads(old[0]);assert c["revision"]==347 and len(c["failure_counters"])==737
other=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];otherbytes=[p.read_bytes() for p in other]
p739=B/"mu_sdk_root_coordinator_source_v4_codex/934c2f06dc1946e5aa7d5e04589dfdd2/original-tool-io.json"
p741=B/"mu_sdk_trusted_host_v4_delta_review_codex/3874b7621ecbe249b42144ded9b65406/failure-origin.741.json"
p743=B/"mu_sdk_root_coordinator_v4_independent_review_codex/a576a6bb513846a4b4636de1ca6eda54/failure-origin.743.json"
pending=[(739,p739,1,"Source constructor guessed a .planning path; independent Python/native null. OriginalIO selector739;740 empty match is a nonfailure observation"),
 (741,p741,None,"Reviewer functions.exec JS parse error before exec_command"),
 (742,ST/"failure-origin.742.visible-tool-response.json",None,"Root JS .index instead of .indexOf failed before patch; explicit transport capture gap"),
 (743,p743,None,"Reviewer command launch rejected os206 length before shell/Python/native started"),
 (744,ST/"failure-origin.744.original-tool-io.json",1,"Root read-only Get-Content guessed missing origins filename; output diagnostic suppressed")]
nonfailure=save("diagnostic740.no-match.observation.original.json",dict(observed_ordinal=740,original_io_ref=pin(p739),failure_counted=False,classification="RG_EMPTY_MATCH_QUERY_OBSERVATION",capture_scope="Source author original IO selector740",counter_reset=False))
final=json.loads((ST/"prepare.finalized.actual.json").read_bytes());bootstrap=json.loads((ST/"bootstrap.result.json").read_bytes());life=json.loads((ST/"bootstrap.lifecycle.actual.json").read_bytes())
assert final["status"]=="PREPARED" and final["provider_requests"]==0 and bootstrap["db_counts"]==dict(Task=1,Run=0,BudgetLedgerEntry=0,resource_effects=0) and life["all_owned_jobs_cleanup_confirmed"] is True and life["error"] is None
review_path=B/"staged_runtime_actual_component_review_codex/8355e6db26554f058a841dc0f4a88329/handoff.json"
review=json.loads(review_path.read_bytes());assert review["decision"]=="PASS_ACTUAL_COMPONENT_NO_PROVIDER" and review["runtime_qualification"] is False
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
gm=types.ModuleType("root_cp348_guard");gm.__file__=str(gp);exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
guard=gm.SourceReadGuard();guard.acquire([pin(gp),pin(tp),pin(Path(__file__).resolve())])
tm=types.ModuleType("root_cp348_tx");tm.__file__=str(tp);exec(compile(guard.get_buffer(str(tp)),str(tp),"exec"),tm.__dict__)
def transform(checkpoint,ownership):
 assert checkpoint["revision"]==347 and len(checkpoint["failure_counters"])==737 and ownership["revision"]==168
 keys={x.get("origin_key") for x in checkpoint["failure_counters"]}
 for ordinal,path,outer,detail in pending:
  ref=pin(path);key=hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest();assert key not in keys;keys.add(key)
  checkpoint["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=ordinal,immutable_origin_ref=ref,actual_outer_exit=outer,actual_python_exit=None,actual_native_exit=None,provider_requests=0,diagnostic=detail),counted_once=True,counter_reset=False,automatic_retry=False))
 assert checkpoint["failure_counters"][:737]==c["failure_counters"] and len(checkpoint["failure_counters"])==742
 checkpoint.update(expected_previous_revision=347,revision=348,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 w=checkpoint["work_in_progress"]
 w.update(r348_registered_failure_count=742,r348_highest_observed_diagnostic_ordinal=744,r348_uncounted_no_match_diagnostic_ref=nonfailure,mu_sdk_source_authors_active=["codex:/root/command_queue_impl: resident coordinator v5 consolidated Source fixes"],mu_sdk_source_readonly_reviewers_active=[],mu_sdk_actual_cli_init_state="ACTUAL_INIT_REUSED_CONTINUED_ORDINARY_CLI_DRAFT_AND_STAGED_PREPARATION_PASSED_INDEPENDENT_COMPONENT_REVIEW",mu_sdk_actual_staged_bootstrap_ref=pin(ST/"bootstrap.result.json"),mu_sdk_actual_staged_runtime_prepare_ref=pin(ST/"runtime.prepare.actual.json"),mu_sdk_actual_staged_finalize_ref=pin(ST/"prepare.finalized.actual.json"),mu_sdk_actual_staged_lifecycle_ref=pin(ST/"bootstrap.lifecycle.actual.json"),mu_sdk_actual_staged_component_review_handoff_ref=pin(review_path),mu_sdk_controller_state="C7_O4_READY_SOURCE_ONLY_NO_TRIAL",mu_sdk_root_coordinator_v4_state="BLOCKED_SOURCE_R01_EXACT_ARGV_PATH_ORDER_AND_R02_COMPLETE_FOUR_JOB_PROOF",mu_sdk_root_coordinator_v4_independent_review_handoff_ref=pin(B/"mu_sdk_root_coordinator_v4_independent_review_codex/a576a6bb513846a4b4636de1ca6eda54/handoff.json"),mu_sdk_runtime_id=final["runtime_id"],mu_sdk_draft_goal_id=final["draft_goal_id"],mu_sdk_qualification_task_id=final["qualification_task_id"],mu_sdk_qualification_task_status="DRAFT",mu_sdk_qualification_admitted=False,mu_sdk_qualification_runs=0,mu_sdk_live_execution_grant_issued=False,mu_sdk_actual_external_provider_requests_current_trial=0,mu_sdk_runtime_qualification=False,mu_sdk_all_bootstrap_owned_jobs_closed=True,mu_sdk_staged_source_guard_entries_closed=17,mu_sdk_next_action="Consume existing PREPARED receipt after coordinator v5 Source fixes and nonauthor review; preserve successful CLI/bootstrap; begin exactly one qualification1+ordinary2 shared300s trial only after readiness")
 checkpoint["note"]="Actual successful zero-provider continuation of existing initialized project, all4 Native Jobs/extra dup handles and17 Source guards closed. Independent56 component checks and real read-only DB:ordinaryGoalDRAFT/Task0, qualificationTask1DRAFT,Run/effects/budget/qualification_run0, plan1. C4Sourceblocked two interface/proof groups; C5Source in progress, no setup rerun. Preserve old737 failures; append739/741-744 once (740 no-match observation). Total742/highest744. No runtime qualification,grant,formal acceptance advanced;6/22 historical parents0/42 current formal. Main/head/OW168/SS/CM unchanged."
 return checkpoint,ownership
try:
 transaction=tm.update_pair(refs,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in other]==otherbytes and json.loads(cp.read_bytes())["revision"]==348
finally:
 cleanup=guard.close();assert cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"];save("source_guard.cleanup.actual.json",cleanup)
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),other_canonical_refs=[pin(p) for p in other],old737_preserved=True,registered_failures=742,highest_diagnostic_ordinal=744,provider_requests=0,formal_acceptance=False))
resume=save("RESUME.r348.original.json",dict(schema="researchos.root-resume-prepared-sdk-v4",repository_root=str(R),project_id=c["project_id"],head=c["head"],checkpoint_ref=pin(cp),checkpoint_revision=348,ownership_revision=168,current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=742,highest_diagnostic_ordinal=744,controller="C7_O4_SOURCE_READY",coordinator="V4_SOURCE_BLOCKED_V5_CONSOLIDATED_FIX_PENDING",bootstrap_ref=pin(ST/"bootstrap.result.json"),finalized_preparation_ref=pin(ST/"prepare.finalized.actual.json"),component_review_ref=pin(review_path),runtime_id=final["runtime_id"],qualification_task_id=final["qualification_task_id"],draft_goal_id=final["draft_goal_id"],qualification_admitted=False,provider_requests_current_trial=0,all_jobs_closed=True,source_guard_entries_closed=17,next_action="Complete v5 Source+indie; consume current PREPARED, never recreate initialization/preparation. Single bounded real trial qualification1+ordinary2/8192tokens/300s.",completion_asserted=False,proof_ref=proof))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_PREPARED_NO_PROVIDER",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,registered_failures=742,highest_diagnostic_ordinal=744,qualification=False,provider_requests=0,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=742,provider_requests=0)),flush=True)

