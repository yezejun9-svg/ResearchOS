import ast,copy,hashlib,json,re
from pathlib import Path
N=Path(__file__).resolve().parent;source=N/'run_c19_consumers.actual_owned.py';raw=source.read_bytes();tree=ast.parse(raw);choice=json.loads((N/'source.choice.json').read_bytes());contract=json.loads(Path(choice['contract_ref']['path']).read_bytes())
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def pin(p):
 p=Path(p).resolve();data=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
names={'require','typed','job_closed','validate_report_binding','validate_modes','validate_scope','environment'}
selected=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in names]
env=dict(Path=Path,re=re,__file__=str(source),pin=pin)
constants=['R','T','W','N','O','E','PRODUCER','PRODUCER_TEMP','ROUTES','EXPECTED_NATIVE','EXPECTED_FORMAL','SELECTED']
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),'<constants-only>','exec'),env)
exec(compile(ast.Module(body=selected,type_ignores=[]),'<pure-controls-only>','exec'),env)
check('exact_seven_pure_functions',len(selected)==7)
def reject(label,fn):
 rejected=False
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError):rejected=True
 check(label,rejected)
fake=dict(path=str(env['T']/'synthetic-not-a-real-receipt.json'),sha256='0'*64,bytes=1)
check('typed_positive',env['typed'](fake)==fake)
for key,value in [('bytes',True),('bytes',-1),('bytes',256*1024*1024+1),('sha256','sha256:'+'0'*64),('sha256','Z'*64),('path','relative.json')]:reject('typed_reject_'+key+'_'+str(value)[:12],lambda k=key,v=value:env['typed'](dict(fake,**{k:v})))
reject('typed_reject_extra_key',lambda:env['typed'](dict(fake,extra=True)))
routes=env['ROUTES'];run='1'*32;src={p:'sha256:'+'2'*64 for p in contract['source_roster']};go=dict(path='SYNTHETIC_GO_NOT_EXECUTED',sha256='3'*64,bytes=1)
report=dict(run_id=run,status='PASS',exit_code=0,timed_out=False,task_id='W09',check_id=None,case_id='C19',selected_tests=env['SELECTED'],passed_tests=env['SELECTED'],assertion_ids=env['EXPECTED_NATIVE'],assertions=5,formal_construction_acceptance='NOT_RUN_POSTRUN_REVIEW_PENDING',formal_case_accepted_delta=0,version_manifest=dict(source_sha256=src,os='Windows',os_release='11'),go_executable=go,actual_invocation=['SYNTHETIC_ONLY'])
request={k:dict(fake,path=str(env['T']/(k+'.json'))) for k in ('producer_closed_ref','native_packet_ref','report_ref','tool_run_ref','producer_review_handoff_ref','producer_review_manifest_ref','caller_review_handoff_ref','caller_review_manifest_ref','canonical_vector_ref')}
request['modes']=[dict(route=list(r),decision_ref=dict(fake,path=str(env['T']/('mode'+str(i)+'.json'))),independent_review_ref=fake) for i,r in enumerate(routes)]
closed=dict(status='C19_NATIVE_PRODUCER_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW',all_owned_jobs_closed=True,native_packet_ref=request['native_packet_ref'])
packet=dict(original_report_ref=request['report_ref'],original_tool_run_ref=request['tool_run_ref'],consumer_source_root=str(env['T']),formal_acceptance=False,run_id=run)
tool=dict(run_id=run,schema='researchos.w09-native-producer-tool-run.v1',report_sha256='0'*64,actual_invocation=['SYNTHETIC_ONLY'],native_exit_code=0)
env['validate_report_binding'](request,closed,packet,report,tool,contract);check('same_report_tool_positive_synthetic_only',True)
for label,field,value in [('failed_report','status','FAIL'),('case_A06','case_id','A06'),('formal_preaccepted','formal_case_accepted_delta',1),('wrong_roster','selected_tests',['OTHER']),('four_native_ids','assertions',4)]:
 altered=copy.deepcopy(report);altered[field]=value;reject('report_reject_'+label,lambda a=altered:env['validate_report_binding'](request,closed,packet,a,tool,contract))
altered=copy.deepcopy(report);altered['version_manifest']['source_sha256'].pop(contract['source_roster'][0]);reject('report_reject_missing_source21',lambda:env['validate_report_binding'](request,closed,packet,altered,tool,contract))
bad=copy.deepcopy(packet);bad['original_report_ref']['sha256']='4'*64;reject('report_reject_foreign_packet_report',lambda:env['validate_report_binding'](request,closed,bad,report,tool,contract))
relative='execution/receipts/W09/retrieval/run-'+run+'/report.json';stdout_sha='5'*64
decisions=[dict(schema='researchos.w09-mode-decision.v2',route=list(route),mode='FIXTURE',decision='QUALIFIED',input_origin='OWNED_TEMP_DIR',reviewer_role='INDEPENDENT_NON_AUTHOR',producer_id='SYNTHETIC_PRODUCER',reviewer_id='SYNTHETIC_REVIEWER',run_id=run,report_ref=relative,report_sha256='0'*64,stdout_sha256=stdout_sha,source_sha256=src,go_executable=go) for route in routes]
review=dict(schema='researchos.w09-independent-mode-review.v1',actor_id='SYNTHETIC_REVIEWER',actor_role='INDEPENDENT_NON_AUTHOR',producer_id='SYNTHETIC_PRODUCER',decision='QUALIFIED',run_id=run,report_sha256='0'*64,source_sha256=src,go_executable=go,run_os='Windows',run_os_release='11')
reviews=[copy.deepcopy(review),copy.deepcopy(review)]
env['validate_modes'](request,report,decisions,reviews,relative,stdout_sha);check('two_route_mode_positive_synthetic_in_memory_only',True)
for label,key,value in [('same_author','reviewer_id','SYNTHETIC_PRODUCER'),('template_unqualified','decision','QUALIFIED_ONLY_AFTER_REAL_INDEPENDENT_REVIEW'),('wrong_route','route',list(routes[1])),('wrong_run','run_id','6'*32),('wrong_temp_origin','input_origin','USER_PROFILE'),('wrong_source','source_sha256',{})]:
 altered=copy.deepcopy(decisions);altered[0][key]=value;reject('mode_reject_'+label,lambda a=altered:env['validate_modes'](request,report,a,reviews,relative,stdout_sha))
