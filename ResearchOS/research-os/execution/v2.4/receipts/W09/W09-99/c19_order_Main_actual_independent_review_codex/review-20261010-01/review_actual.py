from pathlib import Path
from datetime import datetime
import hashlib,json,re,types,sys,copy
N=Path(__file__).parent
R=next(p for p in N.parents if (p/'AGENTS.md').is_file())
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
A=S/'c19-order-Main-adoption-3f1955cfb53d4d25bbb059db06007f51'
ROOT='codex:/root';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ACTOR='codex:/root/attach_restore_independent_review'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def samebytes(a,b):return a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def read(p):return json.loads(Path(p).read_bytes())
refs={}
def add(ref):
 p=Path(ref['path']);actual=pin(p);assert actual==ref,('pin',ref,actual)
 if str(p) in refs:assert refs[str(p)]==ref
 refs[str(p)]=ref;return read(p) if p.suffix=='.json' else p.read_bytes()
def values(v,depth=0):
 if depth>10:return
 yield v
 if isinstance(v,dict):
  for x in v.values():yield from values(x,depth+1)
 elif isinstance(v,list):
  for x in v:yield from values(x,depth+1)
 elif isinstance(v,str):
  try:d=json.loads(v)
  except (ValueError,TypeError):return
  yield from values(d,depth+1)
def closed(d):
 assert d['closed'] is True and d['retained_handles_count']==0 and d['errors']==[]
 assert all(e.get('closed') is True and e.get('verified') is True for e in d.get('entries',[]))
req=add(pin(A/'adoption.actual.request.root.json'));adopt=add(pin(A/'adoption.closed.root.json'));consumed=add(pin(A/'registration.closed.root.json'))
for p in A.rglob('*'):
 if p.is_file():add(pin(p))
for key in ['source_handoff_ref','source_manifest_ref','calling_contract_ref','review_handoff_ref','review_manifest_ref','review_decision_ref','Root_adopter_review_handoff_ref','Root_adopter_review_manifest_ref','Root_adopter_review_decision_ref','Root_adopter_accepted_Source_ref','Root_adopter_acceptance_input_guard_closed_ref','scope_ref','sourcecandidate_ref','before_source_ref','config_ref']:
 add(req[key])
for key in ['source_manifest_ref','review_manifest_ref','Root_adopter_review_manifest_ref']:
 for ref in read(req[key]['path'])['members']:add(ref)
for ref in req['closed_review_guard_refs']:closed(add(ref))
target=Path(req['target_path']);add(adopt['actual_Main_ref'])
for ref in req['current_canonical_refs'][2:]:add(ref)
root_events=[]
def audit(ref,actor,digest,chunk=None,operation=None):
 d=add(ref);raw=add(d['original_capture_ref']);lines=raw.splitlines(keepends=True)
 assert len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==d['original_line_sha256']
 with Path(d['source_audit_path']).open('rb') as f:
  for offset,line in zip(d['source_line_offsets'],lines):
   f.seek(offset);assert f.read(len(line))==line
 rows=[json.loads(x) for x in lines];head,call,result=rows
 assert head['type']=='session_meta' and head['payload']['id']==THREAD
 assert d['actor_id']==actor and d['binding_sha256']==digest
 assert digest in (lines[1]+lines[2]).decode('utf-8')
 if actor!=ROOT:
  assert call['type']=='inter_agent_communication_metadata' and result['payload']['type']=='agent_message'
  assert result['payload']['author']==actor.removeprefix('codex:') and result['payload']['recipient']=='/root'
  assert result['ordinal']==call['ordinal']+1 and result['timestamp']==call['timestamp'] and result['metadata']['client_authored'] is False
 else:
  assert call['payload']['call_id']==result['payload']['call_id']
 if chunk:
  matches=[v for v in values(result['payload']['output']) if isinstance(v,dict) and v.get('chunk_id')==chunk]
  assert len(matches)==1;actual=matches[0]
  assert actual['exit_code']==0 and 'ROOT_ACTUAL_PYTHON_EXIT=0' in actual['output']
  cin=call['payload'].get('input',call['payload'].get('arguments',''))
  assert 'adopt_c19_order.Main.v3.root.py' in cin and (' '+operation+' ') in cin
  assert req['Root_adopter_accepted_Source_ref']['sha256']==pin(S/'adopt_c19_order.Main.v3.root.py')['sha256']
  root_events.append(dict(operation=operation,chunk_id=chunk,actual_outer_exit=0,actual_Python_exit=0,
   Native_exit=None,Go_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,
   Root_thread_id=head['payload']['id'],source_audit_path=d['source_audit_path'],
   call_id=call['payload']['call_id'],call_timestamp=call['timestamp'],result_timestamp=result['timestamp'],audit_ref=ref))
 return dict(actor_id=actor,session_id=head['payload']['id'],call_id=call['payload'].get('call_id'),audit_ref=ref)
