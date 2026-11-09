"""Seal actual independent IO and final published Source review contract only."""
import ast,copy,hashlib,json,os,types
from datetime import datetime,timezone
from pathlib import Path
D=Path(__file__).resolve().parent
W=D.parent.parent
S=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04'
PR=W/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261010-03'
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
ACTOR='codex:/root/full_w09_source_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (D/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/name)
def inert(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def capture(m,chunks):
 limit=AUDIT.stat().st_size;calls={};found={};start=max(0,limit-64*1024*1024)
 with AUDIT.open('rb') as f:
  header=f.readline();f.seek(start)
  if start:f.readline()
  while f.tell()<limit:
   off=f.tell();line=f.readline();item=json.loads(line);p=item.get('payload')
   if item.get('type')!='response_item' or type(p) is not dict:continue
   if p.get('type') in ('custom_tool_call','function_call'):calls[p['call_id']]=(off,line,item)
   if p.get('type') in ('custom_tool_call_output','function_call_output'):
    matches={v['chunk_id']:v for v in m.structured_documents(p.get('output')) if type(v) is dict and v.get('chunk_id') in chunks and type(v.get('output')) is str}
    for chunk,result in matches.items():
     assert chunk not in found,'NONUNIQUE_ACTUAL_CHUNK'
     call=calls[p['call_id']];found[chunk]=(call,(off,line,item),result,header,limit)
 assert set(found)==set(chunks),(list(found),chunks)
 output=[]
 for chunk in chunks:
  call,last,result,header,limit=found[chunk];rows=[(0,header),(call[0],call[1]),(last[0],last[1])]
  head=json.loads(header)['payload'];assert head['id']==os.environ['CODEX_THREAD_ID']=='01a1215b-7210-7613-b033-756b9d553b83' and head['agent_path']==ACTOR.removeprefix('codex:') and head['parent_thread_id']==ROOT_THREAD
  assert result['exit_code']==0 and 'python_exit=0' in result['output'].casefold()
  with AUDIT.open('rb') as f:
   for off,line in rows:f.seek(off);assert f.read(len(line))==line
  name='actual-review-'+chunk
  with (D/(name+'.raw.jsonl')).open('xb') as f:f.write(b''.join(line for off,line in rows))
  raw=pin(D/(name+'.raw.jsonl'))
  binding=save(name+'.binding.json',dict(schema='researchos.main23-M4-independent-review-actual-tool-binding.v1',review_author=ACTOR,reviewer_thread_id=head['id'],parent_root_thread_id=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_size_observed=limit,source_line_offsets=[off for off,line in rows],source_line_bytes=[len(line) for off,line in rows],original_line_sha256=[hashlib.sha256(line).hexdigest() for off,line in rows],original_capture_ref=raw,original_call_id=call[2]['payload']['call_id'],actual_tool_name=call[2]['payload']['name'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=last[2]['timestamp'],actual_chunk_id=chunk,actual_outer_exit=0,actual_python_exit=0,Native_exit=None,Go_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,Root_grant=False))
  output.append(dict(chunk_id=chunk,raw_ref=raw,binding_ref=binding,outer_exit=0,Python_exit=0))
 return output
def main():
 m=inert(S/'main23_root.source.py','M4_published_review_inert');h=read(S/'HDF.json');finite=read(D/'finitechecks.json');stdout=read(D/'Root-tool-stdout-format.Source-interface.json');author=read(D/'actual-Source-author-FINAL-proof.json')
 assert finite['failed']==[] and finite['status']=='ACCEPTED_SOURCE_ONLY' and stdout['status']=='PASS_SOURCE_ONLY'
 pairs=capture(m,['3c3db1','7d8922','477a4a','01147a','6057f9','45b2b2','0fbeac'])
 index=save('actual-independent-tool-IO-index.json',dict(schema='researchos.main23-M4-independent-review-actual-tool-index.v1',review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],actual_pairs=pairs,Source_only=True,execution_grant=False,formal_acceptance=False))
 prh=read(PR/'HDF.json');olddecision=read(PR/'decision.json');created=datetime.now(timezone.utc).isoformat()
 decision=copy.deepcopy(olddecision)
 decision.update(review_author=ACTOR,reviewed_utc=created,source_author=h['source_author'],builder_source_author=h['builder_source_author'],root_thread_id=ROOT_THREAD,source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],calling_contract_ref=h['contract_ref'],source_inputs_ref=h['source_inputs_ref'],finitechecks_ref=pin(D/'finitechecks.json'),Source_guard_ref=finite['Source_guard_ref'],blocking_findings=[],actual_runtime_qualification_ref=None,actual_request_ref=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False)
 decision.update(status='ACCEPTED_SOURCE_ONLY',verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',reviewer_thread_id=os.environ['CODEX_THREAD_ID'],M4_time_contract='RESOLVED_INDEPENDENT_WRAPPER_CREATED_AND_EXACT_PAYLOAD_CREATED_CAUSAL_ORDER',M4_peer_FINAL_contract='RESOLVED_ANCHORED_BACKEND_FINAL_AND_STRICT_COMPLETE_JSON',prior_M3_review_refs=[pin(PR/'HDF.json'),prh['manifest_ref'],prh['source_decision_ref']],prior_14782_checks_not_rerun=True,unchanged_14670_pins_reused=True,Root_tool_decoder_unchanged=True,all_identity_resource_TP_Job_failure_gates_unchanged=True,actual_tool_IO_index_ref=index,Source_author_actual_FINAL_ref=pin(D/'actual-Source-author-FINAL-proof.json'),Root_stdout_Source_interface_ref=pin(D/'Root-tool-stdout-format.Source-interface.json'),Root1066_old_multiline_capture_not_qualified=True,original1064_ref=h['original1064_ref'],new_Source_review_failures=[],time_fixtures_and_peer_mutants_Source_only=True,Scope_qualification_witness_Root_grant_created=False,live_CP_OW_held=False,Main_Canon_Source_written=False,Go_Native_SQL_dispatcher_model_runs=0,next_Root_requirements=['Fresh Root resource-only Scope and independent actual loaded runtime review for exact M4 Source','Actual nonauthor runtime FINAL and original peer capture; no self-issued review','Single-line complete typed Root observer JSON before wrapper','Actual payload_created_utc after peer and before Root call, actual wrapper.created_utc after Root output, both no future time','Actual published Source review FINAL captured by Root then fresh Root observation witness','Fresh current4 dynamic CAS, original unique failure ledger, exact request/lease/activation inputs before product execution'])
 dr=save('decision.json',decision)
 local=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
 manifest=save('MF.json',dict(schema='researchos.main23-root-independent-source-mf.v3',review_author=ACTOR,source_author=h['source_author'],members=local,excluded=['HDF.json','MF.json','postpublication immutable guard/contract proofs and later actual seal output'],execution_grant=False,formal_acceptance=False))
 review=copy.deepcopy(prh)
 review.update(review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],reviewed_utc=created,status='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',verdict='ACCEPTED_SOURCE_ONLY',source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],calling_contract_ref=h['contract_ref'],manifest_ref=manifest,source_decision_ref=dr,finitechecks_ref=pin(D/'finitechecks.json'),Source_guard_ref=finite['Source_guard_ref'],checks=len(finite['checks'])+stdout['checks']+author['checks'],held_refs=finite['held_refs'],blocking_findings=0,execution_grant=False,formal_acceptance=False,parent_acceptance=False,actual_runtime_qualification_ref=None,Root_qualification_or_grant_created=False,prior_14782_checks_reused_not_rerun=True,actual_peer_ordinals=[60922,60970],actual_Source_author_FINAL_ref=pin(D/'actual-Source-author-FINAL-proof.json'),original1064_preserved=True,Root_stdout_Source_interface_ref=pin(D/'Root-tool-stdout-format.Source-interface.json'),actual_tool_IO_index_ref=index,all_Source_guards_closed=True,retained_handles_count=0,live_CP_OW_held=False,Source_only=True)
 hr=save('HDF.json',review)
 refs=m.local_refs([hr,manifest,dr,pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*read(h['manifest_ref']['path'])['members'],*local])
 guard=m.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(refs)
  fn=copy.deepcopy(next(n for n in ast.parse(Path(h['caller_ref']['path']).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='own_review'))
  stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='witness' for t in n.targets))
  fn.name='published_own_review_prefix';fn.body=fn.body[:stop]+[ast.Return(value=ast.Constant(value=True))];ast.fix_missing_locations(fn)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'UNCHANGED_OWN_REVIEW_PREFIX_ONLY_NO_ROOT_WITNESS','exec'),m.__dict__)
  request=dict(source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],review_hdf_ref=hr,review_mf_ref=manifest,review_decision_ref=dr)
  assert m.published_own_review_prefix(request) is True
  assert all(m.same_ref(m.pin(r['path']),r) for r in refs)
 finally:closed=guard.close();gr=save('published-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 contract=save('published-contract-check.json',dict(actual_final_HDF_MF_decision_validate_by_unmodified_own_review_prefix=True,actual_final_review_refs=[hr,manifest,dr],stop_before_actual_Root_witness=True,future_Root_witness_not_synthesized=True,actual_runtime_qualification=None,held_published_refs=len(refs),Source_guard_ref=gr,retained_handles_count=0,execution_grant=False,formal_acceptance=False))
 seal=save('complete-independent-Source-review-seal.json',dict(status='ACCEPTED_SOURCE_ONLY',verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',review_author=ACTOR,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],review_refs=[hr,manifest,dr],actual_review_hostpairs=pairs,published_contract_check_ref=contract,Source_guard_ref=gr,checks=review['checks'],new_review_failures=[],old_failure_ordinals_preserved=[1064,1065,1066],execution_grant=False,formal_acceptance=False,parent_acceptance=False,actual_runtime_qualification=None,retained_handles_count=0,STOP=True))
 print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY',review_refs=[hr,manifest,dr],published_contract_check_ref=contract,seal_ref=seal,Source_guard_ref=gr,retained_handles_count=0,execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
