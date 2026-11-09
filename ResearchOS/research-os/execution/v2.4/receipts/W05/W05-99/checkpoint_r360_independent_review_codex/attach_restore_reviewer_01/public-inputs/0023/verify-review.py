from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
S=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r359-native-ttl-prelaunch-accepted-attach-restore-fence-open")
refs={}
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(r):
 a=pin(r['path']);assert a['sha256']==r['sha256'].removeprefix('sha256:') and a['bytes']==r['bytes'],str(r['path'])
 key=str(Path(a['path']).resolve()).casefold()
 if key in refs:assert refs[key]==a
 refs[key]=a;return Path(a['path']).read_bytes()
def rd(p):return json.loads(verify(pin(p)))
def write(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
handoff=json.loads(verify(dict(path=str(S/'handoff.json'),sha256='a3bc9103f43dd3a5b5568163bb2c7036cdaee0e9f3d9bbb1f803ffe23b5e459a',bytes=1182)))
mf=json.loads(verify(handoff['manifest_ref']))
for r in mf['members']:verify(r)
facts=json.loads(verify(dict(path=str(S/'checkpoint.execution.facts.json'),sha256='9ab25341d9f072445f77258f3c1728ddda17ccd53ce6285ea33b272f87481df5',bytes=19536)))
assert facts['schema']=='researchos.root-cp359-evidence-facts.v1' and not facts['formal_acceptance'] and len(facts['reviews'])==4
reviews=[];manifests=[]
for x in facts['reviews']:
 reviews.append(json.loads(verify(x['handoff_ref'])));m=json.loads(verify(x['manifest_ref']));manifests.append(m)
 members=m['members'];members=members.values() if isinstance(members,dict) else members
 for r in members:verify(r)
for x in reviews:assert x['formal_acceptance'] is False
for r in facts['actual_refs']:verify(r)
pair=rd(S/'canonical_pair.actual.json');t=Path(pair['transaction']['transaction_journal'])
for p in t.iterdir():
 if p.is_file():verify(pin(p))
intent=rd(t/'intent.json');committed=rd(t/'committed.json')
for r in intent['before_refs']+intent['after_refs']+committed['after_refs']:verify(r)
assert intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False
assert committed['written_indices']==[0,1] and committed['both_verified_while_exclusively_held']
before_raw=(t/'0.before.json').read_bytes();now_raw=verify(handoff['checkpoint_ref'])
assert hashlib.sha256(before_raw).hexdigest()=='370c3b73f630a952a80c9082b27ed09e28278cc79bdf65bfbe453c317cb42064' and len(before_raw)==4093175
assert hashlib.sha256(now_raw).hexdigest()=='f52e1416c81fefedde08725c3a7c9250a8e478b22e38b1e6ec1f7e42be236ecc' and len(now_raw)==4108524
assert now_raw==(t/'0.after.proposed.json').read_bytes()
before=json.loads(before_raw);now=json.loads(now_raw)
assert before['revision']==358 and now['revision']==359 and now['expected_previous_revision']==358
ow=verify(pair['ownership_ref']);assert ow==(t/'1.before.json').read_bytes()==(t/'1.after.proposed.json').read_bytes() and json.loads(ow)['revision']==168
other=[]
for r in manifests[0]['base_refs']:
 if Path(r['path']).name in ['step_state.json','commands.json']:
  verify(r);other.append(r)
assert len(other)==2
changed=sorted(k for k in set(before)|set(now) if before.get(k)!=now.get(k))
assert changed==sorted(['updated_at','failure_counters','revision','note','expected_previous_revision','work_in_progress'])
assert len(before['failure_counters'])==823 and len(now['failure_counters'])==829 and now['failure_counters'][:823]==before['failure_counters']
diags=facts['diagnostics'];assert [x['ordinal'] for x in diags]==list(range(826,832))
keys={x.get('origin_key') for x in before['failure_counters']}
for d,entry in zip(diags,now['failure_counters'][823:]):
 r=d['origin_ref'];verify(r);expected=hashlib.sha256((r['sha256']+'#'+str(d['ordinal'])).encode()).hexdigest()
 assert expected==entry['origin_key'] and expected not in keys;keys.add(expected)
 assert entry['counted_once'] and not entry['counter_reset'] and not entry['automatic_retry'] and entry['evidence_ref']==r
 pl=entry['original_payload'];assert pl['observed_ordinal']==d['ordinal'] and pl['immutable_origin_ref']==r and pl['diagnostic']==d['description']
 for k in ['actual_outer_exit','actual_python_exit','actual_native_exit']:assert pl[k]==d[k]
 assert pl['inferred_exits_are_not_directly_observed']==(d['ordinal']==831)
expected_exits=[[1,1,None],[None,None,None],[None,None,None],[1,None,None],[1,1,None],[1,None,None]]
assert [[d[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit']] for d in diags]==expected_exits
origins=[json.loads(verify(d['origin_ref'])) for d in diags]
assert origins[1]['process_started'] is False and origins[1]['filesystem_action_started'] is False
assert origins[2]['original_full_input_object_persisted'] is False and origins[2]['original_tool_result_capture']=='copied_exact_rendered_tool_result' and origins[2]['no_process_started']
assert origins[4]['missing_runtime_module_exact_path'] is None and origins[4]['actual_native_exit'] is None and 'inference' in origins[4]['guard_scope']
assert origins[5]['actual_python_exit'] is None and origins[5]['original']['result']['chunk_id']=='c77bda'
assert origins[5]['original']['result']['exit_code']==1 and 'ROOT_PYTHON_EXIT=' not in origins[5]['original']['result']['output']
expected_wip=dict(before['work_in_progress']);expected_wip.update(facts['work_in_progress'])
expected_wip.update(r359_registered_failure_count=829,r359_highest_observed_diagnostic_ordinal=831,mu_sdk_r359_facts_ref=pin(S/'checkpoint.execution.facts.json'))
assert now['work_in_progress']==expected_wip and now['note']==facts['checkpoint_note']
g=rd(S/'source_guard.cleanup.actual.json')
assert g['closed'] and g['verification']=='PASSED' and g['share_mode']=='FILE_SHARE_READ_ONLY' and g['retained_handles_count']==0 and not g['errors'] and g['failure'] is None
assert len(g['entries'])==159
for e in g['entries']:assert e['verified'] and e['final_path_match'] and e['closed'];verify(e)
rio=json.loads(verify(dict(path=str(S/'original-root-tool-io/original-tool-io.json'),sha256='155c037c8358010d2c40dc2248fd48776cc7a8f9b636c0fdfaad30af73c78217',bytes=3777)))
assert [x['result']['chunk_id'] for x in rio['operations']]==['86e90c','a80582']
for op in rio['operations']:assert op['result']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in op['result']['output']
assert rio['actual_outer_exit']==rio['actual_python_exit']==0 and rio['checkpoint_revision']==359 and rio['next_diagnostic_ordinal']==832
assert rio['registered_failure_count']==829 and rio['highest_observed_diagnostic_ordinal']==831 and not rio['counter_reset']
w=facts['work_in_progress'];cc=w['mu_sdk_r359_compile'];pre=w['mu_sdk_r359_native_prelaunch'];att=w['mu_sdk_r359_attach_source'];hist=w['mu_sdk_r359_history_fixture'];pres=w['mu_sdk_r359_preserved']
assert cc['status']==reviews[1]['decision'] and cc['sources']==43 and cc['unchanged_sources']==42 and cc['modified_files']==1 and cc['TTL_expressions']==2
for k,v in {'packages':364,'compiler_inputs':3793,'products':599,'embeds':38,'tools':8,'compiler_guard_set_count':3920,'compile_Jobs_closed':7,'Git_Jobs_closed':5,'compile_guard_groups_closed':5,'isolation_guard_groups_closed':2,'new_unit_passes':0}.items():assert cc[k]==v
assert cc['old_units_not_rerun'] and not cc['Main_adopted'] and reviews[1]['unit_execution'] is False and reviews[1]['native_case_execution'] is False
assert pre['status']==reviews[2]['decision'] and pre['case']=='positive-replay' and pre['fresh_case_id']=='26c5c890ef5144d4'
assert pre['native_cases_started']==pre['signatures_created']==0 and not pre['native_pass'] and not pre['TTL_refresh']
assert pre['frozen_inputs']==4084 and pre['initial_credential_max_TTL_minutes']==15 and pre['concrete_grant_minutes']==4
assert pre['no_automatic_approval'] and pre['manual_sign_each_exact_payload'] and pre['SQL_inspection_before_specific_release']
cfg=json.loads(verify(pre['config_ref']));hc=json.loads(verify(cfg['HarnessConfig']))
assert not Path(cfg['ControllerDirectory']).exists() and not Path(hc['OutputDirectory']).exists()
assert reviews[3]['verdict']=='REQUEST_CHANGES' and reviews[3]['source_component_accepted'] is False and reviews[3]['important_blocking_count']==1
assert att['status']==reviews[3]['status']=='SOURCE_REJECTED_UNRESOLVED_RESTORE_FENCE_BYPASS'
assert att['finding']=='ATTACH-RESTORE-001' and att['finding_static_only'] and not att['native_reproduction'] and not att['current_candidate_adopted']
assert att['active_asynchronous_takeover']==att['historical_cached_ACK_terminal']=='OPEN_BRANCH' and att['original_runtime8_failures_preserved']
assert hist['product_upgrade_acceptance'] is False and hist['status'].endswith('IN_PROGRESS_NOT_ACCEPTED') and hist['ordinary_positive_upgrade']=='BLOCKED_NO_MATCHING_HISTORICAL20_PROGRAM_BACKUP_UPGRADE'
assert pres['current_formal_accepted']==0 and pres['historical_accepted_parents']==6 and pres['required_parents']==22 and pres['required_formal']==42
for k in ['original_trial_business_open','original_trial_once_consumed','original_trial_clock_expired','original_positive_native_attempt_failed_closed','original_positive_TTL_fail_820_preserved']:assert pres[k]
for k in ['original_trial_DB_touched','original_trial_financial_closed','overall_completion','counter_reset']:assert pres[k] is False
assert pres['original_trial_provider_requests'] is None and pres['global_provider_requests'] is None
resume=rd(S/'RESUME.r359.original.json')
assert resume['checkpoint_revision']==359 and resume['ownership_revision']==168 and resume['registered_failures']==829 and resume['highest_observed_diagnostic_ordinal']==831
assert resume['current_formal_accepted']==0 and resume['signatures_created']==0 and not resume['native9_accepted'] and not resume['completion_asserted']
# Verify the selected Main source pins from accepted T7's input guard, without rerunning Git or any workload.
root=Path(resume['repository_root'])
compile_guard_path=Path(facts['actual_refs'][0]['path']).parent/'input-source-guard.cleanup.actual.json'
mg=rd(compile_guard_path);main_refs=[]
for e in mg['entries']:
 p=Path(e['path'])
 if p.is_relative_to(root) and p.relative_to(root).parts[0] not in ['.local','execution']:
  verify(e);main_refs.append(pin(p))
assert len(main_refs)==14
review=dict(schema='researchos.independent-cp359-canonical-review.v1',decision='CP359_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY',
 checkpoint_ref=handoff['checkpoint_ref'],ownership_ref=pair['ownership_ref'],unchanged_step_commands_refs=other,
 changed_top_keys=changed,old823prefix_exact=True,appended_ordinals=list(range(826,832)),registered_failures=829,highest_ordinal=831,next_diagnostic_ordinal_as_Root_report=832,
 exact_WIP_facts_plus_three_fields=True,all_other_CP_fields_unchanged=True,counter_reset=False,automatic_retry=False,
 transaction_exact_before_after_current=True,transaction_exclusive_both_verified=True,source_guard_closed_entries=159,source_guard_retained_handles=0,
 original_root_outer_exit=0,original_root_python_exit=0,four_independent_reviews_and_manifest_members_verified=True,
 diagnostic_exit_tuples=expected_exits,diagnostic828_complete_original_input_persisted=False,diagnostic828_rendered_result_only=True,
 diagnostic830_bootstrap_close_observed=False,diagnostic830_OS_exit_release_inference_only=True,diagnostic831_Python_exit_observed=None,diagnostic831_inferred_exit1_not_direct=True,
 T7_compile_component_accepted=True,single_positive_prelaunch_Source_accepted=True,new_native_started=0,new_signatures=0,old25units_not_rerun=True,new_unit_passes=0,
 attach_Source_accepted=False,attach_finding='ATTACH-RESTORE-001',attach_finding_static_only=True,restore_fence_fix_pending=True,
 legacy_fixture_Source_pending_unaccepted=True,old_runtime8_failures_preserved=True,
 selected_Main_source_refs=main_refs,Main_product_adopted=False,Owner_accepted=False,original_business_accepted=False,
 original_once_consumed=True,original_clock_expired=True,original_provider_requests=None,financial_closed=False,
 current_formal_accepted=0,required_formal=42,required_parents=22,overall_completion=False,
 new_mechanical_errors=0,authority='NONE',scope='Canonical consistency only; no Go/native/SQL/model/sign/private or canonical mutation',stop=True,
 limits=['Attach restore finding is inherited from its sealed static review, not a new native reproduction','Unsealed legacy/revised attach author branches remain pending; this checkpoint does not accept them','Source prelaunch acceptance remains separate from actual native execution','828 full original dispatch input unavailable and 831 Python exit lacks marker; original qualifications preserved'])
write('review.json',review)
for r in list(refs.values()):verify(r)
write('verified-input-pins.json',dict(schema='researchos.independent-verified-pins.v1',references=list(refs.values()),count=len(refs),drift_count=0))
print(json.dumps(dict(decision=review['decision'],references=len(refs),drift=0,guard_entries=159,Main_pinned_sources=14,new_errors=0),ensure_ascii=True))