source=read(req['source_handoff_ref']['path']);review=read(req['review_decision_ref']['path']);rv3=read(req['Root_adopter_review_decision_ref']['path'])
audits=[]
for key,actor,digest in [
 ('author_witness_ref',source['source_author'],source['decision_ref']['sha256']),
 ('review_witness_ref',req['reviewer_actor'],req['review_decision_ref']['sha256']),
 ('Root_adopter_actual_peer_witness_ref',ACTOR,req['Root_adopter_review_decision_ref']['sha256'])]:
 audits.append(audit(req[key],actor,digest))
for name,chunk,op,digest in [
 ('registration','6fabe4','register',pin(A/'adoption.actual.request.root.json')['sha256']),
 ('adoption-closed','5676e1','adopt',pin(A/'adoption.closed.root.json')['sha256']),
 ('consumed-closure','cc6c5c','close',pin(A/'registration.closed.root.json')['sha256'])]:
 audit(pin(S/('w09.c19-order-Main-'+name+'.actual-audit.root.json')),ROOT,digest,chunk,op)
# Guard stable sources only; historical canonical states are represented by TP archived bytes.
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
assert pin(gp)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
m=types.ModuleType('independent_c19_main_guard');m.__file__=str(gp);sys.modules[m.__name__]=m;exec(compile(gp.read_bytes(),str(gp),'exec'),m.__dict__)
g=m.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=512*1024*1024)
checks=[]
def check(name,condition,evidence):
 assert condition,name
 checks.append(dict(name=name,passed=True,evidence=evidence))
