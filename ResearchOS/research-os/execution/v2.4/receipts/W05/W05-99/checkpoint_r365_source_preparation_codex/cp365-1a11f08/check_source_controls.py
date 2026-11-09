import ast,copy,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 q=pin(v['path']);assert q==v;return q
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
facts=json.loads((N/'checkpoint.execution.facts.json').read_bytes());fr=pin(N/'checkpoint.execution.facts.json')
old=[Path(v['path']).read_bytes() for v in facts['canonical_refs']]
c0,o0=map(json.loads,old[:2]);before=copy.deepcopy(c0);before_ownership=copy.deepcopy(o0)
pending=facts['diagnostics'];checks=[]
def check(name,v):
 checks.append(dict(name=name,passed=bool(v)));assert v,name
tree=ast.parse((N/'checkpoint_c12_failed_archived.atomic.py').read_bytes())
selected=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in ('transform','raw_failure_array')]
check('exact_two_pure_functions_extracted',len(selected)==2)
class FixedNow:
 def isoformat(self):return 'SOURCE_ONLY_FIXED_TIMESTAMP'
class FixedDateTime:
 @staticmethod
 def now(_):return FixedNow()
env=dict(copy=copy,json=json,hashlib=hashlib,verify=verify,facts=facts,fr=fr,pending=pending,before=before,before_ownership=before_ownership,old=old,datetime=FixedDateTime,timezone=type('Z',(),{'utc':None}))
exec(compile(ast.Module(body=selected,type_ignores=[]),'<pure-source-controls>','exec'),env)
c,o=env['transform'](copy.deepcopy(c0),copy.deepcopy(o0))
check('CP365_OW169',c['revision']==365 and o['revision']==169)
check('exact_23_new_original_diagnostics',len(c['failure_counters'])==923 and [v['original_payload']['observed_ordinal'] for v in c['failure_counters'][900:]]==list(range(903,926)))
for i in range(900):check('old_failure_record_'+str(i)+'_unchanged',c['failure_counters'][i]==c0['failure_counters'][i])
keys=[v['origin_key'] for v in c['failure_counters'] if 'origin_key' in v]
check('new_origin_keys_unique_and_not_in_old',len({v['origin_key'] for v in c['failure_counters'][900:]})==23 and not ({v['origin_key'] for v in c['failure_counters'][900:]} & {v.get('origin_key') for v in c0['failure_counters']}))
check('original924_native_NULL_preserved',c['failure_counters'][-2]['original_payload']['actual_native_exit'] is None)
check('original925_not_native_failure',c['failure_counters'][-1]['original_payload']['actual_native_exit'] is None)
check('cutoff_high925_next926',c['work_in_progress']['r365_highest_observed_diagnostic_ordinal_at_cutoff']==925 and c['work_in_progress']['root_next_failure_ordinal_live']==926)
check('all_historical_workers_preserved',c['workers'][:-1]==c0['workers'])
check('exact_one_new_Root_C19_worker',c['workers'][-1]==facts['w09_scope_registration']['worker'])
check('active_parents_W05_W09_only',c['work_in_progress']['construction_active_parents']==['W05','W09'])
check('stale_authors_and_reviewers_cleared',c['work_in_progress']['mu_sdk_source_authors_active']==[] and c['work_in_progress']['mu_sdk_source_readonly_reviewers_active']==[])
check('two_old_current_writer_fields_cleared',c['work_in_progress']['configuration_handler_writer'] is None and c['work_in_progress']['desktop_http_exact15_source_writer'] is None)
sub=o['card_path_bindings']['W09-99']['subtasks']
check('old_Exact4_subtask_unchanged',sub['causal_test_source_exact4']==o0['card_path_bindings']['W09-99']['subtasks']['causal_test_source_exact4'])
check('new_scope_owner_root_source_writer_NULL',sub['c19_fixture_producer']['owner']=='codex:/root' and sub['c19_fixture_producer']['current_source_writer'] is None)
scope_ref=facts['w09_scope_registration']['scope_ref']
check('scope_pins_standard_three_keys',set(scope_ref)=={'path','sha256','bytes'} and Path(scope_ref['path']).is_absolute() and len(scope_ref['sha256'])==64)
check('owner_worker_same_scope_ref',sub['c19_fixture_producer']['scope_ref']==scope_ref==c['workers'][-1]['scope_ref'])
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
inverse_c=copy.deepcopy(c)
for k in ('expected_previous_revision','revision','updated_at','updated_by','note','workers','work_in_progress','failure_counters'):inverse_c[k]=copy.deepcopy(c0[k])
check('CP_full_old_byte_inverse',encoded(inverse_c)==old[0])
inverse_o=copy.deepcopy(o);del inverse_o['card_path_bindings']['W09-99']['subtasks']['c19_fixture_producer']
for k in ('revision','updated_at','updated_by'):inverse_o[k]=o0[k]
check('OW_full_old_byte_inverse',encoded(inverse_o)==old[1])
oldarr=env['raw_failure_array'](old[0]);newarr=env['raw_failure_array'](encoded(c))
check('old900_raw_array_prefix_exact',newarr.startswith(oldarr.rstrip()[:-1].rstrip()+','))
allowed=set(facts['work_in_progress'])|{'r365_registered_failure_count','r365_highest_observed_diagnostic_ordinal_at_cutoff','r365_next_failure_ordinal_at_cutoff','mu_sdk_r365_facts_ref','later_diagnostics_observed_after_cutoff','root_next_failure_ordinal_live','construction_active_parents'}
for k,v in c0['work_in_progress'].items():
 if k not in allowed:check('unrelated_wip_'+k,c['work_in_progress'][k]==v)
