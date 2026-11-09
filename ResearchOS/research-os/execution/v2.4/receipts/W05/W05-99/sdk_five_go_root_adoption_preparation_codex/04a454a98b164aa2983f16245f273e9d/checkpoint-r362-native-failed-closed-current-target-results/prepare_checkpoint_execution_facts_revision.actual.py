import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def check(p,h,n):
 ref=pin(p);assert (ref["sha256"],ref["bytes"])==(h,n);return ref
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
review_specs=[
("checkpoint_r361_independent_review_codex/attach_restore_reviewer_03","0a78591cd1b0e30baded3c0e4e9bd055a1e513674698c84b3233bc9710b33845",6107,"6e20e9a80cd61b0c95481d3c6820befe06735d9256f1ec150b924d269d50b6f0",278104),
("typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8","4ee5b9e622d4c6bc3b6e8832069ec6fef81262a529ccf6a73985f15af3de64ab",4931,"8191c6d38df790531d1cc3c34dba2a913e0d0e2964787571d85a92286ff4b5d9",44166),
("legacy_migration_fixture_revision_independent_review_codex/attach_restore_reviewer_02","86852319669c0b34a31fff88c3c3c3ed5c7517d11b4b91d042cafa82fb2e0b05",8904,"a6f6c272854093ff87f4defc67fb4b8cf1ae2dd7b9a8126e97044c6205213aca",70838),
("session_expired_writer_attach_fixture_independent_review_codex/5f3e09c72caf4d1991adf5174a87b19e","31588047abcbc69139dc026bb89dd8aea9461c912925458512aa2d5d06368f0a",3644,"a1357ecbf8a27c9cb3b78ef315ec67fc9d3cb75bc7076bb558c2500ee110ad90",37276),
("native_migration_controller_temp_env_independent_review_codex/b6af18c92e674ec19d8cd0cd0721a3f4","e60c15edbe089e4da258d32ea2d5a43d678ea0fd9fbd5836878f6b455c54835c",3841,"ab048b3bbbf2dfee080c6e4fa83f34706726f27987fd3b872d40cb463b2d7b22",74888),
("native_temp_prelaunch_actual_independent_review_codex/b5bf0ed767204b69a82b86acff0e23f1","0659037dfc6759e0de7d0994b166f6430a2dd8f92d3a2cc99c9cff3f3667fc24",4443,"ec5f88f86d098eae397cd55c289460a591c5c3991684091882948e7d4d700526",58536),
("native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d","7c0ad0872da573a5a6948b2c6e7d55a438e57e3cc2ba65b70329e9cea6dd2518",4535,"8edd94cc087bf2f042fcec9a892f04687eb0898dc67c683e2fe710f85cbf58bb",5044),
("native_temp_actual_failure_independent_review_codex/c13a1cf32d414d74b350883ebd8e4d09","71f4741962f59b915cd4c60c31d21bdc36e69df82027abec15ca32a84b8a8f38",4391,"2c985afcd67c8bc02960b1e6976c50a8367156a7ae924f40f31b6d8b97221105",4981)
]
reviews=[]
for d,hh,hn,mh,mn in review_specs:
 h=check(B/d/"HDF.json",hh,hn);m=check(B/d/"MF.json",mh,mn)
 members=json.loads(Path(m["path"]).read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 for v in members:check(v["path"],v["sha256"].removeprefix("sha256:"),v["bytes"])
 reviews.append(dict(name=d,handoff_ref=h,manifest_ref=m,formal_acceptance=False))
diagnostic_dirs={
848:"typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8",
849:"integration_codex/native-temp-compile-unit-root-1791508539969",
850:"native_migration_controller_temp_env_independent_review_codex/b6af18c92e674ec19d8cd0cd0721a3f4",
851:"integration_codex/native-temp-compile-unit-root-1791508539969",
852:"typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8",
853:"session_expired_writer_attach_fixture_revision_codex/leg-1a11e3e93437fe089b15fdf6a164840",
854:"session_expired_writer_attach_fixture_revision_codex/leg-1a11e3e93437fe089b15fdf6a164840",
855:"session_expired_writer_attach_fixture_revision_codex/leg-1a11e3e93437fe089b15fdf6a164840",
856:"native_temp_prelaunch_actual_independent_review_codex/b5bf0ed767204b69a82b86acff0e23f1",
857:"session_expired_writer_attach_fixture_independent_review_codex/5f3e09c72caf4d1991adf5174a87b19e",
858:"native_temp_prelaunch_actual_independent_review_codex/b5bf0ed767204b69a82b86acff0e23f1",
868:"integration_codex/native-temp-failed-root-release-1791509915469",
869:"native_temp_actual_failure_independent_review_codex/c13a1cf32d414d74b350883ebd8e4d09",
870:"shared_recovery_observation_fence_revision_codex/sf-1a11e3e93437fe089b15fdf6a164840",
871:"integration_codex/current-attach-q5-leg2-targeted-root-1791510290800",
872:"shared_recovery_observation_fence_revision_codex/sf-1a11e3e93437fe089b15fdf6a164840"
}
exits={848:(0,1,None),849:(1,1,None),850:(1,1,None),851:(1,None,None),852:(0,1,None),853:(1,None,None),854:(0,None,None),855:(None,None,None),856:(0,None,None),857:(0,1,None),858:(0,0,None),868:(1,1,1),869:(None,None,None),870:(1,None,None),871:(1,1,1),872:(1,None,None)}
descriptions={
848:"Independent Q5 initial HDF/MF basename read failed; actual marker Python1.",
849:"Root compile preparation assumed MF dict; .values on list failed before guard/compile.",
850:"Independent controller Source ref dict comparison falsely treated slash metadata as drift.",
851:"Root PowerShell read used guessed context-prerequisite filename.",
852:"Independent Q5 exact inverse initially used original instead of sequential offsets.",
853:"Expired-writer Source rg used wrong contracts root.",
854:"Expired-writer Source read guessed absent types.go.",
855:"Source inline process creation failed with CreateProcess206; no process exit observed.",
856:"Independent prelaunch PowerShell array concatenation combined paths.",
857:"Expired-writer independent static regex overescape.",
858:"Prelaunch initial Source review false REQUEST_CHANGES from old C/B whitelist omission; executed exits0.",
868:"Actual native broker rejected four-key ENV against old pair-only Python preflight; held outer/Python/Go exit1; broker independently held exit NULL, source-reported1.",
869:"Independent failed-native review history read rejected invalid offset; no shell.",
870:"Shared SQL fence Source rg used T6 cwd for absent .local path.",
871:"Root current ATT3/Q5/LEG2/expired target actual 152PASS/5FAIL/0SKIP, three failed parents; outer/Python/Go1.",
872:"Shared SQL fence Source Windows explicit globs invalid os error123."
}
pending=[]
for n,d in diagnostic_dirs.items():
 ref=pin(B/d/f"failure-origin.{n}.json");json.loads(Path(ref["path"]).read_bytes())
 a,p,g=exits[n];pending.append(dict(ordinal=n,origin_ref=ref,actual_outer_exit=a,actual_python_exit=p,actual_native_exit=g,description=descriptions[n]))
tr=check(B/"shared_epoch_readonly_trace_codex/d8b61b3e-3f39-4cb4-a043-9b935f2a0cd1/failed-original-tool-io.json","4e1e422535feef26222283c3510069ac4ce32f93d190227ea4199eb9a0b43287",9290)
trace=json.loads(Path(tr["path"]).read_bytes());assert trace["failed_call_count"]==len(trace["calls"])==9
for offset,item in enumerate(trace["calls"]):
 n=859+offset
 a=item.get("exit_code") if item["tool"]=="tools.exec_command" else None
 ref=save(f"failure-origin.{n}.qualified.json",dict(ordinal=n,immutable_bundle_ref=tr,original_index=item["index"],original_payload=item,actual_outer_exit=a,actual_python_exit=None,actual_native_exit=None,counted_once=True,counter_reset=False))
 pending.append(dict(ordinal=n,origin_ref=ref,actual_outer_exit=a,actual_python_exit=None,actual_native_exit=None,description="Readonly shared epoch trace distinct failed original call; exact bundle index preserved."))
r873=pin(O/"failure-origin.873.json");pending.append(dict(ordinal=873,origin_ref=r873,actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,description="Root collaboration Source dispatch rejected thread limit; no shell/process executed."))
for n,a,p,g,description in [(874,1,1,None,"Root CP362 facts preparation hardpin transcription failed before guards or canonical mutation."),(875,1,None,None,"Root PowerShell diagnostic pipeline syntax rejected before body/process execution.")]:
 ref=pin(O/f"failure-origin.{n}.json")
 pending.append(dict(ordinal=n,origin_ref=ref,actual_outer_exit=a,actual_python_exit=p,actual_native_exit=g,description=description))
pending.sort(key=lambda v:v["ordinal"]);assert [v["ordinal"] for v in pending]==list(range(848,876))
actual_specs=[
("integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest/validation.closed.json","9ecbf95ad3c89757479f611742a081d31aff0bbffbd1277aa1d10e0e82d52f5d",10813),
("integration_codex/native-temp-positive-serve-root-1791509017626/serve-outer.closed.json","675075d2ec43f63ec3ef3db7788ecc1920145af2b7abac44ef88434e37379508",1131387),
("integration_codex/current-attach-q5-leg2-targeted-root-1791510290800/validation.closed.json","1f5bbf0fd7ac125875059c4e6e516dfd7419548283ab330cc965b21af58f0593",39787),
("integration_codex/current-attach-q5-leg2-targeted-root-1791510290800/source.integration.choice.json","8fee24f844dbb06581ea15b7f8665844ce4335fc93a0532d096433a810cea343",5610),
("integration_codex/native-temp-controller-config-root-1791508950616/controller.public.config.json","19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af",1163646),
("native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2/HDF.json","ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824",6761),
("native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2/MF.json","deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc",9803),
("shared_recovery_observation_fence_revision_codex/sf-1a11e3e93437fe089b15fdf6a164840/HDF.json","bbc8bc66c45303e794c3c919230f2b94f28e204c8cee979e18f184229c5e94c4",5456),
("shared_recovery_observation_fence_revision_codex/sf-1a11e3e93437fe089b15fdf6a164840/MF.json","ea372e96ff20e4ba0feeab742b6d245071c7aefddc800a79e8598f6971e25d02",16363)
]
actual_refs=[check(B/d,h,n) for d,h,n in actual_specs]
wp=dict(
status="ROOT_CURRENT_TARGET_ACTUAL_FAILED_CLOSED_BROKER4_SOURCE_REVIEW_PENDING_SHARED_SQL_COMPATIBILITY_BRANCH_BLOCKED",
next_action="Finish BR4 independent Source review, Root pure17 boundary actual, prepare fresh current-context exact broker-source HC/CFG/prelaunch review and one bounded native positive. Repair two ATT3 fixtures without weakening schema. Historical ordinary upgrade needs matching program+backup/restore; shared SQL fence needs legal old24 compatibility transition. No new paid trial until original business closes.",
mu_sdk_r362=dict(
cp361_consistency_accepted=True,reviews=reviews,actual_refs=actual_refs,
T8_compile_and_28_boundary_units_limited_accepted=True,T8_native_positive_failed_868=True,
T8_owned_jobs_closed=True,T8_whole_sql_87_tables_equal_before=True,T8_specific_fixture_released=True,
T8_broker_held_exit=None,T8_broker_source_reported_exit=1,
T9_target_actual=dict(parents=54,pass_terminals=152,fail_terminals=5,skip_terminals=0,old25_and_prior6_runtime_failures_now_pass=True,independent_actual_review="PENDING",full_domain_acceptance=False,formal_acceptance=False,owned_jobs_closed=True),
T9_failed_parents=["TestClientAttachSettledAcquisitionCompletesAndReplays","TestClientAttachPreservesStaleAndBindingGates","TestClientTranscriptIndexUpgradesExistingSessionTable"],
broker4_source="SOURCE_ACCEPTED_PENDING_ROOT_BOUNDARY_ACTUAL",broker4_17_pure_tests="NOT_RUN",
shared_sql_fence="SOURCE_BLOCKED_OLD24_TRIGGER_HASH_AND_HISTORICAL_TEMPLATE_COMPATIBILITY_NO_CANDIDATE",
historical20_ordinary_upgrade="BLOCKED_NO_MATCHING_PROGRAM_BACKUP_ISOLATED_RESTORE_UPGRADE",
original_trial_once_consumed=True,original_trial_clock_expired=True,original_trial_business_open=True,original_trial_financial_closed=False,original_trial_provider_requests=None,global_provider_requests=None,
historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,overall_completion=False,counter_reset=False,
old845_failure_records_unchanged=True))
facts=dict(schema="researchos.root-cp362-failed-closed-current-target-facts.v1",formal_acceptance=False,reviews=reviews,diagnostics=pending,actual_refs=actual_refs,trace_bundle_ref=tr,work_in_progress=wp,
checkpoint_note="CP362 preserves CP361 qualified provenance and all845 existing failures. Appends28 distinct original848..875; T8 native ENV rejection fully inspected/released/Jobs closed. T9 current Source target 152PASS5FAIL0SKIP unaccepted pending independent review. Q5/CTL3/expired Source approved only. Broker4 Source sealed pending review; sharedSQL old24/historical compatibility blocked only this branch. 6 historical parents,0 current formal; original paid business remains open.",
next_action=wp["next_action"])
ref=save("checkpoint.execution.facts.json",facts)
print(json.dumps(dict(facts_ref=ref,diagnostics=len(pending),registered_after=873,highest=875,next=876,reviews=len(reviews))),flush=True)


