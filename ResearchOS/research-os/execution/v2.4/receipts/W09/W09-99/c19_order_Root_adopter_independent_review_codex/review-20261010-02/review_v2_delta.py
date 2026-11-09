from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,types
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).parent
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
C=W/'nf5_c19_main_order_candidate_source_codex/candidate-20261010-01'
Q=W/'nf5_c19_main_order_independent_review_codex/review-candidate-20261010-01'
OLD=W/'c19_order_Root_adopter_independent_review_codex/review-20261010-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
script=S/'adopt_c19_order.Main.v2.root.py';assert pin(script)['sha256']=='0edf185c7e5e7f90122b5f50512d10ee9a40ccee01abe150cc81f6b6bd180a31' and pin(script)['bytes']==29628
guardpath=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
guardraw=guardpath.read_bytes();assert hashlib.sha256(guardraw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
source=json.loads((C/'HDF.json').read_bytes());review=json.loads((Q/'decision.json').read_bytes())
refs=[pin(p) for p in [script,guardpath,C/'HDF.json',C/'MF.json',C/'root-calling-adoption-contract.source.json',
 Q/'decision.json',Q/'HDF.json',Q/'MF.json',Path(source['guard_ref']['path']),Path(review['guard_ref']['path']),OLD/'decision.json',OLD/'original-adopter.source.py']]
gm=types.ModuleType('v2_stable_source_guard');exec(compile(guardraw,str(guardpath),'exec'),gm.__dict__);guard=gm.SourceReadGuard()
try:
 guard.acquire(refs)
 raw=guard.get_buffer(str(script));tree=ast.parse(raw);functions={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 names=['require','same_ref','proofs','exact_four','guarded']
 ns={'Path':Path,'ROOT':'codex:/root','THREAD':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','AFTER':'b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11',
 'CANON':[R/'execution/v2.4'/x for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']],
 'IMPORT_PINS':[(None,None)]*3,'unique':lambda x:x,'json':json}
 exec(compile(ast.Module(body=[functions[x] for x in names],type_ignores=[]),'EXACT_V2_AST_FUNCTIONS','exec'),ns)
 docs={}
 for ref in refs:
  if Path(ref['path']).suffix=='.json':docs[str(Path(ref['path']))]=json.loads(guard.get_buffer(ref['path']))
 ns['load_ref']=lambda ref:copy.deepcopy(docs[str(Path(ref['path']))])
 audit_calls=[]
 ns['imported']=lambda *args:types.SimpleNamespace(actual_audit=lambda *a:audit_calls.append(a))
 cfg=dict(source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),calling_contract_ref=pin(C/'root-calling-adoption-contract.source.json'),
 review_decision_ref=pin(Q/'decision.json'),review_handoff_ref=pin(Q/'HDF.json'),review_manifest_ref=pin(Q/'MF.json'),
 reviewer_actor=review['reviewer'],closed_review_guard_refs=[source['guard_ref'],review['guard_ref']],
 review_witness_binding_sha256=pin(Q/'decision.json')['sha256'],author_witness_ref={'synthetic':'author'},review_witness_ref={'synthetic':'review'})
 checks=[]
 def passed(name,cond,details):
  assert cond,name;checks.append(dict(id=name,passed=True,details=details,synthetic_or_static_only=True))
 ns['proofs'](cfg)
 passed('v2_exact_published_Backup_review_data_match',len(audit_calls)==2 and audit_calls[1][1:]==(review['reviewer'],pin(Q/'decision.json')['sha256']),
  'Only actual_audit primitive mocked; exact published HDF/MF/decision/contract/8checks/guards data satisfy new fixed gates.')
 changed=copy.deepcopy(docs[str(Q/'HDF.json')]);changed['contract_ref']=dict(changed['contract_ref'],sha256='f'*64)
 original=docs[str(Q/'HDF.json')];docs[str(Q/'HDF.json')]=changed
 try:ns['proofs'](cfg);rejected=False
 except ValueError as e:rejected=str(e)=='REVIEW_HDF_BINDING:contract_ref'
 docs[str(Q/'HDF.json')]=original
 passed('v2_new_review_HDF_contract_binding_rejects_drift',rejected,'New fixed HDF contract chain validated directly; prior6 matrix not replayed.')
 four=[dict(path=str(p),sha256='0'*64,bytes=1) for p in ns['CANON']]
 ns['exact_four'](four);four[1]=dict(four[0])
 try:ns['exact_four'](four);rejected=False
 except ValueError as e:rejected=str(e)=='EXACT_FOUR_LITERAL_CANONICAL_PATHS'
 passed('v2_new_exact4_duplicate_path_rejected',rejected,'Exact length plus ordered literal path gate.')
 records=[];writes=[0];original_error=ValueError('primary_action')
 class FakeGuard:
  def acquire(self,refs):pass
  def close(self):return dict(closed=True,errors=[],retained_handles_count=0)
 ns['imported']=lambda *args:types.SimpleNamespace(SourceReadGuard=lambda **kw:FakeGuard())
 def mocked_save(path,value):
  writes[0]+=1
  if writes[0]==1:raise OSError('closed_receipt_publication')
  records.append(copy.deepcopy(value));return {'synthetic':'record'}
 ns['save']=mocked_save
 def action():raise original_error
 try:ns['guarded']([],Path('D:/synthetic/guard.closed.json'),action);same=False
 except ValueError as e:same=e is original_error
 passed('v2_guarded_preserves_primary_and_structured_secondary',same and records[0]['primary_error']=="ValueError('primary_action')" and records[0]['cleanup_errors'][0]['stage']=='publish.guard.closed',
  'New aggregate evidence branch retains primary object and structured publication failure.')
 # Exact new adoption-finally AST only, no Root entry or Windows API invoked.
 adopt=functions['adopt'];tries=[x for x in adopt.body if isinstance(x,ast.Try)]
 main_try=next(x for x in tries if any(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='acquire' and isinstance(v.func.value,ast.Name) and v.func.value.id=='authority_guard' for v in ast.walk(x)))
 events=[];fin_ns=dict(handle=1,ctypes=types.SimpleNamespace(c_void_p=lambda _:types.SimpleNamespace(value=-1)),close_error=None,
 cleanup_errors=[],authority_closed=None,written=False,out=Path('D:/synthetic'),save=lambda *a:None,
 authority_guard=types.SimpleNamespace(close=lambda:events.append('authority_closed')))
 def exploding_close(h):events.append('target_close_raised');raise OSError('synthetic_FFI_close_failure')
 fin_ns['close']=exploding_close
 try:exec(compile(ast.Module(body=main_try.finalbody,type_ignores=[]),'EXACT_V2_ADOPT_FINALLY_ONLY','exec'),fin_ns)
 except OSError:pass
 passed('v2_unwrapped_target_CloseHandle_exception_skips_authority_guard_close',events==['target_close_raised'],
  'New Canon authority guard can remain retained if the preceding close(handle) raises; no real handle or Root stage ran.')
 atext=ast.get_source_segment(raw.decode(),functions['authority'])
 passed('v2_owner_flags_branch_still_unclosed_static',all(s not in atext for s in ['one_shot_consumed','future_execution_permitted','lease_status','current_source_writer']),
  'Original AUTHORITY-002 owner/worker binding branch is unchanged; prior mock not repeated.')
 save('delta-controls.json',dict(checks=checks,count=len(checks),old6_controls_rerun=False,Root_stage_calls=0,actual_audit_calls=0,Native_Go_SQL_TP_calls=0))
 save('input-pins.json',dict(refs=refs,stable_Source_only=True,live_Canon_Main_not_held=True))
 save('original-v2.source.py',raw,True)
 save('findings.json',[
 dict(id='C19-ADOPT-AUTHORITY-002',status='PARTIALLY_FIXED_REMAINS_OPEN',priority=1,line=224,end_line=225,
 repaired=['fixed exact4 paths/length','exact request/scope/contract target/output refs','Canon-only guard acquired before exclusive Main target and released afterward on normal close'],
 remaining='owner/worker current_source_writer, lease issued/expiry equality, lease_status and one_shot_consumed/future_execution_permitted remain unchecked',
 fix='Set explicit active/unconsumed fields in register; require both records match Scope times and Root writer, ACTIVE/False/True; close marks CLOSED/consumed/no future execution.'),
 dict(id='C19-ADOPT-FAILURE-003',status='PARTIALLY_FIXED_REMAINS_OPEN',priority=2,line=410,end_line=416,
 repaired=['guarded collects primary and secondary failures','adopt primary re-raised with traceback after most cleanup/publication failures'],
 remaining='close(handle) executes outside try/except in finally; an FFI/Python exception skips authority_guard.close and all subsequent failure recording',
 fix='Wrap target CloseHandle in try/except and append its exception to cleanup_errors, then always attempt authority_guard.close; never fabricate successful target closure.')])
 save('decision.json',dict(schema='researchos.c19-root-adopter-independent-source-decision.v1',
 actor_id='codex:/root/attach_restore_independent_review',actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',source_author='codex:/root',
 decision='REQUEST_CHANGES_SOURCE_ONLY',source_ref=refs[0],prior_decision_ref=pin(OLD/'decision.json'),
 C19_ADOPT_REVIEW_001='CLOSED_SOURCE_IN_SCOPE',C19_ADOPT_AUTHORITY_002='PARTIALLY_FIXED_OPEN',C19_ADOPT_FAILURE_003='PARTIALLY_FIXED_OPEN',
 findings_ref=pin(N/'findings.json'),controls_ref=pin(N/'delta-controls.json'),old6_controls_rerun=False,
 actual_Backup_review_data_bound=True,actual_audit_primitive_invoked=False,CAND_independent_review_substituted=False,
 Native_Go_SQL_TP_RootStage_calls=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,Main_adopted=False,STOP=True))
finally:
 closed=guard.close();save('input-guard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
assert all(pin(ref['path'])==ref for ref in refs)
print(json.dumps(dict(decision_ref=pin(N/'decision.json'),guard_ref=pin(N/'input-guard.closed.json'),inputs=len(refs),guardclosed0=True),ensure_ascii=False))

