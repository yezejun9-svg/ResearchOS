import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def fixed(p,h,n):
 v=pin(p);assert v["sha256"]==h and v["bytes"]==n;return v
def save(n,v):
 with (O/n).open("xb") as stream:stream.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/n)
specs=[
("checkpoint_r358_independent_review_codex/1a11ded6095-7d2f0833","c7adf78ef37f59dc784ba4656aab5345e4d92a03df3fee243066fb69076ddb85",1647,"6a598f086a46fd4094872b63017793b4d0874c1fd070328ecb8018f38b4a5f72",61993),
("native_ttl_compile_independent_review_codex/1a11df34822-e8b67939","e62d0dbb7e7090637846c2c0ea18da0419382907b7137d8d3b84648bab6f2f01",2076,"8a806e734ce8ec485ae0f5bdc9088ed5bc3c3e244e6e848bdc3e98c2d2761f6e",1075300),
("native_ttl_prelaunch_independent_review_codex/1a11dfd4106-fa062434","59ab09d797aa3ada8094052b7c8f0f08c90a8fc7d74ff849f32d69afef30bd41",2464,"ca5f597a402886e8363a4708c7028ba5850f9ac2b829bc31457f5de82655149d",1068421),
("session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e","6a423c8ed07697cf640acac59fa4d3e92a749bc10c517e27642030d614881e51",4439,"f90992dc7a9a61798953f85f304aa45fec8effc8b13f86be69958bf622ef561f",14814)]
reviews=[]
for name,h,n,m,mn in specs:
 hd=fixed(B/name/"HDF.json",h,n);mf=fixed(B/name/"MF.json",m,mn)
 assert json.loads(Path(hd["path"]).read_bytes())["formal_acceptance"] is False
 members=json.loads(Path(mf["path"]).read_bytes())["members"]
 for ref in (members.values() if isinstance(members,dict) else members):
  fixed(ref["path"],ref["sha256"].removeprefix("sha256:"),ref["bytes"])
 reviews.append(dict(name=name,handoff_ref=hd,manifest_ref=mf,formal_acceptance=False))
spec=[
(826,"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e/failure-origin.826.json","fecbeca86193f211320c89707310cd9f982237a898519cbaba135ce1d6d12cb3",2011,1,1,"Q4 seal wrongly demanded byte equality between original Q3 Goal Source and actual T6 gofmt output. Three runtime Sources equal; Goal has separately preserved formatting delta. Old seal failed; distinct revision sealed actual contract gap."),
(827,"session_attach_contract_revision_codex/1a11ded594f5378b7512125d/diagnostic-827.json","5ca6f036c4e2c4272f8fe73524bd6706cd82da1233f7e2cef0eb0a47748bec0a",8724,None,None,"Source constructor orchestration JS SyntaxError before any tool or filesystem/native process; complete original input/result retained."),
(828,"integration_codex/root-delegation-diagnostic-828-thread-limit-10f7852f/failure-origin.828.json",None,None,None,None,"Collaboration followup rejected before dispatch because active slots full; exact rendered error copied, original full input object not independently persisted. Author subsequently sent FINAL/STOP before distinct successful dispatch. No process or mutation."),
(829,"session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e/diagnostic-829.json","2d05aeb23cb452adecf84c33868995f6e2229d284954d9ddd4733bdba2a3f856",47552,1,None,"Reviewer read absent report.md before actual CONTRACT-MAPPING.md enumeration; original FileNotFoundError b4b80d exactIO retained, no Python marker/native."),
(830,"integration_codex/root-config-diagnostic-830-runtime-module-37adf39e/failure-origin.830.json",None,None,1,1,"Pure T7 controller config context rejected loaded runtime DLL absent from frozen inventory; missing path NULL, no child native started. Old full guard closed; bootstrap cleanup not observed, OS exit release is inference. New distinct config preloads held controller/observed Source before freezing and closes guards."),
(831,"session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e/diagnostic-831.json","6987598388273752476d4161eb78b0d2bb03379104ce0589a2a59072ebb64385",2538,1,None,"Reviewer seal Source had Python SyntaxError extra parenthesis. Original script and c77bda IO retained. No marker so actual Python exit NULL; inferred exit1 separated. Distinct seal_revision completed REQUEST_CHANGES.")]
diagnostics=[]
for ordinal,name,h,n,outer,py,desc in spec:
 ref=fixed(B/name,h,n) if h else pin(B/name)
 diagnostics.append(dict(ordinal=ordinal,origin_ref=ref,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,description=desc))
