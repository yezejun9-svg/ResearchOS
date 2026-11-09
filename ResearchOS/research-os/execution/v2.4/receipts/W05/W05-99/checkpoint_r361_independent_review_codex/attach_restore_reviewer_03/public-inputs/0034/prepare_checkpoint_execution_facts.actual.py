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
specs=json.loads((O/"review_specs.json").read_bytes());reviews=[]
for spec in specs:
 hd=fixed(B/spec["name"]/"HDF.json",spec["h"],spec["n"]);mf=fixed(B/spec["name"]/"MF.json",spec["m"],spec["mn"])
 assert json.loads(Path(hd["path"]).read_bytes()).get("formal_acceptance",False) is False
 members=json.loads(Path(mf["path"]).read_bytes())["members"]
 for ref in (members.values() if isinstance(members,dict) else members):
  fixed(ref["path"],ref["sha256"].removeprefix("sha256:"),ref["bytes"])
 reviews.append(dict(name=spec["name"],handoff_ref=hd,manifest_ref=mf,formal_acceptance=False))
assert len(reviews)==4
restore="session_attach_restore_revision_codex/1a11e02f790732395c39325fbb4668d"
legacy="legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9"
legacy2="legacy_migration_fixture_source_revision_codex/fc052947b4d14f769bff1e735151c52d"
release="integration_codex/native-positive-ttl-failed-root-release-1791505647184"
attach_review="session_attach_restore_independent_review_codex/attach_restore_independent_review"
spec=[
(832,restore+"/diagnostics-832-834.json",1,None,None,"Source required absent T6 client_journal.go read failed; exact original IO preserved in joint832/834 artifact. No Source/native mutation."),
(833,legacy+"/failure-origin.833.json",1,1,None,"Legacy source seal excerpt-bounds assertion failed before outputs; original script and marked exit1 retained; distinct seal_revision0 does not reset."),
(834,restore+"/diagnostics-832-834.json",0,None,None,"Source Get-Content guessed manifest.json instead actual MF.json, nonterminating error with outer0; exact IO retained, actual Python/native NULL."),
(835,release+"/failure-origin.835.json",1,1,1,"T7 actual backup rehearsal1 before authority payload due broker discarding TEMP/TMP and C:/Windows MkdirTemp denied. Root wholeSQLread/stateFalse, specific manual release; three Jobs including rehearsal, all guards closed. Original modeltrial unaffected."),
(836,release+"/failure-origin.836.json",0,None,None,"Root read rg literal Windows backup*.go filename os123 nonterminating followed by successful enumeration outer0; corrected -g query. Original nested input not separately persisted, exact returned result retained."),
(837,release+"/failure-origin.837.json",None,None,None,"Root inline accumulatedIO command exceeded Windows CreateProcess limit os206; no process launched, all exitsNULL. Full command+renderederror retained; apply_patch new-file correction succeeded."),
(838,attach_review+"/diagnostic-838.json",None,None,None,"Reviewer inline accumulatedIO command exceeded Windows CreateProcess limit os206; all exitsNULL, original full input+renderederror retained. Distinct file+short entry sealed REQUEST_CHANGES.")]
diagnostics=[dict(ordinal=o,origin_ref=pin(B/p),actual_outer_exit=e,actual_python_exit=y,actual_native_exit=n,description=d) for o,p,e,y,n,d in spec]
actual_names=[
"integration_codex/native-positive-ttl-serve-root-052db2c7da5645f6/serve-outer.closed.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/controller.closed.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/test.invocation.json",
"integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime/test.stdout.raw",
"integration_codex/native-positive-ttl-root-api-a4a432c97c744d98/inspection-positive.json",
release+"/root-concrete-release.approval.json",release+"/original-tool-io.json",
restore+"/HDF.json",restore+"/MF.json",legacy+"/HANDOFF.json",legacy+"/MANIFEST.json",legacy2+"/HDF.json",legacy2+"/MF.json",legacy2+"/postseal-tool-io.json",
attach_review+"/bootstrap-tool-io.json",attach_review+"/seal-tool-receipt.json"]
actual=[pin(B/p) for p in actual_names]
wip={
"mu_sdk_r360_native_T7_actual":dict(status="NATIVE_T7_POSITIVE_FAILED_TEMP_ENV_REHEARSAL_ALL_JOBS_AND_GUARDS_CLOSED_COMPONENT_REVIEW_ACCEPTED",review=reviews[3],source_inputs=43,case="positive-replay",case_id="26c5c890ef5144d4",native_rehearsal_actual_exit=1,native_harness_actual_exit=1,root_marked_python_exit=1,outer_shell_exit=1,OwnedJobs_closed=3,signatures_created=0,payload_phase_reached=False,whole_SQL_read_complete=True,typed_tables=87,schema_objects=296,schema_versions=list(range(1,24)),expected_state_matches=False,expected_target_baseline_available=False,data_versions=[2,2],database_bytes_unchanged_during_read=True,SQL_reader_guard_entries_closed=156,existing_DB_guard_entries_closed=1,existing_DB_and_fixture_deleted_by_test_cleanup=True,database_native_ID_is_historical_only=True,DB_immutable_claim=False,Root_specific_release=True,Main_adopted=False,native_positive_accepted=False,native9_accepted=False,Owner_authority_accepted=False,original_business_accepted=False,global_provider_requests=None,source_repair="nativeHarnessBroker propagate frozen isolated TEMP/TMP to backup child"),
"mu_sdk_r360_attach_source":dict(status="SOURCE_REJECTED_LATEST_NATIVE_OBSERVATION_TIMESTAMP_ORDER",review=reviews[1],finding="ATTACH-RESTORE-002",finding_static_only=True,native_reproduction=False,new_Source_revision_assigned=True,next_Source_author="/root/command_queue_impl",current_candidate_adopted=False,true_fresh_restore_positive="BLOCKED_PENDING_ROOT_NATIVE_RESOURCE",active_asynchronous_takeover="OPEN",historical_cached_ACK_terminal="OPEN",original_runtime8_failures_preserved=True),
"mu_sdk_r360_legacy_source":dict(status="SOURCE_V1_REJECTED_ROLLBACK_NO_PROJECT_V2_DB_ONLY_SEALED_PENDING_INDEPENDENT_REVIEW",review=reviews[2],finding="LEGACY-ROLLBACK-001",finding_static_only=True,native_reproduction=False,original12_testnames_preserved=True,original126_assertions_preserved=True,original9_unrelated_bodies_preserved=True,Git_history20_commit="3225a31fd25969c6a5e071a2fc686cb4a835e162",historical_DDL_blob="9efc768f8f4cfb6ac31e1f88a78ad095877328af",v2_handoff_ref=pin(B/legacy2/"HDF.json"),v2_manifest_ref=pin(B/legacy2/"MF.json"),v2_copy_manifest_exclusion_disclosed=True,v2_review_accepted=False,current_candidate_adopted=False,next_Source_review="/root/typed_fixture_source_review",ordinary_upgrade="BLOCKED_NO_MATCHING_HISTORY20_PROGRAM_BACKUP_RESTORE_AUTHORIZED_UPGRADE"),
"mu_sdk_r360_preserved":dict(CP359_consistency_review=reviews[0],old829_failure_prefix_preserved=True,original_positive_TTL_fail_820_preserved=True,original_trial_business_open=True,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_DB_touched=False,original_trial_provider_requests=None,global_provider_requests=None,original_trial_financial_closed=False,historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,overall_completion=False,counter_reset=False,old_Q3_T6_runtime8_actual_FAIL_immutable=True)}
value=dict(schema="researchos.root-cp360-evidence-facts.v1",formal_acceptance=False,reviews=reviews,diagnostics=diagnostics,actual_refs=actual,work_in_progress=wip,
checkpoint_note="CP360 preserves old829 failure prefix and appends originals832..838 once (836 registered/highest838). T7 TTL43 actual positive failed in backup rehearsal because broker drops TEMP/TMP; native backup1/Go1/RootPy1, whole typedSQL87tables/schema296 versions1..23 stateFalse, exact manual release, three Jobs and guards closed. Independent review accepts failedSQLcleanup component only, noNativepositive/Owner/originalbusiness/formal. ATT2 Source rejected variable RFC3339Nano TEXT latest ordering (ATTACH-RESTORE-002), immutable ATT3 assigned; Legacy Source rejected missingProject rollback fixture (LEGACY-ROLLBACK-001), immutable minimal DB-only revision assigned. Original trial onceexpired/providerNULL/financialOPEN preserved; no paid modeltrial or counter reset; Main and all22parents/42formal thresholds unchanged.",
next_action="Independently verify CP360/current task_packet. Source fix broker isolated TEMP/TMP and independently approve Source, then fresh isolated TTL43 compile and exactly one manual Root positive native case; no refresh/autoapproval/new modeltrial. Source repair chronological latest-observation comparison and legacy db-only rollback fixture, then independent Source review and fresh Root targeted composition. Build real historical20 release and authorized backup/isolatedrestore/upgrade resource branch without pretending authority from partial Gitentries. Continue complete DAG and 42 formal current gates.")
print(json.dumps(dict(facts_ref=save("checkpoint.execution.facts.json",value),review_count=len(reviews),diagnostics=[item["ordinal"] for item in diagnostics])),flush=True)
