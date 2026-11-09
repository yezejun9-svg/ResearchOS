import sys
sys.dont_write_bytecode=True
import hashlib,json,types,re,os,platform,stat,tempfile,subprocess,time,signal,ctypes
from pathlib import Path,PureWindowsPath

R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/w09c19-1a11f08'
W=R/'execution/v2.4/receipts/W09/W09-99'
N=Path(__file__).resolve().parent
O=W/'integration_codex/w09c19-consumers-1a11f30'
E=R/'.local/w09c19-consumers-env-1a11f30'
PRODUCER=W/'integration_codex/w09c19-producer-1a11f08'
PRODUCER_TEMP=R/'.local/w09c19-producer-env-1a11f08/temp'
ROUTES=(('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19'))
EXPECTED_NATIVE=['C19-01','C19-02','C19-03','C19-04','C19-05']
EXPECTED_FORMAL=['C19-01','C19-02','C19-03']
SELECTED=['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown']
CHOICE_SHA='6dab14b88b18f5f8117ec179f85ceafce44f06ebfe9f16b024ffc69edb537ebf'
CHOICE_BYTES=20131

def require(ok,code):
 if not ok:raise ValueError(code)
def pin(path):
 path=Path(path).resolve(strict=True);raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def typed(ref):
 require(isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'},'EXACT_TYPED_REF')
 require(isinstance(ref['path'],str) and Path(ref['path']).is_absolute(),'ABSOLUTE_REF')
 require(isinstance(ref['sha256'],str) and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None,'BARE_SHA256')
 require(type(ref['bytes']) is int and 0<=ref['bytes']<=256*1024*1024,'BOUNDED_TYPED_BYTES')
 return ref
def verify(ref):
 typed(ref);actual=pin(ref['path'])
 require(actual==dict(path=str(Path(ref['path']).resolve(strict=True)),sha256=ref['sha256'],bytes=ref['bytes']),'EXACT_REF_PIN')
 return actual
def load(ref):
 ref=verify(ref)
 with Path(ref['path']).open('rb') as f:raw=f.read(ref['bytes']+1)
 require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'EXACT_READ_PIN')
 return json.loads(raw)
def repo_relative(path):
 path=Path(path);require(path.is_absolute(),'CANDIDATE_ABSOLUTE_REF')
 lexical=path.relative_to(T);require(lexical.parts and not any(x in ('..','.') for x in lexical.parts),'CANDIDATE_RELATIVE_REF')
 current=T
 for part in lexical.parts:
  current=current/part;info=current.lstat()
  require(not current.is_symlink() and not current.is_junction() and not (getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT),'NO_CANDIDATE_REPARSE')
 require(path.resolve(strict=True)==current and current.is_file(),'CANDIDATE_REGULAR_REF')
 return lexical.as_posix()
def relative_ref(ref):
 require(isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'},'RELATIVE_TYPED_REF')
 rel=ref['path'];require(isinstance(rel,str) and rel and '\\' not in rel and not PureWindowsPath(rel).drive and ':' not in rel and not rel.startswith('/') and all(p not in ('','.','..') for p in rel.split('/')),'RELATIVE_CANONICAL_PATH')
 path=T/rel;require(repo_relative(path)==rel,'RELATIVE_ROUNDTRIP')
 return verify(dict(path=str(path),sha256=ref['sha256'],bytes=ref['bytes']))
def unique(refs):
 result={}
 for ref in refs:
  v=verify(ref);key=v['path'].casefold();require(key not in result or result[key]==v,'DUPLICATE_PIN_DRIFT');result[key]=v
 return list(result.values())
def manifest_refs(ref):
 value=load(ref)['members'];values=list(value.values()) if isinstance(value,dict) else value
 require(isinstance(values,list),'MANIFEST_MEMBERS_LIST')
 return [verify(v) for v in values]
def module(path,raw):
 m=types.ModuleType('root_c19_consumer_'+Path(path).stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),'exec'),m.__dict__);return m
def save(name,value):
 with (O/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/name)
def job_closed(result):
 if not isinstance(result,dict):return False
 cleanup=result.get('job_cleanup',{})
 return (not cleanup.get('errors') and cleanup.get('active_processes_last_observed')==0
  and all(cleanup.get(k) is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))
