import sys
sys.dont_write_bytecode=True
import ast,base64,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
C=W/'main_c19_source_registry_v2_source_codex/Mainv2-1a11fbc'
CP=B/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
ACTOR='codex:/root/attach_fixture_source_review'
pins={};checks=[];controls=[]
def rawpin(p,b):return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def pin(p):
 p=Path(p).resolve(strict=True);return rawpin(p,p.read_bytes())
def read(r):
 r=dict(path=str(Path(r['path']).resolve(strict=True)),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);assert pin(r['path'])==r
 assert r['path'] not in pins or pins[r['path']]==r
 pins[r['path']]=r;return Path(r['path']).read_bytes()
def load(r):return json.loads(read(r))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ck(n,v):
 assert v,n
 checks.append(n)
hr=dict(path=str(C/'HDF.json'),sha256='bfcb5010778c27ed4065bc6cda5d963e8f568f2207a413e7b5029b541f0613e7',bytes=9816)
h=load(hr);mf=load(h['manifest_ref'])
for ref in mf['members']:read(ref)
for ref in load(h['source_input_pins_ref'])['refs']:read(ref)
cp_h=load(dict(path=str(CP/'HDF.json'),sha256='896e0eaa99a9470eb9f01a099760b0538520bf99cb9f18506619f88b4d5d86a6',bytes=3059))
for ref in load(cp_h['manifest_ref'])['members']:read(ref)
facts=load(cp_h['facts_ref']);scope0=load(facts['scope_ref']);raw=[read(r) for r in facts['canonical_refs']];oldcp,oldow=[json.loads(b) for b in raw[:2]]
contract=load(h['root_calling_contract_ref']);change=load(h['change_set_ref'])
caller=read(h['caller_ref']);inv=load(h['caller_complete_byte_inverse_ref']);metadata=load(h['metadata_complete_byte_inverse_ref'])
def check_inverse(label,iv,old_ref,new_ref):
 old=read(old_ref);new=read(new_ref)
 ck(label+'_whole_inputs',base64.b64decode(iv['whole_before_base64'])==old and base64.b64decode(iv['whole_after_base64'])==new)
 restored=new
 for span in reversed(iv['spans']):
  assert restored[span['after_start']:span['after_end']]==base64.b64decode(span['after_base64'])
  restored=restored[:span['after_start']]+base64.b64decode(span['before_base64'])+restored[span['after_end']:]
 ck(label+'_whole_byte_inverse',restored==old)
check_inverse('caller',inv,inv['original_ref'],inv['proposed_ref'])
for row in metadata['files']:check_inverse('metadata_'+row['name'],row['inverse'],row['original_ref'],row['proposed_ref'])
oldcaller=read(inv['original_ref']);oldchange=load(next(row['original_ref'] for row in metadata['files'] if row['name']=='change-set.json'))
for index,(new,old) in enumerate(zip(change['targets'],oldchange['targets'])):
 ck('target'+str(index)+'_bytes_unchanged',new['target']==old['target'] and read(new['after_source_ref'])==read(old['after_source_ref']))
 if new['before_ref'] is not None:ck('target'+str(index)+'_before_archive_unchanged',read(new['before_archive_ref'])==read(old['before_archive_ref']))
