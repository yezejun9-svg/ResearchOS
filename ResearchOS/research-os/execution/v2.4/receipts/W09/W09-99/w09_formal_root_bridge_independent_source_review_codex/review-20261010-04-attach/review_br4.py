from pathlib import Path
from datetime import datetime,timezone
import ast,copy,json,hashlib,types,sys
N=Path(__file__).parent;W=N.parents[1];R=next(p for p in N.parents if (p/'AGENTS.md').is_file())
S=W/'w09_formal_root_bridge_source_codex/bridge-20261010-04'
ROOT='codex:/root';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUTHOR='codex:/root/full_w09_source_review';BACKEND='/root/full_w09_source_review'
REVIEWER='/root/attach_restore_independent_review'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def read(p):return json.loads(Path(p).read_bytes())
refs={}
def add(ref):
 assert pin(ref['path'])==ref,ref
 refs[str(Path(ref['path']))]=ref
 return read(ref['path'])
def allrefs(v):
 if isinstance(v,dict):
  if set(v)=={'path','sha256','bytes'}:yield v
  else:
   for x in v.values():yield from allrefs(x)
 elif isinstance(v,list):
  for x in v:yield from allrefs(x)
def remember(ref):
 assert pin(ref['path'])==ref
 key=str(Path(ref['path']));assert key not in refs or refs[key]==ref;refs[key]=ref
