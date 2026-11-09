import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def fixed(p,h,n):
 v=pin(p);assert v["sha256"]==h and v["bytes"]==n;return v
def save(name,v):
 with (O/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
specs=[
("checkpoint_r360_independent_review_codex/attach_restore_reviewer_01","9f0e0b22982448c127c9c9d27ebad19d207e9e68d9d41e65a80b8e7486d6432a",3886,"130bb82ccff3476de143de6dc565dfd059877079b92a8a772e433addbce98927",78285),
("session_attach_restore_time_independent_review_codex/7b81fec959684c2a9de9b0e475479c27","16773c9c272354533218607aeadbfeaa0013118bcd0e9ff8f588b5b3facba9f3",4467,"bccefe5d25a951d96f58f492312a740d71cb51acb7487852b38662deae87098c",27537),
("legacy_migration_fixture_revision_independent_review_codex/attach_restore_reviewer_02","86852319669c0b34a31fff88c3c3c3ed5c7517d11b4b91d042cafa82fb2e0b05",8904,"a6f6c272854093ff87f4defc67fb4b8cf1ae2dd7b9a8126e97044c6205213aca",70838),
("native_temp_independent_review_codex/20261009-01a11e22","7ed8bc9380c2ef4a7acbd74c402213a43b072be6d2e810fad1d03cf865be6c0f",3310,"5cf3fa351a1ce624d22e85440ced5d3b319a44caf44ba91a734dac86cbd36c98",46077)]
reviews=[]
for name,h,n,m,mn in specs:
 hd=fixed(B/name/"HDF.json",h,n);mf=fixed(B/name/"MF.json",m,mn)
 members=json.loads(Path(mf["path"]).read_bytes())["members"]
 for ref in (members.values() if isinstance(members,dict) else members):fixed(ref["path"],ref["sha256"].removeprefix("sha256:"),ref["bytes"])
 reviews.append(dict(name=name,handoff_ref=hd,manifest_ref=mf,formal_acceptance=False))
cp=fixed(R/"execution/v2.4/checkpoint.json","685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56",4126105)
c=json.loads(Path(cp["path"]).read_bytes());assert c["revision"]==360 and len(c["failure_counters"])==836
qualified=[]
for ordinal in (833,835):
 matches=[v for v in c["failure_counters"] if v.get("original_payload",{}).get("observed_ordinal")==ordinal];assert len(matches)==1
 qualified.append(dict(ordinal=ordinal,original_canonical_record=matches[0],original_canonical_record_sha256=hashlib.sha256(json.dumps(matches[0],ensure_ascii=True,sort_keys=True,separators=(",",":")).encode()).hexdigest()))
counterproof=fixed(B/"checkpoint_r360_independent_review_codex/attach_restore_reviewer_01/exit-833-counterproof.json","068dc27028471f63e90a019c8558c197c5d05d960223481dace4d323c6d1ffc6",2027)
rehearsal=B/"integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4/facts/00-rehearsal/invocation.json"
harness=B/"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/test.invocation.json"
origin=B/"integration_codex/native-positive-ttl-failed-root-release-1791505647184/failure-origin.835.json"
r=json.loads(rehearsal.read_bytes());h=json.loads(harness.read_bytes());o=json.loads(origin.read_bytes())
assert r["Result"]["creation_time_100ns"]==134359787476336016 and h["result"]["creation_time_100ns"]==134359787460741284
assert o["native_rehearsal_creation_time_100ns"]!=r["Result"]["creation_time_100ns"] and o["native_harness_creation_time_100ns"]!=h["result"]["creation_time_100ns"]
qualification=save("evidence-accuracy.qualification.json",dict(schema="researchos.root-evidence-accuracy-qualification.v1",old_checkpoint_ref=cp,qualified_original_records=qualified,
old833_counterproof_ref=counterproof,ordinal833=dict(actual_outer_exit=1,actual_python_exit=None,source_reported_python_exit=1,inferred_python_exit=1,no_marker_or_independent_python_exit_observed=True),
ordinal835=dict(original_origin_ref=pin(origin),rehearsal_native_ref=pin(rehearsal),harness_native_ref=pin(harness),source_reported_rehearsal_FILETIME_decimal=str(o["native_rehearsal_creation_time_100ns"]),actual_rehearsal_FILETIME_decimal=str(r["Result"]["creation_time_100ns"]),source_reported_harness_FILETIME_decimal=str(o["native_harness_creation_time_100ns"]),actual_harness_FILETIME_decimal=str(h["result"]["creation_time_100ns"]),reason="JavaScript Number JSON.stringify cannot preserve exact uint64; all corrected identity fields are decimal strings",actual_native_exits_preserved=[1,1],original_origin_unchanged=True),
count_reset=False,original_origin_keys_unchanged=True,original_immutable_sources_unchanged=True,formal_acceptance=False))
spec=[
(839,"integration_codex/root-delegation-diagnostic-839-thread-limit/failure-origin.839.json",None,None,None,"Root reviewer dispatch hit slot limit before author FINAL; no process/Source/canonical changes; exact input/error retained. Later confirmed free slot list before new dispatch."),
(840,"checkpoint_r360_independent_review_codex/attach_restore_reviewer_01/diagnostic-840.json",1,1,None,"Reviewer incorrectly parsed commands revision39 as leading SHA digits; immutable first strict-pin audit rejected before Sourceguard/canonical writes. New corrected audit completed REQUEST_CHANGES due actual833 exit provenance."),
(841,"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491/failure-origin.841.json",1,None,None,"Temp-env author construct Python SyntaxError before marker; actual outer1/PythonNULL, inferred1 separate. Original input/source kept, distinct construct_revision0."),
(842,"session_attach_restore_time_independent_review_codex/7b81fec959684c2a9de9b0e475479c27/failure-origin.842.json",1,None,None,"ATT3 reviewer assumed replacement list .items mapping, AttributeError with no Python marker; actualouter1/PythonNULL/inferred1 separately. Distinct correct shape entry completed independent Source approval."),
(843,"integration_codex/root-metadata-diagnostic-843-filetime-precision/failure-origin.843.json",None,None,None,"Root JS Number serialization precision failure in835 FILETIMEs; native exact raw invocation remains unchanged. Detection query0 is separately recorded and is not a failed process exit. Qualification preserves original wrong source-reported fields and exact native decimal identities."),
(844,"legacy_migration_fixture_revision_independent_review_codex/attach_restore_reviewer_02/diagnostic-844.json",None,None,None,"Reviewer JS template Go backtick parser SyntaxError before nested tool/process/write. Full original functions input/renderederror retained; chr96 new entry completed Source approval."),
(845,"typed_runtime_goal_fixture_attach_binding_revision_codex/q5-1a11e02f790732395c39325fbb4668d/failure-origin.845.json",1,None,None,"Q5 Source PS nested array concatenation produced nonexistent path/hash/bytes as single Get-FileHash operand; outer1 noPython/native/Source unlocked. Immutable original IO and distinct PSCustomObject correction0 retained."),
(846,"native_temp_independent_review_codex/20261009-01a11e22/failure-origin.846.json",1,1,None,"Temp-env reviewer used lower result instead rehearsal upper Result, KeyError; actualouter1/markerPy1, all three guards closed, originalfailed entry kept. New revision0 and seal0; Source only with Root execution prerequisites.")]
diagnostics=[dict(ordinal=a,origin_ref=pin(B/p),actual_outer_exit=e,actual_python_exit=y,actual_native_exit=n,description=d) for a,p,e,y,n,d in spec]
actual_names=[
"session_attach_restore_time_revision_codex/att3-1a11e02f790732395c39325fbb4668d/HDF.json",
"session_attach_restore_time_revision_codex/att3-1a11e02f790732395c39325fbb4668d/MF.json",
"legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d/HDF.json",
"legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d/MF.json",
"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491/HDF.json",
"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491/MF.json",
"integration_codex/native-temp-isolation-root-1791506570123/isolation.ready.json",
"integration_codex/native-temp-isolation-root-1791506570123/canonical.pre-run.exact.json",
"integration_codex/native-temp-isolation-root-1791506570123/source-guard.cleanup.actual.json",
"integration_codex/native-temp-isolation-root-1791506570123/runtime-source-guard.cleanup.actual.json"]
actual=[pin(B/n) for n in actual_names]+[qualification,counterproof,pin(harness),pin(rehearsal)]
wip={
"mu_sdk_r361_evidence_accuracy":dict(status="CP360_REJECTED_EXIT833_QUALIFIED_ACTUAL_PYTHON_NULL_ORIGIN835_UINT64_IDENTITIES_QUALIFIED_FROM_EXACT_NATIVE_RECEIPTS",review=reviews[0],qualification_ref=qualification,original_source833_reported1_preserved=True,effective833_python_exit=None,effective835_rehearsal_FILETIME_decimal=str(r["Result"]["creation_time_100ns"]),effective835_harness_FILETIME_decimal=str(h["result"]["creation_time_100ns"]),old_all836_counts_and_origin_keys_preserved=True,only_two_old_counter_records_qualified=True,counter_reset=False,CP360_receipts_immutable=True),
"mu_sdk_r361_attach_source":dict(status="ATT3_SOURCE_ONLY_APPROVED_FRESH_NATIVE_RESTORE_POSITIVE_AND_SHARED_TEXT_DEPENDENCIES_BLOCKED",review=reviews[1],old_001_002_counterexamples_statically_closed=True,helper_UTC_actual_time_comparison=True,current_candidate_adopted=False,Root_native_actual_approved=False,fresh_positive="BLOCKED_PENDING_ROOT_RESOURCE",shared_TEXT_dependencies_remain=True,active_async_takeover="OPEN",cached_ACK_reconciliation="OPEN",Q5_fixture_binding_Source_in_progress=True,original_T6_runtime8_FAIL_preserved=True),
"mu_sdk_r361_legacy_source":dict(status="LEGACY_V2_SOURCE_APPROVED_MINIMAL_DB_ONLY_ROLLBACK_REACHABLE_STATIC_ROOT_ACTUAL_PENDING",review=reviews[2],tests_preserved=12,assertion_calls_preserved=126,unrelated_bodies_preserved=9,true20_SQL_Git_provenance=True,Root_unit_actual_done=False,current_candidate_adopted=False,ordinary_upgrade="BLOCKED_NO_HISTORICAL20_MATCHING_RELEASE_BACKUP_RESTORE_AUTHORIZED_UPGRADE"),
"mu_sdk_r361_native_temp_source":dict(status="BROKER_TEMP_SOURCE_APPROVED_28_ENV_LEAVES_PENDING_NEW_CTL3_AND_FRESH_ROOT_COMPOSITION",review=reviews[3],current_candidate_adopted=False,Go_actual_done=False,unit_parents=2,unit_leaves=28,original_assertions_preserved=84,initial_credential_minutes=15,grant_minutes=4,controller_proof_key_pending=True,controller_Source_author="/root/backup_regression_resources",Root_T8_detached_resource_ready_ref=actual[6],T8_5_Git_jobs_closed=True,T8_2_read_guard_groups_closed=True,T8_source_overlay=False,Root_case_started=False,native_positive_accepted=False,native9_accepted=False),
"mu_sdk_r361_preserved":dict(original_T7_failure835_and_native_exits1_preserved=True,old_positive_TTL_fail820_preserved=True,original_trial_business_open=True,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_DB_touched=False,original_trial_provider_requests=None,global_provider_requests=None,original_trial_financial_closed=False,historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,overall_completion=False,counter_reset=False)}
facts=dict(schema="researchos.root-cp361-evidence-facts.v1",formal_acceptance=False,reviews=reviews,diagnostics=diagnostics,actual_refs=actual,qualification_ref=qualification,work_in_progress=wip,checkpoint_note="CP361 preserves all836 old count/origin identities, qualifies only833 Python exit NULL versus source-reported1 and835 exact native FILETIME decimal identities (original immutable origins unchanged), adds eight distinct originals839..846 once: registered844/highest846/noreset. Independent Source ATT3 chronological restore-attach guard and Legacy2 schema-only rollback fixes accepted within Source scope; freshnative restore positive/sharedTEXT/ordinaryhistorical20 release gates stillBLOCKED. Broker isolatedTEMP Source plus28envleaves approved contingent newCTL3 proof-key/frozenenv/resource and freshRootactual. Root T8 detachedworktree fiveGitJobs/two guards closed without Source overlay. Original onceexpired/business/financialOPEN/providerNULL preserved; Main/Owner/nativepositive/nine/formal notaccepted. All22/42 thresholds stay unchanged.",next_action="Independently review correctedCP361, exact833/835 qualification and task_packet. Finish CTL3 proof-key Source independent review then fresh taggedRoot composition/28 envleaves, fresh fixed/frozen public config and manualonepositive native case withoutTTLrefresh/autoapproval/newmodeltrial. Complete Q5 actualAttachResult revision/epoch binding Source independently and run freshRootruntime composition with ATT3; Root execute Legacy2 primitive/retrieval units while ordinaryhistory20 release/resource branch remainsblocked. Continue all22 parents and42 current formal gates.")
print(json.dumps(dict(facts_ref=save("checkpoint.execution.facts.json",facts),qualification_ref=qualification,reviews=4,diagnostics=[x["ordinal"] for x in diagnostics])),flush=True)