ck('source21_contract_unchanged',change['source21']==oldchange['source21'])
decision=dict(schema='researchos.w09-main-c19-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id=ACTOR,source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=h['manifest_ref'],caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],exact_targets=h['exact_business_targets'],formal_case_accepted_delta=0,actual_adoption_executed=False)
ck('intended_decision_contract_exact_fields',set(decision)==set(contract['source_review_required_fields']) and decision['schema']==contract['source_review_decision_schema'] and decision['decision']==contract['source_review_decision_value'])
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=read(dict(path=str(gp),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
gm=types.ModuleType('mainv2review_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(graw,str(gp),'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(pins.values()))
try:
 main=types.ModuleType('reviewed_mainv2_source');main.__file__=str(C/'adopt_main_c19.source.py');exec(compile(caller,main.__file__,'exec'),main.__dict__)
 ck('new_fixed_N_and_OUT',main.N==C and main.OUT==C/'actual-adoption')
 ck('contract_argv_local_caller',contract['future_argv'][6]==str(C/'adopt_main_c19.source.py') and contract['caller_ref']==h['caller_ref'] and contract['change_set_ref']==h['change_set_ref'])
 ck('contract_journal_binding',contract['runtime_journal_root']==contract['owner_exact_field_bindings']['journal_root']==str(main.OUT))
 _,actual_source_refs=main.manifest_refs(pin(C/'HDF.json'),h['manifest_ref'])
 ck('real_source_manifest_local_and_contract_member',h['root_calling_contract_ref'] in actual_source_refs and h['caller_ref'] in actual_source_refs and h['change_set_ref'] in actual_source_refs)
 def normalize(tree):
  tree=copy.deepcopy(tree);tree.body=[n for n in tree.body if not(isinstance(n,ast.FunctionDef) and n.name=='validate_scope') and not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='N' for t in n.targets))];return ast.dump(tree,include_attributes=False)
 ck('all_other_caller_AST_unchanged',normalize(ast.parse(caller))==normalize(ast.parse(oldcaller)))
 prior_scope=next(v for v in ast.parse(oldcaller).body if isinstance(v,ast.FunctionDef) and v.name=='validate_scope')
 current_scope=next(v for v in ast.parse(caller).body if isinstance(v,ast.FunctionDef) and v.name=='validate_scope')
 ck('scope_validator_only_boundary_changed',ast.dump(ast.Module(body=prior_scope.body[:3]+prior_scope.body[4:],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=current_scope.body[:3]+current_scope.body[5:],type_ignores=[]),include_attributes=False))
 registration=dict(json=json,copy=copy,hashlib=hashlib,TARGETS=contract['exact_targets'],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
 rt=ast.parse(read(cp_h['writer_ref']));names={'require','facts_scope','validate_live_context','transform'}
 exec(compile(ast.Module(body=[v for v in rt.body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'<pure-root-registration-functions>','exec'),registration)
 realread=main.read_ref
 def cross(label,scope_mutation=None,decision_mutation=None,owner_mutation=None):
  memory={}
  def put(p,value):
   p=Path(p);b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();r=rawpin(p,b);memory[str(p)]=b;return r
  def virtual_read(r):
   if r['path'] not in memory:return realread(r)
   b=memory[r['path']];assert rawpin(r['path'],b)==r;return b
  d=copy.deepcopy(decision)
  if decision_mutation:decision_mutation(d)
  dr=put(N/'SYNTHETIC_DECISION_NEVER_WRITTEN.json',d)
  qm=put(N/'SYNTHETIC_REVIEW_MF_NEVER_WRITTEN.json',dict(members=[dr]))
  qh=put(N/'SYNTHETIC_REVIEW_HDF_NEVER_WRITTEN.json',dict(actor_id=ACTOR,manifest_ref=qm,source_decision_ref=dr))
  sc=copy.deepcopy(scope0);sc.update(caller_ref=h['caller_ref'],change_set_ref=h['change_set_ref'],source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=h['manifest_ref'],source_review_handoff_ref=qh,source_review_manifest_ref=qm,source_review_decision_ref=dr,journal_root=str(main.OUT))
  if scope_mutation:scope_mutation(sc)
  sr=put(W/'integration_codex/root-main-seven-target-scope-20261009/SYNTHETIC_NEW_SCOPE_NEVER_WRITTEN.json',sc)
  f=copy.deepcopy(facts);f.update(scope_ref=sr,calling_contract_ref=h['root_calling_contract_ref'],reviews=[dict(handoff_ref=pin(C/'HDF.json'),manifest_ref=h['manifest_ref']),dict(handoff_ref=qh,manifest_ref=qm),dict(handoff_ref=sc['component_review_handoff_ref'],manifest_ref=sc['component_review_manifest_ref'])])
  registration['load']=lambda r:json.loads(virtual_read(r));registration['read']=virtual_read
  reg_error=main_error=None
  bindings={'EXACT_ROOT_REGISTRATION_SCOPE_REF':sr,'EXACT_ORDERED_SEVEN_ABSOLUTE_TARGETS':contract['exact_targets'],'THIS_SOURCE_HDF_REF':pin(C/'HDF.json'),'THIS_SOURCE_MF_REF':h['manifest_ref'],'FUTURE_SOURCE_INDEPENDENT_HDF_REF':qh,'FUTURE_SOURCE_INDEPENDENT_MF_REF':qm}
  def resolve(v):return copy.deepcopy(bindings.get(v,v)) if isinstance(v,str) else copy.deepcopy(v)
  owner={k:resolve(v) for k,v in contract['owner_exact_field_bindings'].items()};worker={k:resolve(v) for k,v in contract['checkpoint_worker_exact_field_bindings'].items()}
  try:
   got=registration['facts_scope'](f);assert got==(sc,owner,worker)
  except ValueError as exc:reg_error=str(exc)
  if reg_error is None:
   lc=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc='SYNTHETIC_CONTROL_ONLY',source_cutoff=dict(highest_ordinal=f['highest_observed_ordinal'],next_failure_ordinal=f['next_failure_ordinal']),next_original_failure_ordinal=f['next_failure_ordinal'],pending=[])
   cp,ow=registration['transform'](copy.deepcopy(oldcp),copy.deepcopy(oldow),f,put(N/'SYNTHETIC_FACTS_NEVER_WRITTEN.json',f),oldcp,oldow,owner,worker,'SYNTHETIC_CONTROL_ONLY',lc)
  else:
   cp,ow=copy.deepcopy(oldcp),copy.deepcopy(oldow);cp['revision']=367;ow['revision']=171;cp['workers'].append(worker);ow['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption']=owner
  if owner_mutation:owner_mutation(cp,ow)
  vr=put(W/'integration_codex/root-main-seven-target-scope-20261009/SYNTHETIC_VECTOR_NEVER_WRITTEN.json',dict(schema=contract['vector_schema'],checkpoint_revision=367,ownership_revision=171,refs=[put(main.CANON[0],cp),put(main.CANON[1],ow),facts['canonical_refs'][2],change['targets'][6]['before_ref']]))
  main.read_ref=virtual_read
  try:main.validate_scope(sc,sr,change,h['change_set_ref'],h['caller_ref'],pin(C/'HDF.json'),h['manifest_ref'],actual_source_refs,vr)
  except ValueError as exc:main_error=str(exc)
  finally:main.read_ref=realread
  controls.append(dict(name=label,registration_error=reg_error,Main_error=main_error,virtual_document_count=len(memory)))
  return reg_error,main_error
 ck('full_real_Root_to_Main_interface_pass',cross('valid_same_integer_zero_scope')==(None,None))
 for field in contract['scope_strict_integer_zero_fields']:
  for name,value in [('false',False),('float',0.0),('nonzero',1),('null',None)]:
   errors=cross(field+'_'+name,lambda d,f=field,v=value:d.update({f:v}));ck('both_reject_'+field+'_'+name,all(errors))
 for field in contract['scope_boolean_false_fields']:
  errors=cross(field+'_integer_zero',lambda d,f=field:d.update({f:0}));ck('both_reject_boolflag_integer0_'+field,all(errors))
 for name,mutate in [('author_actor',lambda d:d.update(actor_id='codex:/root/command_queue_impl')),('Root_actor',lambda d:d.update(actor_id='codex:/root')),('wrong_schema',lambda d:d.update(schema='wrong')),('wrong_source',lambda d:d['source_manifest_ref'].update(sha256='0'*64))]:
  errors=cross('decision_'+name,decision_mutation=mutate);ck('both_reject_decision_'+name,all(errors))
 error=cross('owner_scope_wrong',owner_mutation=lambda c,o:o['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption']['scope_ref'].update(sha256='0'*64))
 ck('Main_rejects_wrong_registered_owner',error[0] is None and error[1]=='REGISTERED_EXACT_ROOT_OWNER')
 mt=next(v for v in ast.parse(caller).body if isinstance(v,ast.FunctionDef) and v.name=='main')
 namespace=[v for v in mt.body if isinstance(v,ast.Expr) and isinstance(v.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value in ('ROOT_REQUEST_NAMESPACE','ROOT_SCOPE_NAMESPACE') for a in v.value.args)]
 env=dict(Path=Path,W=W,require=main.require,sref=dict(path=str(W/'integration_codex/root-main-seven-target-scope-20261009/SYNTHETIC_SCOPE.json')),qref=dict(path=str(W/'integration_codex/root-main-seven-target-scope-20261009/SYNTHETIC_REQUEST.json')))
 exec(compile(ast.Module(body=namespace,type_ignores=[]),'<pure-namespace-gates>','exec'),env)
 ck('future_Scope_Request_namespace_pass',len(namespace)==2)
 ck('canon_four_unchanged',[Path(r['path']).read_bytes() for r in facts['canonical_refs']]==raw)
 save('controls.json',controls)
finally:
 cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup);assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
ck('all_pins_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()));save('checks.json',checks);save('source-decision.json',decision)
save('result.json',dict(status='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION',checks=len(checks),pins=len(pins),cross_controls=len(controls),new_original_failures=[],virtual_Scope_CP_OW_vector_only=True,actual_adoption_executed=False,Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_case_accepted_delta=0,requires_Root_new_scope_registration_vector_request=True))
print(json.dumps(dict(status='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION',checks=len(checks),pins=len(pins),cross_controls=len(controls),new_failures=0)))