hdfref=dict(path=str(S/'HDF.json'),sha256='9fd03a5b17973da0755dbeae637ca1bad6c6252d744342d232bac89f0511e10f',bytes=13534)
mfref=dict(path=str(S/'MF.json'),sha256='d04fc76135f8c8d08212c2be1a76b334a9be074e49c94c363e27fffce091740e',bytes=4651)
hdf=add(hdfref);mf=add(mfref)
for ref in mf['members']:remember(ref)
assert hdf['manifest_ref']==mfref
for ref in allrefs(hdf):remember(ref)
inputs=read(hdf['source_inputs_ref']['path'])
for ref in allrefs(inputs):remember(ref)
for ref in read(hdf['base_mf_ref']['path'])['members']:remember(ref)
contract=read(hdf['root_calling_contract_ref']['path'])
auditref=dict(path=str(W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge04-source-author.actual-audit.root.json'),sha256='f8c46a9e4959faa0211dafab10bafc1d50c7ff63b672de68d6305f1b491d9dfa',bytes=1112)
origin=add(auditref);remember(origin['original_capture_ref'])
lines=Path(origin['original_capture_ref']['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==origin['original_line_sha256']
with Path(origin['source_audit_path']).open('rb') as stream:
 for offset,line in zip(origin['source_line_offsets'],lines):
  assert offset+len(line)<=origin['source_prefix_size_observed'];stream.seek(offset);assert stream.read(len(line))==line
header,metadata,message=map(json.loads,lines)
assert header['type']=='session_meta' and header['payload']['id']==THREAD
assert origin['actor_id']==AUTHOR and origin['binding_sha256']==hdfref['sha256']
assert metadata['type']=='inter_agent_communication_metadata' and message['payload']['type']=='agent_message'
assert message['payload']['author']==BACKEND and message['payload']['recipient']=='/root' and message['metadata']['client_authored'] is False
assert metadata['timestamp']==message['timestamp'] and message['ordinal']==metadata['ordinal']+1
content=message['payload']['content'];assert len(content)==1 and content[0]['type']=='input_text'
assert hdfref['sha256'] in content[0]['text'] and mfref['sha256'] in content[0]['text']
# Verify author build provenance from its actual bounded original session lines too.
buildbind=read(hdf['actual_source_build_host']['binding_ref']['path'])
buildraw=Path(hdf['actual_source_build_host']['raw_ref']['path']).read_bytes().splitlines(keepends=True)
assert len(buildraw)==3
buildhead=json.loads(buildraw[0])
assert buildhead['payload']['id']==hdf['actual_source_thread']
assert [hashlib.sha256(line).hexdigest() for line in buildraw]==buildbind['original_line_sha256']
assert buildbind['actor_id']==BACKEND and buildbind['actor_thread_id']==hdf['actual_source_thread']
with Path(buildbind['source_audit_path']).open('rb') as stream:
 for offset,line in zip(buildbind['source_line_offsets'],buildraw):
  assert offset+len(line)<=buildbind['source_prefix_size_observed'];stream.seek(offset);assert stream.read(len(line))==line
for refname in ('source_guard_ref','seal_source_guard_ref'):
 c=read(hdf[refname]['path']);assert c['closed'] is True and c['retained_handles_count']==0 and c['errors']==[]
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
assert pin(gp)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
gm=types.ModuleType('br4_independent_stable_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=512*1024*1024)
checks=[];controls=[]
def check(name,ok,evidence):
 assert ok,name
 checks.append(dict(name=name,passed=True,evidence=evidence))
try:
 guard.acquire(list(refs.values()))
 before=Path(hdf['original_Attach_contribution']['source_ref']['path']).read_bytes()
 after=Path(hdf['source_ref']['path']).read_bytes()
 pairs=[
 ('AUTHOR = "codex:/root/attach_restore_independent_review"','AUTHOR = "codex:/root/full_w09_source_review"'),
 ('AUTHOR_BACKEND = "/root/attach_restore_independent_review"','AUTHOR_BACKEND = "/root/full_w09_source_review"'),
 ('BRIDGE_GENERATION = "bridge-20261010-03"','BRIDGE_GENERATION = "bridge-20261010-04"'),
 ('VERIFIER = "/root/full_w09_source_review"','VERIFIER = "/root/backup_regression_resources"')]
 calculated=before
 for old,new in pairs:
  assert calculated.count(old.encode())==1;calculated=calculated.replace(old.encode(),new.encode(),1)
 inverse=after
 for old,new in reversed(pairs):
  assert inverse.count(new.encode())==1;inverse=inverse.replace(new.encode(),old.encode(),1)
 check('only_four_literal_constants_changed_complete_inverse',calculated==after and inverse==before,dict(before_ref=hdf['original_Attach_contribution']['source_ref'],after_ref=hdf['source_ref'],replacement_names=['AUTHOR','AUTHOR_BACKEND','BRIDGE_GENERATION','VERIFIER']))
 t0=ast.parse(before);t1=ast.parse(after)
 functions0={x.name:ast.dump(x,include_attributes=False) for x in t0.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 functions1={x.name:ast.dump(x,include_attributes=False) for x in t1.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 assert functions0==functions1
 source0=before.decode().splitlines(keepends=True);source1=after.decode().splitlines(keepends=True)
 for f0,f1 in zip([x for x in t0.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))],[x for x in t1.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))]):
  assert ''.join(source0[f0.lineno-1:f0.end_lineno])==''.join(source1[f1.lineno-1:f1.end_lineno])
 assert Path(hdf['consumer_launcher_ref']['path']).read_bytes()==Path(hdf['original_Attach_contribution']['consumer_launcher_ref']['path']).read_bytes()
 assignment=lambda t,k:next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==k for x in n.targets))
 for k in ('STAGES','ROUTES','CANON','TRUSTED','PUBLIC_TEMP','RESOURCE_PARENT_REF','RESOURCE_AUDIT_REF','RESOURCE_OWNER_REF'):
  assert ast.dump(assignment(t0,k),include_attributes=False)==ast.dump(assignment(t1,k),include_attributes=False)
 stages=assignment(t1,'STAGES').value
 assert [ast.literal_eval(k) for k in stages.keys]==contract['stages']
 check('all_functions_launcher_stages_routes_authority_gates_unchanged',True,dict(function_count=len(functions1),stages=contract['stages'],six_routes=contract['six_routes'],launcher_ref=hdf['consumer_launcher_ref']))
 constants={k:ast.literal_eval(assignment(t1,k).value) for k in ('AUTHOR','AUTHOR_BACKEND','BRIDGE_GENERATION','VERIFIER','ROOT_ACTOR','THREAD')}
 check('truthful_new_author_generation_selfrefs_ancestry',constants['AUTHOR']==AUTHOR and constants['AUTHOR_BACKEND']==BACKEND
  and constants['BRIDGE_GENERATION']==hdf['generation']==contract['generation']=='bridge-20261010-04'
  and hdf['source_author']==contract['source_author']==AUTHOR and hdf['source_author_backend']==contract['source_author_backend']==BACKEND
  and hdf['source_revision_uuid']==contract['source_revision_uuid'] and len(hdf['source_revision_uuid'])==32
  and contract['source_ref']==hdf['source_ref'] and contract['consumer_launcher_ref']==hdf['consumer_launcher_ref']
  and contract['contract_ref']==hdf['contract_ref'] and hdf['original_Attach_contribution']['source_author']=='codex:/root/attach_restore_independent_review',
  dict(author_origin_ref=auditref,source_revision_uuid=hdf['source_revision_uuid'],original_contribution=hdf['original_Attach_contribution']))
 def condition(function,code):
  f=next(x for x in t1.body if isinstance(x,ast.FunctionDef) and x.name==function)
  found=[x for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='need' and len(x.args)>1 and isinstance(x.args[1],ast.Constant) and x.args[1].value==code]
  assert len(found)==1
  return compile(ast.Expression(found[0].args[0]),'<pure-source-condition>','eval')
 def evaluate(case,compiled,env,expected):
  actual=eval(compiled,{'__builtins__':{}},dict(constants,**env))
  assert actual is expected,(case,actual,expected)
  controls.append(dict(case=case,passed=True,expected=expected,actual=actual,pure_AST_only=True,actual_stage_calls=0))
 sourcepredicate=condition('source_review','SOURCE_REVIEW_BINDING')
 base=dict(source_ref=hdf['source_ref'])
 for actor,want in [(REVIEWER,True),(AUTHOR,False),(BACKEND,False),(ROOT,False),('/root',False)]:
  evaluate('Source_review_actor:'+actor,sourcepredicate,dict(review=dict(base,reviewer_id=actor),req=dict(bridge_source_ref=hdf['source_ref'])),want)
 rolespredicate=condition('roles','ACTUAL_VERIFIER_SOURCE_AUTHOR')
 for label,verifier,authors,want in [
  ('current_Backup_Full',constants['VERIFIER'],[BACKEND],True),
  ('old_Full_verifier',BACKEND,[BACKEND],False),
  ('old_Attach_Source',constants['VERIFIER'],[REVIEWER],False),
  ('canonical_relabel',constants['VERIFIER'],[AUTHOR],False)]:
  evaluate('roles:'+label,rolespredicate,dict(registry=dict(roles=dict(verifier=verifier,source_authors=authors))),want)
 capturepredicate=condition('capture','REAL_FORMAL_REVIEW')
 context={'path':'SYNTHETIC_CONTEXT','sha256':'0'*64}
 for actor,want in [(constants['VERIFIER'],True),(BACKEND,False),('codex:'+constants['VERIFIER'],False)]:
  evaluate('formal_review_actor:'+actor,capturepredicate,dict(review=dict(reviewer_id=actor,issuer_id=actor,context_ref=context),req=dict(context_ref=context),ref2=lambda x:x),want)
 propose=next(x for x in t1.body if isinstance(x,ast.FunctionDef) and x.name=='propose')
 common=next(x.value for x in ast.walk(propose) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='common' for t in x.targets))
 scope_fields={ast.literal_eval(k):eval(compile(ast.Expression(v),'<pure-source-field>','eval'),{'__builtins__':{}},constants) for k,v in zip(common.keys,common.values) if ast.literal_eval(k) in ('source_actor','source_author_canonical','generation')}
 assert scope_fields==dict(source_actor=BACKEND,source_author_canonical=AUTHOR,generation='bridge-20261010-04')
 check('changed_actor_semantics_and_fresh_scope_fields',True,dict(pure_conditions=len(controls),future_scope_fields=scope_fields,
 source_reviewer_backend=REVIEWER,verifier_backend=constants['VERIFIER'],controls_are_not_actual_peer_or_Root_grants=True))
 check('required_runtime_and_formal_boundaries_preserved',hdf['execution_grant'] is False and hdf['formal_acceptance'] is False
  and hdf['future_Root_scope'] is None and hdf['future_Root_request'] is None and hdf['future_Mode_refs'] is None
  and contract['future_Root_request_scope_grant_lease_refs'] is None and contract['actual_executed'] is False,
  dict(old22_18_44_controls_rerun=False,Root_stage_calls=0,Native_Go_SQL_TP_Mode_calls=0,
   NF6_qualification='PENDING_ACTUAL_CURRENT_NF6_FACTS_AND_INDEPENDENT_REVIEW',
   prior_Attach_contribution_preserved=True,review_scope='Current BR4 authored delta and unchanged-baseline evidence; no retroactive self-acceptance of original Attach contribution.'))
