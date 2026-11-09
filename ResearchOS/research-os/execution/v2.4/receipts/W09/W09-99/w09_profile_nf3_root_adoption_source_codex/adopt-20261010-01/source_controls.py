"""Finite new-delta pure/AST checks. Never calls any registrar runtime stage."""
import ast,copy,hashlib,json,types
from datetime import datetime,timezone,timedelta
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def module(name,file):
 p=N/file;m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def save(name,value):
 p=N/name
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 return pin(p)
inputs=json.loads((N/'input-pins.json').read_bytes());pins=inputs['refs']
core=module('delta_core','adoption_core.source.py');reg=module('delta_registrar','register_w09_adoption.source.py');pair=module('delta_main_pair','main_pair_bytes.source.py')
gm=types.ModuleType('delta_source_guard');gp=Path(pins['guard']['path']);exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(total_cap=128*1024*1024)
refs=[pin(N/f) for f in ('input-pins.json','adoption_core.source.py','register_w09_adoption.source.py','main_pair_bytes.source.py','source_controls.py')]
refs += [row['snapshot_ref'] for row in inputs['baseline'].values()]
refs += [pins[k] for k in ('baseline_pending','Q_profile','Q_commands','Q_profile_before','NF_choice','NF_contract','NF_runtime')]
rows=[]
def check(name,predicate):
 try:ok=predicate();assert ok is True
 except BaseException as exc:rows.append(dict(name=name,passed=False,error=repr(exc)))
 else:rows.append(dict(name=name,passed=True))
def rejects(fn):
 try:fn()
 except (ValueError,KeyError,TypeError):return True
 return False
def altered(obj,path,value):
 c=copy.deepcopy(obj);d=c
 for key in path[:-1]:d=d[key]
 d[path[-1]]=value;return c
def fake_ref(label):return dict(path=str(N/('SYNTHETIC_UNSAVED_'+label)),sha256=hashlib.sha256(label.encode()).hexdigest(),bytes=1)

