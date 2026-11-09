from pathlib import Path
import ast,copy,difflib,hashlib,json,types
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).parent
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
script=S/'adopt_c19_order.Main.v3.root.py';assert pin(script)['sha256']=='22db0c829a38b374d95521f8aab896f47b81b54be5277631c389344152468103' and pin(script)['bytes']==30446
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=gp.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
refs=[pin(p) for p in [script,N/'original-v2.source.py',N/'delta-controls.json',N/'decision.json',gp]]
gm=types.ModuleType('v3_delta_source_guard');exec(compile(graw,str(gp),'exec'),gm.__dict__);guard=gm.SourceReadGuard()
try:
 guard.acquire(refs)
 raw=guard.get_buffer(str(script));old=guard.get_buffer(str(N/'original-v2.source.py'))
 tree,oldtree=ast.parse(raw),ast.parse(old)
 funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 oldfuncs={x.name:x for x in oldtree.body if isinstance(x,ast.FunctionDef)}
 dumped=lambda x:ast.dump(x,include_attributes=False)
 changed=[name for name in funcs if dumped(funcs[name])!=dumped(oldfuncs[name])]
 assert set(changed)=={'authority','register','adopt','close_registration'}
 # Ensure v3 adopt changed only its main try/finally: exact same preconditions/write/CAS/exception body.
 def adoption_try(f):
  return next(x for x in f.body if isinstance(x,ast.Try) and any(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='acquire' and isinstance(v.func.value,ast.Name) and v.func.value.id=='authority_guard' for v in ast.walk(x)))
 clean,oldclean=copy.deepcopy(funcs['adopt']),copy.deepcopy(oldfuncs['adopt'])
 adoption_try(clean).finalbody=[];adoption_try(oldclean).finalbody=[]
 assert dumped(clean)==dumped(oldclean)
 auth=copy.deepcopy(funcs['authority']);loop=next(x for x in auth.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='record')
 auth.body.remove(loop);assert dumped(auth)==dumped(oldfuncs['authority'])
 reg=copy.deepcopy(funcs['register'])
 owner_assign=next(x for x in ast.walk(reg) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owner' for t in x.targets))
 new_fields={'lease_status','one_shot_consumed','future_execution_permitted'}
 values={k.arg:ast.literal_eval(k.value) for k in owner_assign.value.keywords if k.arg in new_fields}
 assert values==dict(lease_status='ACTIVE',one_shot_consumed=False,future_execution_permitted=True)
 owner_assign.value.keywords=[k for k in owner_assign.value.keywords if k.arg not in new_fields]
 assert dumped(reg)==dumped(oldfuncs['register'])
 close=copy.deepcopy(funcs['close_registration'])
 update=next(v for v in ast.walk(close) if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='update')
 assert ast.literal_eval(next(k.value for k in update.keywords if k.arg=='lease_status'))=='CLOSED'
 update.keywords=[k for k in update.keywords if k.arg!='lease_status']
 assert dumped(close)==dumped(oldfuncs['close_registration'])
 save('v2-to-v3.diff',''.join(difflib.unified_diff(old.decode().splitlines(True),raw.decode().splitlines(True),fromfile='pinned-v2',tofile='pinned-v3')).encode(),True)
 ns={};exec(compile(ast.Module(body=[funcs['require']],type_ignores=[]),'V3_REQUIRE_ONLY','exec'),ns)
 base=dict(current_source_writer='codex:/root',lease_issued_at='issued',lease_expires_at='expires',lease_status='ACTIVE',one_shot_consumed=False,future_execution_permitted=True)
 scope=dict(lease_issued_at='issued',lease_expires_at='expires')
 def run_fields(owner,worker):
  local=dict(ns,ROOT='codex:/root',owner=owner,workers=[worker],scope=scope)
  exec(compile(ast.Module(body=[loop],type_ignores=[]),'EXACT_V3_NEW_AUTHORITY_LOOP_ONLY','exec'),local)
 run_fields(copy.deepcopy(base),copy.deepcopy(base))
 mutations={'current_source_writer':'codex:/root/other','lease_issued_at':'other','lease_expires_at':'expired','lease_status':'REVOKED','one_shot_consumed':True,'future_execution_permitted':False}
 rejected=[]
 for position in ('owner','worker'):
  for key,value in mutations.items():
   owner,worker=copy.deepcopy(base),copy.deepcopy(base)
   (owner if position=='owner' else worker)[key]=value
   try:run_fields(owner,worker);okay=False
   except ValueError as e:okay=str(e)=='CURRENT_UNREVOKED_UNCONSUMED_ROOT_WRITER'
   assert okay,(position,key);rejected.append(position+'.'+key)
 # Execute only the repaired finalbody with synthetic FFI failure and synthetic guard.
 events=[];records=[];original_primary=ValueError('prior-primary')
 def target_close(_):events.append('target-close-error');raise OSError('synthetic_FFI_close_failure')
 def authority_close():
  events.append('authority-close');return dict(closed=True,errors=[],retained_handles_count=0)
 def saved(path,value):records.append((str(path),copy.deepcopy(value)));return {'synthetic':'saved'}
 fin_ns=dict(handle=1,ctypes=types.SimpleNamespace(c_void_p=lambda _:types.SimpleNamespace(value=-1)),close_error=None,
 cleanup_errors=[],authority_closed=None,written=True,out=Path('D:/synthetic'),save=saved,close=target_close,
 authority_guard=types.SimpleNamespace(close=authority_close),primary=(original_primary,None))
 exec(compile(ast.Module(body=adoption_try(funcs['adopt']).finalbody,type_ignores=[]),'EXACT_V3_REPAIRED_FINALLY_ONLY','exec'),fin_ns)
 assert events==['target-close-error','authority-close']
 assert fin_ns['primary'][0] is original_primary and fin_ns['cleanup_errors'][0]['stage']=='close.target'
 assert fin_ns['authority_closed']['closed'] is True
 target_observation=next(v for p,v in records if p.endswith('target-handle.closed.json'))
 assert target_observation['target_handle_closed'] is False and target_observation['CloseHandle_error'] is not None
 save('v3-delta-controls.json',dict(branch_controls=[
  dict(id='v3_owner_worker_exact_active_unconsumed_fields',passed=True,baseline_passed=True,rejected_field_mutations=rejected),
  dict(id='v3_FFI_target_close_exception_still_closes_Canon_authority',passed=True,events=events,
   primary_preserved=True,target_closed_not_fabricated=True,authority_close_observed=True)],
 exact_AST_changed_functions=changed,all_other_v2_source_unchanged=True,only_new_two_branches_executed=True,
 v2_successful_prefix_not_rerun=True,old6_not_rerun=True,real_handles_in_mock=False,Native_Go_SQL_TP_RootStage_actual_audit_calls=0))
 save('original-v3.source.py',raw,True)
 save('v3-input-pins.json',dict(refs=refs,stable_Source_only=True,live_Main_Canon_not_held=True))
 save('decision-v3.json',dict(schema='researchos.c19-root-adopter-independent-source-decision.v1',
 actor_id='codex:/root/attach_restore_independent_review',actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',source_author='codex:/root',
 decision='ACCEPTED_SOURCE_ONLY',accepted_source_ref=refs[0],source_ref=refs[0],prior_v1_accepted=False,prior_v2_accepted=False,
 prior_v2_decision_ref=pin(N/'decision.json'),reused_v2_prefix_ref=pin(N/'delta-controls.json'),v3_delta_controls_ref=pin(N/'v3-delta-controls.json'),
 findings=dict(C19_ADOPT_REVIEW_001='CLOSED_SOURCE_IN_SCOPE',C19_ADOPT_AUTHORITY_002='CLOSED_SOURCE_IN_SCOPE',C19_ADOPT_FAILURE_003='CLOSED_SOURCE_IN_SCOPE'),
 acceptance_scope='Exact v3 Root adopter Source and three prior findings only; no actual registration/adoption/closure or runtime execution was performed by reviewer.',
 CAND_independent_review_substituted=False,Root_actual_peer_preflight_not_rerun=True,
 actual_Main_adoption_proven=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False,RootScope_issued=False,
 Native_Go_SQL_TP_RootStage_actual_audit_calls=0,STOP=True))
finally:
 closed=guard.close();save('v3-input-guard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
assert all(pin(ref['path'])==ref for ref in refs)
print(json.dumps(dict(decision_ref=pin(N/'decision-v3.json'),guard_ref=pin(N/'v3-input-guard.closed.json'),inputs=len(refs),guardclosed0=True),ensure_ascii=False))