finally:
 closed=guard.close();save('source-guard.closed.json',closed)
assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
controlref=save('delta-review-controls.json',dict(checks=checks,checks_passed=len(checks),pure_AST_controls=controls,pure_AST_control_count=len(controls),Rootstage_Native_Go_SQL_TP_Mode_calls=0,old22_18_44_not_rerun=True))
save('input-pins.json',list(refs.values()))
decision=save('decision.json',dict(schema='researchos.w09-formal-root-bridge-independent-source-review.v1',
 decision='ACCEPTED_SOURCE_ONLY',reviewer_id=REVIEWER,reviewer_actor='codex:'+REVIEWER,actor_role='INDEPENDENT_NON_AUTHOR_OF_BR4',
 source_author=AUTHOR,source_author_backend=BACKEND,Root_thread_id=THREAD,
 created_utc=datetime.now(timezone.utc).isoformat(),source_ref=hdf['source_ref'],consumer_launcher_ref=hdf['consumer_launcher_ref'],
 source_hdf_ref=hdfref,source_mf_ref=mfref,calling_contract_ref=hdf['root_calling_contract_ref'],contract_ref=hdf['contract_ref'],
 source_actual_author_ref=auditref,source_actual_author_meta=dict(backend=message['payload']['author'],timestamp=message['timestamp'],Root_thread_id=THREAD),
 findings=[],checks_ref=controlref,source_guard_ref=pin(N/'source-guard.closed.json'),all_Source_guards_closed_zero=True,
 source_revision_uuid=hdf['source_revision_uuid'],generation=hdf['generation'],checks_passed=len(checks),pure_AST_controls=len(controls),
 historical_Attach_contribution_preserved=True,old22_18_44_controls_rerun=False,
 execution_grant=False,formal_acceptance=False,parent_acceptance=False,RootScope_qualification_created=False,
 Root_stage_Native_Go_SQL_TP_Mode_calls=0,Main_Canon_Scope_writes=0,
 Root_next_step='Fresh actual Root Scope/current4/finite lease/resource binding and current NF6 qualifications remain required; this accepts BR4 Source only.',
 STOP_after_seal=True))
print(json.dumps(dict(decision_ref=decision,controls_ref=controlref,decision='ACCEPTED_SOURCE_ONLY',checks=len(checks),
 pure_AST_controls=len(controls),SourceGuard_handles=len(refs),SourceGuard_closed0=True),ensure_ascii=False))

