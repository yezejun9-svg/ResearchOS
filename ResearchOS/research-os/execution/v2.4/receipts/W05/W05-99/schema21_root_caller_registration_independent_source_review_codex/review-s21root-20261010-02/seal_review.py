"""Task76 seal. Source chain acceptance only; Root witnesses remain required."""
import ast,hashlib,json,os,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent
Q=B/'schema21_root_caller_registration_source_codex/s21root-20261010-02'
P=B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-01'
ACTOR='codex:/root/full_w09_source_review';ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
ROOT_AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
def doc(path):return json.loads(Path(path).read_bytes())
def pin(path):
 path=Path(path);raw=path.read_bytes();return dict(path=path.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (D/name).open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(path,name):
 value=types.ModuleType(name);value.__file__=str(path);exec(compile(Path(path).read_bytes(),str(path),'exec'),value.__dict__);return value

def actual_review_pairs(m):
 chunks={'3eb483':1089,'342f52':None};found={};calls={};size=AUDIT.stat().st_size;lower=max(0,size-64*1024*1024)
 with AUDIT.open('rb') as stream:
  header=stream.readline();stream.seek(lower)
  if lower:stream.readline()
  while stream.tell()<size:
   offset=stream.tell();line=stream.readline()
   if offset+len(line)>size:break
   row=json.loads(line);payload=row.get('payload')
   if row.get('type')!='response_item' or type(payload) is not dict:continue
   if payload.get('type') in ('custom_tool_call','function_call'):calls[payload['call_id']]=(offset,line,row)
   elif payload.get('type') in ('custom_tool_call_output','function_call_output'):
    for host in m.structured_documents(payload.get('output')):
     if type(host) is dict and host.get('chunk_id') in chunks and type(host.get('output')) is str:
      assert host['chunk_id'] not in found;found[host['chunk_id']]=(calls[payload['call_id']],(offset,line,row),host)
 assert set(found)==set(chunks)
 identity=json.loads(header)['payload'];assert identity['id']==os.environ['CODEX_THREAD_ID']=='01a1215b-7210-7613-b033-756b9d553b83'
 assert identity['agent_path']==ACTOR.removeprefix('codex:') and identity['parent_thread_id']==ROOT_THREAD
 results=[]
 for chunk,ordinal in chunks.items():
  first,last,host=found[chunk];rows=[(0,header),(first[0],first[1]),(last[0],last[1])]
  with AUDIT.open('rb') as stream:
   for offset,line in rows:stream.seek(offset);assert stream.readline()==line
  with (D/('actual-review-'+chunk+'.raw.jsonl')).open('xb') as stream:stream.write(b''.join(line for offset,line in rows))
  raw=pin(D/('actual-review-'+chunk+'.raw.jsonl'));exit_value=1 if ordinal==1089 else 0
  assert host['exit_code']==exit_value and 'Python_exit='+str(exit_value) in host['output']
  binding=save('actual-review-'+chunk+'.binding.json',dict(schema='researchos.old21-independent-caller-actual-review-host-binding.v1',review_author=ACTOR,reviewer_thread_id=identity['id'],parent_root_thread_id=ROOT_THREAD,
   source_audit_path=AUDIT.as_posix(),source_prefix_size_observed=size,source_line_offsets=[offset for offset,line in rows],source_line_bytes=[len(line) for offset,line in rows],original_line_sha256=[hashlib.sha256(line).hexdigest() for offset,line in rows],original_capture_ref=raw,
   original_call_id=first[2]['payload']['call_id'],tool_call_timestamp=first[2]['timestamp'],tool_result_timestamp=last[2]['timestamp'],chunk_id=chunk,actual_outer_exit=exit_value,actual_python_exit=exit_value,
   actual_native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,Root_assigned_original_ordinal=ordinal,original_invocation_retained=True,counter_reset=False,execution_grant=False,formal_acceptance=False))
  results.append(dict(chunk_id=chunk,original_ordinal=ordinal,raw_ref=raw,binding_ref=binding,outer_exit=exit_value,Python_exit=exit_value))
 return results

def actual_Source_final(m,source):
 size=ROOT_AUDIT.stat().st_size;lower=max(0,size-64*1024*1024);selected=None
 actor=source['source_author'].removeprefix('codex:');envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor+'\nPayload:\n'
 required=[pin(Q/'HDF.json'),pin(Q/'MF.json'),source['caller_ref'],source['contract_ref']]
 with ROOT_AUDIT.open('rb') as stream:
  header=stream.readline();stream.seek(lower)
  if lower:stream.readline()
  previous=None
  while stream.tell()<size:
   offset=stream.tell();line=stream.readline()
   if offset+len(line)>size:break
   row=json.loads(line);payload=row.get('payload')
   if row.get('type')=='response_item' and type(payload) is dict and payload.get('type')=='agent_message' and payload.get('author')==actor and payload.get('recipient')=='/root':
    content=payload.get('content')
    if type(content) is list and len(content)==1 and type(content[0]) is dict and type(content[0].get('text')) is str and content[0]['text'].startswith(envelope):
     try:body=m.strict(content[0]['text'][len(envelope):])
     except (ValueError,TypeError):body=None
     if type(body) is dict:
      triples=[v for v in m.structured_documents(body) if type(v) is dict and set(v)=={'path','sha256','bytes'}]
      if all(any(m.same_ref(want,got) for got in triples) for want in required) and previous and previous[2].get('type')=='inter_agent_communication_metadata':selected=(header,previous,(offset,line,row))
   previous=(offset,line,row)
 assert selected is not None,'ACTUAL_TASK73_SOURCE_FINAL_REQUIRED'
 header,first,last=selected;rows=[(0,header),(first[0],first[1]),(last[0],last[1])]
 assert first[2]['ordinal']+1==last[2]['ordinal'] and first[2]['timestamp']==last[2]['timestamp'] and last[2]['metadata']['client_authored'] is False
 with ROOT_AUDIT.open('rb') as stream:
  for offset,line in rows:stream.seek(offset);assert stream.readline()==line
 with (D/'actual-Task73-Source-author-Root-Final.raw.jsonl').open('xb') as stream:stream.write(b''.join(line for offset,line in rows))
 raw=pin(D/'actual-Task73-Source-author-Root-Final.raw.jsonl')
 binding=save('actual-Task73-Source-author-Root-Final.observation.json',dict(schema='researchos.independent-actual-Source-author-observation.v1',observed_by=ACTOR,source_author=source['source_author'],source_thread_id=source['source_thread_id'],root_thread_id=ROOT_THREAD,
  source_audit_path=ROOT_AUDIT.as_posix(),source_prefix_size_observed=size,source_line_offsets=[offset for offset,line in rows],source_line_bytes=[len(line) for offset,line in rows],original_line_sha256=[hashlib.sha256(line).hexdigest() for offset,line in rows],original_capture_ref=raw,
  original_delivery_ordinal=last[2]['ordinal'],message_id=last[2]['payload']['id'],received_at=last[2]['timestamp'],full_Source_refs=required,issued_by_Root=False,Root_witness=False,execution_grant=False,formal_acceptance=False))
 return raw,binding

def main():
 source=doc(Q/'HDF.json');mf=doc(Q/'MF.json');m=module(Q/'old21_root.source.py','old21_Source_seal_only')
 delta=doc(D/'independent-delta-checks.json');assert delta['passed']==59 and delta['failed']==0 and delta['status']=='ACCEPTED_SOURCE_ONLY'
 for name in ('independent-delta-Source-guard.closed.json','continuation-delta-Source-guard.closed.json'):
  guard_doc=doc(D/name);assert guard_doc['closed'] and guard_doc['retained_handles_count']==0 and not guard_doc['errors']
 pairs=actual_review_pairs(m)
 failed=save('original1089.full-IO.json',dict(schema='researchos.old21-independent-review-original-failure.v1',original_ordinal=1089,
  actual_origin=pairs[0],original_script_ref=pin(D/'review_delta.py'),actual_closed_guard_ref=pin(D/'independent-delta-Source-guard.closed.json'),
  diagnosis='Reviewer read finite-source-guard wrapper as raw SourceReadGuard dict; KeyError closed. Original preserved.',
  actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,reset=False,Root_assigned=True))
 index=save('actual-independent-review-IO-index.json',dict(actual_pairs=pairs,original_failure_ref=failed,original_unique_failure_invocations=1,counter_reset=False))
 gm=module(m.GUARD_REF['path'],'Task76_seal_guard');guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(m.local_refs([pin(Q/'HDF.json'),pin(Q/'MF.json')]+mf['members']+[pin(D/'independent-delta-checks.json'),pin(D/'continuation-delta-Source-guard.closed.json')],m.CANON))
  old=module(P/'seal_review.py','prior_sealer_functions_only');bridged=dict(source)
  bridged['old_original_failures']=[1071,1072,1076,1077,1079];bridged['Source_old_failed_guard_status']=source['old_failed_guard_status']
  old.D=D
  author_hosts=old.original_Source_hosts(m,bridged)
  assert doc(author_hosts['path'])['pair_count']==12
  author_raw,author_observation=actual_Source_final(m,source)
 finally:
  closed=guard.close();meta_guard=save('metadata-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 when=datetime.now(timezone.utc).isoformat()
 bindings=dict(source_hdf_ref=pin(Q/'HDF.json'),source_mf_ref=pin(Q/'MF.json'),caller_ref=source['caller_ref'],registrar_ref=source['registrar_ref'],calling_contract_ref=source['contract_ref'])
 decision=save('decision.json',dict(schema='researchos.old21-caller-independent-source-decision.v1',status='ACCEPTED_SOURCE_ONLY',verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_author=ACTOR,source_author=source['source_author'],builder_source_author=source['builder_source_author'],root_thread_id=ROOT_THREAD,
  reviewer_thread_id=os.environ['CODEX_THREAD_ID'],reviewed_utc=when,independent_non_author=True,**bindings,
  finitechecks_ref=pin(D/'independent-delta-checks.json'),Source_guard_ref=pin(D/'continuation-delta-Source-guard.closed.json'),metadata_guard_ref=meta_guard,actual_review_IO_index_ref=index,original_failure_ref=failed,
  actual_Source_author_final_raw_ref=author_raw,actual_Source_author_final_observation_ref=author_observation,Source_author_original_host_audit_ref=author_hosts,
  prior_Task70_review_refs=source['Task70_CHANGES_REQUIRED_refs'],reused_builder_review_refs=source['known_builder_Source_review_refs'],prior32_and_builder853_not_reexecuted=True,author39_not_reexecuted=True,
  changed_functions=delta['changed_functions'],full_01_Source_inverse_verified=True,blocking_findings=[],resolved_Task70_findings=['OLD21_EMPTY_PENDING_COUNTER_ROLLBACK','OLD21_BUILDER_LEGACY_TYPED_DELIVERY_INCOMPATIBLE'],
  guard_current_closed=True,retained_handles_count=0,old_failed_guard_status='UNKNOWN_NOT_SERIALIZED',old_original_failures_retained=[1071,1072,1076,1077,1079],new_original_review_failure_retained=1089,
  Root_required_next=['Capture this actual normal FINAL as original Root header+peer metadata+message, then Root actual Source review witness','New resource-only old21 Scope and independent complete runtime manifest/source/resource qualification','Root fresh current4/resume/case/output paths/acyclic owner-worker and valid lease','Root dynamic CAS propose/check/activate with complete inverse and pending once-only ledger','Already completed actual OLD21_BUILD_PREREQUISITES hostpair before execute','Actual old21 dual control/backup offline build under Owned Job; preserve full returned state','Postreturn complete actual Root call/result, then independent programme qualification'],
  Source_only=True,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,
  RootScope_or_runtime_qualification_created=False,actual_Go_Native_SQL_model_dispatcher_TP_calls=0,live_Canon_held=0,STOP=True))
 local=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
 manifest=save('MF.json',dict(schema='researchos.old21-caller-independent-source-manifest.v1',review_author=ACTOR,source_author=source['source_author'],members=local,excluded=['HDF.json','MF.json','postpublication guard/interface/seal outputs'],execution_grant=False,formal_acceptance=False))
 hdf=save('HDF.json',dict(schema='researchos.old21-caller-independent-source-handoff.v1',status='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_author=ACTOR,source_author=source['source_author'],builder_source_author=source['builder_source_author'],root_thread_id=ROOT_THREAD,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],reviewed_utc=when,independent_non_author=True,**bindings,
  manifest_ref=manifest,source_decision_ref=decision,decision_ref=decision,finitechecks_ref=pin(D/'independent-delta-checks.json'),Source_guard_ref=pin(D/'continuation-delta-Source-guard.closed.json'),actual_review_IO_index_ref=index,original_failure_ref=failed,
  Source_delta_checks_passed=59,Source_checks_unresolved=0,current_review_guards_closed=True,retained_handles_count=0,old_failed_guard_status='UNKNOWN_NOT_SERIALIZED',original1089_retained=True,
  Source_only=True,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,STOP=True))
 held=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  held.acquire(m.local_refs([hdf,manifest,decision]+local+[pin(Q/'HDF.json'),pin(Q/'MF.json'),source['caller_ref'],source['contract_ref']]))
  tree=ast.parse(Path(source['caller_ref']['path']).read_bytes());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='own_review')
  end=next(i for i,x in enumerate(function.body) if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='witness' for y in x.targets))
  function.body=function.body[:end]+[ast.Return(value=ast.Constant(value=True))];function.name='published_Source_prefix_only'
  ns=dict(m.__dict__);exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'<actual published own_review Source prefix only>','exec'),ns)
  request=dict(source_hdf_ref=bindings['source_hdf_ref'],source_mf_ref=bindings['source_mf_ref'],review_hdf_ref=hdf,review_mf_ref=manifest,review_decision_ref=decision,Source_only_interface_check=True)
  assert ns['published_Source_prefix_only'](request) is True
  try:m.own_review(request)
  except KeyError as exc:assert exc.args==('review_hostpair_witness_ref',)
  else:raise ValueError('ROOT_EXTERNAL_WITNESS_MUST_REMAIN_REQUIRED')
 finally:
  closed=held.close();published_guard=save('published-review-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
 interface=save('published-own-review-interface.json',dict(actual_published_Source_HDF_MF_decision_prefix_pass=True,review_refs=[hdf,manifest,decision],Root_external_witness_still_required=True,RootScope_qualification_or_grant_created=False,Source_only=True,Source_guard_ref=published_guard,execution_grant=False,formal_acceptance=False))
 seal=save('complete-independent-Source-review-seal.json',dict(status='ACCEPTED_SOURCE_ONLY',review_refs=[hdf,manifest,decision],published_interface_ref=interface,published_guard_ref=published_guard,original_failure_ref=failed,actual_review_IO_index_ref=index,
  current_review_guards_closed=True,retained_handles_count=0,old_unknown_guards_preserved=True,execution_grant=False,formal_acceptance=False,STOP=True))
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',review_refs=[hdf,manifest,decision],original1089_ref=failed,original1089_raw_ref=pairs[0]['raw_ref'],original1089_binding_ref=pairs[0]['binding_ref'],seal_ref=seal,guard_ref=published_guard,delta_checks=59,closed0=True,execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))
if __name__=='__main__':main()
