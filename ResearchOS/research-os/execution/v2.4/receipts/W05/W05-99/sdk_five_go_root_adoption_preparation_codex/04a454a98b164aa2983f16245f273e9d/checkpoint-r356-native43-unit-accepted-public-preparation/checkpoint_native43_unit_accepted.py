import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(r):
 a=pin(r["path"]);assert a["sha256"]==r["sha256"] and a["bytes"]==r["bytes"];return a
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
def module(p,b):
 m=types.ModuleType("root_cp356_"+p.stem);m.__file__=str(p);exec(compile(b,str(p),"exec"),m.__dict__);return m
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json";old=[p.read_bytes() for p in (cp,ow)];pair=[pin(cp),pin(ow)]
assert pair[0]["sha256"]=="9383bb6cfd090e4d6d2e51d8f7d97d6819e86f7cfa0b27c034dc772eae88fde9"
assert pair[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==355 and len(before["failure_counters"])==802
assert before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb" and before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb"
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_before=[p.read_bytes() for p in others]
C=B/"checkpoint_r355_independent_review_codex/aafa77b516544cbea04fab32c51b5703"
I=B/"native43_compile_unit_independent_review_codex/7c2e92659f544a66bf33d1fb09c0eb10"
F=B/"native_orchestration_read_failure_codex/805-2f8d31a9ad003"
A=B/"integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5"
ISO=B/"integration_codex/native-harness43-isolation-root-1b43ec8438c3470e"
P=B/"integration_codex/native-migration-positive-root-73df768bc70b4f64"
L=B/"legacy_first_turn_contract_review_codex/17301aa504cea371af1ac4c671c00a24"
expected={C:("ea29a029dc8934f765e00cb86fd2864b3df11ef794c0162ef3049937234527c8","6ec08b1701782ee81f2d685775893dabd99e39c50ea64c89be4441c9d89b17b6"),I:("4e44ca2e39571f8642632a01e2953ab707ec28aa125555e5790cc0c08ac53a86","eb277565276ec4fad286fe98ad9fdc8afa93eb3462a346dbe3b687e3f930569b"),F:("a4cd2291e5d94995f89db7f9965e4da7f0dc2097ba5aa6739f7d80df0fbcf6a5","6463ab6801dc0658661ea0609606d63ed4490745029d09ae0e0b4c7251272669")}
refs=[]
for d,(h,m) in expected.items():
 assert pin(d/"HDF.json")["sha256"]==h and pin(d/"MF.json")["sha256"]==m
 members=json.loads((d/"MF.json").read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 refs += [pin(d/"HDF.json"),pin(d/"MF.json")]+[verify(r) for r in members]
assert json.loads((I/"HDF.json").read_bytes())["decision"]=="NATIVE43_COMPILE_AND_EXACT_ERROR24_UNIT_ACTUAL_ACCEPTED_COMPONENT_ONLY_STOP"
assert pin(A/"validation.closed.json")["sha256"]=="83f63ea38fc0af3b97cb5fb33000c9c98abe4cb048ee516c364f02dc142540d8"
actual=json.loads((A/"validation.closed.json").read_bytes());assert actual["unit_pass_count"]==25 and actual["unit_fail_count"]==actual["unit_skip_count"]==0 and actual["native_migration_cases_executed"]==0 and actual["all_owned_jobs_closed"]
assert pin(P/"public-config.prepared.json")["sha256"]=="91b777422c1f30524fbf1708f9035768705b8af08f9cfa2f68c0a35e0b2e0ef6"
assert pin(P/"native-harness.public.config.json")["sha256"]=="ef404512f197dda8223526af9f301fa922b54a84416e43094f79202e70f9fd32"
assert pin(L/"report.md")["sha256"]=="8ef791fcd0ed3ea4274a2bdc4767f59e7b5a18673e1a06c414ab11e18810da40"
pending=[(805,F/"failure-origin.805.json",1,None,None,"Source guessed recovery_enroll/main_windows.go, distinct from800; readonly Get-Content OS missing path."),
 (806,C/"failure-origin.806.json",1,None,None,"Reviewer assumed all old counters contain origin_key; heterogeneous old KeyError; actualPythonNULL inferred1."),
 (807,I/"failure-origin.807.json",1,None,None,"Reviewer assumed formatted Source list was dict; AttributeError items(); actualPythonNULL inferred1."),
 (808,L/"failure-origin.808.json",0,None,None,"Readonly rg literal Windows wildcard path os123 in first command; second independent command successful; outer0 but firstinner rg exitNULL, no inference to success.")]
refs += [pin(p) for _,p,_,_,_,_ in pending]
for d,names in ((A,("validation.closed.json","original-tool-io.json","formatted.source-members.json","actual-tagged-compiler-input-inventory.json","source-overlay.json","binary-source-guard.cleanup.actual.json","compiler-source-guard.cleanup.actual.json","candidate-source-guard.cleanup.actual.json","input-source-guard.cleanup.actual.json")),
 (ISO,("isolation.ready.json","original-tool-io.json")),
 (P,("public-config.prepared.json","native-harness.public.config.json","public-config.original-tool-io.json","input-source-guard.cleanup.actual.json")),
 (L,("report.md","seal.json","refs.json","tool-io.json"))):
 refs += [pin(d/n) for n in names]
refs += [verify(r) for r in actual["binary_refs"].values()]
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
refs += [pin(gp),pin(tp),pin(Path(__file__).resolve()),pin(sys.executable)];refs=list({r["path"]:r for r in refs}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs);tm=module(tp,guard.get_buffer(str(tp)))
def transform(c,o):
 assert c["revision"]==355 and o["revision"]==168
 keys={v.get("origin_key") for v in c["failure_counters"]}
 for n,p,outer,py,native,detail in pending:
  r=pin(p);key=hashlib.sha256((r["sha256"]+"#"+str(n)).encode()).hexdigest();assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=r,original_payload=dict(observed_ordinal=n,immutable_origin_ref=r,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=native,new_component_provider_requests=0,diagnostic=detail),counted_once=True,counter_reset=False,automatic_retry=False))
 assert c["failure_counters"][:802]==before["failure_counters"] and len(c["failure_counters"])==806
 c.update(expected_previous_revision=355,revision=356,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(r356_registered_failure_count=806,r356_highest_observed_diagnostic_ordinal=808,mu_sdk_cp355_independent_review_ref=pin(C/"HDF.json"),
  mu_sdk_native43_compile_unit_state="INDEPENDENT_ACCEPTED_24LEAVES1PARENT25PASS0FAIL0SKIP_FOUR_BINARIES_AND_TAGGED_TEST_COMPILED_NO_NATIVE_CASE",
  mu_sdk_native43_compile_unit_actual_ref=pin(A/"validation.closed.json"),mu_sdk_native43_compile_unit_independent_ref=pin(I/"HDF.json"),
  mu_sdk_native43_source_root=actual["current_source_root"],mu_sdk_native43_source_files=43,mu_sdk_native43_compiler_input_ref=actual["compiler_input_inventory_ref"],
  mu_sdk_native43_binary_refs=actual["binary_refs"],mu_sdk_native_migration_fixture_state="EXACT_REJECTION_SOURCE_AND_24UNIT_ACTUAL_INDEPENDENTLY_ACCEPTED_NINE_NATIVE_CASES_PENDING",
  mu_sdk_native_positive_public_preparation_ref=pin(P/"public-config.prepared.json"),mu_sdk_native_positive_public_configuration_ref=pin(P/"native-harness.public.config.json"),
  mu_sdk_native_positive_hostile_flow_state="NOT_STARTED_PUBLIC_POSITIVE_CONFIG_AND_FOUR_CASE_BINARIES_PREPARED_NO_SIGNED_RELEASE_GRANT_REAL_OWNER_OR_TOKEN",
  mu_sdk_legacy_first_turn_contract_report_ref=pin(L/"report.md"),mu_sdk_legacy_first_turn_fixture_disposition="FORMAL_HOST_CONFIGURE_TYPED_REF_FIXTURE_TO_REPAIR_NO_PRODUCTION_GATE_WEAKENING_OR_ERROR_ORDER_CHANGE_FRESH_LEGACY_COMPATIBILITY_OPEN",
  mu_sdk_source_authors_active=["command_queue_impl:Root_only_controller_Source","backup_regression_resources:typed_runtime_and_goal_test_fixtures"],
  mu_sdk_source_readonly_reviewers_active=["prepared_native_authority_review:Root_controller_Source_then_native_actual"],
  mu_sdk_next_action="Review sealed Root controller Source; owned isolated onecase native preparation, exact Root-only issuer release/grant signatures, real Owner/native private pipe and Control token, planned one replay and eight negatives; independent exact case evidence before fixture release. Typed host.configure and Goal valid-model fixtures Source only in independent branch. FULL25fail/4skip preserved; originalDB/history16/adoption+abandonment and live SDK trial remain separate; do not reset original once/300s/deadline/failure counts.")
 c["note"]="CP356 preserves CP355 old802prefix and adds805-808once=>806registered/high808. CP355trueindieaccepted. FreshT5 43Source original41byteequal+accepted nativeexact2Source, actual tagged compiler364packages3793selectedInputsincluding TestGoFiles/XTestGoFiles38embeds599protectedproduct8toolrefs; 8executing+5isolationJobs0/idle0closed, guards97/44/3918/5+isolation10closed. Trueindie accepts pure24matchingunit leaves+1parent25pass, fourcurrentbinsandnew42258944testbinary compile; noNative9/issuerSignature/Owner/nativeToken. Positive publicconfig and unique casecopies prepared without privatekeysidecar or originalDB writes. Formalfirstpath host.configure typedref; freshlegacy session-created onlymodelref cannot recover originaltrusted profile; productioncompatibilityopen, fixtures torepair without gateweakening/leaseorderingchanges. FULL1261pass25fail4skip preserved FAILED, oldsource267/199trueindieaccepted immutable. OriginalRunQUEUED/TaskRUNNING/PREPAREDdispatch/providerNULL/recordedEffects0/financialunknownclosedfalse untouched; once consumed/300s expired no reset/newtrial. OW168/SS/CM/Head/project/13dirty/indexempty maintained; GoalACTIVE6of22historical/0of42currentformal/nevercompleted."
 return c,o
try:
 tx=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_before and json.loads(cp.read_bytes())["revision"]==356
finally:
 clean=guard.close();save("source_guard.cleanup.actual.json",clean);assert clean["closed"] and not clean["errors"] and clean["retained_handles_count"]==0
proof=save("canonical_pair.actual.json",dict(transaction=tx,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old802prefix_preserved=True,registered_failures=806,highest_observed_diagnostic_ordinal=808,production_db_writes=0,new_component_provider_requests=0,original_trial_provider_requests=None,formal_acceptance=False))
resume=save("RESUME.r356.original.json",dict(schema="researchos.root-resume-native43-unit-accepted.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=356,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=806,highest_observed_diagnostic_ordinal=808,native43_actual_ref=pin(A/"validation.closed.json"),native43_independent_ref=pin(I/"HDF.json"),native9_executed=False,positive_public_configuration_ref=pin(P/"native-harness.public.config.json"),original_trial_business_open=True,original_trial_provider_requests=None,financial_closed=False,once_consumed=True,original_clock_expired=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action="Independent Rootcontroller Source -> actual isolated native single positive then eight negatives; typed fixture branch; original business/adoption/abandonment/history/live trial separate."))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_NATIVE43_UNIT_ACCEPTED_POSITIVE_PUBLIC_PREPARATION_NATIVE_NOT_STARTED",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=806,highest_observed_diagnostic_ordinal=808)),flush=True)