def validate_report_binding(request,closed,packet,report,tool,contract):
 require(closed['status']=='C19_NATIVE_PRODUCER_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW' and closed['all_owned_jobs_closed'] is True,'PRODUCER_NOT_CLOSED')
 require(closed['native_packet_ref']==request['native_packet_ref'],'CLOSED_PACKET_REF')
 require(packet['original_report_ref']==request['report_ref'] and packet['original_tool_run_ref']==request['tool_run_ref'],'PACKET_REPORT_TOOL_REF')
 require(Path(packet['consumer_source_root'])==T and packet['formal_acceptance'] is False,'PACKET_CANDIDATE')
 require(packet['run_id']==report['run_id']==tool['run_id'] and re.fullmatch('[0-9a-f]{32}',report['run_id']) is not None,'SAME_RUN')
 require(report['status']=='PASS' and report['exit_code']==0 and report['timed_out'] is False,'PRODUCER_REPORT_NOT_PASS')
 require(report['task_id']=='W09' and report['check_id'] is None and report['case_id']=='C19','EXACT_C19')
 require(report['selected_tests']==SELECTED and sorted(report['passed_tests'])==sorted(SELECTED),'EXACT_TWO_NATIVE_TESTS')
 require(sorted(report['assertion_ids'])==EXPECTED_NATIVE and report['assertions']==5,'EXACT_FIVE_NATIVE_IDS')
 require(report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING' and report['formal_case_accepted_delta']==0,'PRODUCER_NOT_FORMAL')
 require(tool['schema']=='researchos.w09-native-producer-tool-run.v1' and tool['report_sha256']==request['report_ref']['sha256'],'TOOL_REPORT_BINDING')
 require(set(report['version_manifest']['source_sha256'])==set(contract['source_roster']) and len(contract['source_roster'])==21,'EXACT_SOURCE21')
 require(tool['actual_invocation']==report['actual_invocation'] and tool['native_exit_code']==0,'TOOL_NATIVE_INVOCATION')
def validate_modes(request,report,decisions,reviews,report_relative,stdout_sha):
 require(len(request['modes'])==len(decisions)==len(reviews)==2,'EXACT_TWO_MODE_DECISIONS')
 require(request['modes'][0]['decision_ref']!=request['modes'][1]['decision_ref'],'DISTINCT_MODE_DECISIONS')
 require(request['modes'][0]['independent_review_ref']==request['modes'][1]['independent_review_ref'],'SAME_INDEPENDENT_MODE_REVIEW')
 for route,spec,d,r in zip(ROUTES,request['modes'],decisions,reviews):
  require(spec['route']==list(route) and d['route']==list(route),'MODE_ROUTE')
  require(d['schema']=='researchos.w09-mode-decision.v2' and d['mode']=='FIXTURE' and d['decision']=='QUALIFIED','QUALIFIED_MODE_ONLY')
  require(d['input_origin']=='OWNED_TEMP_DIR' and d['reviewer_role']=='INDEPENDENT_NON_AUTHOR' and d['producer_id'] and d['reviewer_id'] and d['producer_id']!=d['reviewer_id'],'MODE_NONAUTHOR')
  require(d['run_id']==report['run_id'] and d['report_ref']==report_relative and d['report_sha256']==request['report_ref']['sha256'] and d['stdout_sha256']==stdout_sha,'MODE_RUN_BINDING')
  require(d['source_sha256']==report['version_manifest']['source_sha256'] and d['go_executable']==report['go_executable'],'MODE_SOURCE_GO')
  require(r['schema']=='researchos.w09-independent-mode-review.v1' and r['actor_id']==d['reviewer_id'] and r['actor_role']=='INDEPENDENT_NON_AUTHOR' and r['producer_id']==d['producer_id'] and r['decision']=='QUALIFIED','REVIEW_NONAUTHOR')
  require(r['run_id']==report['run_id'] and r['report_sha256']==d['report_sha256'] and r['source_sha256']==d['source_sha256'] and r['go_executable']==d['go_executable'],'REVIEW_SAME_RUN')
  require(r['run_os']==report['version_manifest']['os'] and r['run_os_release']==report['version_manifest']['os_release'],'REVIEW_OS')
def validate_scope(scope,request):
 require(scope['schema']=='researchos.root-w09-c19-component-consumer-scope.v1' and scope['executor']=='codex:/root' and scope['status']=='ROOT_AUTHORIZED_COMPONENT_CONSUMPTION_ONLY','ROOT_CONSUMER_SCOPE')
 require(scope['candidate_root']==str(T) and scope['consumer_receipt_root']==str(O) and scope['consumer_environment_root']==str(E),'ROOT_FIXED_PATHS')
 require(scope['routes']==[list(r) for r in ROUTES] and scope['formal_case_accepted_delta']==0 and scope['formal_dispatcher'] is False and scope['registry_write'] is False and scope['producer_rerun'] is False,'ROOT_COMPONENT_BOUNDARY')
 for field in ('producer_closed_ref','native_packet_ref','report_ref','tool_run_ref','producer_review_handoff_ref','producer_review_manifest_ref','caller_review_handoff_ref','caller_review_manifest_ref','canonical_vector_ref','modes'):
  require(scope[field]==request[field],'ROOT_SCOPE_BINDING_'+field)
 require(scope['source_caller_ref']==pin(__file__),'ROOT_CALLER_SOURCE')
def environment(report_relative,tool_relative,mode_relative,request):
 return {'SystemRoot':'C:/Windows','WINDIR':'C:/Windows','ComSpec':'C:/Windows/System32/cmd.exe','PATH':'C:/Windows/System32','PATHEXT':'.COM;.EXE;.BAT;.CMD','USERPROFILE':str(E/'profile'),'LOCALAPPDATA':str(E/'profile'),'APPDATA':str(E/'profile'),'TEMP':str(PRODUCER_TEMP),'TMP':str(PRODUCER_TEMP),'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'C19','RESEARCHOS_W09_NATIVE_REPORT_REF':report_relative,'RESEARCHOS_W09_NATIVE_REPORT_SHA256':request['report_ref']['sha256'],'RESEARCHOS_W09_TOOL_RUN_REF':tool_relative,'RESEARCHOS_W09_TOOL_RUN_SHA256':request['tool_run_ref']['sha256'],'RESEARCHOS_W09_MODE_DECISION_REF':mode_relative,'RESEARCHOS_W09_MODE_DECISION_SHA256':request['_current_mode_sha']}

def main():
 require(len(sys.argv)==4,'usage: caller REQUEST_ABSOLUTE_PATH REQUEST_SHA256 REQUEST_BYTES')
 request_ref=verify(dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3])))
 require(Path(request_ref['path']).is_relative_to(W),'REQUEST_W09_NAMESPACE')
 request=load(request_ref);require(request['schema']=='researchos.w09-c19-component-consumer-request.v1','REQUEST_SCHEMA')
 require(not O.exists() and not E.exists(),'FRESH_CONSUMER_OUTPUT_AND_ENVIRONMENT')
 O.mkdir();E.mkdir();(E/'profile').mkdir()
 guards=[];cleanups=[];invocations=[];results=[];error=None;input_refs=[];snapshots={}
 try:
  choice_ref=verify(dict(path=str(N/'source.choice.json'),sha256=CHOICE_SHA,bytes=CHOICE_BYTES));choice=load(choice_ref)
  contract=load(choice['contract_ref']);require(contract['consumer_root']==str(T),'CONTRACT_CANDIDATE')
  gp=Path(choice['guard_ref']['path']);hp=Path(choice['owned_helper_ref']['path'])
  for v in choice['input_refs']:verify(v)
  require(pin(sys.executable)['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','LOCKED_PYTHON')
  closed=load(request['producer_closed_ref']);packet=load(request['native_packet_ref']);report=load(request['report_ref']);tool=load(request['tool_run_ref'])
  require(Path(request['producer_closed_ref']['path'])==PRODUCER/'validation.closed.json' and Path(request['native_packet_ref']['path'])==PRODUCER/'native-packet.public-index.json','EXACT_PRODUCER_RECEIPTS')
  validate_report_binding(request,closed,packet,report,tool,contract)
  report_relative=repo_relative(request['report_ref']['path']);tool_relative=repo_relative(request['tool_run_ref']['path'])
  run_dir=Path(request['report_ref']['path']).parent
  require(run_dir.parent==T/'execution/receipts/W09/retrieval' and run_dir.name=='run-'+report['run_id'],'FIXED_NATIVE_RUN_DIRECTORY')
  require(Path(request['tool_run_ref']['path']).parent==run_dir and tool['report_ref']==report_relative,'SAME_REPORT_TOOL_DIRECTORY')
  input_refs=[request_ref,choice_ref,pin(__file__)]+choice['input_refs']
  for field in ('producer_closed_ref','native_packet_ref','report_ref','tool_run_ref','producer_review_handoff_ref','producer_review_manifest_ref','caller_review_handoff_ref','caller_review_manifest_ref','root_consumer_scope_ref','canonical_vector_ref'):input_refs.append(verify(request[field]))
  input_refs+=manifest_refs(request['producer_review_manifest_ref'])+manifest_refs(request['caller_review_manifest_ref'])
  for field in ('producer_review_handoff_ref','producer_review_manifest_ref','caller_review_handoff_ref','caller_review_manifest_ref','root_consumer_scope_ref'):
   require(Path(request[field]['path']).is_relative_to(W),'REVIEW_SCOPE_W09_NAMESPACE')
  producer_review=load(request['producer_review_handoff_ref'])
  require(producer_review.get('formal_acceptance',False) is False,'PRODUCER_REVIEW_NOT_FORMAL')
  validate_scope(load(request['root_consumer_scope_ref']),request)
  vector=load(request['canonical_vector_ref']);require(vector['schema']=='researchos.w09-c19-canonical-input-vector.v1' and vector['checkpoint_revision']==365,'CANONICAL_VECTOR_CP365')
  canonical=[R/'execution/v2.4'/(n+'.json') for n in ('checkpoint','path_ownership','step_state','commands')]
  require(len(vector['refs'])==4 and {str(Path(v['path'])) for v in vector['refs']}=={str(p) for p in canonical},'EXACT_FOUR_CANONICAL')
  input_refs += [verify(v) for v in vector['refs']]
  require(json.loads(canonical[0].read_bytes())['revision']==365 and json.loads(canonical[1].read_bytes())['revision']==169,'CP365_OW169')
  pre_ref=verify(closed['canonical_pre_run_ref']);pre=load(pre_ref)
  require(pre['canonical_input_vector_ref']==request['canonical_vector_ref'] and pre['refs']==vector['refs'],'SAME_PRODUCER_CANONICAL_VECTOR')
  input_refs.append(pre_ref)
  expected_cleanup={str(PRODUCER/(n+'-source-guard.cleanup.actual.json')) for n in ('compiler','candidate','runtime','input')}
  require(len(request['producer_guard_cleanup_refs'])==4 and {str(Path(v['path'])) for v in request['producer_guard_cleanup_refs']}==expected_cleanup,'EXACT_FOUR_PRODUCER_GUARDS')
  for ref in request['producer_guard_cleanup_refs']:
   value=load(ref);require(value['closed'] is True and not value['errors'] and value['retained_handles_count']==0,'PRODUCER_GUARD_NOT_CLOSED');input_refs.append(verify(ref))
  raw_refs=[]
  for rel,key in zip(report['raw_evidence_references'],('stdout_sha256','stderr_sha256')):
   path=T/rel;require(repo_relative(path)==rel and path.parent==run_dir,'RAW_RUN_REF');v=pin(path);require(v['sha256']==tool[key],'RAW_TOOL_PIN');raw_refs.append(v)
  require(len(raw_refs)==2,'EXACT_TWO_NATIVE_RAW_FILES');input_refs+=raw_refs
  source_refs=[]
  for relative in contract['source_roster']:
   path=T/relative;require(repo_relative(path)==relative,'SOURCE21_CANONICAL_PATH');v=pin(path)
   require(report['version_manifest']['source_sha256'][relative]=='sha256:'+v['sha256'],'SOURCE21_REPORT_PIN');source_refs.append(v)
  input_refs+=source_refs
  for relative,v in choice['six_source_refs'].items():require(pin(T/relative)['sha256']==v['sha256'] and pin(T/relative)['bytes']==v['bytes'],'REVIEWED_SIX_SOURCE_UNCHANGED')
  go_ref=verify(report['go_executable']);lock_ref=pin(T/'execution/toolchains/locked.json');lock=load(lock_ref)
  require(go_ref['sha256']==lock['tools']['go']['sha256'] and Path(go_ref['path'])==Path(lock['tools']['go']['path']),'LOCKED_GO_READ_ONLY')
  input_refs += [go_ref,lock_ref]
  owned_refs=[relative_ref(v) for v in report['owned_export']['members']]
  require(owned_refs and len({v['path'] for v in owned_refs})==len(owned_refs),'UNIQUE_OWNED_MEMBERS')
  require(all(Path(v['path']).is_relative_to(run_dir/'owned') for v in owned_refs),'OWNED_RUN_BOUNDARY')
  require({v['path'] for v in owned_refs}=={str(p.resolve()) for p in (run_dir/'owned').rglob('*.raw')},'FULL_OWNED_PACKET')
  input_refs+=owned_refs
  mapped={}
  for pair in packet['raw_copy_mapping']:
   a,b=verify(pair['original_ref']),verify(pair['archive_ref']);require(Path(a['path']).is_relative_to(run_dir) and Path(b['path']).is_relative_to(PRODUCER/'native-packet'),'PACKET_ARCHIVE_BOUNDARY')
   require((a['sha256'],a['bytes'])==(b['sha256'],b['bytes']) and a['path'] not in mapped,'PACKET_RAW_COPY');mapped[a['path']]=a;input_refs += [a,b]
  require({str(p.resolve()) for p in run_dir.rglob('*') if p.is_file()}==set(mapped),'COMPLETE_RAW_PACKET_MAPPING')
  decisions=[];reviews=[];mode_relatives=[]
  for spec in request['modes']:
   mode_ref=verify(spec['decision_ref']);review_ref=verify(spec['independent_review_ref'])
   mode_relatives.append(repo_relative(mode_ref['path']));repo_relative(review_ref['path'])
   require(not Path(mode_ref['path']).is_relative_to(run_dir) and not Path(review_ref['path']).is_relative_to(run_dir),'MODE_REVIEW_OUTSIDE_PRODUCER')
   d=load(mode_ref);r=load(review_ref);require(relative_ref(d['independent_review_ref'])==review_ref,'EXACT_MODE_REVIEW_REF');decisions.append(d);reviews.append(r);input_refs += [mode_ref,review_ref]
  validate_modes(request,report,decisions,reviews,report_relative,raw_refs[0]['sha256'])
  require(PRODUCER_TEMP.is_dir() and not PRODUCER_TEMP.is_junction() and not PRODUCER_TEMP.is_symlink(),'PRODUCER_TEMP_ROOT')
  gm=module(gp,Path(verify(choice['guard_ref'])['path']).read_bytes());helper=module(hp,Path(verify(choice['owned_helper_ref'])['path']).read_bytes())
  for mod in list(sys.modules.values()):
   for field in ('__file__','__cached__'):
    path=getattr(mod,field,None)
    if path and Path(path).is_file():input_refs.append(pin(path))
  python_root=Path(sys.base_prefix)
  for p in (python_root/'Lib').rglob('*'):
   if p.is_file() and p.suffix.lower() in ('.py','.pyc') and 'site-packages' not in p.parts:input_refs.append(pin(p))
  for path in sys.path:
   if path and Path(path).is_file():input_refs.append(pin(path))
  for p in (python_root/'DLLs').iterdir():
   if p.is_file() and p.suffix.lower() in ('.pyd','.dll'):input_refs.append(pin(p))
  input_refs += [pin(p) for p in helper.runtime_resource_paths()]+[pin(sys.executable)]
  input_refs=unique(input_refs);snapshots={v['path']:v for v in input_refs}
  inputs_ref=save('consumer.inputs.exact.json',dict(refs=input_refs,source_roster_count=21,owned_members=len(owned_refs),same_native_report_ref=request['report_ref'],same_native_tool_run_ref=request['tool_run_ref'],read_only=True))
  guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guards.append(('all-consumer-inputs',guard));guard.acquire(input_refs+[inputs_ref])
  helper=module(hp,guard.get_buffer(str(hp)))
  for route,spec,mode_relative in zip(ROUTES,request['modes'],mode_relatives):
   label='01-research-fixture' if route[0]=='test.research.fixture' else '02-retrieval'
   request_env=dict(request,_current_mode_sha=spec['decision_ref']['sha256']);env=environment(report_relative,tool_relative,mode_relative,request_env)
   argv=[str(Path(sys.executable)),'-S','-B','-X','utf8',str(T/'ops/ci/w09_formal_router.py'),route[0]]
   out=O/(label+'.stdout.raw');err=O/(label+'.stderr.raw');result=None;launch_error=None
   try:
    with out.open('xb') as stdout,err.open('xb') as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,120,creation_flags=0x08000000)
   except BaseException as exc:launch_error=repr(exc)
   finally:
    receipt=save(label+'.invocation.json',dict(route=list(route),argv=argv,cwd=str(T),public_environment=env,result=result,exception=launch_error,actual_consumer_python_exit=result.get('actual_exit') if result else None,actual_new_product_native_exit=None,stdout_ref=pin(out) if out.is_file() else None,stderr_ref=pin(err) if err.is_file() else None,report_ref=request['report_ref'],tool_run_ref=request['tool_run_ref'],mode_decision_ref=spec['decision_ref'],formal_dispatcher=False,formal_case_accepted_delta=0,new_Go_SQL_API_model_calls=0))
    invocations.append(receipt);results.append(result)
   print(json.dumps(dict(progress=label,actual_consumer_python_exit=result.get('actual_exit') if result else None,invocation_ref=receipt)),flush=True)
   require(launch_error is None and job_closed(result) and result['error'] is None and result['actual_exit']==0 and result['timed_out'] is False,'CONSUMER_INVOCATION_FAILED')
   output=json.loads(out.read_bytes());require(output['status']=='PASS' and output['assertion_ids']==EXPECTED_FORMAL and output['assertions']==3 and output['native_assertion_ids']==EXPECTED_NATIVE,'EXACT_C19_COMPONENT_RESULT')
   require(output['formal_acceptance']=='PENDING_INDEPENDENT_VERIFIER' and output['case_id']=='C19' and output['check_id'] is None and output['native_tool_run_ref']==tool_relative,'COMPONENT_NOT_FORMAL')
  require(all(pin(p)==v for p,v in snapshots.items()),'ALL_INPUTS_REMAIN_EXACT')
 except BaseException as exc:error=repr(exc)
 finally:
  for name,guard in reversed(guards):
   try:
    value=guard.close();ref=save(name+'.guard.cleanup.actual.json',value);cleanups.append(dict(name=name,ref=ref,closed=value['closed'] is True and not value['errors'] and value['retained_handles_count']==0))
   except BaseException as exc:cleanups.append(dict(name=name,closed=False,error=repr(exc)))
  if any(not v['closed'] for v in cleanups):error=(error+'; ' if error else '')+'CONSUMER_GUARD_CLEANUP_FAILED'
  status='TWO_C19_COMPONENT_CONSUMERS_CLOSED_PENDING_INDEPENDENT_REVIEW' if error is None and len(results)==2 and all(job_closed(v) for v in results) else 'FAILED_COMPONENT_CONSUMER_CLOSED_NO_RETRY'
  ref=save('consumers.closed.json',dict(status=status,error=error,request_ref=request_ref,invocation_refs=invocations,guard_cleanups=cleanups,all_owned_jobs_closed=bool(results) and all(job_closed(v) for v in results),all_acquired_guards_closed=all(v['closed'] for v in cleanups),routes=[list(r) for r in ROUTES],formal_dispatcher=False,formal_case_accepted_delta=0,formal_case_count=1,formal_cases_accepted=0,registry_written=False,producer_rerun=False,new_Go_SQL_API_model_calls=0,canonical_written=False,Main_adopted=False))
  print(json.dumps(dict(closed_ref=ref,status=status,caller_python_exit=0 if error is None else 1)),flush=True)
 return 0 if error is None else 1

if __name__=='__main__':sys.exit(main())
