import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(path):
 p=Path(path).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def expected(path,h,n):
 ref=pin(path);assert ref["sha256"]==h and ref["bytes"]==n;return ref
specs=[
("checkpoint_r357_independent_review_codex/1a11db9e0dff7ad081d6e06d","1576f4f6744fa913d61f183711174773a04102b0aac33c16eb99c3946b02ec14",1315,"a96ce0319a0d9c5be58f28b68e81bca08edb501ec689ce41baf285c5c35a564c",39645),
("typed_runtime_goal_fixture_q3_independent_review_codex/9c5969e8d1a94b1eab93205758bb53a9","5b1f8246ac53616115ecc0062c09390215474ff4078d9ef60720c7273c18aa6b",20213,"aff8c5323eac009f92923857970d47a2c7ee0ed2a3fe292c9a356d279a8dfd2b",2713),
("workspace_epoch_fixture_independent_review_codex/4f3906c8c9e6422281cfc0bdb33a488a","3f147b427b06ecedafa2b8832842440fa1f1d3e2160f11963ad4646975dcb857",11666,"17631a6f0112adc2fbea99826bc34607502290e7364c2ef345d3cb17ca12ae1e",2664),
("native_positive_failed_closed_independent_review_codex/1a11dd67f1a9f3b2848ac45b8","8850ada4a694f314a2766e51bbc17da76b2c22520f6ae5d5c9ed2c48194eefc8",1597,"ce26faf95f76d7c11f94fc16246e968218f429b0a70071473f6f3e7672940cbb",1052179),
("native_migration_ttl_independent_review_codex/1a11ddd38bb-fa0099f8","3a7ff3bf882f632b4c15181e5cbc2652c8984469d78d58431a856f31d576c8bb",1351,"3913939aff7b778204a9dd1eb51079a23f34a92fec0da254a8de3755d2d89a0b",10284),
("typed_q3_epoch_actual_independent_review_codex/7340313b128c426b97c9acb20731fa73","6420c14e76af76385ada0eecdea47273c439a15e076ea9e74fec4dec8e5d44fd",4112,"7f6b5e0ddb7ec8b1b6663a83fc5a99135cd44e55322be552ddced717b60ad2a6",33741)]
reviews=[]
for name,h,n,m,mn in specs:
 hd=expected(B/name/"HDF.json",h,n);mf=expected(B/name/"MF.json",m,mn)
 document=json.loads(Path(hd["path"]).read_bytes())
 assert document.get("formal_acceptance") is False
 manifest=json.loads(Path(mf["path"]).read_bytes());members=manifest["members"]
 members=members.values() if isinstance(members,dict) else members
 for member in members:expected(member["path"],member["sha256"].removeprefix("sha256:"),member["bytes"])
 reviews.append(dict(name=name,handoff_ref=hd,manifest_ref=mf,formal_acceptance=False))
diag_specs=[
(818,"checkpoint_r357_independent_review_codex/1a11db9e0dff7ad081d6e06d/original-tool-io.json","84250b070407e393ff64bfd3aa9b0bd8a1605ee74da805c6a17b317d7887e2bf",81784,1,None,None,"Reviewer attempted read_bytes on transaction directory: PermissionError13. Corrected is_file enumeration; original failure preserved."),
(819,"integration_codex/root-read-diagnostic-819-native-source-name-07c3c79d/failure-origin.819.json","8a22cda20cdd1521ab97cd5e8e9f89600e9ce7bf83c8a00f48fecbc1b3f02db1",2130,1,None,None,"Root guessed missing native harness filename; original exact rendered result copied with provenance label after original exec did not store it."),
(820,"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/failure-origin.820.closed-qualified.json","d298a2d181d5b75fcc02a304916adc6a522152922ba61b153f3f7f0a99256047",14621,1,1,1,"Original native positive failed at credential TTL greater than fifteen minutes. Nested Python1/Go1 directly observed, two Jobs closed. Initial native-exit-null origin remains immutable."),
(821,"integration_codex/root-inspection-diagnostic-821-sharing-a51cfb0f/failure-origin.821.json","637d4d131d9a735831bb83cb8596f82a8ad3af3d7723b4ab4e1dc3f270bf97f2",2474,1,1,None,"APIv3 read guard for retained writable SQLite failed errno32 before successful SQL read. APIv4 distinct Source later performed truthful shared read SQL snapshot; old failure not reset."),
(822,"native_migration_credential_ttl_revision_codex/1a11dd62452c7c895d4e2f51/diagnostic-822.json","c9788a3c20241243a45ebf58113cce1eaa3d6801efb8cf3ec51e889c6f93ccd3",1473,None,None,None,"Source author load returned undefined; store undefined rejected in functions.exec before any shell/native process."),
(823,"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/failure-origin.823.json","dd9f109a588644a038a12461516ebd9d9191a6b4f54f8eee89ef3ef8a7b7ec52",4415,1,1,None,"T6 actual49Sources25parentScopes61PASS6FAIL0SKIP, primary official test2json reporter exit1 directly observed; individual native-child PID/exit remain NULL, propagated exit1 only inferred. All four Jobs/five guards closed. Eight native leaves fail attach ACKNOWLEDGED/revision3."),
(824,"native_migration_ttl_independent_review_codex/1a11ddd38bb-fa0099f8/diagnostics.json","f051f55dad9d48a7d3233b864aa1664bd97a1b5818f34a154d9d41a6472eb0c9",3291,1,None,None,"TTL reviewer guessed absent HANDOFF.md/manifest.json before enumeration; original tool cb0cfa exit1."),
(825,"native_migration_ttl_independent_review_codex/1a11ddd38bb-fa0099f8/diagnostics.json","f051f55dad9d48a7d3233b864aa1664bd97a1b5818f34a154d9d41a6472eb0c9",3291,1,None,None,"TTL reviewer read absent top-level AGENTS.md rather than repository AGENTS.md; original tool9c3d17 exit1. Shared immutable origin file but distinct ordinal/event.")]
diagnostics=[]
for ordinal,name,h,n,outer,py,native,description in diag_specs:
 diagnostics.append(dict(ordinal=ordinal,origin_ref=expected(B/name,h,n),actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=native,description=description))
