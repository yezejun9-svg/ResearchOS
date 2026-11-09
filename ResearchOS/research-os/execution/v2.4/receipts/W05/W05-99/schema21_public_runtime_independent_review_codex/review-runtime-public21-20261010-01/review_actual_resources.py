"""Independent bounded resource review. No Root stage, database or child call."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,ntpath,re,sys,traceback,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02';S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
Q=S/'public21-current-resource-root-20261010-02';M=B/'integration_codex/public21-runtime-3260013e7e24465cbce754a9c534262d';D=Path(__file__).resolve().parent
ROOT='codex:/root';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98';AUTHOR='codex:/root/backup_regression_resources';REVIEWER='codex:/root/full_w09_source_review'
LOG=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
SUPPORT=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
support=types.ModuleType('bounded_review_support');support.__file__=str(SUPPORT);exec(compile(SUPPORT.read_bytes(),str(SUPPORT),'exec'),support.__dict__);support.D=D
pin=support.pin
def ref(p,sha,size):return {'path':str(p),'sha256':sha,'bytes':size}
MANIFEST=ref(M/'runtime-manifest.root.json','e115d3ad0cdbe60d211527a9053097164cb4ac002248ce71fc2cba8e9c60d8a2',153704)
SCOPE=ref(Q/'qualification-scope.root.json','ac1dea4fd51ef2e844030d04c93d0ec2165506c0e9b0611af14df775622bf6e7',1631)
REQUEST=ref(Q/'runtime-prepare.request.root.json','489eb1dca3047116e1ef8bf5b2424b7e732247a7c5def783a4af4638d986d091',6775)
PREPARE_GUARD=ref(M/'prepare.guard.closed.json','5beebd15f34a94350a8a439604236a27b3465099213681f7847f5de7c305ef86',191371)
SCOPE_AUDIT=ref(S/'w09.public21-caller02-runtime-scope-issued.actual-audit.root.json','f022aeb9f25e02916f1dd93fb6351a1c152058fb47afbdb2467c4335cd07b1a9',1105)
PREPARE_AUDIT=ref(S/'w09.public21-caller02-runtime-prepare-completed.actual-audit.root.json','31ef58f1ee83aa276733251ad7060d1a0083a3ec2aed14fbb1f51f76bb088b8a',1110)
checks=[];details={};failure=None;closed=None
def check(name,ok,evidence=None):
 entry={'name':name,'passed':bool(ok)}
 if evidence is not None:entry['evidence']=evidence
 checks.append(entry)
 if not ok:raise ValueError(name)
def strict(raw):
 def pairs(xs):
  out={}
  for k,v in xs:
   if k in out:raise ValueError('DUPLICATE_JSON_KEY')
   out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
def key(p):return ntpath.normcase(ntpath.normpath(str(p)))
def when(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def plain(ref):return type(ref) is dict and set(ref)=={'path','sha256','bytes'} and type(ref['path']) is str and type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None and type(ref['bytes']) is int and ref['bytes']>=0
def preliminary(r):
 raw=Path(r['path']).read_bytes()
 if len(raw)!=r['bytes'] or hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('PRELIMINARY_INPUT_PIN')
 return strict(raw)
manifest=preliminary(MANIFEST);scope_audit=preliminary(SCOPE_AUDIT);prepare_audit=preliminary(PREPARE_AUDIT)
resources=manifest['resource_refs'];extras=[MANIFEST,SCOPE,REQUEST,PREPARE_GUARD,SCOPE_AUDIT,PREPARE_AUDIT,scope_audit['original_capture_ref'],prepare_audit['original_capture_ref']]
allrefs=[];seen={}
for r in resources+extras:
 if not plain(r):raise ValueError('EXACT_RESOURCE_REF_SHAPE')
 k=key(r['path'])
 if k in seen:
  if seen[k]!=r:raise ValueError('DUPLICATE_PATH_DISTINCT_REF_OBJECT')
 else:seen[k]=r;allrefs.append(r)
live={key(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')}
if any(key(r['path']) in live for r in allrefs):raise ValueError('LIVE_CANON_RESOURCE_HANDLE_FORBIDDEN')
held=support.guard()
def raw(r):return held.get_buffer(r['path'])
def doc(r):return strict(raw(r))
def required(rs,label):
 missing=[r for r in rs if key(r['path']) not in resource_map or resource_map[key(r['path'])]!=r]
 check(label,not missing,{'required_count':len(rs),'missing':missing})
def members(value):return [{k:r[k] for k in ('path','sha256','bytes')} for r in value['members']]
def root_pair(audit_ref,expected_chunk,binding_digest):
 audit=doc(audit_ref);lines=raw(audit['original_capture_ref']).splitlines(keepends=True)
 check(expected_chunk+'_root_original_three_rows',len(lines)==3 and all(x.endswith(b'\n') for x in lines) and audit['actor_id']==ROOT and audit['Root_thread_id']==THREAD and Path(audit['source_audit_path'])==LOG and audit['binding_sha256']==binding_digest)
 rows=[strict(x) for x in lines]
 check(expected_chunk+'_root_original_offsets',type(audit['source_prefix_size_observed']) is int and all(type(x) is int and 0<=x<audit['source_prefix_size_observed'] for x in audit['source_line_offsets']) and len(audit['source_line_offsets'])==3 and [hashlib.sha256(x).hexdigest() for x in lines]==audit['original_line_sha256'])
 with LOG.open('rb') as f:
  for offset,line in zip(audit['source_line_offsets'],lines):f.seek(offset);check(expected_chunk+'_readback_'+str(offset),f.read(len(line))==line)
 a,z=rows[1],rows[2];call,out=a['payload'],z['payload']
 check(expected_chunk+'_actual_root_identity',rows[0]['type']=='session_meta' and rows[0]['payload']['id']==THREAD and call['type']=='custom_tool_call' and out['type']=='custom_tool_call_output' and call['call_id']==out['call_id'] and call['name']=='exec' and 'tools.exec_command' in call['input'])
 hosts=[x for x in support.docs(out['output']) if 'chunk_id' in x]
 check(expected_chunk+'_actual_host_exit',len(hosts)==1 and hosts[0]['chunk_id']==expected_chunk and type(hosts[0]['exit_code']) is int and hosts[0]['exit_code']==0 and hosts[0]['output'].splitlines()[-1]=='ROOT_ACTUAL_PYTHON_EXIT=0')
 text=hosts[0]['output'];typed=[strict(x) for x in text.splitlines() if x.startswith('{')]
 check(expected_chunk+'_single_typed_result',len(typed)==1 and type(typed[0]) is dict and typed[0]['execution_grant'] is False and typed[0]['formal_acceptance'] is False)
 cmdmatch=re.search(r'cmd:("(?:[^"\\]|\\.)*")',call['input']);check(expected_chunk+'_real_command_decoded',cmdmatch is not None)
 cmd=json.loads(cmdmatch.group(1));check(expected_chunk+'_locked_python',cmd.startswith("& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -B -X utf8 "))
 return dict(call_timestamp=a['timestamp'],result_timestamp=z['timestamp'],command=cmd,result=typed[0],call_id=call['call_id'],raw_ref=audit['original_capture_ref'],audit_ref=audit_ref)
try:
 held.acquire(allrefs)
 manifest=doc(MANIFEST);scope=doc(SCOPE);request=doc(REQUEST);prepare_guard=doc(PREPARE_GUARD)
 resource_map={key(r['path']):r for r in resources}
 check('exact_unique_ordered_current_resource_refs',len(resource_map)==len(resources) and all(plain(r) for r in resources),{'count':len(resources),'bytes':sum(r['bytes'] for r in resources),'all_refs_acquired':len(allrefs)})
 check('prepare_guard_exact_full_resource_array',prepare_guard['verification']=='PASSED' and prepare_guard['closed'] is True and prepare_guard['retained_handles_count']==0 and prepare_guard['failure'] is None and prepare_guard['errors']==[] and prepare_guard['share_mode']=='FILE_SHARE_READ_ONLY' and [{k:e[k] for k in ('path','sha256','bytes')} for e in prepare_guard['entries']]==resources and all(e['verified'] is True and e['final_path_match'] is True and e['closed'] is True for e in prepare_guard['entries']))
 check('new_root_scope_manifest_actor_and_source_binding',manifest['schema']=='researchos.root-public21-runtime-manifest.v1' and scope['schema']=='researchos.root-public21-runtime-qualification-scope.v1' and scope['slice_id']=='PUBLIC21_RUNTIME_RESOURCE_QUALIFICATION' and manifest['issued_by']==scope['issued_by']==request['issued_by']==ROOT and manifest['root_thread_id']==scope['root_thread_id']==request['root_thread_id']==THREAD and manifest['source_author']==manifest['runner_source_author']==AUTHOR and all(v['execution_grant'] is False for v in (manifest,scope,request)) and manifest['formal_acceptance'] is scope['formal_acceptance'] is False and all(manifest[k]==scope[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref')) and manifest['qualification_scope_ref']==request['qualification_scope_ref']==SCOPE and request['source_hdf_ref']==scope['source_hdf_ref'] and request['source_mf_ref']==scope['source_mf_ref'])
 start,end=when(scope['created_utc']),when(scope['lease_expires_at']);now=datetime.now(timezone.utc)
 check('finite_fresh_resource_only_scope',start<=now<end and 0<(end-start).total_seconds()<=1800,{'created':scope['created_utc'],'expires':scope['lease_expires_at'],'review_checked_utc':now.isoformat(),'remaining_seconds':(end-now).total_seconds()})
 scope_pair=root_pair(SCOPE_AUDIT,'205cad',SCOPE['sha256']);prepare_pair=root_pair(PREPARE_AUDIT,'4478a1',MANIFEST['sha256'])
 check('actual_root_scope_issued_before_actual_cli_prepare',when(scope_pair['call_timestamp'])<=start<=when(scope_pair['result_timestamp'])<=when(prepare_pair['call_timestamp'])<=when(prepare_pair['result_timestamp'])<=now and scope_pair['result']['qualification_scope_ref']==SCOPE and prepare_pair['result']['runtime_manifest_ref']==MANIFEST and prepare_pair['result']['independent_runtime_review_required'] is True and prepare_pair['result']['Root_qualification_issuance_required'] is True)
 cmd=prepare_pair['command'];cli=str(N/'public21_root.source.py').replace('\\','/')
 check('real_prepare_fixed_same_source_cli_request',"'"+cli+"' prepare '"+REQUEST['path']+"' "+REQUEST['sha256']+' '+str(REQUEST['bytes']) in cmd and request['output_root']==str(M) and scope_pair['result']['current_refs']==request['before_canonical_refs'] and scope_pair['result']['expected_revisions']==request['expected_revisions'],{'future_entry_must_be':manifest['caller_ref'],'prepared_as___main__':True,'Root_helpers_are_not_runtime_entry':True})
 check('no_live_canon_held',not any(key(r['path']) in live for r in allrefs),{'historical_current4_is_data_only':request['expected_revisions']})
 source=doc(manifest['source_hdf_ref']);source_mf=doc(manifest['source_mf_ref']);caller_ref=source['caller_ref'];contract=doc(manifest['runner_contract_ref']);leaf_hdf=doc(request['runner_source_refs']['hdf']);leaf_mf=doc(request['runner_source_refs']['mf'])
 caller=support.inert(caller_ref['path'],raw(caller_ref));base=caller.base()
 check('current_source_entry_and_same_locked_python',manifest['caller_ref']==caller_ref==source['registrar_ref'] and scope['caller_ref']==caller_ref and contract['locked_python_ref']==resource_map[key(sys.executable)] and contract['locked_python_ref']['path']==str(Path(sys.executable)))
 required([manifest['source_hdf_ref'],manifest['source_mf_ref'],caller_ref,caller.OC3_REF,base.GUARD_REF,base.TP_REF,contract['locked_python_ref'],*request['runner_source_refs'].values(),leaf_hdf['input_manifest_ref'],caller.PROGRAMME_REF,contract['owned_job']], 'mandatory_caller_leaf_guard_TP_python_owned_job_refs')
 groups={'CallerSourceMF':members(source_mf),'LeafSourceMF':members(leaf_mf),'CallerAcceptedReviewMF':members(doc(request['review_mf_ref'])),'LeafAcceptedReviewMF':members(doc(request['runner_review_refs']['mf'])),'LeafInputManifest':doc(leaf_hdf['input_manifest_ref'])['references']}
 for name,refs in groups.items():required(refs,'complete_'+name)
 programme=doc(caller.PROGRAMME_REF);programme_mf=doc(programme['review_refs'][1]);required([*programme['review_refs'],*members(programme_mf),*programme['program_refs'].values(),programme['provenance_ref'],programme['payload_ref'],programme['root_issuance_binding_ref'],programme['independent_peer_delivery_binding_ref']],'existing_actual_programme_qualified_closure_pins')
 check('real_qualified_old21_programmes_reused_not_reexecuted',programme['status']=='QUALIFIED_OLD21_BUILD' and programme['independent_non_author'] is True and programme['all_owned_jobs_idle_and_closed'] is True and programme['formal_acceptance'] is False and programme['execution_grant'] is False and contract['old21_control']==programme['program_refs']['control'] and contract['old21_backup']==programme['program_refs']['backup'])
 source_witness=doc(request['review_hostpair_witness_ref']);runner_witness=doc(request['runner_review_witness_ref'])
 observer_groups=[('SOURCE_REVIEW_WITNESS',source_witness,[request[k] for k in ('review_hdf_ref','review_mf_ref','review_decision_ref')],REVIEWER),('RUNNER_SOURCE_REVIEW_WITNESS',runner_witness,list(request['runner_review_refs'].values()),'codex:/root/attach_restore_independent_review')]
 for operation,witness,expected,actor in observer_groups:
  binding_ref=witness['capture_binding_ref'];binding=doc(binding_ref);capture=raw(binding['original_capture_ref'])
  caller.validate_root_capture(binding,capture,expected,operation,actor)
  check('fresh_actual_'+operation+'_identity_refs_offsets',witness['issued_by']==ROOT and witness['root_thread_id']==THREAD and when(binding['tool_result_timestamp'])<=when(witness['created_utc'])<=start,{'binding_ref':binding_ref,'review_refs':expected})
 pre=doc(request['preparation_host_binding_ref']);expected=[SCOPE,manifest['source_hdf_ref'],manifest['source_mf_ref'],*request['runner_review_refs'].values(),*request['before_canonical_refs']]
 caller.validate_root_capture(pre,raw(pre['original_capture_ref']),expected,'RUNTIME_MANIFEST_PREREQUISITES')
 check('fresh_actual_runtime_prerequisite_capture_full_refs',when(scope_pair['result_timestamp'])<=when(pre['tool_call_timestamp'])<=when(pre['tool_result_timestamp'])<=when(prepare_pair['call_timestamp']),{'binding_ref':request['preparation_host_binding_ref'],'live_refs_not_reread_or_held':True})
 import sqlite3,_sqlite3
 job=support.inert(contract['owned_job']['path'],raw(contract['owned_job']));loaded_resources=[pin(p) for p in job.runtime_resource_paths()]
 required(loaded_resources,'actual_loaded_python_windows_SQLite_DLL_runtime_resources')
 sqlite_required=[pin(sqlite3.__file__),pin(_sqlite3.__file__),pin(Path(sys.executable).parent/'DLLs/sqlite3.dll')]
 required(sqlite_required,'mandatory_actual_SQLite_extension_DLL_stdlib')
 interpreter_refs=[]
 for name,module in tuple(sys.modules.items()):
  if module is sys.modules.get('__main__'):continue
  for field in ('__file__','__cached__'):
   p=getattr(module,field,None)
   if p and Path(p).is_file() and Path(p).is_relative_to(Path(sys.executable).parent):interpreter_refs.append(pin(p))
 required(interpreter_refs,'actual_required_interpreter_stdlib_and_existing_cache')
 counts={}
 for r in resources:counts[Path(r['path']).suffix.lower()]=counts.get(Path(r['path']).suffix.lower(),0)+1
 details={'scope_pair':scope_pair,'prepare_pair':prepare_pair,'mandatory_group_counts':{name:len(refs) for name,refs in groups.items()},'runtime_loaded_resource_refs':loaded_resources,'interpreter_observed_refs':interpreter_refs,'resource_suffix_counts':counts,'resource_refs':resources,'expected_common_fields':{k:manifest[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref','qualification_scope_ref')},'python_ref':contract['locked_python_ref'],'control_ref':contract['old21_control'],'prior_successes_reused':{'Task106_Source_checks':14,'Task106_current_Source_guard_refs':59,'Caller01_Source_controls':58,'historic_runtime_refs':353,'historic_Source_checks':17,'new_product_calls':0},'later_actual_root_payload_wrapper_and_peer_witness':'REQUIRED_AFTER_THIS_TRUE_FINAL_NOT_EMITTED'}
except BaseException as e:
 failure={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 closed=held.close();guard_ref=support.write('runtime-resources.guard.closed.json',closed)
 report=support.write('runtime-resource-review.result.json',{'schema':'researchos.public21-runtime-bounded-resource-review-result.v1','review_author':REVIEWER,'source_author':AUTHOR,'runner_source_author':AUTHOR,'root_thread_id':THREAD,'created_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'successful_check_count':sum(x['passed'] for x in checks),'failure':failure,'guard_ref':guard_ref,'details':details,'runtime_manifest_ref':MANIFEST,'qualification_scope_ref':SCOPE,'prepare_request_ref':REQUEST,'prepare_guard_ref':PREPARE_GUARD,'Root_scope_actual_audit_ref':SCOPE_AUDIT,'Root_prepare_actual_audit_ref':PREPARE_AUDIT,'actual_Root_stages_or_products':0,'formal_acceptance':False,'execution_grant':False})
print(json.dumps({'report_ref':report,'guard_ref':guard_ref,'successful_checks':sum(x['passed'] for x in checks),'failed_checks':[x['name'] for x in checks if not x['passed']],'failure':failure,'all_refs':len(allrefs),'guard_retained_handles_count':closed['retained_handles_count'],'closed':closed['closed'],'formal_acceptance':False,'execution_grant':False},ensure_ascii=False,allow_nan=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:sys.exit(1)
