import copy,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent;U='0e298790cd484ec9ba319a379e7e34ed'
N=P/('integration_codex/cli58-fresh-held2-r334-v2-'+U);A=P/('cli58_fresh_compiler_authorization_codex/'+U);S=P/('integration_codex/cli58-r334-stage-close-'+U)
C=[];INPUTS={};JOBS=[];RT=[]
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def load(p):
 p=path(p);INPUTS[str(p)]=ref(p);return json.loads(p.read_bytes())
def pin(r):
 p=path(r['path']);raw=p.read_bytes();a=ref(p);INPUTS[str(p)]=a;ck('pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return raw
def rd(r):return json.loads(pin(r))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def allrefs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=v.keys():yield v
  else:
   for x in v.values():yield from allrefs(x)
 elif isinstance(v,list):
  for x in v:yield from allrefs(x)
s=load(N/'scope_registration.json');b=load(N/'binding.json');p=load(N/'prepared_refs.json');g=load(A/'authorization.execute.json');PF=path(s['new_grant_preflight_root'])
expected={N/'manifest.json':'b7ce1ee00a3c95dd9791b9c4ca3a4beaf4b39f2ce8de742aac65c75dbd1da95c',A/'manifest.json':'10d76062ac8b3f2a7470467fbfb5b011135af84a460d1fcc73fff9319a1bda24',A/'authorization.execute.json':'c6cb6b5af8a2d61f4975de838e3a28825af55707dcc6a9397cdf537a6677ef0b',N/'registration-audit.json':'36c439fbafd5012bb8a1ade4965c1914b01c751e53aa75af06f02167ec16c16a',N/'invocation.json':'9ebce0e0aedebc18c0f81adceac6c97bd3a54ad9916a3ec1a2f4214e52ccf1fb',N/'canonical-write.verified.json':'a1ecb745db5b196b16990e13545b18f57a2c3b03ce8c7937738452a21475ef72'}
for f,h in expected.items():ck('expected '+str(f),ref(f)['sha256']==h)
manifests=[]
for directory in [N,A,PF]:
 mf=load(directory/'manifest.json');ck('MF count '+str(directory),mf['count']==len(mf['entries']) and mf['excluded_only_self'] is True)
 for r in mf['entries']:pin(r)
 manifests.append({'manifest_ref':ref(directory/'manifest.json'),'member_count':mf['count']})
for r in g['registration_refs'].values():pin(r)
for r in g['authority_review_refs'].values():pin(r)
ra=load(N/'registration-audit.json');inv=load(N/'invocation.json');intent=load(N/'canonical-write.intent.json');verified=load(N/'canonical-write.verified.json')
ck('actual registration tuple',ra['before']==[333,161,524] and ra['after']==[334,162,532] and ra['actual_registration_exit']==0 and ra['formal_increment']==0)
ck('verified tuple',[verified['checkpoint'],verified['ownership'],verified['failure_origins']]==ra['after'] and verified['step_state_commands_unchanged'] is True)
ck('actual three refs',ra['invocation_ref']==g['registration_refs']['invocation'] and ra['intent_ref']==g['registration_refs']['intent'] and ra['verified_ref']==g['registration_refs']['verified'])
ck('review chain',inv['review_ref']==ra['review_ref']==g['authority_review_refs']['registration_review_ref'] and inv['review_ref']['sha256']=='61f51723fa0d97d142f5fe2041df85e5abbce97b16bfb81815a508d661a301db' and g['authority_review_refs']['runner_review_ref']==b['controller_review_ref'])
def job(z,label):
 jc=z['job_cleanup'];ck(label+' actual owned0 identity',z['actual_exit']==0 and z['timed_out'] is False and z['error'] is None and z['resumed'] is True and isinstance(z['owned_child_pid'],int) and z['owned_child_pid']>0 and isinstance(z['creation_time_100ns'],int) and z['creation_time_100ns']>0)
 ck(label+' cleanup',all(jc[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and jc['active_processes_last_observed']==0 and jc['errors']==[] and jc['termination_requested'] is False)
job(inv['result'],'register child')
ck('register nullable outer/firstcause',inv['actual_exit']==0 and inv['wrapper_error'] is None and inv['actual_outer_tool_exit'] is None and inv['automatic_retry'] is False and inv['counter_reset'] is False)
for n in ['stdout','stderr']:ck('register raw '+n,ref(N/(n+'.raw'))['sha256']==inv[n+'_sha256'])
ck('register pinned command',inv['argv'][1:5]==['-I','-S','-X','utf8'] and path(inv['argv'][5])==N/'register.py' and inv['runner_sha256']==ref(N/'register.py')['sha256'] and inv['wrapper_sha256']==ref(N/'run.py')['sha256'] and path(inv['cwd'])==R)
ck('register actual exact review argument',json.loads(inv['argv'][-1])==inv['review_ref'])
old=[pin(r) for r in p['original_refs']];desired=[pin(r) for r in p['desired_refs']];oldcp,oldow=map(json.loads,old[:2]);cp,ow=map(json.loads,desired[:2]);cut=rd(b['origin_cut_ref']);prefix=rd(b['failure_prefix430_ref'])
ck('full524+exact8/prefix430',cp['failure_counters']==oldcp['failure_counters']+cut['origins'] and len(oldcp['failure_counters'])==524 and len(cut['origins'])==8 and cp['failure_counters'][:430]==prefix['failure_counters'])
for row in cut['origins']:ck('original payload '+row['evidence_ref']['sha256'],rd(row['evidence_ref'])==row['original_payload'])
rc=copy.deepcopy(cp);ro=copy.deepcopy(ow)
for k in ['revision','expected_previous_revision','updated_at','updated_by','failure_counters']:
 if k in oldcp:rc[k]=oldcp[k]
 else:rc.pop(k,None)
for k in ['cli43_fresh_compiler_held2_scope_ref','cli43_fresh_compiler_current_source_authority_ref','cli43_fresh_compiler_controller_review_ref']:
 if k in oldcp['work_in_progress']:rc['work_in_progress'][k]=oldcp['work_in_progress'][k]
 else:rc['work_in_progress'].pop(k,None)
for k in ['revision','amended_at','amended_by']:
 if k in oldow:ro[k]=oldow[k]
 else:ro.pop(k,None)
ck('protected fields unchanged',rc==oldcp and ro==oldow and old[2:]==desired[2:])
ck('two writes exact transition',intent['transition']=={'checkpoint':[333,334],'ownership':[161,162],'failures':[524,532]} and len(intent['metadata'])==2 and len(intent['unchanged'])==2 and intent['automatic_retry'] is False)
for i,x in enumerate(intent['metadata']):
 ck('intent desired original '+str(i),x['path']==p['canonical_before'][i]['path'] and x['original_ref']==p['original_refs'][i] and x['desired_ref']==p['desired_refs'][i])
 d=load(N/('canonical-write.'+Path(x['path']).stem+'.done.json'));ck('completed write '+str(i),d['sha256']==p['desired_refs'][i]['sha256'] and d['intent_ref']==g['registration_refs']['intent'])
for i,row in enumerate(g['canonical_copies']):
 raw=pin(row['ref']);ck('live/grant/desired '+row['canonical_path'],row['canonical_path']==p['canonical_before'][i]['path'] and raw==desired[i]==path(row['canonical_path']).read_bytes())
ck('current tuple/source',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[334,162,532] and cp['head']==s['source_commit'])
ck('grant exact scoped identity',g['schema']=='researchos.cli43-compiler-authorization.v1' and g['actor']=='codex:/root' and g['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and g['actual_registration_completed'] is True and g['scope_ref']==p['scope_ref'] and path(s['new_authorization_root'])==A)
for k,v in g['binding'].items():ck('grant binding '+k,k in s and s[k]==v)
roots=[path(s[k]) for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']]
ck('five disjoint roots UUID',len(set(roots))==5 and all(U in x.name for x in roots) and all(not x.is_relative_to(y) for x in roots for y in roots if x!=y))
tails={'head':['rev-parse','HEAD'],'status':['status','--porcelain=v1','--untracked-files=no'],'index':['diff','--cached','--name-only']}
for directory in [N,PF]:
 for f in sorted(directory.glob('*.invocation.json')):
  d=load(f)
  if 'kind' not in d:continue
  kind=d['kind'];job(d['result'],str(f));out=pin(d['stdout_ref']);err=pin(d['stderr_ref']);ck('Git raw/argv '+str(f),d['argv'][1:]==tails[kind] and d['actual_stage_native_exit']==0 and d['wrapper_error'] is None and err==b'' and path(d['cwd'])==R and d['environment']['GIT_OPTIONAL_LOCKS']=='0')
  if kind=='head':ck('HEAD '+str(f),out.decode().strip()==s['source_commit'])
  elif kind=='status':ck('status '+str(f),hashlib.sha256(out).hexdigest()==s['main_git']['status_sha256'] and len(out)==894 and len(out.splitlines())==13 and sum(x[:2]==b' D' for x in out.splitlines())==11)
  else:ck('index '+str(f),out==b'')
  JOBS.append({'invocation_ref':ref(f),'kind':kind,'argv':d['argv'],'result':d['result'],'stdout_ref':d['stdout_ref'],'stderr_ref':d['stderr_ref']})
ck('24 unique readonlyGit identities',len(JOBS)==24 and len({(x['result']['owned_child_pid'],x['result']['creation_time_100ns']) for x in JOBS})==24)
pre=rd(g['prelaunch_evidence_ref'])
for r in allrefs(pre):pin(r)
ck('prelaunch real finalround',pre['source_round']=='grant-final' and pre['point_in_time_only'] is True and len(pre['git'])==3)
for d in pre['git']:ck('prelaunch matches original PF invocation '+d['kind'],d==load(PF/('grant-final.'+d['kind']+'.invocation.json')))
rt=rd(s['runtime_resources_ref']);allowed={str(path(r['path'])).casefold():(r['sha256'],r['bytes']) for r in rt['files']}
for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']:
 r=s[k];allowed[str(path(r['path'])).casefold()]=(r['sha256'],r['bytes'])
for directory in [N,PF,A]:
 for f in sorted(directory.glob('*runtime*.json')):
  if f.name=='runtime-with-current58-root-metadata.json':continue
  d=load(f)
  ck('runtime pointtime qualification '+str(f),d['point_in_time_only'] is True and d['Python_lifecycle_proof'] is False and d['all_observed_inputs_pre_pinned'] is True)
  for r in d['files']:ck('observed allowed '+str(f)+' '+r['path'],allowed.get(str(path(r['path'])).casefold())==(r['sha256'],r['bytes']))
  RT.append({'ref':ref(f),'observed_files':len(d['files'])})
for r in g['runtime_observation_refs']:pin(r)
run=load(N/'run.tool-observations.closed.json');stage=load(S/'before-cli-launch.json')
ck('run actual outer/native0',run['actual_outer_tool_exit']==run['actual_python_exit']==0)
for k in ['seal','grant']:
 d=stage[k];ck(k+' actual tool/Python0',d['actual_outer_tool_exit']==d['actual_python_exit']==0 and d['terminal_poll_result']['exit_code']==0)
for r in stage['actual_registration_refs']['refs']:pin(r)
for r in stage['pending_late_origin_refs']:pin(r)
ck('late snapshot fixed not appended',stage['registered_failure_count']==532 and stage['known_observed']==540 and len(stage['pending_late_origin_refs'])==8 and stage['counter_reset'] is False)
ck('no product acceptance',stage['formal_increment']==0 and ra['formal_increment']==0 and s['source_acceptance'] is False and s['actual_cases'] is None)
head=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head;ck('direct Main HEAD unchanged',head==s['source_commit'])
save('audit.json',{'checks':C,'failed':[x for x in C if not x['passed']],'input_refs':list(INPUTS.values()),'manifest_results':manifests,'git_jobs':JOBS,'runtime_observations':RT,'scope_ref':p['scope_ref'],'grant_ref':ref(A/'authorization.execute.json'),'registration_audit_ref':ref(N/'registration-audit.json'),'prior_draft_review_ref':inv['review_ref'],'stage_observation_ref':ref(S/'before-cli-launch.json'),'current_canonical':[ref(x['canonical_path']) for x in g['canonical_copies']],'product_executor_read':False,'candidate_calls':0,'native_Git_calls':0,'canonical_writes':0,'full_resource_tree_rehashed':False,'new_failure_origins':[]})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'manifest_counts':[x['member_count'] for x in manifests],'Git_jobs':len(JOBS),'runtime_observations':len(RT),'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