for k,v in c0.items():
 if k not in ('expected_previous_revision','revision','updated_at','updated_by','note','workers','work_in_progress','failure_counters'):check('unrelated_CP_'+k,c[k]==v)
for label,amend in [('wrong_CP_revision',lambda x,y:x.update(revision=363)),('wrong_OW_revision',lambda x,y:y.update(revision=167)),('duplicate_owner',lambda x,y:y['card_path_bindings']['W09-99']['subtasks'].update(c19_fixture_producer={})),('duplicate_worker',lambda x,y:x['workers'].append(copy.deepcopy(facts['w09_scope_registration']['worker']))),('changed_old_failure',lambda x,y:x['failure_counters'][0].update(source_only_mutation=True)),('unexpected_active_parents',lambda x,y:x['work_in_progress'].update(construction_active_parents=['W04']))]:
 x,y=copy.deepcopy(c0),copy.deepcopy(o0);amend(x,y)
 rejected=False
 try:env['transform'](x,y)
 except AssertionError:rejected=True
 check('reject_'+label,rejected)
env['pending']=[copy.deepcopy(pending[0]),copy.deepcopy(pending[0])]+copy.deepcopy(pending[2:])
rejected=False
try:env['transform'](copy.deepcopy(c0),copy.deepcopy(o0))
except AssertionError:rejected=True
check('reject_duplicate_original_origin',rejected)
check('four_canonical_original_bytes_unchanged',[Path(v['path']).read_bytes() for v in facts['canonical_refs']]==old)
for v in json.loads((N/'facts-inputs.original-pins.json').read_bytes()):check('original_input_unchanged_'+v['path'],pin(v['path'])==v)
proof=save('source-controls.json',dict(status='PASS',checks=checks,count=len(checks),execution_kind='AST_EXTRACTED_TRANSFORM_ON_IN_MEMORY_CLONES_ONLY',canonical_transaction_imported=False,writer_main_executed=False,actual_Git_Go_SQL_Native_API=False,formal_acceptance=False))
inverse=save('canonical-inverse.source-proof.json',dict(original_canonical_refs=facts['canonical_refs'],old900_semantic_and_raw_prefix_equal=True,CP_full_inverse_equal=True,OW_full_inverse_equal=True,SS_CM_byte_unchanged=True,allowed_CP_top_fields=['expected_previous_revision','revision','updated_at','updated_by','note','workers','work_in_progress','failure_counters'],allowed_OW_paths=['/revision','/updated_at','/updated_by','/card_path_bindings/W09-99/subtasks/c19_fixture_producer'],future_CP_clone_ref=dict(sha256=hashlib.sha256(encoded(c)).hexdigest(),bytes=len(encoded(c))),future_OW_clone_ref=dict(sha256=hashlib.sha256(encoded(o)).hexdigest(),bytes=len(encoded(o))),timestamp_is_synthetic_not_actual=True))
print(json.dumps(dict(status='PASS',check_count=len(checks),proof_ref=proof,inverse_ref=inverse)))
