import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
V=B/"integration_codex/trusted-host-v5-lossless-build-root-17f16d9253094e14bedfb51b";I=B/"mu_sdk_trusted_host_v5_independent_review_codex/13bf51dc0fa942e692d70a0ab98b2e08";C=B/"predispatch_launch_causality_review_codex/04e6a187dc5642f19a7c97bb853632a4";S=B/"mu_sdk_predispatch_recovery_semantics_review_codex/5ed5d9b72e72455daae65ad9c5e2f697";P=B/"checkpoint_r349_independent_review_codex/f0c1a7df78214c9aafb54033b01a8d09"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";old=[p.read_bytes() for p in (cp,ow)];refs=[pin(cp),pin(ow)]
assert refs[0]["sha256"]=="6c0d3468f9c55a69b9bd488c88bfeb7002333be970bb24160ba902982fba9a6b" and refs[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==349 and len(before["failure_counters"])==747
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_bytes=[p.read_bytes() for p in others]
for directory in (I,C,P):
 m=json.loads((directory/"manifest.json").read_bytes())
 for ref in m["members"]:
  actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"]
assert pin(I/"handoff.json")["sha256"]=="bea14b66c8e69e1dfdd06180f7e340dc63b22b7b4bba54c703d3cc3301020f37" and pin(C/"handoff.json")["sha256"]=="a72a51eb300ec5b4cbc625f2cba399273f25560f7621718c2e9fba199cd87d0d" and pin(P/"handoff.json")["sha256"]=="80276b80ca39ab8ccf3d22e31589e9083ab0cdf9e113fd0f011b8df7ee9d44be"
validation=json.loads((V/"reader-validation.closed.json").read_bytes());review=json.loads((I/"handoff.json").read_bytes())
assert validation["status"]=="ACTUAL_GO_READER_TESTS_AND_COMPILE_PASSED_SOURCE_ONLY" and validation["go_test_pass_count"]==27 and validation["target_host_executions"]==0 and validation["provider_requests"]==0
assert review["decision"]=="READY_SOURCE_AND_ACTUAL_GO_COMPONENT_ONLY" and not review["model_trial_authority"]
binary=validation["binary_ref"];assert pin(binary["path"])==binary and binary["sha256"]=="dee632a6b72d007b460cd060580b9070d04ce47aa53080ca39e56db364898f71"
frozen=[pin(V/n) for n in ("reader-validation.closed.json","formatted.source-members.json","original-tool-io.json","input-source-guard.cleanup.actual.json","formatted-source-guard.cleanup.actual.json")]+[pin(I/n) for n in ("handoff.json","manifest.json","review.json","failure-origin.750.json")]+[pin(C/n) for n in ("handoff.json","manifest.json","review.json","failure-origin.751.json")]+[pin(S/"review.json"),pin(P/"handoff.json"),binary]
pending=[(750,I/"failure-origin.750.json",1,1,None,"Independent Source diff reader Path.read_text default encoding misdecoded UTF8 MF and JSONDecodeError; corrected explicit UTF8 diff check passed; no Native/SQL/provider"),
 (751,C/"failure-origin.751.json",1,None,None,"Read-only causal reviewer guessed nonexistent cmd search root; original stored input/result retained; no Python/Native/SQL/provider")]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
gm=types.ModuleType("root_cp350_guard");gm.__file__=str(gp);exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire([pin(gp),pin(tp),pin(Path(__file__).resolve())]+frozen)
tm=types.ModuleType("root_cp350_tx");tm.__file__=str(tp);exec(compile(guard.get_buffer(str(tp)),str(tp),"exec"),tm.__dict__)
def transform(c,ownership):
 assert c["revision"]==349 and ownership["revision"]==168
 keys={x.get("origin_key") for x in c["failure_counters"]}
 for n,p,outer,python,native,detail in pending:
  ref=pin(p);key=hashlib.sha256((ref["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=native,provider_requests=0,diagnostic=detail),counted_once=True,counter_reset=False,automatic_retry=False))
 assert c["failure_counters"][:747]==before["failure_counters"] and len(c["failure_counters"])==749
 c.update(expected_previous_revision=349,revision=350,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(r350_registered_failure_count=749,r350_highest_observed_diagnostic_ordinal=751,mu_sdk_cp349_independent_review_handoff_ref=pin(P/"handoff.json"),mu_sdk_trusted_host_v5_state="READY_SOURCE_AND_ACTUAL_GO_COMPONENT_ONLY",mu_sdk_trusted_host_v5_actual_validation_ref=pin(V/"reader-validation.closed.json"),mu_sdk_trusted_host_v5_original_tool_io_ref=pin(V/"original-tool-io.json"),mu_sdk_trusted_host_v5_independent_handoff_ref=pin(I/"handoff.json"),mu_sdk_trusted_host_v5_binary_ref=binary,mu_sdk_trusted_host_v5_actual_go_test_count=27,mu_sdk_trusted_host_v5_actual_owned_jobs_closed=3,mu_sdk_trusted_host_v5_actual_guard_entries_closed=46,mu_sdk_predispatch_launch_causality_handoff_ref=pin(C/"handoff.json"),mu_sdk_predispatch_recovery_semantics_ref=pin(S/"review.json"),mu_sdk_business_reconciliation_state="CUSTOM_GAP_NO_EXISTING_TERMINAL_PRE_DISPATCH_API",mu_sdk_prepared_abandonment_source_state="AUTHORIZED_NARROW_SOURCE_CANDIDATE_UNDER_CONSTRUCTION_PRODUCTION_WITNESS_AND_MIGRATION_GATES_OPEN",mu_sdk_source_authors_active=["codex:/root/trusted_go_lossless_source_v5: receipt-only prepared-run-abandonment candidate"],mu_sdk_source_readonly_reviewers_active=[],mu_sdk_next_action="Construct and actual-test isolated trusted prepared-run abandonment Source with immutable history, CAS/native authority and no synthetic worker journal; independent review; no populated migration/live reconciliation/model relaunch before concrete production witness and migration-prebackup gates.")
 c["note"]="Hostv5 narrowly fixes pinned owned-job FILETIME reader while general/grant/once domain canonical rules remain. Actual owned Go27nodes25leaf tests pass/compile Native3jobs0closed/46guardentriesclosed; trueindie59refs source+Go component only. CP349 trueindie39checks40pins0drift preserved. Existing cancel/recovery has no demonstrated terminal pre-dispatch path; reviewed current coordinator commitsSTARTEDworkerlocator beforeStartBridge, absence proof conditional. Receipt-only prepared-run-abandonment Source candidate authorized, private Native witness/0024 migration-prebackup integration still OPEN; don't alter production/old once/clock/attempts or fakeObservation. Provider currentfailedtrialnull/modelEffects0 remain scoped; no new model calls. Old747failures exactlypreserved, append750/751 once=>749/highest751;noreset. Main/head/OW168/SS/CM unchanged.6/22 historical parents0/42 currentformal,Goalactive/notcomplete."
 return c,ownership
try:
 transaction=tm.update_pair(refs,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==350
finally:
 cleanup=guard.close();assert cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"];save("source_guard.cleanup.actual.json",cleanup)
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),other_canonical_refs=[pin(p) for p in others],old747_preserved=True,registered_failures=749,highest_diagnostic_ordinal=751,model_trial_provider_requests=None,new_go_test_provider_requests=0,formal_acceptance=False))
resume=save("RESUME.r350.original.json",dict(schema="researchos.root-resume-go-reader-ready-business-gap.v1",repository_root=str(R),project_id=before["project_id"],head=before["head"],checkpoint_ref=pin(cp),checkpoint_revision=350,ownership_revision=168,current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=749,highest_diagnostic_ordinal=751,host_v5_component_status=review["decision"],host_v5_validation_ref=pin(V/"reader-validation.closed.json"),host_v5_independent_ref=pin(I/"handoff.json"),host_v5_binary_ref=binary,prepared_business_recovery_status="CUSTOM_GAP_SOURCE_IN_PROGRESS_NATIVE_AUTHORITY_AND_MIGRATION_GATES_OPEN",old_trial_status="FAILED_EXECUTION_CLOSED_BUSINESS_OPEN",old_Run_status="QUEUED",old_Task_status="RUNNING",old_dispatch_status="PREPARED",model_trial_provider_requests=None,recorded_model_effects=0,new_go_test_provider_requests=0,once_consumed=True,clock_reset_permitted=False,automatic_retry=False,next_action="Isolated actual tests/review for receipt-only prepared-run-abandonment candidate. No populated migration/live model trial until production authority and backup/migration gates satisfied.",completion_asserted=False,proof_ref=proof))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_GO_COMPONENT_READY_BUSINESS_CUSTOM_GAP",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,registered_failures=749,highest_diagnostic_ordinal=751,provider_requests=None,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=749,highest_diagnostic_ordinal=751)),flush=True)

