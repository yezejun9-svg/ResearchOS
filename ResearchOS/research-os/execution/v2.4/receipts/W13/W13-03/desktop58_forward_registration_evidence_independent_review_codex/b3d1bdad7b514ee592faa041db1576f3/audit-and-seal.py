from pathlib import Path
import json,hashlib,ast,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts';N=P/'W05/W05-99/integration_codex/desktop58-post-integration-r333-6cd1a3bb23fb45e1bcb26091d2b0a031';A=P/'W13/W13-03/desktop58_forward_head_root_parameters_codex/6cd1a3bb23fb45e1bcb26091d2b0a031'
checks=[];cache={}
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(path(p).read_bytes())
def ck(v,n):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);k=str(p).casefold()
 if k not in cache:cache[k]=pin(p)
 y=cache[k];ck(x['sha256']==y['sha256'] and x['bytes']==y['bytes'],'actualpin '+str(p));return p
def doc(x):return load(verify(x))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(O/n)
def job(d,label):
 c=d['job_cleanup'];ck(d['actual_exit']==0 and d['timed_out'] is False and d['error'] is None and d['resumed'] is True,'native0 '+label);ck(d['owned_child_pid']>0 and d['creation_time_100ns']>0 and c['errors']==[] and c['active_processes_last_observed']==0 and all(c[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'complete ownedJob '+label)
fixed={'manifest.json':('3e5719239ed2e7f19c1f66c0fff7c3c5bf869bdafa7ecd24c05f27d1ebf059af',28540),'registration-audit.json':('1b3ad605732c14633ec90b836aaec970062a2b70d77923f830879353f148a5d9',2057),'canonical-write.verified.json':('febd79b4002bb2d91cab0deb240bcaa623a3f4ed6aa01a07d55c5bdd9b9084b9',426),'canonical-write.intent.json':('a55bc80defda02a51db78273d7e9141414d7ba531ca5e139f19e393373e07507',2241),'invocation.json':('54c7208a930cfdab790b4b65d4b8f2c11a25c6e117978b650dd4700e3370d68a',2505)}
for name,(sha,size) in fixed.items():verify({'path':str(N/name),'sha256':sha,'bytes':size})
mf=load(N/'manifest.json');ck(mf['count']==len(mf['entries'])==87 and mf['self_excluded'] is True,'actual MF87+self')
members={}
for x in mf['entries']:
 pth=verify(x);ck(pth.parent==N and str(pth).casefold() not in members,'MF local unique');members[str(pth).casefold()]=x
ad=load(N/'registration-audit.json');iv=load(N/'invocation.json');intent=load(N/'canonical-write.intent.json');ve=load(N/'canonical-write.verified.json');p=load(N/'prepared_refs.json');req=doc(p['request_ref']);draft=doc(iv['review_ref'])
ck(iv['review_ref']['sha256']=='897fb087aa097940e8f7b3d9c752e03f957a8c3c1b4a68f4ff183dac2680b358' and draft['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and draft['requested_changes']==[],'reuse actual18370 draftchecks')
for field,name in [('register_sha256','register.py'),('wrapper_sha256','run.py'),('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:ck(pin(N/name)['sha256']==draft[field],'draft binding '+name)
ck(len(p['immutable_inputs'])==9148,'prior9148 immutable closure reference retained')
engine=(N/'register.py').read_bytes()
for mode in ['register','run','seal']:
 b=(N/(mode+'.py')).read_bytes();ast.parse(b);ck(b==engine.replace(b"\nMODE = 'register'\n",("\nMODE = '"+mode+"'\n").encode(),1),'onlyMODE inverse '+mode)
job(iv['owned_result'],'actual register child');ck(iv['actual_exit']==0 and iv['wrapper_error'] is None and not iv['automatic_retry'] and not iv['counter_reset'],'actual invocation nofailure')
for stream in ['stdout','stderr']:ck(pin(N/(stream+'.raw'))['sha256']==iv[stream+'_sha256'],'original child stream '+stream)
lock=doc(p['toolchain_lock_ref'])['tools'];expected=[lock['python']['path'],'-I','-S','-X','utf8',str(N/'register.py'),str(path(p['request_ref']['path'])),p['request_ref']['sha256'],str(path(iv['review_ref']['path'])),iv['review_ref']['sha256']]
ck(iv['argv']==expected and path(iv['cwd'])==R,'actual pinned invocation four args')
ck(ad['before']==p['before_tuple']==[332,160,516] and ad['after']==p['after_tuple']==[333,161,524] and ad['registered_head']==p['head'] and ad['actual_registration_exit']==0,'actual post-registration audit tuple/head')
for k,n in [('invocation_ref','invocation.json'),('intent_ref','canonical-write.intent.json'),('verified_ref','canonical-write.verified.json')]:ck(doc(ad[k])==load(N/n) and ad[k]==members[str(N/n).casefold()],'audit manifest exact edge '+k)
ck([ve['checkpoint'],ve['ownership'],ve['failure_origins']]==[333,161,524] and ve['intent_ref']==ad['intent_ref'],'verified tuple/intentsame')
ck(intent['Main_head']==p['head'] and intent['transition']=={'checkpoint':[332,333],'ownership':[160,161],'failures':[516,524]},'actual intent transition')
current=[]
for i,(ca,de,orig) in enumerate(zip(req['canonical_before'],p['desired_refs'],p['original_refs'])):
 target=verify(de).read_bytes();ck(path(ca['path']).read_bytes()==target,'allfour current==desired '+str(i));current.append(pin(ca['path']))
 if i<2:
  d=load(N/('canonical-write.'+path(ca['path']).stem+'.done.json'));ck(d['sha256']==de['sha256'] and intent['metadata'][i]['desired_ref']==de and intent['metadata'][i]['original_ref']==orig,'actual completed write'+str(i))
 else:ck(target==verify(orig).read_bytes() and intent['unchanged'][i-2]['sha256']==de['sha256'],'STCM identical '+str(i))
cp=load(current[0]['path']);ow=load(current[1]['path']);oldcp=doc(p['original_refs'][0]);ck(cp['failure_counters'][:516]==oldcp['failure_counters'] and cp['failure_counters'][516:]==p['origins'],'old516+8 preserved exact');ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[333,161,524] and cp['head']==p['head'],'actual current tuple head');ck(cp['current_effective_formal_status']==oldcp['current_effective_formal_status'] and cp['current_effective_formal_status']['formal_cases_accepted']==0,'formal0 unchanged')
lease=ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration'];ck(lease['current_source_writer'] is None and lease['state']=='CLOSED_PENDING_FRESH58_VALIDATION' and lease['actual_head']==p['head'] and lease['source_acceptance'] is False,'source writerclosed only')
counts={'run':0,'register':0,'seal':0};seenstages=set();status=verify(p['status_ref']).read_bytes();gitrefs=[]
for f in sorted(N.glob('*.invocation.json')):
 if f.name=='invocation.json':continue
 d=load(f);label=f.name[:-len('.invocation.json')];mode=label.split('-')[0];ck(mode in counts,'owned query phase');counts[mode]+=1;job(d['owned_result'],label);ck(d['actual_exit']==0 and d['wrapper_error'] is None and not d['automatic_retry'] and not d['counter_reset'],'query closed '+label)
 query=label.rsplit('-',1)[1];args={'head':['rev-parse','HEAD'],'status':['status','--porcelain=v1','--untracked-files=no'],'index':['diff','--cached','--name-only']}[query];ck(d['argv']==[lock['git']['path'],'-c','core.fsmonitor=false',*args] and path(d['cwd'])==R,'exact readonly Git '+label)
 so=N/(label+'.stdout.raw');se=N/(label+'.stderr.raw');ck(str(so).casefold() in members and str(se).casefold() in members,'query original streams MF '+label)
 b=so.read_bytes();ck((b.decode().strip()==p['head']) if query=='head' else b==status if query=='status' else b==b'','query result '+label);gitrefs.append(pin(f));seenstages.add(label.rsplit('-',1)[0])
ck(counts=={'run':3,'register':12,'seal':3} and all(x<=15 for x in counts.values()),'actual Git per-mode bound15')
ck(seenstages=={'run-start','register-start','register-pre-0','register-pre-1','register-after','seal-current'},'all actual before/mid/post guards present')
runtime={str(path(x['path'])).casefold():x for x in p['runtime_files']};runtime.update({str(path(x['path'])).casefold():x for x in p['script_refs'].values()});runtime[str(path(p['helper_ref']['path'])).casefold()]=p['helper_ref'];observations=[]
for f in sorted(N.glob('*.runtime.*.json')):
 d=load(f);ck(d['kind']=='ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE','runtime boundary '+f.name)
 for row in d['files']:
  ref=runtime.get(str(path(row['path'])).casefold());ck(ref is not None and row['sha256']==ref['sha256'] and row['bytes']==ref['bytes'],'runtime matches prepins '+f.name+' '+row['path'])
 observations.append({'ref':pin(f),'file_count':len(d['files'])})
ck(len(observations)==9 and all((N/(mode+'.runtime.after.json')).is_file() for mode in counts),'all3mode runtime beforeimport/before/after')
annex=A/'run-seal.tool-observations.closed.json';verify({'path':str(annex),'sha256':'93195915dba4a331d2f139ef38212b88ab73132e4f475496f2ea77da8942a9fc','bytes':17827});obs=load(annex)
for mode in ['run','seal']:
 d=obs[mode];last=d['polls'][-1]['original_result'];ck(d['session_closed'] is True and d['actual_outer_exit']==d['actual_python_exit']==last['exit_code']==0 and 'ACTUAL_PYTHON_EXIT=0' in last['output'],'Root originaltool explicitbridge '+mode);cmd=d['original_input']['cmd'];ck(str(N/(mode+'.py')) in cmd and p['request_ref']['sha256'] in cmd and '-I -S -X utf8' in cmd and '$LASTEXITCODE' in cmd and path(d['original_input']['workdir'])==R,'Root actualcommand '+mode)
ck(obs['raw_native_streams_claimed'] is False and obs['registered_failure_count']==524 and obs['known_observed_failure_count']==529 and len(obs['post_fixed_cut_pending_origin_refs'])==5,'outer toolobservations distinct from native stream and late5')
for ref in obs['post_fixed_cut_pending_origin_refs']:verify(ref)
ck(obs['new_execution_grant'] is None and obs['fresh58_compiler_or_cases_accepted'] is False and ad['grant_materialized'] is False and ad['compile_GUI_HTTP_models_authorized'] is False,'no fresh grant/productqualification')
ck(not list(N.glob('*.failure.json')),'no actual modefailure artifacts')
ck((R/'.git/refs/heads/main').read_text().strip()==p['head'] and all(not os.path.lexists(R/x) for x in p['old_deleted_paths']),'current direct head and old11D')
for row in current:ck(pin(row['path'])==row,'final currentfour stable '+row['path'])
ar=save('audit.json',{'count':len(checks),'checks':checks,'failed':[x for x in checks if not x['passed']],'actual_manifest_members':87,'actual_git_invocations':counts,'runtime_observations':observations,'prior18370checks_and9148_reference_closure_reused':True,'old6983tree_not_rehashed':True,'new_failure_origins':[]})
decision='SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES'
review=save('review.json',{'schema':'researchos.desktop58-source-head-registration-closed-review.v1','reviewer':'codex:/root/w05_merge_review','decision':decision,'requested_changes':[x for x in checks if not x['passed']],'actual_registration_executed_by_reviewer':False,'actual_registration_evidence_closed':decision=='SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED','post_registration_audit_ref':pin(N/'registration-audit.json'),'registration_manifest_ref':pin(N/'manifest.json'),'invocation_ref':pin(N/'invocation.json'),'intent_ref':pin(N/'canonical-write.intent.json'),'verified_ref':pin(N/'canonical-write.verified.json'),'root_tool_observations_ref':pin(annex),'registration_draft_review_ref':iv['review_ref'],'source_execution_review_ref':p['source_closure_review_ref'],'source_completed_ref':p['completed_ref'],'source_manifest_ref':p['source_manifest_ref'],'actual_head':p['head'],'actual_parent':p['head_before'],'canonical_tuple':[333,161,524],'canonical_refs':current,'registered_failure_prefix516_and_append8_preserved':True,'observed_known_at_Root_annex':529,'post_fixed_cut_pending_origin_refs':obs['post_fixed_cut_pending_origin_refs'],'actual_register_child_exit':0,'actual_run_outer_python_exit':0,'actual_seal_outer_python_exit':0,'actual_Git_counts':counts,'runtime_qualification':'POINT_IN_TIME_NOT_LIFECYCLE','reviewer_candidate_imports_or_native_Git_Job_CAS_product_calls':0,'audit_ref':ar,'source_acceptance':False,'fresh58_qualified':False,'Desktop169_current_qualified':False,'new_execution_grant':None,'formal_increment':0,'formal_cases_accepted':0,'remaining_gates':['Separate new current58 resource/catalog/authority binding and independently reviewed finite execution scope','Fresh compiler and CLI/Desktop169 execution plus actual runtime/fixture closure','Installed GUI/NVDA/P02/SDK and whole formal42 remain OPEN'],'new_failure_origins':[],'status':'STOPPED'})
hdf=save('handoff.json',{'review_ref':review,'decision':decision,'manifest_path':str(O/'manifest.json'),'new_failure_origins':[],'status':'STOPPED'})
rows=[pin(f) for f in sorted(O.iterdir()) if f.is_file()];mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':review,'handoff':hdf,'manifest':mr,'checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