actual_names=[
"integration_codex/native-ttl-compile-root-458f017f3c294bb6/validation.closed.json",
"integration_codex/native-ttl-compile-root-458f017f3c294bb6/original-tool-io.json",
"integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4/public-config.prepared.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-config.prepared.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/original-tool-io.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller.public.config.json",
"integration_codex/native-positive-ttl-serve-root-052db2c7da5645f6/serve_one_positive_ttl.actual_owned.py",
"integration_codex/native-positive-ttl-root-api-a4a432c97c744d98/root_public_api_ttl.actual.py",
"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e/HDF.json",
"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e/MF.json",
"session_attach_contract_revision_codex/1a11ded594f5378b7512125d/HDF.json",
"session_attach_contract_revision_codex/1a11ded594f5378b7512125d/MF.json"]
actual=[pin(B/n) for n in actual_names]
wip={
"mu_sdk_r359_compile":dict(status="T7_TTL43_COMPILE_COMPONENT_ACCEPTED_NATIVE_ACTUAL_PENDING",review=reviews[1],sources=43,unchanged_sources=42,modified_files=1,TTL_expressions=2,packages=364,compiler_inputs=3793,products=599,embeds=38,tools=8,compiler_guard_set_count=3920,GoRef_explicitly_held=True,GoVERSION_held=True,GoSrcModule_held_by_input=True,compile_Jobs_closed=7,Git_Jobs_closed=5,compile_guard_groups_closed=5,isolation_guard_groups_closed=2,old_units_not_rerun=True,new_unit_passes=0,Main_adopted=False),
"mu_sdk_r359_native_prelaunch":dict(status="T7_TTL_PUBLIC_CONFIG_AND_PRELAUNCH_SOURCE_ACCEPTED_SINGLE_POSITIVE_CAN_PROCEED",review=reviews[2],config_ref=actual[5],server_source_ref=actual[6],API_source_ref=actual[7],fresh_case_id="26c5c890ef5144d4",case="positive-replay",frozen_inputs=4084,initial_credential_max_TTL_minutes=15,concrete_grant_minutes=4,TTL_refresh=False,native_cases_started=0,native_pass=False,signatures_created=0,no_automatic_approval=True,manual_sign_each_exact_payload=True,SQL_inspection_before_specific_release=True),
"mu_sdk_r359_attach_source":dict(status="SOURCE_REJECTED_UNRESOLVED_RESTORE_FENCE_BYPASS",review=reviews[3],finding="ATTACH-RESTORE-001",finding_static_only=True,native_reproduction=False,current_candidate_adopted=False,next_Source_author="/root/command_queue_impl",new_revision_assigned=True,active_asynchronous_takeover="OPEN_BRANCH",historical_cached_ACK_terminal="OPEN_BRANCH",original_runtime8_failures_preserved=True),
"mu_sdk_r359_history_fixture":dict(status="SOURCE_AUTHOR_TRUE_LEGACY_DDL_AND_CONTIGUOUS_MIGRATION_FIXTURES_IN_PROGRESS_NOT_ACCEPTED",Git_commit="3225a31fd25969c6a5e071a2fc686cb4a835e162",historical_DDL_blob="9efc768f8f4cfb6ac31e1f88a78ad095877328af",historical20_release_program_needed=True,ordinary_positive_upgrade="BLOCKED_NO_MATCHING_HISTORICAL20_PROGRAM_BACKUP_UPGRADE",primitive_restore_and_retrieval_unit_Source_pending=True,product_upgrade_acceptance=False),
"mu_sdk_r359_preserved":dict(original_positive_native_attempt_failed_closed=True,original_positive_TTL_fail_820_preserved=True,original_trial_business_open=True,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_DB_touched=False,original_trial_provider_requests=None,global_provider_requests=None,original_trial_financial_closed=False,historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,overall_completion=False,counter_reset=False)}
value=dict(schema="researchos.root-cp359-evidence-facts.v1",formal_acceptance=False,reviews=reviews,diagnostics=diagnostics,actual_refs=actual,work_in_progress=wip,checkpoint_note="CP359 preserves old823 failures and records six distinct original diagnostics826..831 once (829 registered/highest831). T7 actual43Sources onlytwoTTL expressions changed: fourCLIprograms+taggedtest compiled, sevencompile/fiveGitJobs and five+two guards closed; independently accepted compiler component, unchanged25units notrerun. New publiccase/config and SERVER/API onlythreeconfig constants differ, 4084Frozeninputs independently accepted for one freshpositive, native actual0/sign0. Production attach Source rejected ATTACH-RESTORE-001 sameowner renewal bypasses restore fence, immutable newrevision assigned; oldruntime8 FAIL preserved. Historical trueDDL/contiguouslegacyfixture Source resource branch in progress, ordinaryupgrade stillblocked. Main/Owner/originalbusiness/formal notaccepted; originalonceexpired/providerNULL, noreset and full22/42threshold preserved.",next_action="After saving and independently reviewing CP359, Root start exactly one new TTL-corrected isolated positive native case using prelaunch-approved config/server/API. Review and sign each concrete public payload manually; no refresh, no new paid modeltrial, wholetypedSQL before specificfixture release. In parallel finish independent-reviewed restore-fence attach Source and genuine legacy fixtures, then fresh isolated target tests. Continue contracts/execution.plan.json and task_packet read-only DAG; noformalaccept until actual independent42cases/22parents.")
print(json.dumps(dict(facts_ref=save("checkpoint.execution.facts.json",value),reviews=len(reviews),diagnostics=[x["ordinal"] for x in diagnostics])),flush=True)