try:
 g.acquire(list(refs.values()))
 check('exact_v3_source_independently_accepted',rv3['decision']=='ACCEPTED_SOURCE_ONLY' and read(req['Root_adopter_review_handoff_ref']['path'])['accepted_source_ref']==req['Root_adopter_accepted_Source_ref'] and req['Root_adopter_accepted_Source_ref']['sha256']=='22db0c829a38b374d95521f8aab896f47b81b54be5277631c389344152468103',req['Root_adopter_review_decision_ref'])
 check('candidate_real_nonauthor_acceptance',review['decision']=='ACCEPTED_SOURCE_ONLY' and review['reviewer']==req['reviewer_actor']=='codex:/root/backup_regression_resources' and source['source_author']=='codex:/root/full_w09_source_review' and review['checks_passed']==8 and all(x['passed'] for x in review['checks']),audits)
 before=Path(adopt['before_archive_ref']['path']).read_bytes();after=Path(adopt['candidate_archive_ref']['path']).read_bytes()
 old=b'selected = GROUPS[check] if check else list(TESTS)'
 new=b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
 check('complete_14509_to_14545_bytes_and_inverse',len(before)==14509 and len(after)==14545 and before.count(old)==after.count(new)==1 and before.replace(old,new,1)==after and after.replace(new,old,1)==before and before==Path(req['before_source_ref']['path']).read_bytes() and after==target.read_bytes()==Path(req['sourcecandidate_ref']['path']).read_bytes(),dict(before=adopt['before_archive_ref'],after=adopt['candidate_archive_ref'],current=adopt['actual_Main_ref']))
 for p in A.glob('*guard.closed.json'):closed(read(p))
 for ref in req['closed_review_guard_refs']:closed(read(ref['path']))
 closed(read(req['Root_adopter_acceptance_input_guard_closed_ref']['path']))
 held=read(A/'canonical-authority-guard.closed.json')
 assert [{k:e[k] for k in ('path','sha256','bytes')} for e in held['entries']]==req['current_canonical_refs']
 targetclose=read(A/'target-handle.closed.json');intent=read(A/'intent.root.json');committed=read(A/'committed.while-owned.json')
 check('exclusive_target_and_canonical_authority_closed0',targetclose==dict(target_handle_closed=True,CloseHandle_error=None,actual_write_complete=True) and intent['mandatory_share_mode']==0 and committed['actual_write_complete'] and committed['actual_readback_while_exclusive'] and committed['current_canonical_refs_held_during_write']==req['current_canonical_refs'] and committed['Source_review_input_guards_closed_before_write'] and held['share_mode']=='FILE_SHARE_READ_ONLY',dict(intent=pin(A/'intent.root.json'),committed=pin(A/'committed.while-owned.json'),target_close=pin(A/'target-handle.closed.json'),canonical_close=adopt['canonical_authority_guard_closed_ref']))
 states=[]
 for journal,before_refs,after_refs in [(req['registration_result']['transaction_journal'],req['expected_current4'][:2],req['current_canonical_refs'][:2]),(consumed['committed']['transaction_journal'],req['current_canonical_refs'][:2],[consumed['committed']['checkpoint_ref'],consumed['committed']['ownership_ref']])]:
  j=Path(journal);ji=read(j/'intent.json');jc=read(j/'committed.json')
  assert ji['expected_refs']==before_refs and jc['after_refs']==after_refs and jc['written_indices']==[0,1] and jc['both_verified_while_exclusively_held'] is True and ji['mandatory_share_mode']==0
  for i in range(2):
   assert samebytes(pin(j/(str(i)+'.before.json')),before_refs[i]) and samebytes(pin(j/(str(i)+'.after.proposed.json')),after_refs[i])
  states.append(tuple(read(j/name) for name in ('0.before.json','1.before.json','0.after.proposed.json','1.after.proposed.json')))
 cp0,ow0,cp1,ow1=states[0];cp1b,ow1b,cp2,ow2=states[1]
 assert cp1==cp1b and ow1==ow1b
 key=req['owner_key'];scope=read(req['scope_ref']['path'])
 activeowner=ow1['card_path_bindings']['W09-99']['subtasks'][key]
 workers=[x for x in cp1['workers'] if x.get('slice_id')==key];assert len(workers)==1
 for record in (activeowner,workers[0]):
  assert record['owner']==record['current_source_writer']==ROOT and record['scope_ref']==req['scope_ref']
  assert record['state']=='ROOT_REGISTERED_SINGLE_TARGET_MAIN_ADOPTION' and record['lease_status']=='ACTIVE'
  assert record['lease_id']==scope['lease_id'] and record['lease_issued_at']==scope['lease_issued_at'] and record['lease_expires_at']==scope['lease_expires_at']
  assert record['one_shot_consumed'] is False and record['future_execution_permitted'] is True
 assert scope['issued_by']==ROOT and scope['root_thread_id']==THREAD and scope['request_id']==req['request_id'] and scope['write_targets']==[str(target)] and scope['execution_limit']==1
 assert scope['sourcecandidate_ref']==req['sourcecandidate_ref'] and scope['independent_review_ref']==req['review_decision_ref']
 for event in root_events[1:]:
  assert datetime.fromisoformat(scope['lease_issued_at'])<=datetime.fromisoformat(event['call_timestamp'])<datetime.fromisoformat(event['result_timestamp'])<datetime.fromisoformat(scope['lease_expires_at'])
 check('historical_root_scope_owner_worker_issuer_entry_lease',True,dict(scope_ref=req['scope_ref'],registration_archive=req['registration_result']['transaction_journal'],Root_events=root_events))
 closedowner=ow2['card_path_bindings']['W09-99']['subtasks'][key];closedworkers=[x for x in cp2['workers'] if x.get('slice_id')==key];assert len(closedworkers)==1
 for record in (closedowner,closedworkers[0]):
  assert record['state']=='CLOSED_ACTUAL_SINGLE_TARGET_MAIN_ADOPTION' and record['current_source_writer'] is None and record['one_shot_consumed'] is True and record['future_execution_permitted'] is False and record['lease_status']=='CLOSED'
  assert record['actual_adoption_ref']==pin(A/'adoption.closed.root.json')
 check('consumed_once_no_future_permission',consumed['scope_consumed'] is True and consumed['future_execution_permitted'] is False,dict(receipt_ref=pin(A/'registration.closed.root.json'),closure_archive=consumed['committed']['transaction_journal']))
 # Exactly the registered worker, subtask, wip pointer, revision and metadata may differ.
 def registration_projection(cp,ow):
  c=copy.deepcopy(cp);o=copy.deepcopy(ow)
  c['workers']=[x for x in c['workers'] if x.get('slice_id')!=key];c['work_in_progress'].pop('c19_order_Main_adoption_scope_ref',None)
  o['card_path_bindings']['W09-99']['subtasks'].pop(key,None)
  for d in(c,o):
   for field in ('revision','expected_previous_revision','updated_at','updated_by'):d.pop(field,None)
  return c,o
 assert registration_projection(cp0,ow0)==registration_projection(cp1,ow1)
 def closure_projection(cp,ow):
  c,o=registration_projection(cp,ow);c['work_in_progress'].pop('c19_order_Main_adoption_closed_ref',None);return c,o
 assert closure_projection(cp1,ow1)==closure_projection(cp2,ow2)
 check('register_adopt_close_separate_exact_canonical_deltas',cp0['revision']==380 and cp1['revision']==381 and cp2['revision']==382 and ow0['revision']==184 and ow1['revision']==185 and ow2['revision']==186 and req['expected_current4'][2:]==req['current_canonical_refs'][2:] and adopt['Canon_unchanged'] is True,dict(Root_events=root_events,canon_revisions=[380,381,382],ownership_revisions=[184,185,186]))
 check('product_and_formal_authority_unchanged',scope['product_execution_permitted'] is False and scope['formal_acceptance'] is False and adopt['formal_acceptance'] is False and adopt['formal_case_accepted_delta']==0 and adopt['four_fresh_Native_and_six_consumers_required'] is True,dict(Source21_qualification_not_accepted_by_this_review=True,Native_or_Mode_result=False,formal_case_accepted_delta=0))
finally:
 guardclosed=g.close();save('input-guard.closed.json',guardclosed)
closed(guardclosed)
save('input-pins.json',list(refs.values()))
decision=save('decision.json',dict(schema='researchos.c19-Main-actual-independent-component-review.v1',decision='ACCEPTED_ACTUAL_MAIN_ADOPTION_COMPONENT_ONLY',reviewer=ACTOR,Root_executor=ROOT,Root_thread_id=THREAD,checks=checks,checks_passed=len(checks),Root_actual_events=root_events,peer_actual_audits=audits,request_ref=pin(A/'adoption.actual.request.root.json'),adoption_ref=pin(A/'adoption.closed.root.json'),consumed_ref=pin(A/'registration.closed.root.json'),guard_ref=pin(N/'input-guard.closed.json'),reviewer_Native_SQL_Go_TP_Rootstage_calls=0,Main_Canon_Scope_writes=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,STOP=True))
print(json.dumps(dict(decision_ref=decision,checks_passed=len(checks),guard_handles=len(refs),guards_closed0=True,Root_actual_events=root_events),ensure_ascii=False))