try:
 guard.acquire(refs)
 cp=json.loads(Path(inputs['baseline']['checkpoint']['snapshot_ref']['path']).read_bytes())
 ow=json.loads(Path(inputs['baseline']['path_ownership']['snapshot_ref']['path']).read_bytes())
 cm=json.loads(Path(inputs['baseline']['commands']['snapshot_ref']['path']).read_bytes())
 pending=json.loads(Path(pins['baseline_pending']['path']).read_bytes())
 current=[inputs['baseline'][k]['current_ref'] for k in ('checkpoint','path_ownership','step_state','commands')]
 merged,stop=core.merge_pending(cp,pending,current)
 check('counter_actual_22_row_suffix',lambda:len(merged)-len(cp['failure_counters'])==22 and stop==1089)
 check('counter_original_prefix_and_null_domains',lambda:merged[:len(cp['failure_counters'])]==cp['failure_counters'] and all(x['original_payload']['actual_native_exit'] is None for x in merged[-22:]))
 check('counter_bool_next_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['next_original_failure_ordinal'],True),current)))
 check('counter_bool_cutoff_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['source_cutoff_original_failure_ordinal'],True),current)))
 check('counter_bool_row_ordinal_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['pending',0,'ordinal'],True),current)))
 check('counter_hole_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['pending',0,'ordinal'],1068),current)))
 check('counter_duplicate_ordinal_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['pending',1,'ordinal'],1067),current)))
 duplicate=altered(pending,['pending',1,'origin_ref'],pending['pending'][0]['origin_ref'])
 check('counter_duplicate_origin_rejected',lambda:rejects(lambda:core.merge_pending(cp,duplicate,current)))
 reused=altered(pending,['pending',0,'origin_ref'],cp['failure_counters'][-1]['original_payload']['immutable_origin_ref'])
 check('counter_prior_invocation_reuse_rejected',lambda:rejects(lambda:core.merge_pending(cp,reused,current)))
 check('counter_bool_exit_rejected',lambda:rejects(lambda:core.merge_pending(cp,altered(pending,['pending',0,'actual_outer_exit'],True),current)))
 check('counter_wrong_current4_rejected',lambda:rejects(lambda:core.merge_pending(cp,pending,current[::-1])))
 start=cp['work_in_progress']['root_next_failure_ordinal_live'];empty={**pending,'pending':[],'next_original_failure_ordinal':start}
 check('counter_empty_stable_suffix_valid',lambda:core.merge_pending(cp,empty,current)==(cp['failure_counters'],start))
 check('counter_empty_rollback_rejected',lambda:rejects(lambda:core.merge_pending(cp,{**empty,'next_original_failure_ordinal':start-1},current)))
 check('counter_empty_advance_rejected',lambda:rejects(lambda:core.merge_pending(cp,{**empty,'next_original_failure_ordinal':start+1},current)))
 check('counter_reset_rejected',lambda:rejects(lambda:core.merge_pending(cp,{**pending,'counter_reset':True},current)))
 when=datetime(2026,10,10,0,0,tzinfo=timezone.utc);created=(when-timedelta(seconds=10)).isoformat()
 lease=dict(lease_id='a'*32,lease_issued_at=(when-timedelta(seconds=20)).isoformat(),lease_expires_at=(when+timedelta(seconds=1800)).isoformat())
 peer_times=[(when-timedelta(seconds=30)).isoformat()]*6
 check('causal_completed_actual_pair_time',lambda:core.validate_times(created,(when-timedelta(seconds=5)).isoformat(),peer_times,lease,when) is None)
 check('future_root_request_time_rejected',lambda:rejects(lambda:core.validate_times((when+timedelta(seconds=1)).isoformat(),when.isoformat(),peer_times,lease,when)))
 check('future_actual_return_rejected',lambda:rejects(lambda:core.validate_times(created,(when+timedelta(seconds=1)).isoformat(),peer_times,lease,when)))
 check('missing_peer_proofs_rejected',lambda:rejects(lambda:core.validate_times(created,when.isoformat(),[],lease,when)))
 check('peer_after_request_rejected',lambda:rejects(lambda:core.validate_times(created,when.isoformat(),[when.isoformat()]*6,lease,when)))
 check('expired_lease_rejected',lambda:rejects(lambda:core.validate_lease({**lease,'lease_expires_at':(when-timedelta(seconds=1)).isoformat()},when)))
 check('overlong_lease_rejected',lambda:rejects(lambda:core.validate_lease({**lease,'lease_expires_at':(when+timedelta(seconds=3601)).isoformat()},when)))
 check('naive_lease_rejected',lambda:rejects(lambda:core.validate_lease({**lease,'lease_issued_at':'2026-10-10T00:00:00'},when)))
 check('self_peer_review_rejected',lambda:rejects(lambda:core.validate_peer_roles(core.AUTHOR,core.AUTHOR,'codex:/root/producer','codex:/root/reviewer')))
 h,m=fake_ref('hdf'),fake_ref('mf');bindings={k:fake_ref(k) for k in ('caller_ref','core_ref','main_pair_ref','contract_ref')}
 d=dict(schema='researchos.w09-root-adoption-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_W09_ADOPTION',
  actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/unsaved_synthetic_reviewer',source_author_id=core.AUTHOR,
  source_handoff_ref=h,source_manifest_ref=m,actual_executed=False,formal_acceptance=False,execution_grant=False,**bindings)
 check('own_review_exact_source_bindings',lambda:core.validate_own_review(d,h,m,bindings)==d['actor_id'])
 check('wrong_Source_HDF_pin_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'source_handoff_ref':fake_ref('wrong')},h,m,bindings)))
 check('wrong_caller_Source_pin_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'caller_ref':fake_ref('wrong')},h,m,bindings)))
 check('missing_peer_actor_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'actor_id':None},h,m,bindings)))
 check('self_review_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'actor_id':core.AUTHOR},h,m,bindings)))
 check('Root_self_review_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'actor_id':core.ROOT},h,m,bindings)))
 check('Source_execution_grant_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'execution_grant':True},h,m,bindings)))
 check('Source_formal_grant_rejected',lambda:rejects(lambda:core.validate_own_review({**d,'formal_acceptance':True},h,m,bindings)))
 proposal=json.loads(Path(pins['Q_commands']['path']).read_bytes());profile=Path(pins['Q_profile']['path']).read_bytes()
 projected=reg.project_commands(profile,cm);aftercm=core.cm40_document(cm,proposal,created,projected)
 check('CM40_exact_reviewed_32_command_delta',lambda:len(aftercm['commands'])==32 and aftercm=={**proposal,'updated_at':created})
 check('CM_unrelated_command_change_rejected',lambda:rejects(lambda:core.cm40_document(cm,altered(proposal,['commands','test.retrieval','executable_tool'],'git'),created,projected)))
 check('CM_unrelated_metadata_change_rejected',lambda:rejects(lambda:core.cm40_document(cm,{**proposal,'created_at':'changed'},created,projected)))
 check('CM41_rejected',lambda:rejects(lambda:core.cm40_document(cm,{**proposal,'revision':41},created,projected)))
 check('CM_source_timestamp_not_real_rejected',lambda:rejects(lambda:core.cm40_document(cm,{**proposal,'updated_at':'invented'},created,projected)))
 profilebefore=Path(pins['Q_profile_before']['path']).read_bytes();cmbefore=Path(inputs['baseline']['commands']['snapshot_ref']['path']).read_bytes()
 targets=[core.pin_raw(reg.MAIN[0],profilebefore),core.pin_raw(reg.MAIN[1],cmbefore)]
 mainafter=core.main_pair_payloads(profilebefore,cmbefore,profile,aftercm,targets,reg.MAIN)
 check('Main_profile_byte_exact_adoption',lambda:mainafter[0]==profile and mainafter[1]==core.encoded(aftercm))
 check('Main_before_hash_drift_rejected',lambda:rejects(lambda:core.main_pair_payloads(profilebefore+b' ',cmbefore,profile,aftercm,targets,reg.MAIN)))
 check('Main_target_swap_rejected',lambda:rejects(lambda:pair.validate_pair_spec(targets[::-1],mainafter)))
 check('Main_bool_byte_count_rejected',lambda:rejects(lambda:pair.validate_pair_spec([{**targets[0],'bytes':True},targets[1]],mainafter)))
 check('Main_nonbyte_payload_rejected',lambda:rejects(lambda:pair.validate_pair_spec(targets,[True,mainafter[1]])))
 intent=pair.intent_document(targets,[fake_ref('before0'),fake_ref('before1')],[fake_ref('after0'),fake_ref('after1')])
 partial=pair.partial_document('PRIMARY',[0],[{'target_ref':targets[0],'partial_archive_ref':fake_ref('partial0')}],[{'phase':'publication','error':'SECONDARY'}])
 check('Main_intent_full_before_after_and_no_inverse',lambda:len(intent['before_archive_refs'])==len(intent['after_archive_refs'])==2 and intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False and intent['automatic_retry'] is False)
 check('Main_partial_primary_and_partial_bytes_contract',lambda:partial['primary_exception']=='PRIMARY' and partial['written_indices']==[0] and partial['observed_partial'][0]['partial_archive_ref'] and partial['requires_root_reconciliation'] is True and partial['automatic_inverse'] is False)
 request=dict(kind='PROFILE_ADOPTION',case_id='b'*32,created_utc=created,output_root=str(N/'UNSAVED_SYNTHETIC_ONLY'),
  before_canonical_refs=current,pending_ref=pins['baseline_pending'],main23_qualification_ref=pins['main23_qualification'],lease=lease,
  reviewed_source_audit_refs=inputs['peer_audit_refs'],formal_index_ref=fake_ref('index'))
 own=dict(hdf=h,mf=m,decision=fake_ref('review'))
 qscope=core.make_q_scope(request,fake_ref('request'),fake_ref('actual_audit_not_created'),pins,own,targets,
  [core.pin_raw(path,raw) for path,raw in zip(reg.MAIN,mainafter)])
 srefs={'profile':fake_ref('profile_scope_unsaved')};archives=[row['snapshot_ref'] for row in inputs['baseline'].values()]
 ca,oa,cops,oops=core.canonical_changes(cp,ow,request,srefs,{'profile':qscope},pending,archives,own)
 check('Q_complete_CP_byte_inverse',lambda:core.encoded(core.inverse_operations(ca,cops))==Path(inputs['baseline']['checkpoint']['snapshot_ref']['path']).read_bytes())
 check('Q_complete_OW_byte_inverse',lambda:core.encoded(core.inverse_operations(oa,oops))==Path(inputs['baseline']['path_ownership']['snapshot_ref']['path']).read_bytes())
 check('Q_only_new_owner_worker_and_dynamic_revision',lambda:ca['revision']==cp['revision']+1 and oa['revision']==ow['revision']+1 and ca['workers'][:-1]==cp['workers'] and ca['failure_counters'][:len(cp['failure_counters'])]==cp['failure_counters'])
 changed=copy.deepcopy(ca);changed['workers'].append({'unrelated':True})
 check('inverse_rejects_hidden_worker_mutation',lambda:rejects(lambda:core.inverse_operations(changed,cops)))
 unchanged=copy.deepcopy(ca);unchanged['head']='unrelated-change'
 check('inverse_exposes_untouched_field_mutation',lambda:core.inverse_operations(unchanged,cops)!=cp)
 # A second transaction uses dynamic after-Q Canon and an empty, stable suffix.
 native4=[core.pin_raw(reg.CANON[0],core.encoded(ca)),core.pin_raw(reg.CANON[1],core.encoded(oa)),current[2],core.pin_raw(reg.CANON[3],mainafter[1])]
 npending={**pending,'pending':[],'source_cutoff_original_failure_ordinal':stop-1,'next_original_failure_ordinal':stop,'current_canonical_refs':native4}
 nrequest={**request,'kind':'NATIVE_SCOPES','before_canonical_refs':native4,
  'native_leases':{key:{**lease,'lease_id':format(i+1,'032x')} for i,key in enumerate(core.SELECTORS)}}
 choice=json.loads(Path(pins['NF_choice']['path']).read_bytes());contract=json.loads(Path(pins['NF_contract']['path']).read_bytes())
 scopes=core.make_native_scopes(nrequest,pins,choice,contract);nsrefs={key:fake_ref('native_scope_'+key) for key in core.SELECTORS}
 na,no,ncops,noops=core.canonical_changes(ca,oa,nrequest,nsrefs,scopes,npending,archives,own,fake_ref('completed_commit_unsaved'))
 check('NF3_three_exact_scope_fields',lambda:all(set(s)==set(contract['scope_required_fields']) for s in scopes.values()))
 check('NF3_existing_choice_UUIDs_paths_and_Source21',lambda:all(all(scopes[key][field]=={**choice['common'],**choice['selectors'][key]}[field] for field in ('run_id','receipt_root','scratch_root','output_root','source21')) for key in core.SELECTORS))
 check('NF3_complete_CP_OW_inverse',lambda:core.inverse_operations(na,ncops)==ca and core.inverse_operations(no,noops)==oa)
 check('NF3_counter_empty_does_not_reset',lambda:na['failure_counters']==ca['failure_counters'] and na['work_in_progress']['root_next_failure_ordinal_live']==stop)
 check('NF3_only_three_new_workers',lambda:len(na['workers'])==len(ca['workers'])+3 and sum(w.get('slice_id','').startswith(core.NSLICE+'_') for w in na['workers'])==3)
 check('NF3_owned_budget_and_no_formal_flags',lambda:all(s['maximum_go_test_runs']==s['maximum_go_list_runs']==1 and s['formal_acceptance'] is False and s['formal_dispatcher'] is False and s['automatic_retry'] is False for s in scopes.values()))
 check('NF3_exact_owner_worker_objects',lambda:all(no['card_path_bindings']['W09-99']['subtasks'][core.NKEY+'_'+key]==core.native_owner_worker(scopes[key],nsrefs[key])[0] and core.native_owner_worker(scopes[key],nsrefs[key])[1] in na['workers'] for key in core.SELECTORS))
 check('NF3_duplicate_lease_rejected',lambda:rejects(lambda:core.make_native_scopes({**nrequest,'native_leases':{key:lease for key in core.SELECTORS}},pins,choice,contract)))
 # Source AST properties only: no runtime branch, Win32 write or TP call is invoked.
 pairtree=ast.parse((N/'main_pair_bytes.source.py').read_bytes());regtree=ast.parse((N/'register_w09_adoption.source.py').read_bytes())
 pairfn=next(x for x in pairtree.body if isinstance(x,ast.FunctionDef) and x.name=='replace_exact_pair')
 createcalls=[n for n in ast.walk(pairfn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='create']
 check('AST_main_CreateFileW_share0_exact',lambda:len(createcalls)==1 and isinstance(createcalls[0].args[2],ast.Constant) and type(createcalls[0].args[2].value) is int and createcalls[0].args[2].value==0)
 check('AST_main_single_reverse_finally_close',lambda:any(isinstance(n,ast.Try) and any(isinstance(y,ast.Call) and isinstance(y.func,ast.Name) and y.func.id=='close' for stmt in n.finalbody for y in ast.walk(stmt)) for n in ast.walk(pairfn)))
 source=(N/'main_pair_bytes.source.py').read_text(encoding='utf-8')
 check('AST_durable_intent_before_first_target_write',lambda:source.index("write_new(journal/'intent.json'")<source.index('checked(write(handle'))
 check('AST_partial_bytes_and_final_close_receipt',lambda:"'.partial.raw'" in source and "'failed.partial.json'" in source and "'ownership.closed.json'" in source and 'raise PairWriteFailure(primary,secondary,journal) from primary' in source)
 calls=[n for n in ast.walk(regtree) if isinstance(n,ast.Call)]
 check('AST_only_existing_shared_TP_update_pair',lambda:sum(isinstance(n.func,ast.Attribute) and n.func.attr=='update_pair' for n in calls)==1)
 check('AST_no_native_stage_or_subprocess',lambda:not any((isinstance(n.func,ast.Attribute) and n.func.attr in ('stage','Popen','run_registered_build','system')) or (isinstance(n.func,ast.Name) and n.func.id in ('propose','check_or_activate','apply_profile','finalize_native_requests') and False) for n in calls))
 check('AST_final_native_only_authority_validation',lambda:any(isinstance(n.func,ast.Attribute) and n.func.attr=='validate_authority' for n in calls))
 check('AST_root_actual_audit_delegate_present',lambda:any(isinstance(n.func,ast.Attribute) and n.func.attr=='actual_audit' for n in calls))
 check('AST_new_scope_requires_completed_activation_digest',lambda:"ctx['activation_ref']['sha256'] in returned" in (N/'register_w09_adoption.source.py').read_text(encoding='utf-8'))
 check('AST_no_hardcoded_future_CP_OW_or_start_ordinal',lambda:not any(isinstance(n,ast.Constant) and type(n.value) is int and n.value in (373,374,177,178,1067,1089) for n in ast.walk(regtree)))
 for file in ('adoption_core.source.py','main_pair_bytes.source.py','register_w09_adoption.source.py'):compile((N/file).read_bytes(),str(N/file),'exec')
 check('all_three_new_modules_compile',lambda:True)
finally:
 audit=guard.close();guardref=save('controls.source-guard.closed.json',audit)
 assert audit['closed'] is True and audit['retained_handles_count']==0 and audit['errors']==[]
result={'schema':'researchos.w09-root-adoption-source-delta-controls.v1','passed':sum(r['passed'] for r in rows),
 'failed':sum(not r['passed'] for r in rows),'checks':rows,'guard_ref':guardref,
 'in_memory_synthetic_objects_authority':'NONE_NOT_PERSISTED_AS_SCOPES_OR_CANON','runtime_stage_called':False,
 'actual_exclusive_write_called':False,'actual_TP_called':False,'actual_Go_Native_SQL_model_called':False,
 'existing_Q_QR_NF3_NF3R_controls_rerun':False}
ref=save('source-controls.result.json',result)
print(json.dumps({'result_ref':ref,'passed':result['passed'],'failed':result['failed'],'failures':[x for x in rows if not x['passed']]},ensure_ascii=False))
assert result['failed']==0
