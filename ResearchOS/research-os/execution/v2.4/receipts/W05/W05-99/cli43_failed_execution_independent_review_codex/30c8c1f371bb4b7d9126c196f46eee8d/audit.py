from pathlib import Path
import json, hashlib, traceback

R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99'
U='71b091d20d94443bbf4e732d201eeb29'
O=Path(__file__).parent
E=P/'cli43_fresh_compiler_executor_codex'/U
L=P/'cli43_fresh_compiler_launcher_codex'/U
G=P/'cli43_fresh_compiler_authorization_codex'/U
N=P/'integration_codex'/('cli43-fresh-held2-r325-'+U)
checks=[]; refs={}; facts={}
def resolve(s):
 p=Path(s); return p if p.is_absolute() else R/p
def ref(p):
 p=resolve(p); b=p.read_bytes(); v={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}; refs[p.as_posix()]=v; return v
def read(p):
 ref(p); return json.loads(resolve(p).read_text(encoding='utf-8'))
def ck(name,ok): checks.append({'check':name,'passed':bool(ok)})
def verify(v):
 a=ref(v['path']); ck('ref:'+a['path'],a['sha256']==v['sha256'] and a['bytes']==v['bytes']); return resolve(v['path'])
def save(name,obj):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def rows(a): return {str(resolve(x['path'])).casefold():(x['sha256'],x['bytes']) for x in a}
def good_job(v):
 c=v['job_cleanup'];return v['error'] is None and not v['timed_out'] and v['resumed'] and all(c[k] is True for k in ('assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')) and c['errors']==[]
