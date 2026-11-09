"""Read-only Scope7 failed actual execution closure audit. No product or Git."""
import collections,datetime,hashlib,json,pathlib
R=pathlib.Path('D:/作品集/ResearchOS/research-os');U='9eccde97a9fa4815941768cacaf590dc';A=pathlib.Path(__file__).parent
P=R/'execution/v2.4/receipts/W13/W13-03'
S=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-'+U+'/scope_registration.json')
F=R/('execution/v2.4/receipts/W05/W05-99/scope7_grant_recovery_root_inputs_codex/'+U+'-r339-667-v31/failure-origin.669.desktop-caller-once.original.json')
reads={}
def read(p):
 p=pathlib.Path(p);b=p.read_bytes()
 reads[p]=b;return b
def doc(p):return json.loads(read(p))
def pin(p):
 p=pathlib.Path(p);b=read(p)
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,obj):
 with (A/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(A/name)
scope=doc(S);failure=doc(F);E=pathlib.Path(scope['output_root']);L=pathlib.Path(scope['outer_output_root']);X=pathlib.Path(scope['export_root']);C=P/'desktop58_root_terminal_closure_codex/fd6fec9e9d2a482d98203421ac21a82b';B=X/'.desktop58-build-receipts'
checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
def checked_ref(x):
 p=pathlib.Path(x['path'])
 if not p.is_absolute():p=R/p
 q=pin(p);check('pin '+q['path'],q['sha256']==x['sha256'] and q['bytes']==x['bytes'])
 return p
for key in ('controller_ref','launcher_ref','debug_helper_ref','owned_helper_ref','roster_ref'):
 checked_ref(scope[key])
check('fixed Scope7 digest',pin(S)['sha256']=='c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859')
er,lr,ci=doc(E/'result.json'),doc(L/'result.json'),doc(C/'root-launch.invocation.json')
li=doc(L/'invocation.json')
bi=doc(checked_ref(failure['original_build_invocation_ref']))
result=bi['result'];debug=result['debug_capture'];cleanup=result['job_cleanup']
check('failure669 same original exec/write_stdin chain',failure['count']==669 and failure['first_result']['session_id']==92813 and failure['polls'][-1]['input']['session_id']==92813 and failure['polls'][-1]['result']['exit_code']==1)
check('Root explicit Python exit bridge one',failure['polls'][-1]['result']['output'].endswith('ACTUAL_PYTHON_EXIT=1\r\n'))
check('all layer actual exit agrees',failure['outer_exit']==failure['python_exit']==failure['actual_launcher_native_exit']==ci['actual_launcher_native_exit']==li['actual_native_exit']==lr['actual_native_inner_exit']==1)
check('builder native rejected termination code agrees',failure['actual_build_native_exit']==bi['actual_native_exit']==result['actual_exit']==cleanup['termination_code_requested']==3758097160)
check('executor last native result exact original',er['last_child_result']==result)
check('launcher inner owned result exact original',lr['inner_result']==li['owned_result'])
check('original grant exits remain unknown',failure['original_grant_terminal']=={'outer':None,'python':None,'native':None})
check('upper wrapper unknown fields preserved',ci['actual_outer_tool_exit'] is None and lr['actual_outer_native_exit'] is None and er['first_error']['actual_native_exit'] is None)
# Pair all process create and exit events chronologically, retaining generation identity.
active={};generations=[];faults=[]
for index,event in enumerate(debug['events']):
 if event.get('debug_event_continued') is not True:faults.append({'index':index,'issue':'not continued'})
 pid=event['pid'];code=event['code']
 if code==3:
  if pid in active:faults.append({'index':index,'issue':'PID created while active','pid':pid})
  record={'pid':pid,'generation':event['process_generation'],'create_event_index':index,'create_tid':event['tid']}
  active[pid]=record;generations.append(record)
 elif code==5:
  record=active.pop(pid,None)
  if record is None:faults.append({'index':index,'issue':'exit without active creation','pid':pid})
  else:record.update(exit_event_index=index,exit_code=event['actual_exit_event_code'],exit_continued=event['debug_event_continued'])
check('806 exact process generations paired',len(generations)==806 and not active and not faults and sorted(x['generation'] for x in generations)==list(range(1,807)))
check('debug declared 806 counts agree',debug['create_process_count']==debug['exit_process_count']==debug['total_processes_last_observed']==806)
rejected=debug['rejected_load_facts']
check('single exact net.exe diagnostic rejection',len(rejected)==1 and rejected[0]['event_code']==3 and rejected[0]['process_generation']==806 and rejected[0]['before']=={'sha256':'bb3e638c8b5b6ef80847e364aeef2796cad25d3539cf9b41d3820fa48943e777','bytes':81920} and rejected[0]['path_from_actual_file_handle'].replace('\\','/').endswith('/Windows/System32/net.exe') and rejected[0]['expected_pin'] is None and rejected[0]['qualified_module'] is False and rejected[0]['diagnostic_only'] is True)
check('rejected generation also has observed exit',any(x['generation']==806 and x['pid']==rejected[0]['pid'] and 'exit_code' in x for x in generations))
check('primary create exit observed',generations[0]['pid']==result['owned_child_pid'] and generations[0]['exit_code']==result['actual_exit'] and debug['exit_event_code']==result['actual_exit'])
check('actual job termination and zero active confirmed',cleanup['termination_requested'] is True and cleanup['termination_succeeded'] is True and cleanup['active_processes_last_observed']==0 and cleanup['job_idle_confirmed'] is True and cleanup['primary_exit_confirmed'] is True)
check('8967 explicit owned handle closes reported',cleanup['explicit_owned_handle_count']==cleanup['explicit_owned_handle_close_successes']==8967 and cleanup['explicit_owned_handles_remaining']==0 and cleanup['handles_closed'] is True)
check('failure finalization error preserved',cleanup['errors']==['RuntimeError: Evidence finalization incomplete after earlier failure; no success'] and debug['complete'] is False and 'process_generations' not in debug and all('after' not in m for m in debug['modules']))
top=[]
for order,name in enumerate(('git-head','export-blobs','build-current58'),1):
 v=doc(E/(name+'.invocation.json'));q=v['result'];dc=q['debug_capture'];cl=q['job_cleanup']
 check(name+' exact request sequence',v['request']==doc(E/(name+'.request.json')) and v['request']['sequence']==order)
 check(name+' native and cleanup closure',v['actual_native_exit']==q['actual_exit'] and cl['primary_exit_confirmed'] is True and cl['job_idle_confirmed'] is True and cl['handles_closed'] is True and cl['active_processes_last_observed']==0)
 top.append({'name':name,'sequence':order,'native_exit':v['actual_native_exit'],'invocation_ref':pin(E/(name+'.invocation.json')),'debug_complete':dc['complete'],'cleanup':cl})
check('only3 native top invocations',er['actual_native_top_commands']==3 and {p.name for p in E.glob('*.invocation.json')}=={x+'.invocation.json' for x in ('git-head','export-blobs','build-current58')})
states=er['all_case_states'];roster=doc(pathlib.Path(scope['roster_ref']['path']))
check('170 states entirely NOT_STARTED',len(states)==170 and all(x['state']=='NOT_STARTED' and x['native_exit'] is None and x['qualified'] is False for x in states))
check('exact169nodeandGo3group',[(x['lane'],x['name']) for x in states]==[('go3','pure-Go-exact3')]+[('node',x['name']) for x in roster['leaves']+roster['regressions']] and len(roster['go_units'])==3)
check('no case/buildinfo/fresh/completion outputs',not list(E.glob('case-*')) and not list(E.glob('buildinfo-*')) and not (E/'fresh-release.json').exists() and not (E/'completed.json').exists() and not (B/'result.json').exists())
check('no case results or observed HTTP',er['rows']==[] and er['actual_observed_HTTP_total']==0)
nested=[]
for p in sorted(B.glob('*.invocation.json')):
 v=doc(p);nested.append({'name':p.stem,'exit_as_recorded_by_builder':v['exit'],'ref':pin(p)})
check('8 nested invocations saved without builder completed result',len(nested)==8 and all(x['exit_as_recorded_by_builder']==0 for x in nested) and not (B/'react-build.invocation.json').exists())
vectors={}
for name in ('before-build.vector.json','build-current58-native-after.vector.json','final.vector.json'):
 v=doc(E/name);vectors[name]=pin(E/name);check(name+' full vector no drift',v['revision']==3 and v['file_count']==25595 and len(v['expected_members'])==len(v['observed_members'])==25595 and v['expected_members']==v['observed_members'] and v['drift']==[])
check('three vector original bytes identical',len({v['sha256'] for v in vectors.values()})==1)
for directory in (E,L):
 check(directory.name+' runtime before/after exact',read(directory/'runtime.before.json')==read(directory/'runtime.after.json'))
canon={'checkpoint.json':'4ed88a919cecc93d544c3b7a88745f45bcbc5b43156517d3ccccc6aa3cdc258b','path_ownership.json':'8d954eff78630ff678ac9d1abbc5a88cadca60285a4d16a32f857ac2f12d37d3','step_state.json':'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','commands.json':'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129'}
current=[]
for name,sha in canon.items():
 p=pin(R/'execution/v2.4'/name);current.append(p);check('current4 '+name,p['sha256']==sha)
inventory={}
for label,directory in [('executor',E),('launcher',L),('caller',C),('nested_builder_receipts',B)]:
 inventory[label]=[pin(p) for p in sorted(directory.iterdir()) if p.is_file()]
for key in ('stdout_ref','stderr_ref','scope_ref','grant_ref'):checked_ref(ci[key])
pairref=put('process-event-pairs.json',{'schema':'researchos.scope7-independent-event-pairs.v1','original_invocation_ref':pin(E/'build-current58.invocation.json'),'all_event_count':len(debug['events']),'event_counts':dict(collections.Counter(x['code'] for x in debug['events'])),'pairs':generations,'faults':faults,'active_after_all_events':active,'independent_kernel_exit_verification':'NOT_AVAILABLE: original failure path intentionally skipped process_generations finalization'})
out={'schema':'researchos.scope7-failed-execution-independent-audit.v1','actor':'codex:/root/w05_merge_review','scope_ref':pin(S),'failure_origin_ref':pin(F),'checks':checks,'check_count':len(checks),'failed_checks':[x for x in checks if not x['passed']],'terminal_refs':{'executor':pin(E/'result.json'),'launcher':pin(L/'result.json'),'caller':pin(C/'root-launch.invocation.json')},'actual_exit_chain':{'outer_tool':1,'root_python':1,'launcher_native':1,'controller_native':1,'builder_native':3758097160},'first_rejected_load_original':rejected[0],'original_process_time_note':'Integer timestamps written entirely through Python JSON, with no JavaScript Number conversion','top_invocations':top,'process_event_pairs_ref':pairref,'all806_event_pair_count':len(generations),'explicit_handle_closure_basis':'Original helper counters 8967 successful CloseHandle calls, 0 remaining, handles_closed true; individual handle ledger not serialized','original_cleanup_errors':cleanup['errors'],'original_debug_complete':debug['complete'],'retained_module_before_fact_count':len(debug['modules']),'module_after_hashes_available':False,'individual_kernel_exit_finalization_available':False,'post_build_not_started':{'case_process_groups':170,'go_assertions_in_group':3,'node_controls':169,'buildinfo_operations':3,'remaining_top_native_commands':scope['native_top_command_cap']-3,'offscreen_controls_declared':scope['offscreen_Electron_controls'],'offscreen_count_note':'Declared separately; not added to top-command or case-state totals'},'nested_builder_invocations':nested,'current_four':current,'vectors':vectors,'original_inventory':inventory,'root_truncated_diagnostic_retained_as_truncated':failure['diagnostic_overlarge_read']['result']['original_token_count'],'new_actual_failures':0,'reviewer_product_git_source_cas_calls':0,'canonical_writes':0,'formal_increment':0,'source_acceptance':False}
p=put('audit.json',out)
print(json.dumps({'audit_root':A.relative_to(R).as_posix(),'audit_ref':p,'checks':len(checks),'failed_checks':out['failed_checks'],'event_pairs':len(generations),'original_files_pinned':sum(map(len,inventory.values()))},ensure_ascii=False))
