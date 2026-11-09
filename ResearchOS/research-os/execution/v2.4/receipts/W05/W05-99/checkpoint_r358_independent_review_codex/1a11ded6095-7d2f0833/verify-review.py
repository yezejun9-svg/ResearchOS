from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
S=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r358-native-failed-closed-q3-epoch-actual-async-attach-open")
refs={}
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(r):
 p=Path(r['path']);a=pin(p);assert a['sha256']==r['sha256'].removeprefix('sha256:') and a['bytes']==r['bytes'],str(p)
 key=str(p.resolve()).casefold()
 if key in refs: assert refs[key]==a
 refs[key]=a;return p.read_bytes()
def observed(p):
 r=pin(p);verify(r);return json.loads(Path(p).read_bytes())
def write(name,value):
 with (HERE/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
h=json.loads(verify(dict(path=str(S/'handoff.json'),sha256='3a15a9cc8fec2896c56630c53230d41748492f25481c6bb9d407249fd303c0c2',bytes=1184)))
mf=json.loads(verify(h['manifest_ref']))
for ref in mf['members']:verify(ref)
facts=observed(S/'checkpoint.execution.facts.json');assert pin(S/'checkpoint.execution.facts.json')['sha256']=='83323640ac317be235b8d1e86689c0446598ab55b4a4f519d97f20ec8176c687'
assert len(facts['reviews'])==6 and len(facts['actual_refs'])==11 and facts['formal_acceptance'] is False
review_hdfs=[];review_manifests=[]
for entry in facts['reviews']:
 hd=json.loads(verify(entry['handoff_ref']));review_hdfs.append(hd)
 mm=json.loads(verify(entry['manifest_ref']));review_manifests.append(mm)
 members=mm['members'];members=members.values() if isinstance(members,dict) else members
 for ref in members:verify(ref)
 assert hd.get('formal_acceptance') is False
for ref in facts['actual_refs']:verify(ref)
for d in facts['diagnostics']:verify(d['origin_ref'])
pair=observed(S/'canonical_pair.actual.json')
t=Path(pair['transaction']['transaction_journal'])
for p in t.iterdir():
 if p.is_file():verify(pin(p))
intent=observed(t/'intent.json');committed=observed(t/'committed.json')
for ref in intent['before_refs']+intent['after_refs']+committed['after_refs']:verify(ref)
assert intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False
assert committed['written_indices']==[0,1] and committed['both_verified_while_exclusively_held'] is True
before_raw=(t/'0.before.json').read_bytes();after_raw=verify(h['checkpoint_ref'])
before=json.loads(before_raw);after=json.loads(after_raw)
assert hashlib.sha256(before_raw).hexdigest()=='71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f'
assert hashlib.sha256(after_raw).hexdigest()=='370c3b73f630a952a80c9082b27ed09e28278cc79bdf65bfbe453c317cb42064' and len(after_raw)==4093175
assert before['revision']==357 and after['revision']==358 and after['expected_previous_revision']==357
assert (t/'0.after.proposed.json').read_bytes()==after_raw
ow_raw=verify(pair['ownership_ref'])
assert ow_raw==(t/'1.before.json').read_bytes()==(t/'1.after.proposed.json').read_bytes()
assert json.loads(ow_raw)['revision']==168
canonical_other=[]
for ref in review_manifests[0]['base_refs']:
 if Path(ref['path']).name in ['step_state.json','commands.json']:
  verify(ref);canonical_other.append(ref)
assert len(canonical_other)==2
changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
assert changed==sorted(['updated_at','failure_counters','revision','note','expected_previous_revision','work_in_progress'])
oldf=before['failure_counters'];newf=after['failure_counters']
assert len(oldf)==815 and len(newf)==823 and newf[:815]==oldf
diags=facts['diagnostics'];assert [x['ordinal'] for x in diags]==list(range(818,826))
keys={x.get('origin_key') for x in oldf}
for d,e in zip(diags,newf[815:]):
 r=d['origin_ref'];key=hashlib.sha256((r['sha256']+'#'+str(d['ordinal'])).encode()).hexdigest()
 assert e['origin_key']==key and key not in keys;keys.add(key)
 assert e['evidence_ref']==r and e['counted_once'] is True and e['counter_reset'] is False and e['automatic_retry'] is False
 p=e['original_payload']
 assert p['observed_ordinal']==d['ordinal'] and p['immutable_origin_ref']==r and p['diagnostic']==d['description']
 for field in ['actual_outer_exit','actual_python_exit','actual_native_exit']:assert p[field]==d[field]
 assert p['inferred_exits_are_not_directly_observed']==(d['ordinal']==823)
assert [diags[2][x] for x in ['actual_outer_exit','actual_python_exit','actual_native_exit']]==[1,1,1]
assert [diags[4][x] for x in ['actual_outer_exit','actual_python_exit','actual_native_exit']]==[None,None,None]
assert [diags[5][x] for x in ['actual_outer_exit','actual_python_exit','actual_native_exit']]==[1,1,None]
assert all(d['ordinal']!=826 for d in diags)
expected_wip=dict(before['work_in_progress']);expected_wip.update(facts['work_in_progress'])
expected_wip.update(r358_registered_failure_count=823,r358_highest_observed_diagnostic_ordinal=825,mu_sdk_r358_facts_ref=pin(S/'checkpoint.execution.facts.json'))
assert after['work_in_progress']==expected_wip and after['note']==facts['checkpoint_note']
g=observed(S/'source_guard.cleanup.actual.json')
assert g['verification']=='PASSED' and g['share_mode']=='FILE_SHARE_READ_ONLY' and g['closed'] is True
assert g['failure'] is None and not g['errors'] and g['retained_handles_count']==0 and len(g['entries'])==155
for e in g['entries']:
 assert e['verified'] and e['final_path_match'] and e['closed'];verify(e)
rio=json.loads(verify(dict(path=str(S/'original-root-tool-io/original-tool-io.json'),sha256='948fe7d88b1b0b587ef32e8a91caca814dbf31574beeac67d9c3c0d6da8d8ff5',bytes=3879)))
assert rio['actual_python_exit']==0 and rio['actual_outer_exit']==0 and rio['canonical_revision']==358
assert rio['separately_pending_diagnostic_ordinal']==826 and rio['next_diagnostic_ordinal']==827 and rio['counter_reset'] is False
assert len(rio['operations'])==2
for op in rio['operations']:assert op['result']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in op['result']['output']
assert rio['operations'][1]['result']['chunk_id']=='cc7794'
resume=observed(S/'RESUME.r358.original.json')
assert resume['checkpoint_revision']==358 and resume['ownership_revision']==168
assert resume['registered_failures']==823 and resume['highest_observed_diagnostic_ordinal']==825
assert resume['current_formal_accepted']==0 and resume['historical_accepted_parents']==6 and resume['formal_required']==42
assert resume['signatures_created']==0 and resume['native9_accepted'] is False
assert resume['original_trial_business_open'] and resume['once_consumed'] and resume['original_clock_expired']
assert resume['original_trial_provider_requests'] is None and resume['financial_closed'] is False and resume['completion_asserted'] is False
w=facts['work_in_progress'];n=w['mu_sdk_r358_native_sql_observation']
assert (n['tables'],n['typed_row_digests'],n['schema_objects'])==(87,280,296)
assert n['versions']==list(range(1,24)) and n['data_version_before']==n['data_version_after']==2
assert n['Jobs_closed']==2 and n['guard_groups_closed']==11 and n['status']=='ACCEPTED_FAILURE_CLEANUP_COMPONENT_ONLY'
for k in ['expected_state_matches','baseline_available','database_source_immutability','native_case_pass','native9_accepted','Owner_accepted']:assert n[k] is False
assert n['held_sidecars']=='INITIAL_ENUMERATED_WAL_ONLY_NOT_FUTURE_SIDECAR_CLOSURE' and n['signatures_created']==0
native_h=review_hdfs[3];assert native_h['Go_actual_exit']==1 and native_h['two_Jobs_closed'] and native_h['guard_observations_closed']==11 and not native_h['native_case_pass']
ttl=w['mu_sdk_r358_native_ttl_source'];assert ttl['status']=='MINIMAL_SOURCE_ACCEPTED_FRESH_ISOLATED_BUILD_REQUIRED'
assert ttl['production_ttl_unchanged'] and not ttl['actual_native_pass'] and not ttl['credentials_refresh_authorized'] and review_hdfs[4]['source_accepted'] and not review_hdfs[4]['native_acceptance']
th=review_hdfs[5];typed=w['mu_sdk_r358_typed_q3_epoch_actual']
assert th['verdict']==typed['status'].removesuffix('_REQUEST_CHANGES')=='FAILED_EXECUTION_CLOSED'
assert th['parent_test_node_counts']=={'pass':61,'fail':6,'skip':0}
assert (typed['sources'],typed['parent_scopes'],typed['pass_nodes'],typed['fail_nodes'],typed['skip_nodes'],typed['native_leaf_failures'])==(49,25,61,6,0,8)
assert th['native_leaf_failure_count']==8 and th['root_owned_jobs']==4 and th['source_guards_closed']==5 and th['all_owned_jobs_closed']
assert th['actual_native_child_pid'] is None and th['actual_native_child_exit'] is None and typed['native_child_exit'] is None
assert typed['primary_reporter_exit']==1 and typed['native_exit1_inference_only']
assert typed['Goal']==typed['writer_epoch']=='ACCEPTED_COMPONENT_OBSERVED_ONLY'
for key in ['runtime_pass','native_pass','FULL_pass','formal_acceptance','canonical_pre_run_receipt_independently_persisted']:assert typed[key] is False
pres=w['mu_sdk_r358_preserved_scope']
assert pres['current_formal_accepted']==0 and pres['historical_accepted_parents']==6 and pres['required_formal']==42
for k in ['Main_product_adopted','original_trial_financial_closed','overall_completion','counter_reset']:assert pres[k] is False
for k in ['original_trial_provider_requests','global_provider_requests']:assert pres[k] is None
for k in ['original_trial_business_open','original_trial_once_consumed','original_trial_clock_expired']:assert pres[k] is True
checks=dict(schema='researchos.independent-cp358-canonical-review.v1',decision='CP358_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY',
 canonical_checkpoint_ref=h['checkpoint_ref'],canonical_ownership_ref=pair['ownership_ref'],canonical_unchanged_refs=canonical_other,
 top_level_changed_keys=changed,old_815_failure_prefix_exact=True,appended_ordinals=list(range(818,826)),registered_failures=823,highest_registered_ordinal=825,
 separately_pending_826_not_registered=True,next_diagnostic_ordinal_as_root_report=827,counter_reset=False,automatic_retry=False,
 work_in_progress_exact_facts_plus_three_counters=True,all_other_CP_fields_unchanged=True,
 transaction_before_after_current_exact=True,transaction_exclusive_both_verified=True,root_tool_actual_outer=0,root_tool_actual_python=0,
 source_guard_entries=155,all_guard_entries_verified_final_path_closed=True,source_guard_retained_handles=0,
 six_independent_review_handoffs_and_manifests_verified=True,
 native820_actual_Go_exit=1,native820_Jobs_closed=2,native_failed_SQL_component_only=dict(tables=87,typed_row_digests=280,schema_objects=296,guard_groups_closed=11),
 typed_actual_counts=dict(source=49,parent_scopes=25,pass_nodes=61,fail_nodes=6,skip_nodes=0,native_leaf_failures=8,Jobs_closed=4,guard_groups_closed=5),
 diagnostic823_reporter_exit=1,diagnostic823_native_child_exit=None,diagnostic823_native_child_exit1_inference_only=True,
 Goal_and_epoch='ACCEPTED_COMPONENT_OBSERVED_ONLY',TTL_source_only=True,Main_accepted=False,native_accepted=False,Owner_accepted=False,
 original_business_accepted=False,formal_accepted=False,overall_completion=False,authority='NONE',new_mechanical_errors=0,
 limitations=['Review checks sealed component receipts and canonical transaction; no Go/native/SQL/model rerun','Prior T6 lacks independently persisted pre-run canonical receipt; preserved as false','Initial WAL only observation does not claim immutable DB or future sidecar closure'],
 scope='Canonical CP358 snapshot only',stop=True)
write('review.json',checks)
for ref in list(refs.values()):verify(ref)
write('verified-input-pins.json',dict(schema='researchos.independent-verified-pins.v1',references=list(refs.values()),count=len(refs),drift_count=0))
print(json.dumps(dict(decision=checks['decision'],references=len(refs),drift=0,guard_entries=155,canonical_checkpoint_ref=h['checkpoint_ref'],new_mechanical_errors=0),ensure_ascii=True))