try:
 manifest_counts={}
 for d in (E,L):
  m=read(d/'manifest.json');ck('manifest count '+d.name,len(m['files'])==m['count']);manifest_counts[d.parent.name]=m['count']
  for x in m['files']:verify(x)
  actual={x.resolve() for x in d.iterdir() if x.is_file() and x.name!='manifest.json'}
  ck('exact member inventory '+d.parent.name,actual=={resolve(x['path']).resolve() for x in m['files']})
 result=read(E/'result.json'); origin=read(E/'failure.origin.json'); go=read(E/'go-list.invocation.json'); bad=go['result'];clean=bad['job_cleanup'];dbg=bad['debug_capture']
 ck('original first cause equals result',origin==result['first_cause'])
 ck('first cause go-list',origin['stage']=='go-list' and origin['last_child_result']==bad and origin['actual_stage_native_exit'] is None)
 ck('observed termination rather than compiler success',go['actual_exit']==bad['actual_exit']==clean['termination_code_requested']==3758097160)
 ck('unknown executable failure retained','Actual CREATE_PROCESS file path/bytes outside pinned executable set' in bad['error'])
 ck('failure capture incomplete',dbg['complete'] is False and clean['errors']!=[])
 ck('owned termination and idle',clean['termination_requested'] and clean['termination_succeeded'] and clean['active_processes_last_observed']==0 and clean['job_idle_confirmed'] and clean['primary_exit_confirmed'])
 ck('22 handles closed',clean['handles_closed'] and clean['explicit_owned_handle_count']==clean['explicit_owned_handle_close_successes']==22 and clean['explicit_owned_handles_remaining']==0)
 process_pids={x['pid'] for x in dbg['events'] if x['code']==3}
 module_pids={x['pid'] for x in dbg['modules'] if x['event_code']==3}
 unknown_pids=sorted(process_pids-module_pids)
 ck('second CREATE_PROCESS lacks qualified image identity',len(process_pids)==2 and len(unknown_pids)==1)
 calls=[]
 for label in ['git-head','git-public-blobs','go-version','go-env','go-list']:
  x=read(E/(label+'.invocation.json')); v=x['result']; calls.append({'label':label,'actual_exit':x['actual_exit'],'argv':x['request']['argv'],'result_ref':ref(E/(label+'.invocation.json'))})
  ck('no retry '+label,x['automatic_retry'] is False and x['counter_reset'] is False)
  if label!='go-list':ck('successful preceding native '+label,x['actual_exit']==v['actual_exit']==0 and good_job(v))
  if label in ['go-version','go-env']:
   dc=v['debug_capture'];ck('actual complete tree '+label,dc['complete'] and dc['create_process_count']==dc['exit_process_count']==1 and dc['exit_event_code']==0)
 ck('five native calls',result['native_calls']==len(calls)==5)
 ck('both case launches absent',len(result['case_roster'])==2 and result['cases']==[] and all(x['state']=='NOT_STARTED' and x['launch_attempted'] is False and x['actual_native_exit'] is None and x['qualified'] is False for x in result['case_roster']))
 ck('NOT_RUN exact roster',result['NOT_RUN']==[x['leaf'] for x in result['case_roster']])
 ck('no acceptance',result['status']=='STOPPED' and result['product_acceptance'] is False and result['formal_increment']==0 and result['SDK_MODEL_external_paid']==0)
 ledger={};previous={}; ledger_facts=[]
 for i in (1,2,3):
  x=read(E/('ledger-add-%03d.json'%i));a=rows(x['added']);full=rows(x['full_members']);ck('ledger unique '+str(i),len(a)==len(x['added']) and len(full)==len(x['full_members']));ck('ledger exact additive '+str(i),not(set(previous)&set(a)) and full==previous|a and x['revision']==i);ledger[i]=full;previous=full;ledger_facts.append({'revision':i,'label':x['label'],'added':len(a),'members':len(full)})
 vector_facts=[]
 for p in sorted(E.glob('*.vector.json')):
  x=read(p); exp=rows(x['expected_members']);obs=rows(x['observed_members']); ck('vector exact prefix '+p.name,exp==obs==ledger[x['revision']] and x['drift']==[] and x['file_count']==len(exp));vector_facts.append({'name':p.name,'revision':x['revision'],'file_count':x['file_count'],'drift':x['drift'],'ref':ref(p)})
 ck('before Go to finally byte identical',ref(E/'before-any-go.vector.json')['sha256']==ref(E/'after-finally.vector.json')['sha256'])
 grant=read(G/'authorization.execute.json');verify(grant['scope_ref'])
 canonical=[]
 for x in grant['canonical_copies']:
  saved=verify(x['ref']); live=R/x['canonical_path']; ck('current canonical equals actual grant '+x['canonical_path'],live.read_bytes()==saved.read_bytes());canonical.append(ref(live))
 for v in grant['registration_refs'].values():verify(v)
 for v in grant['authority_review_refs'].values():verify(v)
 pre=read(verify(grant['prelaunch_evidence_ref'])); git_facts=[]
 for x in pre['git']:
  out=verify(x['stdout_ref']);verify(x['stderr_ref']);ck('grant Git closed '+x['kind'],x['result']['actual_exit']==0 and good_job(x['result']));git_facts.append({'kind':x['kind'],'stdout_ref':x['stdout_ref'],'result':x['result']})
 head_text=(R/'.git/HEAD').read_text(encoding='utf-8').strip();ref(R/'.git/HEAD')
 if head_text.startswith('ref: '):
  hp=R/'.git'/head_text[5:];current_head=hp.read_text(encoding='utf-8').strip();ref(hp)
 else:current_head=head_text
 ck('direct current Git HEAD equals scope',current_head==grant['binding']['source_commit'])
 ck('saved executor Git HEAD', (E/'git-head.stdout.raw').read_text(encoding='utf-8').strip()==current_head)
 runtime_json=read(verify(grant['binding']['runtime_resources_ref']))
 runtime_files=runtime_json if isinstance(runtime_json,list) else runtime_json.get('files',[])
 ck('runtime catalog shape',len(runtime_files)==1250)
 allowed=rows(runtime_files);runtime_facts=[]
 for d in (E,L):
  for f in sorted(d.glob('python-os*.json')):
   x=read(f); rs=rows(x['files']);ck('pointtime runtime pinned '+str(f),all(allowed.get(k)==v for k,v in rs.items()) and x['point_in_time_only'] is True and x['Python_lifecycle_proof'] is False);runtime_facts.append({'ref':ref(f),'count':len(rs),'point_in_time_only':True,'Python_lifecycle_proof':False})
 li=read(L/'invocation.result.json');lc=read(L/'completed.json');ri=read(N/'root-launch.invocation.json');outer=read(N/'root-launch.outer-completion.json')
 ck('launcher propagated inner one',li['actual_native_exit']==li['result']['actual_exit']==lc['actual_inner_native_exit']==lc['program_reported_exit']==1 and good_job(li['result']))
 ck('caller propagated launcher one',ri['actual_launcher_native_exit']==1 and ri['caller_error'] is None and ri['secondary']==[])
 for k in ('stdout_ref','stderr_ref','scope_ref','grant_ref'):verify(ri[k])
 ck('outer separately attributed original observation',outer['actual_outer_tool_exit']==outer['actual_root_caller_python_native_exit']==outer['actual_launcher_native_exit']==1 and outer['completion_chunk']=='663f80' and outer['separate_outer_raw_streams_available'] is False)
 ck('raw layers nullable fields preserved',li['actual_outer_tool_exit'] is None and lc['actual_outer_tool_exit'] is None and ri['actual_outer_tool_exit'] is None)
 facts={'manifest_counts':manifest_counts,'native_calls':calls,'first_cause_ref':ref(E/'failure.origin.json'),'result_ref':ref(E/'result.json'),'unknown_create_process_pids':unknown_pids,'unknown_executable_path':None,'unknown_executable_sha256':None,'go_list':{'observed_native_exit':bad['actual_exit'],'requested_termination_code':clean['termination_code_requested'],'debug_complete':dbg['complete'],'cleanup':clean},'cases':result['case_roster'],'ledger':ledger_facts,'vectors':vector_facts,'runtime':runtime_facts,'canonical_current':canonical,'current_head':current_head,'prelaunch_git':git_facts,'caller_invocation_ref':ref(N/'root-launch.invocation.json'),'outer_observation_ref':ref(N/'root-launch.outer-completion.json'),'single_underlying_failure':True,'separate_outer_raw_streams_available':False,'current_status_index_not_requeried':True,'backing_full_tree_not_rehashed':True}
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'facts':facts,'refs':list(refs.values()),'new_target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except Exception as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'completed_checks':checks,'known_refs':list(refs.values()),'target_executions':0});raise
