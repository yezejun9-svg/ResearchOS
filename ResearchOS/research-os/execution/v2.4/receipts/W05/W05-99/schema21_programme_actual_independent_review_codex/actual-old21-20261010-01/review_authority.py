"""Review original Root observations only; grants and registration are never invoked."""
from pathlib import Path
import json,hashlib,types,ntpath,datetime,traceback
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
C=B/'integration_codex/old21-caller-9c80f2c133f443bb8a2a629680cbba5d';ROOT='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
Q=B/'fresh_main23_programme_actual_independent_review_codex/actual-main23-20261010-01/review_checks.py'
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
q=types.ModuleType('authority_read_primitives');exec(compile(Q.read_bytes(),str(Q),'exec'),q.__dict__)
checks=[]
def need(ok,label):q.need(ok,label);checks.append(label)
def refs(x):
 if isinstance(x,dict):
  if set(x)==q.REF_KEYS:return [x]
  return [r for v in x.values() for r in refs(v)]
 if isinstance(x,list):return [r for v in x for r in refs(v)]
 return []
def candidates(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from candidates(v)
 elif isinstance(x,list):
  for v in x:yield from candidates(v)
 elif isinstance(x,str):
  try:v=json.loads(x)
  except (ValueError,TypeError):return
  if not isinstance(v,str):yield from candidates(v)
sealref=pin(D/'old21.v3.actual.complete-hostpair-seal.root.json')
need(sealref['sha256']=='9150002913211f281505f16d841e7b0ca73ad474e33338a6d5c859e4995a2014','EXACT_ROOT_SEAL')
seal=q.doc(sealref);state=q.doc(seal['persisted_builder_state_ref']);caller=q.doc(seal['caller_return_ref']);actual=q.doc(seal['actual_request_ref']);scope=q.doc(actual['scope_ref']);facts=q.doc(actual['facts_ref']);activation=q.doc(actual['registration_result_ref']);runtime=q.doc(actual['runtime_qualification_ref']);prior=q.doc(actual['prebuild_host_binding_ref'])
contract=q.doc(state['contract_ref']);registration=q.doc(scope['registration_request_ref']);runtime_review=q.doc(runtime['review_decision_ref'])
post_archives=[pin(D/('historical.cp374.before-old21.'+n)) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
allrefs={};live={q.canonical(str(R/'execution/v2.4'/n)) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}
for r in [pin(__file__),pin(Q),sealref,state['contract_ref']]+post_archives+refs(seal)+refs(actual)+refs(scope)+refs(facts)+refs(activation)+refs(registration)+[actual['runtime_qualification_ref'],actual['prebuild_host_binding_ref'],prior['original_capture_ref'],runtime['review_hdf_ref'],runtime['review_mf_ref'],runtime['review_decision_ref'],runtime['caller_ref'],state['root_context']['source_review_ref'],state['root_context']['caller_source_review_ref']]:
 key=q.canonical(r['path'])
 if key in live:continue
 need(key not in allrefs or q.ref_key(allrefs[key])==q.ref_key(r),'CONSISTENT_AUTHORITY_PIN_'+str(len(allrefs)));allrefs[key]=r
gm=types.ModuleType('authority_read_guard');exec(compile(q.exact(contract['source_guard_ref']),contract['source_guard_ref']['path'],'exec'),gm.__dict__)
allrefs[q.canonical(contract['source_guard_ref']['path'])]=contract['source_guard_ref']
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);error=None;result={}
try:
 guard.acquire(list(allrefs.values()))
 need(seal['root_thread_id']==ROOT and seal['issued_by']=='codex:/root','ROOT_SEAL_IDENTITY')
 need(caller['builder_returned_state']==state and caller['actual_request_ref']==seal['actual_request_ref'],'SEALED_ACTUAL_DURABLE_PAIR')
 need(state['root_context']['root_request_ref']==seal['actual_request_ref'] and state['root_context']['scope_ref']==actual['scope_ref'],'ROOT_CONTEXT_SCOPE_BINDING')
 need(scope['issued_by']==facts['issued_by']==actual['issued_by']=='codex:/root' and scope['builder_ref']==contract['builder_ref'] and scope['builder_contract_ref']==state['contract_ref'] and scope['case_request_ref']==state['request_ref'],'ROOT_SCOPE_CASE_SOURCE')
 need(activation['facts_ref']==actual['facts_ref'] and activation['scope_ref']==actual['scope_ref'] and activation['mode']=='activate' and activation['complete_inverse'] is True,'ROOT_ACTIVATION_SCOPE')
 need(activation['proposed_after_refs']==actual['current_canonical_refs'][:2] and activation['SS_CM_unchanged'] is True,'ROOT_ACTIVATION_POST_VECTOR')
 for current,archive in zip(actual['current_canonical_refs'],post_archives):need((current['sha256'],current['bytes'])==(archive['sha256'],archive['bytes']),'FULL_POST_ACTUAL_ARCHIVE_EXACT')
 need(activation['full_before_archive_refs']==facts['before_archive_refs'],'ROOT_REGISTRATION_BEFORE_ARCHIVES')
 for current,archive in zip(facts['before_canonical_refs'],facts['before_archive_refs']):need((current['sha256'],current['bytes'])==(archive['sha256'],archive['bytes']),'HISTORICAL_BEFORE_ARCHIVE_EXACT')
 need(runtime['status']=='QUALIFIED_FOR_OLD21_BUILD' and runtime['formal_programme_qualification'] is False and runtime['root_thread_id']==ROOT and runtime['independent_non_author'] is True,'ROOT_RESOURCE_QUALIFIED')
 need(runtime['builder_contract_ref']==state['contract_ref'] and runtime['runtime_manifest_ref']==state['root_context']['runtime_manifest_ref'],'RUNTIME_EXACT_BUILD_INPUTS')
 need(runtime_review['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and runtime_review['resource_refs']==runtime['resource_refs'],'INDEPENDENT_RUNTIME_DECISION_EXACT')
 need(state['qualified_resource_binding']['source_author']==contract['source_author'] and state['qualified_resource_binding']['reviewer_actor']!=contract['source_author'],'NONAUTHOR_BUILDER_SOURCE_REVIEW')
 need(seal['program_refs']==state['candidate_for_independent_review']['program_refs'] and seal['closed_receipt_ref']==state['closed_receipt']['ref'],'SEAL_EXACT_CANDIDATES')
 audits=[]
 def original(binding_ref,raw_ref,label):
  binding=q.doc(binding_ref);raw=q.exact(raw_ref);parts=[]
  need(binding['original_capture_ref']==raw_ref and binding['root_thread_id']==ROOT,'ORIGINAL_BINDING_'+label)
  with Path(binding['source_audit_path']).open('rb') as f:
   for offset,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(offset);part=f.read(size);need(len(part)==size and hashlib.sha256(part).hexdigest()==digest,'ORIGINAL_AUDIT_LINE_'+label);parts.append(part)
  need(len(parts)==3 and b''.join(parts)==raw,'FULL_ORIGINAL_API_BYTES_'+label)
  rows=[json.loads(x) for x in parts]
  need(rows[0]['payload']['id']==ROOT and rows[1]['payload']['call_id']==rows[2]['payload']['call_id']==binding['original_call_id'],'ORIGINAL_ROOT_CALL_ID_'+label)
  return rows,binding
 priorrows,pb=original(actual['prebuild_host_binding_ref'],prior['original_capture_ref'],'prerequisites')
 for p in seal['complete_original_hostpairs']:
  chunk=p['actual_chunk_id'];rows,binding=original(p['capture_binding_ref'],p['original_raw_ref'],chunk)
  matches=[x for x in candidates(rows[2]['payload']['output']) if x.get('chunk_id')==chunk]
  need(len(matches)==1,'ACTUAL_CHUNK_UNIQUE_'+chunk);observed=matches[0]
  need(observed.get('exit_code')==p['actual_exit'] and observed.get('session_id')==p['actual_session_id'],'ACTUAL_SESSION_EXIT_'+chunk)
  audits.append(dict(chunk=chunk,call=rows[1],result=rows[2],observed=observed,binding_ref=p['capture_binding_ref']))
 need([a['chunk'] for a in audits]==['fabc19','1e8ac7','bc2712','d24278','d33198','59a3a4','4710a4','b5c6ba','56a923'],'EXACT_ACTUAL_HOST_SEQUENCE')
 start=audits[1];finish=audits[6]
 need(start['observed']['session_id']==17390,'ACTUAL_BUILD_SESSION')
 for a in audits[2:7]:need('17390' in a['call']['payload']['input'],'ORIGINAL_BUILD_POLL_SESSION_'+a['chunk'])
 need(seal['actual_request_ref']['sha256'] in start['call']['payload']['input'],'ACTUAL_START_EXACT_REQUEST')
 need(finish['observed']['exit_code']==0 and 'PYTHON_EXIT' in finish['observed']['output'] and '0' in finish['observed']['output'],'ACTUAL_BUILD_OUTER_PYTHON_ZERO')
 need('truncat' in finish['observed']['output'].lower() and seal['actual_API_stdout_truncation_retained'] is True,'ORIGINAL_STDOUT_TRUNCATION_PRESERVED')
 starttime=datetime.datetime.fromisoformat(start['call']['timestamp'].replace('Z','+00:00'));endtime=datetime.datetime.fromisoformat(finish['result']['timestamp'].replace('Z','+00:00'));lease=datetime.datetime.fromisoformat(scope['lease_expires_at']);prior_time=datetime.datetime.fromisoformat(priorrows[2]['timestamp'].replace('Z','+00:00'))
 need(prior_time<starttime<endtime<lease,'ORIGINAL_HOST_TIME_WITHIN_SCOPE')
 need(all(starttime.timestamp()*1e9<=x['started_at_unix_ns']<=x['ended_at_unix_ns']<=endtime.timestamp()*1e9 for x in state['calls']),'ALL_NINE_GO_WITHIN_ORIGINAL_HOST_INTERVAL')
 result=dict(root_thread_id=ROOT,root_scope_ref=actual['scope_ref'],root_actual_request_ref=seal['actual_request_ref'],root_complete_hostpair_seal_ref=sealref,original_hostpairs_checked=9,prior_hostpair_checked=True,caller_ref=runtime['caller_ref'],runtime_qualification_ref=actual['runtime_qualification_ref'],builder_contract_ref=state['contract_ref'],original_api_truncation_preserved=True,durable_json_lossless_python_ints=True,live_canonical_read=False,formal_acceptance=False,execution_grant=False)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closed=guard.close()
gr=save('authority-Source-guard.closed.json',closed);q.clean_guard(closed)
out=save('authority-review-checks.json',dict(status='ROOT_ACTUAL_AUTHORITY_REVIEW_PASSED' if error is None else 'REVIEW_DIAGNOSTIC_FAILURE',check_count=len(checks),checks=checks,error=error,result=result,guard_ref=gr,held_refs=len(allrefs),formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=out,guard_ref=gr,checks=len(checks),error=error),ensure_ascii=False),flush=True);print('PYTHON_EXIT_CODE='+str(1 if error else 0),flush=True)
raise SystemExit(1 if error else 0)
