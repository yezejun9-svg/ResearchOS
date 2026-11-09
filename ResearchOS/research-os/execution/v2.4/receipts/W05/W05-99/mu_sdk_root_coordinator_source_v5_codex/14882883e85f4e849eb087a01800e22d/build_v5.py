"""One C5 Source constructor; two pure groups using pinned actual public records."""
import ast,copy,difflib,hashlib,json,math
from pathlib import Path,PureWindowsPath
OUT=Path(__file__).resolve().parent
OLD=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v4_codex/934c2f06dc1946e5aa7d5e04589dfdd2")
REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_v4_independent_review_codex/a576a6bb513846a4b4636de1ca6eda54")
ACTUAL=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/staged-runtime-prepare-root-59ef355458e14c0082ae8f82d98")
ACTUAL_REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/staged_runtime_actual_component_review_codex/8355e6db26554f058a841dc0f4a88329")
inputs=[]
def pin(p):
 raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
 raw=Path(ref['path']).read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'input drift';inputs.append(ref);return raw
def obj(ref):return json.loads(read(ref))
def put(name,value):return rawput(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def rawput(name,raw):
 with (OUT/name).open('xb') as f:f.write(raw)
 return pin(OUT/name)
oldh=obj({'path':str(OLD/'handoff.json'),'sha256':'2c96eec1d77e1b20eb9fe87dc6a2d2aa1db774182dfaa82509b6a2ae07ff84bd','bytes':4840})
oldm=obj(oldh['manifest_ref'])
for ref in oldm['members']:read(ref)
rh=obj({'path':str(REVIEW/'handoff.json'),'sha256':'2680d373dbbc4589752718b88c9048dbefe7f8b0d07a0fb58a0e6233dac1779e','bytes':1896})
review=obj(rh['review_ref']);rm=obj(rh['manifest_ref'])
for ref in rm['members']:read(ref)
assert {b['id'] for b in review['blockers']}=={'R01','R02'}
arh=obj({'path':str(ACTUAL_REVIEW/'handoff.json'),'sha256':'1db3e70d7bc5dc722bf8d967675c0b4eba8beb17bbbea2ff2b884eed4dfc6728','bytes':2034})
actualreview=obj(arh['review_ref'])
assert actualreview['decision']=='PASS_ACTUAL_COMPONENT_NO_PROVIDER'
caller=actualreview['source_ref'];read(caller)
bootstrap=obj(actualreview['bootstrap_ref']);runtime=obj(actualreview['runtime_prepare_ref']);prepared=obj(actualreview['prepare_ref']);lifecycle=obj(actualreview['lifecycle_ref'])
seedref=pin(ACTUAL/'seed.public.actual.json');seed=obj(seedref)
closures={};invocations={};before_resume={};closure_refs={}
for label in ('runtime-prepare','normal-host','cli-goal','finalize-prepare'):
 ref=pin(ACTUAL/(label+'.closure.actual.json'));closure_refs[label]=ref;closure=obj(ref);closures[label]=closure
 invocations[label]=obj(closure['invocation_ref']);before_resume[label]=obj(closure['before_resume_ref'])
fixed=json.loads(read(oldh['fixed_pins_ref']))
helper_review_ref=json.loads((OLD/'reuse-evidence.json').read_bytes())['current_helper_source_review_ref']
helperreview=obj(helper_review_ref);helpermembers=obj(helperreview['source_members_ref'])
for ref in helpermembers:read(ref)
read(json.loads((OLD/'reuse-evidence.json').read_bytes())['helper_compile_ref'])
before=read(oldh['source_ref']).decode();after=before;edits=[]
def replace(old,new):
 global after
 assert after.count(old)==1,old[:100]
 after=after.replace(old,new);edits.append((old,new))
replace('ENV_KEYS = {','STAGED_CALLER_SOURCE = '+repr(caller)+'\nENV_KEYS = {')
start=after.index('def validate_staged_closure(');end=after.index('def validate_staged_preparation(',start)
replace(after[start:end],"def same_absolute_path(actual, expected):\n    if type(actual) is not str or type(expected) is not str or '\\x00' in actual + expected:\n        return False\n    a, b = Path(actual), Path(expected)\n    return a.is_absolute() and b.is_absolute() and '..' not in a.parts and '..' not in b.parts and a == b\n\ndef exact_argv(actual, expected, path_positions):\n    return (type(actual) is list and len(actual) == len(expected) and\n            all(same_absolute_path(a, b) if i in path_positions else type(a) is str and a == b\n                for i, (a, b) in enumerate(zip(actual, expected))))\n\ndef validate_staged_closure(closure, label, invocation_ref, before_resume, invocation, owner_pid, expected_exit):\n    require(closure.get('schema') == 'researchos.staged-native-owned-closure.v1' and closure.get('label') == label and closure.get('invocation_ref') == invocation_ref and closure.get('closed') is True, 'staged invocation closure binding differs')\n    identity = closure.get('identity')\n    require(type(owner_pid) is int and owner_pid > 0 and type(identity) is dict and all(type(identity.get(k)) is int and identity[k] > 0 for k in ('owner_pid', 'runner_pid', 'creation_time_100ns')) and all(type(identity.get(k)) is str and identity[k] for k in ('run_uuid', 'job_binding_id')), 'staged original held identity is incomplete')\n    require(identity['owner_pid'] == owner_pid and all(identity.get(k) is True for k in ('captured_before_resume', 'held_job_handle', 'held_primary_handle')), 'staged Job does not belong to the original lifecycle parent')\n    require(type(before_resume) is dict and before_resume.get('assigned_before_resume') is True and before_resume.get('resumed') is False and json.dumps(before_resume.get('identity'), sort_keys=True) == json.dumps(identity, sort_keys=True), 'staged original before-resume capture differs')\n    result = invocation.get('result')\n    require(type(expected_exit) is int and native_closed(result) and result.get('error') is None and type(result.get('actual_exit')) is int and result['actual_exit'] == expected_exit and result.get('timed_out') is False and result.get('resumed') is True and invocation.get('error') is None and type(invocation.get('actual_native_exit')) is int and invocation['actual_native_exit'] == expected_exit, 'staged owned native completion differs')\n    require(type(result.get('owned_child_pid')) is int and result['owned_child_pid'] == identity['runner_pid'] and type(result.get('creation_time_100ns')) is int and result['creation_time_100ns'] == identity['creation_time_100ns'], 'staged invocation process identity differs')\n    start, end = closure.get('observed_monotonic_start'), closure.get('observed_monotonic_end')\n    require(type(start) in (int, float) and type(end) in (int, float) and math.isfinite(start) and math.isfinite(end), 'staged closure original timing missing')\n    proof = closure.get('actual_fresh_cleanup')\n    require(matching_idle_proof(proof, identity, start, end) and type(proof.get('primary_exit_code')) is int and proof['primary_exit_code'] == expected_exit, 'staged closure held identity or original fresh idle proof differs')\n    watchdog, producer = closure.get('watchdog_cleanup'), closure.get('duplicate_producer_cleanup')\n    deadline = before_resume.get('actual_deadline_monotonic')\n    require(type(deadline) in (int, float) and math.isfinite(deadline) and type(watchdog) is dict and type(watchdog.get('deadline_monotonic')) in (int, float) and watchdog['deadline_monotonic'] == deadline and watchdog.get('duplicate_handle_closed') is True and watchdog.get('errors') == [], 'staged watchdog duplicate remains open or differs')\n    require(type(producer) is dict and all(producer.get(k) is True for k in ('closed', 'job_handle_closed', 'primary_handle_closed')) and producer.get('errors') == [] and producer.get('run_uuid') == identity['run_uuid'] and type(producer.get('owner_pid')) is int and producer['owner_pid'] == owner_pid, 'staged producer duplicate remains open or differs')\n\ndef validate_bootstrap_jobs(lifecycle, closures, invocations, before_resume):\n    labels = {'runtime-prepare', 'normal-host', 'cli-goal', 'finalize-prepare'}\n    require(set(closures) == set(invocations) == set(before_resume) == labels, 'exact four original owned-job chains required')\n    jobs = lifecycle.get('jobs')\n    require(type(jobs) is list and len(jobs) == 2 and {j.get('label') for j in jobs} == {'normal-host', 'cli-goal'}, 'exact original continuation Jobs required')\n    for job in jobs:\n        require(json.dumps(job, sort_keys=True) == json.dumps(closures[job['label']], sort_keys=True), 'continuation Job differs from pinned original closure')\n    stop = lifecycle.get('host_stop')\n    require(type(stop) is dict and stop.get('planned_pre_trial_host_teardown') is True and stop.get('actual_TerminateJobObject_return') is True and type(stop.get('requested_exit_code')) is int and stop['requested_exit_code'] == 0xE0000508, 'actual planned normal Host teardown required')\n    for label in sorted(labels):\n        closure = closures[label]\n        validate_staged_closure(closure, label, closure['invocation_ref'], before_resume[label], invocations[label], lifecycle.get('actual_parent_pid'), 0xE0000508 if label == 'normal-host' else 0)\n\n")
oldargv="""        argv = [binary['path'], '-phase', phase, '-seed', doc['host_seed_ref']['path'], '-receipt', doc[ref_key]['path']]
        if phase == 'finalize-prepare':
            argv.extend(['-draft-goal-id', bootstrap['goal_id']])
        require(invocation.get('argv') == argv and Path(invocation.get('cwd', '')) == ROOT, 'staged owned invocation differs')
"""
newargv="""        argv = [binary['path'], '-phase', phase, '-seed', doc['host_seed_ref']['path']]
        if phase == 'finalize-prepare':
            argv.extend(['-draft-goal-id', bootstrap['goal_id']])
        argv.extend(['-receipt', doc[ref_key]['path']])
        path_positions = {0, 4, 8 if phase == 'finalize-prepare' else 6}
        require(exact_argv(invocation.get('argv'), argv, path_positions) and same_absolute_path(invocation.get('cwd'), str(ROOT)), 'staged owned invocation differs')
"""
replace(oldargv,newargv)
replace('    def open(self):\n',"    def _load_bootstrap_job_chain(self):\n        # Only public pinned records; original producer handles are already closed.\n        require(self.input['staged_caller_source_ref'] == STAGED_CALLER_SOURCE, 'actual staged caller Source pin differs')\n        refs = [self.input['staged_caller_source_ref']]\n        pinned(refs[0])\n        keys = {'runtime-prepare': 'runtime_prepare_closure_ref', 'normal-host': 'normal_host_closure_ref', 'cli-goal': 'cli_goal_closure_ref', 'finalize-prepare': 'finalize_prepare_closure_ref'}\n        closures, invocations, before = {}, {}, {}\n        for label, key in keys.items():\n            closure_ref = self.input[key]\n            closure = read_json(closure_ref)\n            invocation_ref, before_ref = closure['invocation_ref'], closure['before_resume_ref']\n            refs.extend([closure_ref, invocation_ref, before_ref])\n            closures[label] = closure\n            invocations[label] = read_json(invocation_ref)\n            before[label] = read_json(before_ref)\n        lifecycle = read_json(self.input['bootstrap_lifecycle_ref'])\n        require(lifecycle.get('prepare_closed_refs') == [self.input['runtime_prepare_closure_ref'], self.input['finalize_prepare_closure_ref']], 'bootstrap continuation omitted preparation closures')\n        validate_bootstrap_jobs(lifecycle, closures, invocations, before)\n        return refs\n\n"+'    def open(self):\n')
firstvalidate="        validate_bootstrap(self.bootstrap, read_json(doc['bootstrap_lifecycle_ref']), read_json(doc['bootstrap_guard_cleanup_ref']), initial_review, initial_snapshot)\n"
replace(firstvalidate,firstvalidate+"        self.bootstrap_job_refs = self._load_bootstrap_job_chain()\n")
replace('+ self.bootstrap_refs + self.helper_refs\n','+ self.bootstrap_refs + self.bootstrap_job_refs + self.helper_refs\n')
secondvalidate="        validate_bootstrap(self.bootstrap, json.loads(self.source_guard.get_buffer(doc['bootstrap_lifecycle_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['bootstrap_guard_cleanup_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['initial_cli_init_component_review_ref']['path'])), json.loads(self.source_guard.get_buffer(initial_handoff['partial_bootstrap_snapshot_ref']['path'])))\n"
replace(secondvalidate,secondvalidate+'        self._load_bootstrap_job_chain()\n')
oldloop="""        lifecycle = read_json(self.input['bootstrap_lifecycle_ref'])
        closure_refs = [self.input['runtime_prepare_closure_ref'], self.input['finalize_prepare_closure_ref']]
        require(lifecycle.get('prepare_closed_refs') == closure_refs, 'bootstrap continuation omitted the staged preparation closures')
        for label, closure_key, invocation_key in (('runtime-prepare', 'runtime_prepare_closure_ref', 'runtime_prepare_invocation_ref'), ('finalize-prepare', 'finalize_prepare_closure_ref', 'finalize_prepare_invocation_ref')):
            closure = read_json(self.input[closure_key])
            self._guard([closure['before_resume_ref']])
            validate_staged_closure(closure, label, self.input[invocation_key], read_json(closure['before_resume_ref']))
"""
newloop="""        for label, closure_key, invocation_key in (('runtime-prepare', 'runtime_prepare_closure_ref', 'runtime_prepare_invocation_ref'), ('finalize-prepare', 'finalize_prepare_closure_ref', 'finalize_prepare_invocation_ref')):
            require(read_json(self.input[closure_key])['invocation_ref'] == self.input[invocation_key], 'preparation receipt invocation differs from original closure')
        self._load_bootstrap_job_chain()
"""
replace(oldloop,newloop)
compile(after,str(OUT/'root_coordinator.py'),'exec')
inverse=after
for old,new in reversed(edits):
 assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse.encode()==before.encode()
oldast,newast=ast.parse(before),ast.parse(after)
def methods(tree):
 return {n.name:ast.dump(n,include_attributes=False) for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
om,nm=methods(oldast),methods(newast)
assert set(nm)-set(om)=={'_load_bootstrap_job_chain'}
assert {k for k in om if om[k]!=nm[k]}=={'open','prepare'}
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in oldast.body if isinstance(n,ast.FunctionDef)}
newfunc={n.name:ast.dump(n,include_attributes=False) for n in newast.body if isinstance(n,ast.FunctionDef)}
assert {k for k in oldfunc if oldfunc[k]!=newfunc[k]}=={'validate_staged_preparation','validate_staged_closure'}
assert set(newfunc)-set(oldfunc)=={'same_absolute_path','exact_argv','validate_bootstrap_jobs'}
# Only exact free functions are evaluated, with PureWindowsPath; no candidate module import.
names={'require','native_closed','matching_idle_proof','same_absolute_path','exact_argv','validate_staged_closure','validate_bootstrap_jobs','validate_staged_preparation'}
scope={'Path':PureWindowsPath,'ROOT':PureWindowsPath('D:/作品集/ResearchOS/research-os'),'json':json,'math':math}
exec(compile(ast.Module(body=[n for n in newast.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<C5-public-receipt-pure-functions>','exec'),scope)
doc={'host_seed_ref':seedref,'runtime_prepare_receipt_ref':actualreview['runtime_prepare_ref'],'prepare_receipt_ref':actualreview['prepare_ref']}
def staged(iv):
 scope['validate_staged_preparation'](seed,prepared,runtime,bootstrap,doc,fixed['trusted_host_binary'],iv['runtime-prepare'],iv['finalize-prepare'])
staged(invocations)
equiv=copy.deepcopy(invocations)
for label in ('runtime-prepare','finalize-prepare'):
 equiv[label]['argv']=[s.replace('\\','/') if PureWindowsPath(s).is_absolute() else s for s in equiv[label]['argv']]
 equiv[label]['cwd']=equiv[label]['cwd'].replace('\\','/')
staged(equiv)
r01=[]
def rejected(out,name,fn):
 try:fn()
 except (RuntimeError,KeyError,TypeError):out.append({'case':name,'rejected':True})
 else:raise AssertionError('false accept: '+name)
for name,label,index,value in [('foreign_binary','runtime-prepare',0,'D:/foreign.exe'),('relative_binary','runtime-prepare',0,'trusted-qualification-host.exe'),('foreign_seed','runtime-prepare',4,'D:/foreign-seed.json'),('foreign_receipt','finalize-prepare',8,'D:/foreign-receipt.json'),('foreign_goal','finalize-prepare',6,'FOREIGN_GOAL'),('foreign_flag','finalize-prepare',5,'-receipt'),('parent_component_in_path','runtime-prepare',0,str(PureWindowsPath(invocations['runtime-prepare']['argv'][0]).parent/'..'/'trusted-qualification-host.exe'))]:
 iv=copy.deepcopy(invocations);iv[label]['argv'][index]=value;rejected(r01,name,lambda:staged(iv))
iv=copy.deepcopy(invocations);iv['finalize-prepare']['argv']+=['-unexpected','1'];rejected(r01,'extra_arguments',lambda:staged(iv))
iv=copy.deepcopy(invocations);a=iv['finalize-prepare']['argv'];iv['finalize-prepare']['argv']=a[:5]+a[7:9]+a[5:7];rejected(r01,'different_flag_order',lambda:staged(iv))
r01_control={'id':'R01_ACTUAL_ARGV','actual_runtime_and_finalize_receipts_pass_without_rewrite':True,'equivalent_absolute_Windows_path_spelling_passes':True,'negative_cases':r01,'passed':True}
# Group R02: unmodified four actual public closure chains, then layered single-field counterexamples.
scope['validate_bootstrap_jobs'](lifecycle,closures,invocations,before_resume)
r02=[]
def fixture():return tuple(copy.deepcopy(v) for v in (lifecycle,closures,invocations,before_resume))
def trial(v):scope['validate_bootstrap_jobs'](*v)
def sync_job(v,label):
 if label in ('normal-host','cli-goal'):
  v[0]['jobs']=[copy.deepcopy(v[1][x['label']]) for x in v[0]['jobs']]
mutations=[
 ('missing_all_host_proofs',lambda v:v[1].__setitem__('normal-host',{'label':'normal-host','closed':True}),'normal-host'),
 ('original_assigned_false',lambda v:v[3]['runtime-prepare'].update(assigned_before_resume=False),None),
 ('original_resumed_true',lambda v:v[3]['finalize-prepare'].update(resumed=True),None),
 ('actual_pid_foreign',lambda v:v[2]['cli-goal']['result'].update(owned_child_pid=999999),None),
 ('actual_creation_foreign',lambda v:v[2]['normal-host']['result'].update(creation_time_100ns=999999),None),
 ('lifecycle_owner_foreign',lambda v:v[0].update(actual_parent_pid=999999),None),
 ('lifecycle_owner_bool',lambda v:v[0].update(actual_parent_pid=True),None),
 ('fresh_start_bool',lambda v:v[1]['runtime-prepare'].update(observed_monotonic_start=True),None),
 ('fresh_observation_infinite',lambda v:v[1]['cli-goal']['actual_fresh_cleanup'].update(observed_monotonic=float('inf')),'cli-goal'),
 ('fresh_window_stale',lambda v:v[1]['finalize-prepare']['actual_fresh_cleanup'].update(observed_monotonic=0.0),None),
 ('active_processes_bool',lambda v:v[1]['normal-host']['actual_fresh_cleanup'].update(active_processes=False),'normal-host'),
 ('wrong_fresh_pid',lambda v:v[1]['runtime-prepare']['actual_fresh_cleanup'].update(runner_pid=999999),None),
 ('producer_primary_open',lambda v:v[1]['cli-goal']['duplicate_producer_cleanup'].update(primary_handle_closed=False),'cli-goal'),
 ('watchdog_open',lambda v:v[1]['normal-host']['watchdog_cleanup'].update(duplicate_handle_closed=False),'normal-host'),
 ('producer_owner_foreign',lambda v:v[1]['finalize-prepare']['duplicate_producer_cleanup'].update(owner_pid=999999),None),
 ('native_handles_open',lambda v:v[2]['runtime-prepare']['result']['job_cleanup'].update(handles_closed=False),None),
 ('native_exit_bool',lambda v:v[2]['cli-goal']['result'].update(actual_exit=False),None),
 ('host_exit_zero',lambda v:v[2]['normal-host']['result'].update(actual_exit=0),None),
 ('host_timeout',lambda v:v[2]['normal-host']['result'].update(timed_out=True),None),
 ('no_planned_termination',lambda v:v[0]['host_stop'].update(actual_TerminateJobObject_return=False),None),
 ('wrong_planned_exit',lambda v:v[0]['host_stop'].update(requested_exit_code=0),None),
 ('before_identity_alias',lambda v:v[3]['runtime-prepare']['identity'].update(owner_pid=True),None),
]
for name,mutate,sync in mutations:
 v=fixture();mutate(v)
 if sync:sync_job(v,sync)
 rejected(r02,name,lambda:trial(v))
# Guard wiring is structurally checked without running coordinator methods.
loadmethod=next(n for c in newast.body if isinstance(c,ast.ClassDef) for n in c.body if getattr(n,'name',None)=='_load_bootstrap_job_chain')
loadtext=ast.get_source_segment(after,loadmethod)
assert "refs.extend([closure_ref, invocation_ref, before_ref])" in loadtext and "pinned(refs[0])" in loadtext
assert all(x in loadtext for x in ('normal_host_closure_ref','cli_goal_closure_ref','runtime_prepare_closure_ref','finalize_prepare_closure_ref'))
opentext=ast.get_source_segment(after,next(n for c in newast.body if isinstance(c,ast.ClassDef) for n in c.body if getattr(n,'name',None)=='open'))
assert '+ self.bootstrap_refs + self.bootstrap_job_refs + self.helper_refs' in opentext
assert opentext.index('self.bootstrap_job_refs = self._load_bootstrap_job_chain()')<opentext.index("if doc['mode'] == 'NO_PROVIDER':")
assert opentext.count('self._load_bootstrap_job_chain()')==2
r02_control={'id':'R02_ACTUAL_FOUR_JOB_CHAINS','unmodified_actual_four_job_chains_pass':True,'actual_source_caller_ref':caller,'negative_cases':r02,'all_four_closure_invocation_before_resume_refs_guard_wiring_verified':True,'NO_PROVIDER_checks_original_four_job_chain':True,'prior_execution_pipeline_AST_unchanged':True,'full_bytes_inverse_verified':True,'passed':True}
source_ref=rawput('root_coordinator.py',after.encode())
fixed_ref=rawput('fixed-pins.json',(OLD/'fixed-pins.json').read_bytes())
controls_ref=put('delta-controls.json',{'schema':'researchos.pure-delta-controls.v1','controls':[r01_control,r02_control],'new_controls':2,'passed':2,'actual_receipts_modified':False,'candidate_module_imported':False,'coordinator_methods_executed':False,'Native_SQL_provider_calls':0})
rawput('source.forward.diff',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/'root_coordinator.py'),tofile=str(OUT/'root_coordinator.py'))).encode())
rawput('source.inverse.diff',''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile=str(OUT/'root_coordinator.py'),tofile=str(OLD/'root_coordinator.py'))).encode())
placeholder={'path':'ROOT_MUST_SUPPLY_ACTUAL_ABSOLUTE_PATH','sha256':'ROOT_MUST_SUPPLY_EXACT_SHA256','bytes':0}
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json'):
 objdoc=json.loads((OLD/name).read_bytes())
 if 'coordinator_source_ref' in objdoc:objdoc['coordinator_source_ref']=source_ref
 if 'source_ref' in objdoc:objdoc['source_ref']=source_ref
 if 'fixed_pins_ref' in objdoc:objdoc['fixed_pins_ref']=fixed_ref
 if name.startswith('input.'):
  for key in ('normal_host_closure_ref','cli_goal_closure_ref','runtime_prepare_closure_ref','finalize_prepare_closure_ref'):objdoc[key]=placeholder
  objdoc['staged_caller_source_ref']=caller
 put(name,objdoc)
put('input-intake.json',{'input_refs':inputs,'input_drift':0})
put('reuse-evidence.json',{'prior_handoff_ref':pin(OLD/'handoff.json'),'independent_C4_review_handoff_ref':pin(REVIEW/'handoff.json'),'independent_actual_component_review_handoff_ref':pin(ACTUAL_REVIEW/'handoff.json'),'prior_controls_reused_not_rerun':[40,1,2,2],'fixed_roles':24,'fixed_roles_changed':[],'fixed_roles_reused_not_rehashed':24,'actual_receipts_used_as_pure_positive_inputs':True,'actual_caller_source_ref':caller,'helper_source_review_ref':helper_review_ref,'helper_compile_reused':True,'prior_tool_failures_recounted':False})
put('build-result.json',{'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'controls_ref':controls_ref,'constructors':1,'new_controls':2,'passed':2,'new_tool_failures':0,'Native_SQL_provider_calls':0,'Main_canonical_writes':0,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False})
print(json.dumps({'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'new_controls':2,'passed':2,'R01_negative_cases':len(r01),'R02_negative_cases':len(r02),'input_reads':len(inputs)},ensure_ascii=True))

