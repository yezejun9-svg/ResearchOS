import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
V=B/"integration_codex/prepared-abandonment-v2-validation-root-4808160043d8472fa802a31d";S=B/"prepared_run_abandonment_source_v2_codex/a6777ff11e16424eb303721214730682";I=B/"prepared_run_abandonment_independent_review_codex/4f8b191565254fdabddc1b490b12d0a2";D=B/"prepared_abandonment_rehome_validation_failure_codex/753_cf5c2e78c38f1";X=B/"prepared_run_abandonment_scope_diagnostic_codex/20261009T0143Z_7133c137c61fa"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";old=[p.read_bytes() for p in (cp,ow)];refs=[pin(cp),pin(ow)]
assert refs[0]["sha256"]=="9f17ced9489180ed680249949488e1f4a8858a90c3651e5a12a57723db37461b" and refs[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==350 and len(before["failure_counters"])==749 and before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_bytes=[p.read_bytes() for p in others]
m=json.loads((S/"MF.json").read_bytes());source_members=[verify(ref) for ref in m["members"].values()]
assert m["productionAuthority"]=="UNSATISFIED" and m["productionMigration"]=="UNAUTHORIZED"
im=json.loads((I/"manifest.json").read_bytes());independent_members=[verify(ref) for ref in im["members"]]
assert pin(S/"HDF.json")["sha256"]=="92d168267a1bd2ad9e75e734c1cfb53c93e4788075294cc280c9ff0bf9885854" and pin(S/"MF.json")["sha256"]=="bce77647a0862e086cf02d45ff4ec11ead29d81c07b7c65f8cc5f336b6665d6d"
assert pin(I/"review.json")["sha256"]=="b45ef643a6cda053e42c1d5b329f3803ef968dac9dc2035e9947edffb6612e9f"
validation=json.loads((V/"validation.closed.json").read_bytes())
assert validation["status"]=="FAILED_FIXTURE_NATIVE_CLOSED" and validation["actual_native_exit"]==1 and validation["all_owned_jobs_closed"] and validation["main_canonical_unchanged"] and validation["production_db_writes"]==0 and validation["external_provider_requests"]==0
assert validation["test_actions"]["TestPreparedRunAbandonmentSuccessAndIdempotency"]=="fail" and all(v=="pass" for k,v in validation["test_actions"].items() if k!="TestPreparedRunAbandonmentSuccessAndIdempotency")
pending=[
 (752,I/"failure-origin.752.json","56cbd57ec71ee801b39aafef2809b1480b83da5a2441d675a20dd3cd95f1a290",0,None,None,"Read-only independent reviewer included unenumerated nonexistent artifacts.go; rg os2, later listing outer0. No candidate execution; original input/result preserved."),
 (753,D/"failure-origin.753.json","59e788d61f6f4553e6c3a99b665b2374d48379e769afacc51fd1fd49c6223db0",None,None,None,"Source constructor rehome count assertion failed after immutable v2 successful copy. Actual exit codes unobserved; inferred Python1 remains inference only. Original nested full IO capture gap preserved, corrected validation independently0."),
 (754,D/"failure-origin.754.json","af97eada815ffb3066f765efb4831b8178b93988ef6f4389d7b5926f69e34f3f",None,None,None,"Source constructor failure753 export apply_patch rejected because last line must be End Patch; no mutation. Original nested patch/results capture gap explicit; actual process exits null."),
 (755,V/"failure-origin.755.original-tool-io.json","e7ffb837f0c70eaf922f59a51af7590102bc6340c9f9c7e418a1267a5bf4d032",1,1,1,"Root actual isolated native Go test positive qualification fixture hit generic footprint STATE_CONFLICT; old FIXTURE reservation may be the cause, so executor-upload R01 remains separate static finding. Negative fixtures pass, Native1 and RootPython1/outer1 observed; both owned jobs and guards closed; no production DB/provider effects.")]
pending.append((756,B/"prepared_run_abandonment_source_v3_codex/6e97da15b65146e5a6ef73a4804c9d12/failure-origin.756.json","526388f76ac01ffe68713c49f2eaffd5393301f37cfdb56c792541af61f1f77d",0,None,None,"V3 Source author read-only rg guessed nonexistent budget_defaults_test.go; os2, later independent rg match outer0; inner/Python/Native null, original merged input/result saved, no Source/DB/canonical effects."))
for n,p,h,*rest in pending:assert pin(p)["sha256"]==h
frozen=source_members+independent_members+[pin(S/"HDF.json"),pin(S/"MF.json"),pin(I/"handoff.json"),pin(I/"manifest.json")]+[pin(V/n) for n in ("validation.closed.json","formatted.source-members.json","format.invocation.json","test.invocation.json","test.stdout.raw","test.stderr.raw","input-source-guard.cleanup.actual.json","candidate-source-guard.cleanup.actual.json","failure-origin.755.cause-clarification.json")]+[pin(p) for n,p,*rest in pending]+[pin(D/"corrected-validation-original-io.json"),pin(X/"SOURCE_SUBMISSION_SCOPE_MISMATCH.json")]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
base_refs=[]
for n,ref in m["members"].items():
 if n.startswith("candidate-root/") and ref.get("base_sha256"):
  actual=pin(R/n.removeprefix("candidate-root/"));assert actual["sha256"]==ref["base_sha256"];base_refs.append(actual)
frozen+=base_refs+[pin(gp),pin(tp),pin(Path(__file__).resolve())]
frozen=list({ref["path"]:ref for ref in frozen}.values())
gm=types.ModuleType("root_cp351_guard");gm.__file__=str(gp);exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen)
tm=types.ModuleType("root_cp351_tx");tm.__file__=str(tp);exec(compile(guard.get_buffer(str(tp)),str(tp),"exec"),tm.__dict__)
def transform(c,ownership):
 assert c["revision"]==350 and ownership["revision"]==168
 keys={x.get("origin_key") for x in c["failure_counters"]}
 for n,p,h,outer,python,native,detail in pending:
  ref=pin(p);key=hashlib.sha256((ref["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
  payload=dict(observed_ordinal=n,immutable_origin_ref=ref,actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=native,provider_requests=0,diagnostic=detail)
  if n==755:payload.update(causal_clarification_ref=pin(V/"failure-origin.755.cause-clarification.json"),original_failed_model_trial_provider_requests=None)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=payload,counted_once=True,counter_reset=False,automatic_retry=False))
 assert c["failure_counters"][:749]==before["failure_counters"] and len(c["failure_counters"])==754
 c.update(expected_previous_revision=350,revision=351,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(r351_registered_failure_count=754,r351_highest_observed_diagnostic_ordinal=756,mu_sdk_prepared_abandonment_v2_handoff_ref=pin(S/"HDF.json"),mu_sdk_prepared_abandonment_v2_manifest_ref=pin(S/"MF.json"),mu_sdk_prepared_abandonment_v2_actual_validation_ref=pin(V/"validation.closed.json"),mu_sdk_prepared_abandonment_v2_actual_failure_origin_ref=pin(V/"failure-origin.755.original-tool-io.json"),mu_sdk_prepared_abandonment_v2_causal_clarification_ref=pin(V/"failure-origin.755.cause-clarification.json"),mu_sdk_prepared_abandonment_v2_independent_review_ref=pin(I/"review.json"),mu_sdk_prepared_abandonment_scope_mismatch_ref=pin(X/"SOURCE_SUBMISSION_SCOPE_MISMATCH.json"),mu_sdk_prepared_abandonment_source_state="V2_ISOLATED_NATIVE_FIXTURE_FAILED_CLOSED_AND_STATIC_PROFILE_COMPATIBILITY_BLOCK_V3_SOURCE_IN_PROGRESS",mu_sdk_source_authors_active=["codex:/root/command_queue_impl: new immutable prepared-run-abandonment v3 namespace only"],mu_sdk_source_readonly_reviewers_active=["codex:/root/w05_merge_review: private native authority and schema migration design review only"],mu_sdk_business_reconciliation_state="CUSTOM_GAP_OLD_RUN_QUEUED_TASK_RUNNING_DISPATCH_PREPARED_PRESERVED",mu_sdk_next_action="Repair only new v3 Source/profile compatibility and production-like LIVE unknown-cost fixtures; actual Root isolated Go validation and independent review. Separate trusted native authority and fixed schema-only migration/backup restore rehearsal before any populated DB reconciliation. No live trial/retry/reset.")
 c["note"]="CP351 appends752-756 once: original749 prefix exactlypreserved=>754/highest756. v2 Source copied to detached owned worktree, fmt0/testNative1/RootPython1/outer1 positivefixturegeneric footprint conflict, negativecases pass,2ownedjobs/allguardsclosed,Main/canonicalunchanged. Cause clarification preserves failure755 original and separates actual generic rejection from static R01 blanket executorprofileupload defect; old fixture uses FIXTURE dispatch reservation, meaningful LIVE unknown-cost fixture needed. Source v2 and wrongscopev1 immutable/unadopted; SourceScopeMismatch separately recorded, not fabricated toolfailure. v3 Source author scoped to fresh exact W05/W05-99 namespace, independent production nativeauthority/schema-only migration design OPEN. OldmodeltrialFailedClosed businessQUEUED/RUNNING/PREPARED, providerNULL/recordedmodelEffects0,onceconsumed/clocknotreset, no newmodelcalls. Hostv5actualGo27nodes25leaf+indieREADY componentonly retained.6/22 historicalparents0/42currentformalGoalactive/notcomplete. OW168/SS/CM/Head/Main preserved."
 return c,ownership
try:
 transaction=tm.update_pair(refs,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==351
finally:
 cleanup=guard.close();assert cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"];save("source_guard.cleanup.actual.json",cleanup)
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),other_canonical_refs=[pin(p) for p in others],old749_preserved=True,registered_failures=754,highest_diagnostic_ordinal=756,original_model_trial_provider_requests=None,new_fixture_provider_requests=0,actual_fixture_native_exit=1,formal_acceptance=False))
resume=save("RESUME.r351.original.json",dict(schema="researchos.root-resume-prepared-abandonment-fixture-failure.v1",repository_root=str(R),project_id=before["project_id"],head=before["head"],checkpoint_ref=pin(cp),checkpoint_revision=351,ownership_revision=168,current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=754,highest_diagnostic_ordinal=756,source_v2_handoff_ref=pin(S/"HDF.json"),source_v2_manifest_ref=pin(S/"MF.json"),source_v2_actual_status=validation["status"],source_v2_validation_ref=pin(V/"validation.closed.json"),causal_clarification_ref=pin(V/"failure-origin.755.cause-clarification.json"),source_v2_independent_ref=pin(I/"review.json"),prepared_business_recovery_status="V3_SOURCE_IN_PROGRESS_NATIVE_AUTHORITY_AND_SCHEMA_ONLY_UPGRADE_GATES_OPEN",old_trial_status="FAILED_EXECUTION_CLOSED_BUSINESS_OPEN",old_Run_status="QUEUED",old_Task_status="RUNNING",old_dispatch_status="PREPARED",model_trial_provider_requests=None,recorded_model_effects=0,new_fixture_provider_requests=0,once_consumed=True,clock_reset_permitted=False,automatic_retry=False,next_action="Root isolated v3 actual Go validation and independent review; trusted authority+fixed schema-only upgrade need separate Source and actual backup/restore rehearsal; no live model trial until gates satisfied.",completion_asserted=False,proof_ref=proof))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_SOURCE_V2_FIXTURE_FAILED_CLOSED_V3_IN_PROGRESS",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,registered_failures=754,highest_diagnostic_ordinal=756,provider_requests=None,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=754,highest_diagnostic_ordinal=756)),flush=True)