altered=copy.deepcopy(reviews);altered[0]['actor_id']='OTHER';reject('mode_reject_mismatched_reviewer',lambda:env['validate_modes'](request,report,decisions,altered,relative,stdout_sha))
bad=copy.deepcopy(request);bad['modes'][1]['decision_ref']=bad['modes'][0]['decision_ref'];reject('mode_reject_same_decision_twice',lambda:env['validate_modes'](bad,report,decisions,reviews,relative,stdout_sha))
scope=dict(schema='researchos.root-w09-c19-component-consumer-scope.v1',executor='codex:/root',status='ROOT_AUTHORIZED_COMPONENT_CONSUMPTION_ONLY',candidate_root=str(env['T']),consumer_receipt_root=str(env['O']),consumer_environment_root=str(env['E']),routes=[list(v) for v in routes],formal_case_accepted_delta=0,formal_dispatcher=False,registry_write=False,producer_rerun=False,source_caller_ref=pin(source),**request)
env['validate_scope'](scope,request);check('root_scope_positive_synthetic_in_memory_only',True)
for label,key,value in [('wrong_executor','executor','codex:OTHER'),('dispatcher','formal_dispatcher',True),('registry_write','registry_write',True),('producer_rerun','producer_rerun',True),('foreign_output','consumer_receipt_root','SYNTHETIC_FOREIGN'),('foreign_report','report_ref',fake)]:
 bad=copy.deepcopy(scope);bad[key]=value;reject('scope_reject_'+label,lambda a=bad:env['validate_scope'](a,request))
good=dict(job_cleanup=dict(errors=[],active_processes_last_observed=0,**{k:True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')}))
check('closed_job_positive',env['job_closed'](good))
for key,value in [('errors',['SYNTHETIC']),('active_processes_last_observed',1),('handles_closed',False),('job_idle_confirmed',False),('assigned_before_resume',False)]:
 bad=copy.deepcopy(good);bad['job_cleanup'][key]=value;check('closed_job_reject_'+key,not env['job_closed'](bad))
check('closed_job_reject_no_result',not env['job_closed'](None))
clean=env['environment'](relative,'tool.json','mode.json',dict(request,_current_mode_sha='0'*64))
check('explicit_temp_preserves_producer_root',clean['TEMP']==clean['TMP']==str(env['PRODUCER_TEMP']))
check('explicit_profile_is_new_consumer_env',clean['USERPROFILE']==str(env['E']/'profile'))
check('no_pythonpath_home_or_user_credentials',not ({'PYTHONPATH','PYTHONHOME','OPENAI_API_KEY','ANTHROPIC_API_KEY'}&set(clean)))
check('environment_does_not_read_process_environment','os.environ' not in ast.unparse(next(x for x in selected if x.name=='environment')))
run_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run_owned']
check('single_owned_callsite_inside_fixed_two_route_loop',len(run_calls)==1)
check('consumer_timeout120',isinstance(run_calls[0].args[5],ast.Constant) and run_calls[0].args[5].value==120)
check('source_no_Popen_run_system_calls',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('Popen','run','system') for n in ast.walk(tree)))
check('caller_no_product_write_bytes_or_write_text',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('write_bytes','write_text') for n in ast.walk(tree)))
check('child_argv_no_isolated_mode_and_has_S_B',"'-S', '-B', '-X', 'utf8'" in ast.unparse(tree) and "'-I'" not in ast.unparse(tree))
router=ast.parse(Path(contract['source_refs']['ops/ci/w09_formal_router.py']['path']).read_bytes())
check('router_requires_sibling_import',any(isinstance(n,ast.ImportFrom) and n.module=='w09_evidence_closure' for n in router.body))
check('source_roster_exact21',len(contract['source_roster'])==21)
check('source_is_two_C19_components_not_dispatcher',env['ROUTES']==(('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19')))
check('full_python_py_and_pyc_closure','p.suffix.lower() in (\'.py\', \'.pyc\')' in ast.unparse(tree))
check('guard_cleanup_finally_present',any(isinstance(n,ast.Try) and n.finalbody for n in ast.walk(tree)))
check('no_actual_output_or_environment_created',not env['O'].exists() and not env['E'].exists())
for v in json.loads((N/'source-input-pins.original.json').read_bytes()):check('original_input_unchanged_'+v['path'],pin(v['path'])==v)
result=dict(status='PASS',count=len(checks),checks=checks,execution_kind='PURE_EXTRACTED_FUNCTIONS_SYNTHETIC_IN_MEMORY_AND_STATIC_AST_ONLY',mode_receipts_generated=False,actual_guard_or_owned_job=False,actual_consumer_Git_Go_SQL_API_model=False,canonical_written=False,caller_ref=pin(source))
with (N/'source-controls.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS',checks=len(checks),controls_ref=pin(N/'source-controls.json'),caller_ref=pin(source))))
