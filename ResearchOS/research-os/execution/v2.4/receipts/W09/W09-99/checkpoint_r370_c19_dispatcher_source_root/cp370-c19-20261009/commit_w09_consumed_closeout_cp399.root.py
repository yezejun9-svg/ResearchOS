"""Root closes consumed BR8 scopes and appends the immutable diagnostic suffix."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys,types
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];B=V/'receipts/W05/W05-99';R=V.parents[1]
RUN=W/'w09_br8_actual_root/actual-20261010-01';O=S/'cp399-w09-consumed-diagnostics1260-live1262'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
RT=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
PENDING=S/'cp399-w09-closeout-preparation-live1261/pending.root.json'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes'])
 return p,b
def doc(ref):return json.loads(checked(ref)[1])
def save(p,value):
 b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return pin(p)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
assert len(sys.argv)==7
review=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]))
audit=dict(path=sys.argv[4],sha256=sys.argv[5],bytes=int(sys.argv[6]))
pins={name:pin(path) for name,path in {
 'pending':PENDING,'core':CORE,'guard':GUARD,'tp':TP,'runtime':RT,
 'append':S/'ss-append-literal02-actual-root-20261010-01/committed.json',
 'append_guard':S/'ss-append-literal02-actual-root-20261010-01/source-guard.closed.json',
 'consume':RUN/'consume-fb16497eef2f43c2858a3e00df3ba31f/result.json',
 'consume_guard':RUN/'consume-fb16497eef2f43c2858a3e00df3ba31f/source-guard.closed.json',
 'assemble':RUN/'assemble-259182b5a7584e23bc58a273088e06cd/result.json',
 'assemble_guard':RUN/'assemble-259182b5a7584e23bc58a273088e06cd/source-guard.closed.json',
 'derive':RUN/'derive-7f3a638965a04675ac21860b0e09f01e/result.json',
 'derive_actual':S/'w09.literal02-derive-actual.actual-audit.root.json',
 'derive_guard':RUN/'derive-7f3a638965a04675ac21860b0e09f01e/source-guard.closed.json'}.items()}
assert pins['pending']['sha256']=='bc36aaf747792b319c2f41d78015496247bb40b4b02093d61f66df92c1edbd13'
assert pins['core']['sha256']=='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'
assert pins['guard']['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
assert pins['tp']['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
assert pins['runtime']['sha256']=='1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08'
pending=doc(pins['pending']);current=pending['current_canonical_refs']
assert current==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
rd=doc(review);assert rd['decision']=='ACCEPTED_W09_SS_APPEND_AND_DERIVED_CASES_IN_SCOPE' and rd['reviewer_id']=='codex:/root/backup_regression_resources'
assert rd['ss_append_receipt_ref']==pins['append'] and rd['derive_result_ref']==pins['derive'] and rd['accepted_case_ids']==['A06','C19']
runtime=module(RT,'root_closeout_actual_runtime');proofs=runtime.actual_audit(audit,'codex:/root/backup_regression_resources',review['sha256'])
proofs.extend(runtime.actual_audit(pins['derive_actual'],'codex:/root',pins['derive']['sha256']))
derive_actual_at=json.loads(checked(doc(pins['derive_actual'])['original_capture_ref'])[1].splitlines()[-1])['timestamp']
refs=[*pins.values(),review,audit,*proofs,*current[2:]]
for row in pending['pending']:refs.extend(row['source_fact_refs'])
cp=doc(current[0]);owners=doc(current[1]);sub=owners['card_path_bindings']['W09-99']['subtasks']
scopes={}
for selector in ('W09_FULL_FORMAL_CONSUMERS','W09_FULL_FORMAL_ASSEMBLY'):
 origin=sub[selector];scopes[selector]=doc(origin['scope_ref']);refs.append(origin['scope_ref'])
assert not O.exists();O.mkdir();(O/'canonical-journal').mkdir()
normalized={}
for ref in refs:
 p,b=checked(ref);new=dict(path=str(p),sha256=ref['sha256'],bytes=len(b))
 assert str(p) not in normalized or normalized[str(p)]==new;normalized[str(p)]=new
g=module(GUARD,'root_closeout_guard').SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 g.acquire(list(normalized.values()))
 runtime.actual_audit(audit,'codex:/root/backup_regression_resources',review['sha256'])
 for name in ('append_guard','consume_guard','assemble_guard','derive_guard'):
  d=doc(pins[name]);assert d['closed'] and d['retained_handles_count']==0 and not d['errors']
 consume=doc(pins['consume']);assert len(consume['processes'])==6 and consume['producer_rerun'] is False
 for proc in consume['processes']:
  ob=proc['observation'];cl=ob['job_cleanup'];assert proc['actual_exit']==ob['actual_exit']==0 and not ob['timed_out'] and ob['error'] is None
  assert cl['assigned_before_resume'] and cl['job_idle_confirmed'] and cl['primary_exit_confirmed'] and cl['handles_closed'] and cl['active_processes_last_observed']==0 and not cl['errors']
 derive=doc(pins['derive']);assert derive['integrity']=='PARTIAL' and derive['accepted_case_ids']==['A06','C19'] and derive['formal_cases_accepted']==2 and derive['required_formal_cases']==42 and derive['bridge_CAS']=={'status':'PASS'}
 assert next(x for x in derive['owners'] if x['task_id']=='W09')['integrity']=='VALID_ACCEPTED'
 now=datetime.now(timezone.utc).isoformat()
 closure=dict(schema='researchos.w09-br8-consumed-closeout.v1',issued_by='codex:/root',closed_at=now,review_ref=review,review_actual_audit_ref=audit,ss_append_receipt_ref=pins['append'],derive_result_ref=pins['derive'],consumer_result_ref=pins['consume'],assembly_result_ref=pins['assemble'],all_owned_jobs_closed=True,all_source_guards_closed=True,retained_handles_count=0,lease_extension=False,future_execution_authorized=False,automatic_retry=False,producer_replay=False,accepted_case_ids=['A06','C19'],formal_cases_accepted=2,required_formal_cases=42,overall_integrity='PARTIAL',goal_complete=False)
 closure_ref=save(O/'closure.root.json',closure)
 core=module(CORE,'root_closeout_core');tp=module(TP,'root_closeout_tp')
 def transform(before,ownership):
  assert before['revision']==398 and ownership['revision']==197
  c=copy.deepcopy(before);o=copy.deepcopy(ownership);co=[];oo=[]
  def change(d,ops,path,value):
   exists,old=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=old,after=copy.deepcopy(value)));core.put(d,path,value)
  merged,end=core.merge_pending(before,pending,current);assert end==1261
  change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],end)
  workers=copy.deepcopy(c['workers'])
  for selector in scopes:
   old=ownership['card_path_bindings']['W09-99']['subtasks'][selector];assert old['lease_status']=='ACTIVE'
   expiry=datetime.fromisoformat(old['lease_expires_at'].replace('Z','+00:00'));assert expiry<datetime.fromisoformat(now)
   scoped=scopes[selector];assert scoped['slice_id']==selector and scoped['issued_by']=='codex:/root'
   assert datetime.fromisoformat(scoped['created_at'].replace('Z','+00:00'))<expiry
   matches=[w for w in workers if w.get('slice_id')==selector and w.get('scope_ref')==old['scope_ref']];assert len(matches)==1 and matches[0]['lease_status']=='ACTIVE'
   new=copy.deepcopy(old);new.update(lease_status='CONSUMED_NO_FUTURE_EXECUTION',actual_closed=closure_ref,future_execution_authorized=False)
   change(o,oo,['card_path_bindings','W09-99','subtasks',selector],new)
   matches[0].update(lease_status='CONSUMED_NO_FUTURE_EXECUTION',actual_closed=closure_ref,future_execution_authorized=False)
  change(c,co,['workers'],workers)
  assert 'W09-99' not in before['accepted_steps']
  change(c,co,['accepted_steps'],before['accepted_steps']+['W09-99'])
  registration='W09(full current C19/A06 and gates, via independent actual review and Root SS append)'
  assert not any(x.startswith('W09(') for x in before['parent_tasks_accepted'])
  change(c,co,['parent_tasks_accepted'],before['parent_tasks_accepted']+[registration])
  formal=copy.deepcopy(before['current_effective_formal_status'])
  formal.update(derived_from_ref=pins['derive'],actual_at=derive_actual_at,formal_cases_accepted=2,accepted_case_ids=['A06','C19'],overall_integrity='PARTIAL',historical_parent_registrations=before['parent_tasks_accepted']+[registration],effective_parent_count_not_inferred=True,independent_closeout_review_ref=review,Root_scope_metadata_changed_after_derivation=True,Main_files_unchanged=True)
  change(c,co,['current_effective_formal_status'],formal)
  change(c,co,['next_command'],'Complete Main24 Git baseline Source review; Root prepare forty-target composition, issue exact apply grant after reviewing prepared bytes, then build/tests and independent actual review. W09 C19/A06 currently VALID_ACCEPTED, 2/42; all prior successes and failures preserved.')
  change(c,co,['work_in_progress','w09_br8_consumed_closeout'],dict(closure_ref=closure_ref,pending_ref=pins['pending'],registered_through=1260,next_original_failure_ordinal=1261,original_1254_1255_capture_incomplete=True,formal_acceptance_written_in_SS=True,goal_complete=False))
  for key,value in dict(revision=399,expected_previous_revision=398,updated_at=now,updated_by='codex:/root').items():change(c,co,[key],value)
  for key,value in dict(revision=198,updated_at=now,updated_by='codex:/root').items():change(o,oo,[key],value)
  assert core.inverse_operations(c,co)==before and core.inverse_operations(o,oo)==ownership
  assert c['failure_counters'][:len(before['failure_counters'])]==before['failure_counters']
  save(O/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
  return c,o
 result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
 receipt=save(O/'committed.root.json',dict(result,closure_ref=closure_ref,registered_through=1260,next_original_failure_ordinal=1261,counter_reset=False,goal_complete=False))
finally:
 closed=g.close();guard_ref=save(O/'source-guard.closed.root.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
assert current[2:]==[pin(V/n) for n in ('step_state.json','commands.json')]
print(json.dumps(dict(receipt_ref=receipt,guard_ref=guard_ref,current4=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],goal_complete=False),ensure_ascii=False))

