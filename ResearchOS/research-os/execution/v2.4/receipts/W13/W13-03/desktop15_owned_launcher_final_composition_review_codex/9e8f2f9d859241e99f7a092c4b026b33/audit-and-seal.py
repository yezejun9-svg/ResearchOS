from pathlib import Path
import json,hashlib,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
A=R/'execution/v2.4/receipts/W13/W13-03/desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf'
packetpath=A/'owned-source-launch.request.json';checks=[];inputs={}
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ck(v,k):checks.append({'check':k,'passed':bool(v)})
def verify(r):
 p=path(r['path']);x=pin(p);ck((x['sha256'],x['bytes'])==(r['sha256'],r['bytes']),'pin '+str(p));inputs[str(p).casefold()]=x;return p
def doc(r):return json.loads(verify(r).read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(O/n)
def mf(r):
 d=doc(r);ck(d['count']==len(d['entries']),'manifest count '+r['path']);rows={}
 for x in d['entries']:
  p=verify(x);ck(p.is_relative_to(path(r['path']).parent) and str(p).casefold() not in rows,'MF unique/local '+str(p));rows[str(p).casefold()]=x
 return d,rows
def job(j,k):
 c=j['job_cleanup'];ck(j['actual_exit']==0 and j['error'] is None and j['timed_out'] is False and j['resumed'] is True,'actual native0 '+k)
 ck(j['owned_child_pid']>0 and j['creation_time_100ns']>0 and c['errors']==[] and c['active_processes_last_observed']==0 and all(c[x] is True for x in ['unnamed_exclusive_job','assigned_before_resume','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'actual owned identity/cleanup '+k)
packetref=pin(packetpath);ck(packetref['sha256']=='5b090572efe064e24aa2faee26ae86285d7d30c89038722a078f3289d839f2ff' and packetref['bytes']==8195,'literal launch packet pin')
p=json.loads(packetpath.read_bytes());s=doc(p['actual_scope_ref']);g=doc(p['actual_grant_ref']);rr=g['registration_refs'];N=path(rr['manifest']['path']).parent
regmf,regrows=mf(rr['manifest']);gm,grows=mf(p['actual_grant_manifest_ref'])
ck(rr==p['actual_registration_refs'] and g['scope_ref']==p['actual_scope_ref'],'same actual registration/scope refs')
ck(g['schema']=='researchos.desktop15-source-integration-grant.v1' and g['authorized'] is True and g['actual_registration_completed'] is True and g['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and g['actor']=='codex:/root' and g['automatic_retry'] is False,'actual unique grant')
ck(s['authorized'] is True and s['status']=='ROOT_REGISTERED_DESKTOP15_SOURCE_COMMIT_ONCE' and s['owner']=='codex:/root' and g['operation_uuid']==s['operation_uuid']==p['operation_uuid'],'actual active scope')
ck(grows[str(path(p['actual_grant_ref']['path'])).casefold()]['sha256']==p['actual_grant_ref']['sha256'],'grant sealed member')
for key in ['audit','invocation','intent','verified']:ck(regrows[str(path(rr[key]['path'])).casefold()]==rr[key],'registration ref sealed '+key)
ad=doc(rr['audit']);iv=doc(rr['invocation']);it=doc(rr['intent']);ve=doc(rr['verified']);prep=json.loads((N/'prepared_refs.json').read_bytes())
ck(ad['before']==[331,159,509] and ad['after']==[332,160,516] and ad['actual_registration_exit']==0 and ad['registered_head']==s['expected_cli43_head'],'actual registration audit tuple/head')
ck(ad['invocation_ref']==rr['invocation'] and ad['intent_ref']==rr['intent'] and ad['verified_ref']==rr['verified'],'audit exact relations')
ck(iv['actual_exit']==0 and iv['wrapper_error'] is None and iv['automatic_retry'] is False and iv['counter_reset'] is False,'actual registration invocation0')
job(iv['owned_result'],'registration')
review=doc(iv['review_ref']);ck(review['schema']=='researchos.root-registration-source-review.v1' and review['reviewer']=='codex:/root/w05_merge_review' and review['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and review['requested_changes']==[],'actual independent registration review')
for key,name in [('register_sha256','register.py'),('wrapper_sha256','run.py'),('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:ck(pin(N/name)['sha256']==review[key],'actual reviewed '+name)
for stream in ['stdout','stderr']:ck(pin(N/(stream+'.raw'))['sha256']==iv[stream+'_sha256'],'register raw '+stream)
ck([ve['checkpoint'],ve['ownership'],ve['failure_origins']]==[332,160,516] and ve['intent_ref']==rr['intent'],'actual verified tuple')
ck(it['transition']=={'checkpoint':[331,332],'ownership':[159,160],'failures':[509,516]} and it['Main_head']==s['expected_cli43_head'],'actual intent transition')
names=['checkpoint','path_ownership','step_state','commands'];actualdocs=[];owncopies=[]
ck([x['canonical_path'] for x in g['canonical_copies']]==['execution/v2.4/'+n+'.json' for n in names],'ordered four grant copies')
for i,x in enumerate(g['canonical_copies']):
 b=verify(x['ref']).read_bytes();current=R/x['canonical_path'];ck(current.read_bytes()==b,'live4 equals grant '+names[i]);ck(verify(prep['desired_refs'][i]).read_bytes()==b,'desired equals grant '+names[i]);actualdocs.append(json.loads(b))
 with (O/(names[i]+'.observed.json')).open('xb') as f:f.write(b)
 owncopies.append(pin(O/(names[i]+'.observed.json')))
 if i<2:
  done=json.loads((N/('canonical-write.'+names[i]+'.done.json')).read_bytes());ck(done['sha256']==x['ref']['sha256'],'done hash '+names[i]);ck(it['metadata'][i]['desired_ref']==prep['desired_refs'][i],'intent desired '+names[i])
 else:ck(it['unchanged'][i-2]['sha256']==x['ref']['sha256'],'unchanged '+names[i])
cp,ow=actualdocs[:2];before=doc(prep['original_refs'][0]);ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[332,160,516],'actual current tuple')
ck(cp['failure_counters'][:509]==before['failure_counters'] and cp['failure_counters'][509:]==prep['origins'],'old509 plus original7 actual preserved')
ck(cp['work_in_progress']['desktop_exact15_source_integration_scope_ref']==g['scope_ref'] and cp['work_in_progress']['desktop_exact15_source_integration_controller_review_ref']==g['controller_review_ref'],'CP exact scope/review authority')
ck(cp['current_effective_formal_status']['formal_cases_accepted']==0 and cp['head']==s['expected_cli43_head'],'no current source/formal acceptance')
for key in ['launcher_ref','controller_ref','owned_process_helper_ref','runtime_resources_ref']:verify(s[key]);ck(s[key]==p[key],'packet actual code '+key)
cr=doc(g['controller_review_ref']);ck(cr['scope_sha256']==p['actual_scope_ref']['sha256'] and cr['controller_sha256']==s['controller_ref']['sha256'] and cr['launcher_sha256']==s['launcher_ref']['sha256'],'actual fullscope prior review pins')
for phase in ['run','seal','grant']:
 o=p['metadata_phases'][phase];ck(o['exit_code']==0 and 'ACTUAL_PYTHON_EXIT=0' in o['output'],'actual outer/Python bridge '+phase)
 firstline=o['output'].splitlines()[0];summary=json.loads(firstline);ck(summary['actual_metadata_native_exit']==0 and summary['phase']==phase,'metadata child summary '+phase)
 inv=doc(summary['invocation_ref']);ck(inv['actual_native_exit']==0 and inv['first_error'] is None and inv['secondary_errors']==[] and inv['outer_OS_lifecycle_qualification'] is False,'thin caller actual closed '+phase)
 for key in ['stdout_ref','stderr_ref']:verify(inv[key])
for label in ['grant-current-head','grant-current-status','grant-current-index']:
 j=json.loads((N/(label+'.invocation.json')).read_bytes());ck(j['actual_exit']==0 and j['wrapper_error'] is None,'latest saved Git '+label);job(j['owned_result'],label)
ck((N/'grant-current-head.stdout.raw').read_text().strip()==s['expected_cli43_head'] and (N/'grant-current-index.stdout.raw').read_bytes()==b'' and (N/'grant-current-status.stdout.raw').read_bytes()==verify(s['status_ref']).read_bytes(),'latest saved actual Main head/status/index')
ck((R/'.git/HEAD').read_text().strip()=='ref: refs/heads/main' and (R/'.git/refs/heads/main').read_text().strip()==s['expected_cli43_head'],'direct HEAD now')
ck(all(not os.path.lexists(R/x) for x in s['old_deleted_paths']),'old11 absent now')
target=Path(s['new_output_root']);ck(target.parent.is_dir() and not os.path.lexists(target) and not os.path.lexists(target.with_name(target.name+'-outer')),'parent exists and two fresh output leaves')
command=p['exact_exec_command_input'];expected="& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 '"+s['launcher_ref']['path']+"' --scope '"+p['actual_scope_ref']['path']+"' --scope-sha256 '"+p['actual_scope_ref']['sha256']+"' --grant '"+p['actual_grant_ref']['path']+"' --grant-sha256 '"+p['actual_grant_ref']['sha256']+"'\n$actualNativeExit = $LASTEXITCODE\nWrite-Output ('ACTUAL_PYTHON_EXIT=' + $actualNativeExit)\nexit $actualNativeExit"
ck(command['cmd']==expected and Path(command['workdir'])==R and command['max_output_tokens']==4000,'literal PS exact pinned four args/cwd/flags/bridge')
ck(command['cmd'].count('\n')==3 and '\\n' not in command['cmd'],'real newline separators no literal escape')
ck(p['actual_source_launcher_executed'] is False and p['automatic_retry'] is False and p['counter_reset'] is False,'one future source invocation only')
verify(p['pending_origin_ref']);ck(p['actual_canonical_tuple']==[332,160,516] and p['known_observed_failure_origins']==517,'pending one outside fixed516')
pre=R/'execution/v2.4/receipts/W13/W13-03/desktop15_owned_launcher_composition_preliminary_review_codex/778ecf0279e248718e1d59903efb53c2/review.json';pr=json.loads(pre.read_bytes());ck(pin(pre)['sha256']=='8a8492c3009c07af791a10f1df01d7493e10b0eeccca552ca100d9cccf326a2b' and pr['requested_changes']==[],'reuse46 static composition checks')
ar=save('audit.json',{'checks':checks,'count':len(checks),'failed':[x for x in checks if not x['passed']],'actual_candidate_executions':0,'new_failure_origins':[]})
save('verified-inputs.json',list(inputs.values()))
passed=all(x['passed'] for x in checks)
rrv=save('review.json',{'schema':'researchos.desktop15-owned-launcher-final-composition-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_EXACT15_OWNED_SOURCE_LAUNCH' if passed else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'actual_launcher_executed':False,'actual_source_integration_executed':False,'launch_request_ref':packetref,'scope_ref':p['actual_scope_ref'],'grant_ref':p['actual_grant_ref'],'launcher_ref':s['launcher_ref'],'controller_ref':s['controller_ref'],'registration_refs':rr,'grant_manifest_ref':p['actual_grant_manifest_ref'],'preliminary_review_ref':pin(pre),'audit_ref':ar,'canonical_observation_copies':owncopies,'checks_passed':sum(x['passed'] for x in checks),'reused_static_checks':46,'permission_boundary':'Only Root may invoke the literal sealed command once using current unique grant. This review does not execute it or grant any other operation.','actual_metadata_tuple':[332,160,516],'known_failure_origin_observed':517,'late_pending_origin_ref':p['pending_origin_ref'],'source_apply_cap':1,'source_commit_cap':1,'source_paths':15,'combined_paths':58,'inner_observed_seconds':900,'outer_owned_job_seconds_cap':1200,'cleanup_seconds':5,'open_gates':['Actual source import/commit completion and independent closed evidence/post-head registration remain pending.','Fresh58 compiler and independent Desktop169 replay/GUI/NVDA/P02/SDK/formal42 remain OPEN.','Python resource pins are point-in-time; unknown actual resources stop. No full OS lifecycle or time-fit assertion.'],'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'status':'STOPPED'})
hr=save('handoff.json',{'schema':'researchos.public-review-handoff.v1','review_ref':rrv,'decision':'READY_FOR_ROOT_ONCE_ONLY_EXACT15_OWNED_SOURCE_LAUNCH' if passed else 'REQUEST_CHANGES','manifest_path':str(O/'manifest.json'),'new_failure_origins':[],'status':'STOPPED'})
rows=[pin(x) for x in sorted(O.iterdir()) if x.is_file()];mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':rrv,'manifest':mr,'handoff':hr,'checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
