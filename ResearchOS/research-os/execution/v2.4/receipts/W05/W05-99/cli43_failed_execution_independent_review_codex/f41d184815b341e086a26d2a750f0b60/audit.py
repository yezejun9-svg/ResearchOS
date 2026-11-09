from pathlib import Path
import json,hashlib,collections,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='477e329b79944cb0b33f9ead24811760';N=P/('integration_codex/cli43-fresh-held2-r326-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U;O=P/'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60'
checks=[]; refs=[]
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(path(p).read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def check(n,b):
 checks.append({'check':n,'passed':bool(b)})
 if not b:raise ValueError(n)
def verify(r):
 a=pin(r['path']);check('hash '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes']);refs.append(r);return path(r['path'])
def norm(p):return str(Path(p.removeprefix('\\\\?\\')).absolute()).casefold()
def rowsmap(rows):return {norm(x['path']):(x['sha256'],x['bytes']) for x in rows}
try:
 pins={E/'failure.origin.json':'c28ce01137b787d3f1a331d2a738ada8310fa83ac7adeb9ef2c36d42b9ec74d5',E/'result.json':'e885f5b24366eeb28c4bdebe91b2d04a0d3a0303f9c5123cf408b347a15d0175',E/'manifest.json':'cc473e0abc8bbeaffa830b15ab50d5f9c9353622c7b54cbcd4480326c849b347',N/'root-launch.outer-completion.json':'e1de1a71dd149fe6b5d65c1191be26e90153d4fc90d72f085d3ca9884e651d04',N/'root-launch.closed.manifest.json':'0d5acb931cd05379be67196e8f950bdafe3eb8e8782f1e64828b0f5e0019dc56'}
 for p,h in pins.items():check('supplied '+p.name,pin(p)['sha256']==h)
 member_counts={}
 for p,key in [(E/'manifest.json','files'),(L/'manifest.json','files'),(N/'root-launch.closed.manifest.json','members')]:
  m=read(p);rr=m[key];member_counts[str(p)]=len(rr)
  if 'count' in m:check('MF count '+str(p),m['count']==len(rr))
  for r in rr:verify(r)
 s=read(N/'scope_registration.json');g=read(Path(s['new_authorization_root'])/'authorization.execute.json');outer=read(N/'root-launch.outer-completion.json');res=read(E/'result.json');f=read(E/'failure.origin.json');b=read(E/'build-cli.invocation.json');d=b['result']['debug_capture'];j=b['result']['job_cleanup']
 check('first cause original exact',res['first_cause']==f and f['last_child_result']==b['result'])
 check('original stage NULL retained',f['stage']=='build-cli' and f['actual_stage_native_exit'] is None)
 check('actual Go1 independent',b['actual_exit']==1 and b['result']['actual_exit']==1 and d['exit_event_code']==1)
 check('no helper error timeout termination',b['result']['error'] is None and b['result']['timed_out'] is False and j['termination_requested'] is False and j['termination_code_requested'] is None)
 check('complete cleanup',all(j[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[] and j['explicit_owned_handle_count']==284 and j['explicit_owned_handle_close_successes']==284 and j['explicit_owned_handles_remaining']==0)
 check('debug complete25',d['complete'] is True and d['create_process_count']==25 and d['exit_process_count']==25 and len(d['process_generations'])==25 and d['actual_loaded_file_handles_only'] is True)
 process_summary=[]
 for z in d['process_generations']:
  image=z['image'];name=Path(image['path_from_actual_file_handle']).name;process_summary.append({'pid':z['pid'],'creation_time_100ns':z['creation_time_100ns'],'image':name,'independent_exit':z['independent_exit'],'exit_event_code':z['exit_event_code']})
  check('exit match '+str(z['pid']),z['independent_exit']==z['exit_event_code'] and z['exit_continued'] is True and z['job_membership_observed'] is True)
 check('primary1 children0',collections.Counter((z['image'],z['independent_exit']) for z in process_summary)=={('go.exe',1):1,('compile.exe',0):19,('asm.exe',0):5})
 vector_rows=[]; ledgers={};merged={}
 for p in sorted(E.glob('ledger-add-*.json')):
  x=read(p);added=rowsmap(x['added']);full=rowsmap(x['full_members']);check('ledger unique '+p.name,len(full)==len(x['full_members']));check('ledger old prefix '+p.name,all(k in full and full[k]==v for k,v in merged.items()));merged.update(added);check('ledger exact union '+p.name,merged==full);ledgers[x['revision']]=full
 for p in sorted(E.glob('*.vector.json')):
  x=read(p);expected=rowsmap(x['expected_members']);observed=rowsmap(x['observed_members']);check('saved vector complete '+p.name,x['drift']==[] and expected==observed==ledgers[x['revision']] and len(expected)==x['file_count']==len(x['expected_members'])==len(x['observed_members']));vector_rows.append({'ref':pin(p),'revision':x['revision'],'file_count':x['file_count'],'drift':0})
 check('beforeGo through finally same bytes',(E/'before-any-go.vector.json').read_bytes()==(E/'after-finally.vector.json').read_bytes())
 for i,m in enumerate(d['modules']):
  check('debug hFile beforeafter '+str(i),m['before']==m['after']);key=norm(m['path_from_actual_file_handle']);check('debug image pre-pinned '+str(i),key in merged and merged[key]==(m['before']['sha256'],m['before']['bytes']))
 check('native calls6 stages5',res['native_calls']==6 and len(res['stages'])==5)
 for st in res['stages']:
  x=read(verify(st['result_ref']));check('preceding native0 '+st['label'],x['actual_exit']==0 and x['result']['actual_exit']==0 and x['result']['error'] is None and x['result']['timed_out'] is False)
 check('business cases NOT_STARTED',res['cases']==[] and res['NOT_RUN']==s['ordered_cases'] and [z['leaf'] for z in res['case_roster']]==s['ordered_cases'] and all(z['state']=='NOT_STARTED' and z['launch_attempted'] is False and z['actual_native_exit'] is None and z['qualified'] is False for z in res['case_roster']))
 graph=read(E/'go-graph.actual.json');arts=read(E/'build-artifacts.finally.json');check('graph recorded and artifacts partial',len(graph['packages'])==355 and len(graph['all_referenced_files'])==6417 and arts['partial_if_failed'] is True)
 runtime=[]
 for p in list(E.glob('*.python-os.native-after.json'))+[E/'python-os.before.json',E/'python-os.after.json',L/'python-os.before.json',L/'python-os.after.json']:
  x=read(p);check('runtime pointtime '+str(p),x['point_in_time_only'] is True and x['Python_lifecycle_proof'] is False);check('runtime saved pins '+str(p),all(norm(q['path']) in merged and merged[norm(q['path'])]==(q['sha256'],q['bytes']) for q in x['files']));runtime.append({'ref':pin(p),'count':len(x['files'])})
 for row in g['canonical_copies']:
  cp=verify(row['ref']);check('current canonical equals original '+row['canonical_path'],path(row['canonical_path']).read_bytes()==cp.read_bytes())
 headfile=R/'.git/HEAD';h=headfile.read_text().strip();check('Main symbolic HEAD known',h=='ref: refs/heads/main');refhead=R/'.git/refs/heads/main';check('Main current unchanged',refhead.read_text().strip()==s['source_commit']);head_refs=[pin(headfile),pin(refhead)]
 lc=read(L/'completed.json');li=read(L/'invocation.result.json');ci=read(N/'root-launch.invocation.json')
 check('same propagated failure',lc['actual_inner_native_exit']==1 and lc['program_reported_exit']==1 and li['actual_native_exit']==1 and ci['actual_launcher_native_exit']==1 and outer['actual_python_caller_exit']==1 and outer['actual_outer_tool_exit']==1 and outer['underlying_failure_count']==1)
 check('no second firstcause',res['secondary']==[] and lc['secondary']==[] and ci['caller_error'] is None and ci['secondary']==[])
 check('no product qualification',res['product_acceptance'] is False and res['formal_increment']==0 and res['SDK_MODEL_external_paid']==0 and outer['separately_captured_outer_native_raw'] is False and outer['caller_OS_lifecycle_qualification'] is False)
 stderr=(E/'build-cli.stderr.raw').read_text(encoding='utf-8',errors='strict');terms=['error:','fatal','panic','failed','access is denied','cannot ','undefined:'];suspects=[{'line':i+1,'text':line} for i,line in enumerate(stderr.splitlines()) if any(t in line.lower() for t in terms)]
 save('evidence-audit.json',{'checks':checks,'manifest_members':member_counts,'verified_refs':refs,'saved_vector_audit':vector_rows,'runtime_saved_observations':runtime,'process_summary':process_summary,'stderr_review':{'ref':pin(E/'build-cli.stderr.raw'),'line_count':len(stderr.splitlines()),'diagnostic_term_candidates':suspects,'meaning':'No matching line does not prove no diagnostic or a compiler/source root cause.'},'Main_head_refs':head_refs,'full_backing_resource_tree_rehashed':False,'actual_target_execution':False})
 review={'schema':'researchos.cli43-failed-execution-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'FAILED_EXECUTION_EVIDENCE_CLOSED_WITH_QUALIFICATION_WITHHELD','requested_changes':[],'executor_result_ref':pin(E/'result.json'),'executor_manifest_ref':pin(E/'manifest.json'),'first_origin_ref':pin(E/'failure.origin.json'),'launcher_manifest_ref':pin(L/'manifest.json'),'root_completion_ref':pin(N/'root-launch.outer-completion.json'),'root_closed_manifest_ref':pin(N/'root-launch.closed.manifest.json'),'audit_ref':pin(O/'evidence-audit.json'),'confirmed':{'native_calls':6,'stage':'build-cli','Go_primary_native_exit':1,'original_first_cause_stage_exit':None,'debug_tree_complete':True,'processes':25,'compiler_children_exit0':19,'assembler_children_exit0':5,'module_hFile_observations':len(d['modules']),'job_idle':True,'active_processes':0,'owned_handles_closed':284,'owned_handles_remaining':0,'cleanup_errors':[],'timed_out':False,'termination_requested':False,'case_roster':res['case_roster'],'go_list_native_exit':0,'recorded_graph_packages':355,'recorded_graph_files':6417,'partial_build_artifacts':len(arts['files']),'saved_final_vector_files':24743,'saved_vector_drift':0,'live_canonical_equal_grant_copies':True,'Main_head':s['source_commit']},'unresolved':{'primary_Go_exit1_cause':None,'ordinary_source_compile_error_proven':False,'lost_pipe_output_proven':False,'debug_interaction_cause_proven':False,'fresh_compilation_qualified':False,'business_cases_qualified':False},'interpretation':'The runner stopped at its exact actual-exit-zero guard. Primary Go1 is independently supported by the debug exit event and held-process exit query; original stage-level NULL is retained. All recorded compile/asm children exited0. Saved -x stderr has no identified explicit compiler diagnostic; it does not establish why Go returned1. Complete debug/Job records do not prove application pipe content completeness or successful compilation.','underlying_failure_count':1,'propagation':'Inner Python1, launcher1 and Root caller/outer1 propagate the same build-cli first cause; they are not additional origins. Outer completion is a tool-field observation, not separately captured original outer native streams.','preservation':'E52/L8/Root14 manifest members verified byte-for-byte. Saved vector revision chains and before/native-after/final observations audited without rehashing the whole backing public tree. Current4 canonical bytes and direct .git HEAD/ref checked; no native Git invocation. Original8 late origins and this1 remain pending; registered450, reported observed459.','actual_review_target_execution':False,'same_input_retry':False,'source_acceptance':False,'formal_increment':0,'new_reviewer_failure_origins':[],'status':'STOPPED'}
 save('review.json',review);print(json.dumps({'checks':len(checks),'review':pin(O/'review.json')},ensure_ascii=True))
except BaseException:
 save('audit.failure.json',{'traceback':traceback.format_exc(),'checks':checks,'actual_target_execution':False});raise