actual_names=[
"integration_codex/native-positive-serve-v2-root-75dc3afca9b34a99/serve-outer.closed.json",
"integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller-runtime/controller.closed.json",
"integration_codex/native-positive-root-api-v4-7e971c417d4d4d2a/inspection-positive.json",
"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/root.fixture-release.approval.json",
"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/root.concrete-cleanup.decision.json",
"integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f/original-tool-io.json",
"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/validation.closed.json",
"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/original-tool-io.json",
"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/source-overlay.json",
"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/formatted.source-members.json",
"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2/actual-tagged-compiler-input-inventory.json"]
actual=[pin(B/name) for name in actual_names]
wip={
"mu_sdk_r358_native_original_positive":"FAILED_EXECUTION_CLOSED_TTL_BOUNDARY_BEFORE_AUTHORITY_OR_SIGNING",
"mu_sdk_r358_native_failure_component_review":reviews[3],
"mu_sdk_r358_native_sql_observation":dict(status="ACCEPTED_FAILURE_CLEANUP_COMPONENT_ONLY",tables=87,typed_row_digests=280,schema_objects=296,versions=list(range(1,24)),data_version_before=2,data_version_after=2,db_wal_raw_bytes_unchanged=True,expected_state_matches=False,baseline_available=False,held_sidecars="INITIAL_ENUMERATED_WAL_ONLY_NOT_FUTURE_SIDECAR_CLOSURE",database_source_immutability=False,Jobs_closed=2,guard_groups_closed=11,root_cleanup_specific_approval=True,signatures_created=0,native_case_pass=False,native9_accepted=False,Owner_accepted=False),
"mu_sdk_r358_native_ttl_source":dict(status="MINIMAL_SOURCE_ACCEPTED_FRESH_ISOLATED_BUILD_REQUIRED",review=reviews[4],two_calls="time.Hour_to_15*time.Minute",production_ttl_unchanged=True,actual_native_pass=False,credentials_refresh_authorized=False),
"mu_sdk_r358_typed_q3_epoch_actual":dict(status="FAILED_EXECUTION_CLOSED_REQUEST_CHANGES",review=reviews[5],sources=49,parent_scopes=25,pass_nodes=61,fail_nodes=6,skip_nodes=0,native_leaf_failures=8,root_jobs_closed=4,guards_closed=5,verified_unique_file_pins=4141,Goal="ACCEPTED_COMPONENT_OBSERVED_ONLY",writer_epoch="ACCEPTED_COMPONENT_OBSERVED_ONLY",runtime_pass=False,native_pass=False,FULL_pass=False,formal_acceptance=False,canonical_pre_run_receipt_independently_persisted=False,native_child_pid=None,native_child_exit=None,primary_reporter_exit=1,native_exit1_inference_only=True),
"mu_sdk_r358_runtime_attach_gap":dict(status="BLOCKED_PRODUCTION_ATTACH_COMPLETION_AND_SAME_OWNER_RENEWAL",first_actual_failure="session.attach_ACKNOWLEDGED_revision3_expected_COMPLETED",contract_completion_required=True,Source_Q4_candidate_written=False,production_Source_repair_assigned="/root/command_queue_impl",test_fabricated_completion_allowed=False,read_only_snapshot_substitute_for_contract_acceptance=False),
"mu_sdk_r358_preserved_scope":dict(Main_product_adopted=False,historical_accepted_parents=6,current_formal_accepted=0,total_parent_tasks=22,required_formal=42,original_trial_business_open=True,original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_provider_requests=None,original_trial_financial_closed=False,global_provider_requests=None,overall_completion=False,counter_reset=False),
"mu_sdk_r358_reviews":reviews}
facts=dict(schema="researchos.root-cp358-evidence-facts.v1",formal_acceptance=False,reviews=reviews,diagnostics=diagnostics,actual_refs=actual,work_in_progress=wip,
checkpoint_note="CP358 preserves old815 failures and appends eight original diagnostics818..825 once (823 registered/highest825). Native positive attempt failed TTL before authority and closed; independent SQL observation87tables280typed rows296schema objects, specific Root cleanup accepted only as failed-execution components. Minimal TTL Source accepted, fresh build pending. T6 actual49Sources25parents61PASS6FAIL0SKIP closed all4Jobs5guards; independent Goal/epoch observed components accepted, runtime8 attach leaves stillFAIL. Production attach terminal and same-owner lease renewal Source repair assigned. No Main adoption, native9/Owner/original business/formal acceptance or completion; original once/expired business/provider NULL preserved.",
next_action="Seal Q4 contract-gap report; independently review minimal production session.attach completion/renewal Source, then repair fixture actual binding and run fresh isolated combination. In parallel Root prepare a fresh TTL native harness build/config/public case; old positive attempt and all original failures remain immutable. Continue task_packet DAG; no new paid trial until original business legitimately closed.")
f=O/"checkpoint.execution.facts.json"
with f.open("xb") as stream:stream.write((json.dumps(facts,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
print(json.dumps(dict(facts_ref=pin(f),reviews=len(reviews),pending_diagnostics=[x["ordinal"] for x in diagnostics],actual_refs=len(actual))),flush=True)
