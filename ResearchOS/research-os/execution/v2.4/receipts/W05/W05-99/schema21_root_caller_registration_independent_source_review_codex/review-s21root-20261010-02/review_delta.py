"""Task76 independent delta checks. Source-only, no Root authorization."""
import ast,copy,hashlib,json,ntpath,types
from datetime import datetime,timezone
from pathlib import Path

D=Path(__file__).resolve().parent; B=D.parent.parent
Q=B/'schema21_root_caller_registration_source_codex/s21root-20261010-02'
P=B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-01'
ACTOR='codex:/root/full_w09_source_review'
checks=[]

def pin(path):
 path=Path(path); raw=path.read_bytes(); return dict(path=path.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(path):return json.loads(Path(path).read_bytes())
def save(name,value):
 with (D/name).open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m
def note(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
def reject(name,action,code):
 try:action()
 except (ValueError,TypeError,KeyError) as exc:note(name,code in str(exc),observed=str(exc),expected=code,Source_only=True)
 else:note(name,False,observed='UNEXPECTED_ALLOW',expected=code)

def main():
 source=doc(Q/'HDF.json');mf=doc(Q/'MF.json');inputs=doc(source['source_inputs_ref']['path'])
 hdf_ref=pin(Q/'HDF.json');mf_ref=pin(Q/'MF.json')
 assert hdf_ref['sha256']=='05edd46f975d5d85cfa6c157cad648d90ab8c0ac9ad60e8514e280863a4f7492' and hdf_ref['bytes']==12700
 assert mf_ref['sha256']=='73add6a949ad89cebcfe880b49035e6e88eeebdad8fe4309f0baefa9bf85ffdf' and mf_ref['bytes']==13633 and len(mf['members'])==41
 m=load(Q/'old21_root.source.py','old21_Source_delta_only')
 guard_module=load(m.GUARD_REF['path'],'Task76_source_guard')
 guard=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 references=[hdf_ref,mf_ref,m.GUARD_REF]+mf['members']+inputs['references']+[pin(P/'finite-Source-review.json'),pin(P/'metadata-and-inverse-Source-guard.closed.json'),pin(P/'independent-full-Source-inverse.json')]
 refs=m.local_refs(references,m.CANON)
 assert not any(m.canonical(x['path']) in {m.canonical(str(y)) for y in m.CANON} for x in refs)
 try:
  guard.acquire(refs)
  note('exact new Source 41 MF members and delta inputs held; no live Canon',True,held=len(refs),members=41)
  old=Path(source['base_Caller_ref']['path']).read_bytes();new=Path(source['caller_ref']['path']).read_bytes()
  assert hashlib.sha256(new).hexdigest()=='e8ed36695740df69f140b676e3ad3f7ec6a7026202da39407c0b688eeb4b45f7' and len(new)==65093
  old_tree=ast.parse(old);new_tree=ast.parse(new)
  old_funcs={x.name:x for x in old_tree.body if isinstance(x,ast.FunctionDef)}
  new_funcs={x.name:x for x in new_tree.body if isinstance(x,ast.FunctionDef)}
  changed=[name for name in old_funcs if ast.dump(old_funcs[name],include_attributes=False)!=ast.dump(new_funcs[name],include_attributes=False)]
  note('only three approved functions changed',set(changed)=={'failure_rows','projection','validate_peer_delivery'},changed=changed)
  other_old=[x for x in old_tree.body if not isinstance(x,ast.FunctionDef)];other_new=[x for x in new_tree.body if not isinstance(x,ast.FunctionDef)]
  note('all imports/constants/classes/CLI unchanged AST',ast.dump(ast.Module(body=other_old,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=other_new,type_ignores=[]),include_attributes=False))
  inv=doc(source['inverse_ref']['path']);restored=new
  for layer in reversed(inv['layers']):
   inserted=bytes.fromhex(layer['new_hex']);before=bytes.fromhex(layer['old_hex'])
   assert restored.count(inserted)==1
   restored=restored.replace(inserted,before,1)
  note('complete byte inverse restores reviewed 01 Source',restored==old and hashlib.sha256(restored).hexdigest()==source['base_Caller_ref']['sha256'],base_ref=source['base_Caller_ref'],inverse_ref=source['inverse_ref'])
  prior=doc(P/'finite-Source-review.json');prior_inverse=doc(P/'independent-full-Source-inverse.json')
  note('reuse 01 checks and complete original inverse without rerun',prior['check_count']==32 and prior['unexpected_check_failures']==0 and prior_inverse['entire_original_bytes_restored'],prior32_reexecuted=False,builder853_reexecuted=False)
  archives={x['key']:doc(x['snapshot_ref']['path']) for x in source['current_before_archive_refs']}
  cp,ow=archives['checkpoint'],archives['path_ownership']; start=cp['work_in_progress']['root_next_failure_ordinal_live']
  scope_ref=hdf_ref;owner=dict(scope_ref=scope_ref,selected_worker_id=m.ROOT,Source_only_fixture=True)
  worker=dict(scope_ref=scope_ref,selected_owner_ref=mf_ref,worker_id=m.ROOT,Source_only_fixture=True)
  created=datetime.now(timezone.utc).isoformat()
  def rows(value,checkpoint=cp):
   original=m.doc;m.doc=lambda ref:copy.deepcopy(value)
   try:return m.failure_rows(hdf_ref,checkpoint)
   finally:m.doc=original
  def project(value,checkpoint=cp):return m.projection(checkpoint,ow,scope_ref,mf_ref,source['caller_ref'],hdf_ref,owner,worker,value,created)
  def pending(next_value,items):return dict(issued_by=m.ROOT,counter_reset=False,next_original_failure_ordinal=next_value,pending=items,Source_only_in_memory_fixture=True)
  for label,next_value in [('backwards',start-1),('negative',-1),('boolean',True),('string',str(start)),('float',float(start)),('null',None)]:
   value=pending(next_value,[])
   reject('failure_rows rejects '+label,lambda value=value:rows(value),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
   reject('projection rejects '+label,lambda value=value:project(value),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
  empty=pending(start,[]);rows(empty);after_cp,after_ow=project(empty)
  note('empty equal counter accepted and old failure ledger immutable',after_cp['work_in_progress']['root_next_failure_ordinal_live']==start and m.encoded(after_cp['failure_counters'])==m.encoded(cp['failure_counters']),Source_only=True)
  origin=pin(P/'actual-finite-review-0e9134.raw.jsonl')
  row=dict(ordinal=start,origin_ref=origin,origin_selector='SOURCE_ONLY_TASK76_PENDING_FIXTURE',description='Explicit Source-only in-memory control; never an actual failure ledger entry',actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
  valid=pending(start+1,[row]);rows(valid);after_cp,after_ow=project(valid)
  appended=after_cp['failure_counters'][-1]
  note('one contiguous append preserves old rows and unknown NULL',len(after_cp['failure_counters'])==len(cp['failure_counters'])+1 and m.encoded(after_cp['failure_counters'][:-1])==m.encoded(cp['failure_counters']) and appended['original_payload']['actual_python_exit'] is None and appended['original_payload']['actual_native_exit'] is None and after_cp['work_in_progress']['root_next_failure_ordinal_live']==start+1,Source_only=True)
  for label,items,next_value in [('gap',[dict(row,ordinal=start+1)],start+1),('duplicate',[row,copy.deepcopy(row)],start+2),('boolean ordinal',[dict(row,ordinal=True)],start+1),('missing ordinal',[{}],start+1),('non-dict row',[start],start+1),('empty forward',[],start+1)]:
   value=pending(next_value,items)
   reject('failure_rows rejects '+label,lambda value=value:rows(value),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
   reject('projection rejects '+label,lambda value=value:project(value),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
  low_cp=copy.deepcopy(cp);low_cp['work_in_progress']['root_next_failure_ordinal_live']=1
  reject('bool ordinal cannot equal low int 1 in failure_rows',lambda:rows(pending(2,[dict(row,ordinal=True)]),low_cp),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
  reject('bool ordinal cannot equal low int 1 in projection',lambda:project(pending(2,[dict(row,ordinal=True)]),low_cp),'PENDING_CONTIGUOUS_CURRENT_COUNTER')
  duplicate=copy.deepcopy(cp)
  duplicate['failure_counters'].append(copy.deepcopy(appended))
  reject('projection duplicate original SHA+selector rejected',lambda:project(valid,duplicate),'ORIGINAL_INVOCATION_REUSED')
  observation=doc(source['actual_Task68_observation_ref']['path']); raw=Path(source['actual_Task68_raw_ref']['path']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()=='797f80403540a5f9da512f47d8698498c40bf36869fb5b4b4f64600e8d57e083' and len(raw)==27173
  lines=raw.splitlines(keepends=True);header,first,last=[json.loads(line) for line in lines]
  with Path(observation['source_audit_path']).open('rb') as stream:
   for offset,line in zip(observation['source_line_offsets'],lines):stream.seek(offset);assert stream.readline()==line
  note('real Task68 Root original header/metadata/Final offsets retained',header['payload']['id']==m.ROOT_THREAD and last['ordinal']==62210,raw_ref=source['actual_Task68_raw_ref'],observation_ref=source['actual_Task68_observation_ref'])
  # AST extraction begins after original Root binding gate, retaining every peer
  # body/metadata/ref check. This observation is NEVER issued as a Root binding.
  function=copy.deepcopy(new_funcs['validate_peer_delivery']);function.name='pure_peer_interface'
  i=next(i for i,node in enumerate(function.body) if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='payload' for x in node.targets))
  function.body=function.body[i:]
  function.args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('binding','first','last','expected_refs','peer_actor','operation')],kwonlyargs=[],kw_defaults=[],defaults=[])
  ns=dict(m.__dict__);exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'<Task76 exact Source-only peer AST body>','exec'),ns)
  peer=ns['pure_peer_interface'];expected=list(source['known_builder_Source_review_refs'].values())
  peer(observation,first,last,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS')
  note('actual sealed legacy Task68 body now accepted by exact Source interface',True,Source_only_interface=True,Root_binding_issued=False,actual_Root_authorization=False)
  reject('independent observation cannot impersonate Root capture issuer',lambda:m.original_capture_rows(observation,raw,peer=True),'EXTERNAL_ROOT_CAPTURE_IDENTITY')
  reject('legacy Builder alias cannot qualify Caller review',lambda:peer(observation,first,last,expected,ACTOR,'SOURCE_REVIEW_WITNESS'),'PEER_TYPED_DELIVERY_REQUIRED')
  reject('legacy Builder alias cannot qualify runtime review',lambda:peer(observation,first,last,expected,ACTOR,'RUNTIME_QUALIFICATION_ISSUANCE'),'PEER_TYPED_DELIVERY_REQUIRED')
  for field,value in [('author','/root/other'),('recipient','/root/other'),('type','message')]:
   altered=copy.deepcopy(last);altered['payload'][field]=value
   reject('legacy wrong backend '+field,lambda altered=altered:peer(observation,first,altered,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),'ACTUAL_PEER_DELIVERY_REQUIRED')
  altered=copy.deepcopy(last);altered['metadata']['client_authored']=True
  reject('legacy client-authored record rejected',lambda:peer(observation,first,altered,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),'ACTUAL_PEER_DELIVERY_REQUIRED')
  for label,change in [('id',lambda x:x['payload'].update(id='other')),('timestamp',lambda x:x.update(timestamp='2026-10-09T18:03:53.679Z'))]:
   altered=copy.deepcopy(last);change(altered)
   code='EXACT_LEGACY_OLD21_BUILDER_DELIVERY' if label=='id' else 'ACTUAL_PEER_DELIVERY_REQUIRED'
   reject('legacy altered '+label,lambda altered=altered:peer(observation,first,altered,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),code)
  envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+ACTOR.removeprefix('codex:')+'\nPayload:\n'
  delivery=json.loads(last['payload']['content'][0]['text'][len(envelope):])
  for field,value,code in [('component','OTHER','EXACT_LEGACY_OLD21_BUILDER_DELIVERY'),('root_thread_id','other','PEER_REVIEW_REF_BINDING'),('review_author','codex:/root/other','PEER_REVIEW_REF_BINDING'),('operation','SOURCE_OTHER','PEER_REVIEW_REF_BINDING'),('verdict','CHANGES_REQUIRED','PEER_REVIEW_REF_BINDING'),('execution_grant',True,'PEER_REVIEW_REF_BINDING'),('formal_acceptance',True,'PEER_REVIEW_REF_BINDING')]:
   altered=copy.deepcopy(last);body=copy.deepcopy(delivery);body[field]=value;altered['payload']['content'][0]['text']=envelope+json.dumps(body,ensure_ascii=False,indent=2)
   reject('Source fixture legacy altered '+field,lambda altered=altered:peer(observation,first,altered,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),code)
  altered_refs=copy.deepcopy(expected);altered_refs[0]['bytes']+=1
  reject('legacy expected refs cannot alias different package',lambda:peer(observation,first,last,altered_refs,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),'EXACT_LEGACY_OLD21_BUILDER_DELIVERY')
  for label,changed_text in [('trailing',last['payload']['content'][0]['text']+' trailing'),('duplicate',last['payload']['content'][0]['text'].rstrip()[:-1]+',"schema":"duplicate"}'),('wrong anchored sender',last['payload']['content'][0]['text'].replace('Sender: /root/full_w09_source_review','Sender: /root/other',1))]:
   altered=copy.deepcopy(last);altered['payload']['content'][0]['text']=changed_text
   reject('legacy '+label+' reject',lambda altered=altered:peer(observation,first,altered,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),'PEER_TYPED_DELIVERY_REQUIRED')
  altered_binding=copy.deepcopy(observation);altered_binding['message_id']='other'
  reject('legacy observation message ID mismatch rejected',lambda:peer(altered_binding,first,last,expected,ACTOR,'BUILDER_SOURCE_REVIEW_WITNESS'),'PEER_ORIGINAL_IDENTITY')
  # One explicitly synthetic modern Caller body verifies alias is role-local.
  modern=copy.deepcopy(last);body=copy.deepcopy(delivery);body.update(schema='researchos.old21-peer-review-delivery.v2',operation='SOURCE_REVIEW_WITNESS');modern['payload']['content'][0]['text']=envelope+json.dumps(body,ensure_ascii=False,indent=2)
  peer(observation,first,modern,expected,ACTOR,'SOURCE_REVIEW_WITNESS')
  note('modern old21 Caller strict interface remains valid',True,synthetic_Source_body_only=True,actual_Root_witness=False)
  source_guard=doc(source['Source_final_guard_ref']['path']);control_guard=doc(source['controls_guard_ref']['path'])
  note('new successful author guards closed0',all(v['closed'] and v['retained_handles_count']==0 and not v['errors'] for v in (source_guard,control_guard)),old_unknown_guards_not_inferred_closed=True)
  if any(not x['passed'] for x in checks):raise ValueError('UNEXPECTED_INDEPENDENT_DELTA_CHECK_FAILED')
  result_ref=save('independent-delta-checks.json',dict(schema='researchos.old21-caller-independent-delta-review.v1',status='ACCEPTED_SOURCE_ONLY',review_author=ACTOR,source_hdf_ref=hdf_ref,source_mf_ref=mf_ref,caller_ref=source['caller_ref'],contract_ref=source['contract_ref'],checks=checks,passed=len(checks),failed=0,changed_functions=changed,exact_inverse_restored=True,prior32_reexecuted=False,builder853_reexecuted=False,real_Task68_legacy_body_Source_interface_pass=True,Root_issuer_observation_rejected=True,RootScope_grant_qualification_created=False,Go_Native_SQL_TP_model_calls=0,execution_grant=False,formal_acceptance=False))
 finally:
  closed=guard.close();guard_ref=save('independent-delta-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',passed=len(checks),failed=0,result_ref=result_ref,guard_ref=guard_ref,closed0=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False))

if __name__=='__main__':main()
