import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
L=B/"integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff";A=B/"model_trial_failure745_component_review_codex/18f25bd65ef34e189490677e760b9864";D=B/"mu_sdk_go_lossless_recovery_review_codex/58c99c4b508b497d9628de9772b7a1b8"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";old=[p.read_bytes() for p in (cp,ow)];refs=[pin(cp),pin(ow)]
assert refs[0]["sha256"]=="5991855edd56cea2042cbb0231226e46ce574adbb54d783507d7573036a69f6d" and refs[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
c=json.loads(old[0]);assert c["revision"]==348 and len(c["failure_counters"])==742 and c["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
other=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];otherbytes=[p.read_bytes() for p in other]
pending=[
 (745,L/"failure-origin.745.original-tool-io.json",0,0,1,None,"Actual first C5 trial structured FAILED_EXECUTION_CLOSED while shell/Python0; admitNative0 executeNative1; GO sent; contract FILETIME canonical precision rejection before claim/RunAdmitted"),
 (746,A/"failure-origin.746.json",1,None,None,0,"Read-only reviewer guessed nonexistent runtime_coordinator.go; original observed chunkdbfecb; capture gap explicit"),
 (747,D/"failure-origin.747.json",0,None,None,0,"Read-only reviewer guessed two domain filenames; os2 two diagnostics in one tool invocation; inner rg exit unobserved"),
 (748,D/"failure-origin.748.json",1,None,None,0,"Read-only reviewer used wrong relative root; os3 four diagnostics in one invocation; no Python/native/SQL/provider"),
 (749,B/"integration_codex/trusted-host-v5-lossless-build-root-17f16d9253094e14bedfb51b/failure-origin.749.visible-tool-response.json",None,None,None,0,"Root JS undefined raw-tag r before tools/mutation; visible response and exact failing expression; full original input capture gap explicit")
]
expected_pins=[
 (A/"handoff.json","b3d192b3b325469328d39bab4318cd0e3c3b3f3bc617b4ec92f65152c1d86be3",2590),
 (A/"manifest.json","8d84c2f6eb7a3e36a33a2781dbf7fa11d01041b9fda23540b6ef85a32228cacb",9107),
 (A/"review.json","36441f85495593ecf8533a35a746f78eb80246845fcec1211d1019ce550930b4",4664),
 (D/"handoff.json","a42fb38690b6b1a975213bae52191a449269ef6e904b6de47013627de7a7b34b",1543),
 (D/"manifest.json","e0f825f0385ba376fb3ebd6cf00c52eb214467420c2a30d6ed226fb8e5f36d40",1734),
 (D/"review.json","5f0ba293c1fb46ea929f41aab88ece2a55613cda920e4ee83759ab2ed487433a",7770)
]
for p,h,n in expected_pins:assert pin(p)==dict(path=str(p),sha256=h,bytes=n)
for m in (A/"manifest.json",D/"manifest.json"):
 for ref in json.loads(m.read_bytes())["members"]:assert pin(ref["path"])==ref
audit=json.loads((A/"handoff.json").read_bytes());assert audit["decision"]=="FAILURE745_CONFIRMED_CLOSED_DISPATCH_NOT_STARTED" and audit["failed_trial_provider_requests"] is None and audit["recorded_model_effects"]==0 and audit["owned_jobs_confirmed_closed"]==2
life=json.loads((L/"trial-output/root-coordinator.lifecycle.json").read_bytes());assert life["state"]=="FAILED_EXECUTION_CLOSED" and life["go_sent"] is True and life["provider_requests"] is None and life["C7_actual_lifecycle_proven"] is False and life["same_parent_must_remain_alive"] is False
assert len(life["jobs"])==2 and all(j["cleanup"]["closed"] is True for j in life["jobs"])
admit=json.loads((L/"trial-output/host.admitted.json").read_bytes());assert admit["qualification_run_id"]=="7d5bc49c4951a20d0f5b3c9c344b8b45" and admit["qualification_epoch"]==1
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
gm=types.ModuleType("root_cp349_guard");gm.__file__=str(gp);exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
evidence=[pin(p) for p,_,_ in expected_pins]+[pin(p) for _,p,_,_,_,_,_ in pending]+[pin(L/"trial-output"/n) for n in ("root-coordinator.lifecycle.json","host.admitted.json","host-go.once.json","whole-trial-clock.json")]+[pin(L/"wrapper.source-guard.cleanup.actual.json")]
guard=gm.SourceReadGuard();guard.acquire([pin(gp),pin(tp),pin(Path(__file__).resolve())]+evidence)
tm=types.ModuleType("root_cp349_tx");tm.__file__=str(tp);exec(compile(guard.get_buffer(str(tp)),str(tp),"exec"),tm.__dict__)
def transform(checkpoint,ownership):
 assert checkpoint["revision"]==348 and len(checkpoint["failure_counters"])==742 and ownership["revision"]==168
 keys={x.get("origin_key") for x in checkpoint["failure_counters"]}
 for ordinal,path,outer,python,native,provider,detail in pending:
  ref=pin(path);key=hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest();assert key not in keys;keys.add(key)
  checkpoint["failure_counters"].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=ordinal,immutable_origin_ref=ref,actual_outer_exit=outer,actual_python_exit=python,actual_native_exit=native,provider_requests=provider,diagnostic=detail),counted_once=True,counter_reset=False,automatic_retry=False))
 assert checkpoint["failure_counters"][:742]==c["failure_counters"] and len(checkpoint["failure_counters"])==747
 checkpoint.update(expected_previous_revision=348,revision=349,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 checkpoint["work_in_progress"].update(r349_registered_failure_count=747,r349_highest_observed_diagnostic_ordinal=749,mu_sdk_root_coordinator_v5_state="READY_SOURCE_TRUE_INDEPENDENT_REVIEW_ACTUAL_FIRST_TRIAL_FAILED_CLOSED",mu_sdk_root_coordinator_state="ACTUAL_FAILED_CLOSED_BEFORE_GO_CLAIM",mu_sdk_controller_state="C7_O4_SOURCE_READY_C7_ACTUAL_NOT_STARTED",mu_sdk_actual_model_trial_output_ref=pin(L/"trial-output/root-coordinator.lifecycle.json"),mu_sdk_actual_model_trial_failure_origin_ref=pin(L/"failure-origin.745.original-tool-io.json"),mu_sdk_actual_model_trial_failure_independent_handoff_ref=pin(A/"handoff.json"),mu_sdk_actual_model_trial_business_state_ref=pin(A/"business-state.observed.json"),mu_sdk_actual_model_trial_recovery_design_handoff_ref=pin(D/"handoff.json"),mu_sdk_qualification_task_status="RUNNING",mu_sdk_qualification_run_id=admit["qualification_run_id"],mu_sdk_qualification_admitted=True,mu_sdk_qualification_runs=1,mu_sdk_live_execution_grant_issued=True,mu_sdk_current_live_execution_grant_active=False,mu_sdk_current_go_once_consumed=True,mu_sdk_original_trial_clock_reset_permitted=False,mu_sdk_qualification_run_status="QUEUED",mu_sdk_runtime_dispatch_state="PREPARED",mu_sdk_runtime_dispatch_worker="",mu_sdk_actual_external_provider_requests_current_trial=None,mu_sdk_current_trial_recorded_model_effects=0,mu_sdk_actual_model_trial_run_uuid="82f60d687d9e488facd756950df87972",mu_sdk_runtime_qualification=False,mu_sdk_all_trial_owned_jobs_closed=True,mu_sdk_trial_source_guard_entries_closed=86,mu_sdk_c7_actual_lifecycle_proven=False,mu_sdk_business_reconciliation_state="OPEN_PRE_DISPATCH_ADMITTED_RUN_NO_WORKER_JOURNAL",mu_sdk_source_authors_active=["codex:/root/trusted_go_lossless_source_v5: narrow GO FILETIME lossless Source"],mu_sdk_source_readonly_reviewers_active=[],mu_sdk_next_action="Preserve failed Run/once/clock/counters. Actual owned Go black-box tests+compile and independent review of narrow GO reader Source; no model relaunch before legal production pre-dispatch reconciliation.")
 checkpoint["note"]="Actual first C5 trial failed closed after GO: shell/Python0, admitNative0 executeNative1 canonical precision rejection of FILETIME134359521876434319. Independent37checks20pins prove source failure before claim/RunAdmitted; businessRunQUEUED TaskRUNNING dispatchPREPARED workerempty, not reconciled. TwoJobs/all extra dup handles,80+6guard entries closed. provider countnull remainsunknown; recordedmodeleffects0 only. Old742failures byte-for-byte preserved; append745-749once, total747/highest749. Original once consumed and300s clock neverreset, no auto retry. Preserve initializedproject+ordinaryCLIdraft+qualifiedzero-providerpreparation; v5GOreaderSource narrowly underway.6/22 historical parents0/42 current formal; completefalse. OW168/SS/CM/Main unchanged."
 return checkpoint,ownership
try:
 transaction=tm.update_pair(refs,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in other]==otherbytes and json.loads(cp.read_bytes())["revision"]==349
finally:
 cleanup=guard.close();assert cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"];save("source_guard.cleanup.actual.json",cleanup)
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),other_canonical_refs=[pin(p) for p in other],old742_preserved=True,registered_failures=747,highest_diagnostic_ordinal=749,provider_requests=None,recorded_model_effects=0,formal_acceptance=False))
resume=save("RESUME.r349.original.json",dict(schema="researchos.root-resume-failed-sdk-v5",repository_root=str(R),project_id=c["project_id"],head=c["head"],checkpoint_ref=pin(cp),checkpoint_revision=349,ownership_revision=168,current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=747,highest_diagnostic_ordinal=749,actual_trial_status="FAILED_EXECUTION_CLOSED",failed_trial_ref=pin(L/"trial-output/root-coordinator.lifecycle.json"),failure_review_ref=pin(A/"handoff.json"),recovery_design_ref=pin(D/"handoff.json"),qualification_run_id=admit["qualification_run_id"],qualification_run_status="QUEUED",qualification_task_status="RUNNING",dispatch_state="PREPARED",dispatch_worker="",once_consumed=True,clock_reset_permitted=False,automatic_retry=False,provider_requests_current_trial=None,recorded_model_effects=0,all_jobs_closed=True,guard_entries_closed=86,next_action="Narrow GO reader actual owned Go tests/compile+independentreview; production pre-dispatch reconciliation required before any new model trial.",completion_asserted=False,proof_ref=proof))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_ACTUAL_FAILED_CLOSED_BUSINESS_RECONCILIATION_OPEN",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,registered_failures=747,highest_diagnostic_ordinal=749,qualification=False,provider_requests=None,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=747,highest_diagnostic_ordinal=749,provider_requests=None)),flush=True)

