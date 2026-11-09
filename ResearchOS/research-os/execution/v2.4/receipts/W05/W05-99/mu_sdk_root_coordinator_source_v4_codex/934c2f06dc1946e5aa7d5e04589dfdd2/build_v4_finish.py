"""Second and final v4 constructor: add staged duplicate closure and current helper evidence guards."""
import ast,copy,difflib,hashlib,json,math
from pathlib import Path,PureWindowsPath
OUT=Path(__file__).resolve().parent
OLD=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v3_codex/f02d7bbd33534835985bfd5a87f6bd67")
def pin(p):
    raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode();(OUT/name).write_bytes(raw);return pin(OUT/name)
def read(ref):
    raw=Path(ref['path']).read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];inputs.append(ref);return raw
inputs=json.loads((OUT/'input-intake.json').read_bytes())['input_refs']
current_review_ref={'path':"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_host_v4_delta_review_codex/3874b7621ecbe249b42144ded9b65406/review.json",'sha256':'06f6c01a597c877b915443433323460b55093ae2194960f545f3cab55140127a','bytes':4546}
helper_review=json.loads(read(current_review_ref))
reuse=json.loads((OUT/'reuse-evidence.json').read_bytes());compile_ref=reuse['helper_compile_ref']
compile_doc=json.loads(read(compile_ref));members_ref=helper_review['source_members_ref'];members=json.loads(read(members_ref))
for ref in members:read(ref)
def same_pin(a,b):return Path(a['path'])==Path(b['path']) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
assert same_pin(compile_doc['source_members_ref'],members_ref)
fixed=json.loads((OUT/'fixed-pins.json').read_bytes())
assert same_pin(helper_review['binary_ref'],fixed['trusted_host_binary']) and same_pin(compile_doc['binary_ref'],fixed['trusted_host_binary'])
assert helper_review['decision']=='READY_SOURCE_FOR_ZERO_PROVIDER_PREPARATION'
# Snapshot the successful first constructor outputs, never overwrite its originals without a retained copy.
changed=['root_coordinator.py','source.forward.diff','source.inverse.diff','input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json','delta-controls.json','input-intake.json','reuse-evidence.json','build-result.json']
snapshot=OUT/'constructor1-snapshot';snapshot.mkdir()
for name in changed:
    with (snapshot/name).open('xb') as target:target.write((OUT/name).read_bytes())
first=(OUT/'root_coordinator.py').read_text(encoding='utf-8');after=first;edits=[]
def replace(old,new):
    global after
    assert after.count(old)==1,old[:100]
    after=after.replace(old,new);edits.append((old,new))
replace("ENV_KEYS = {","CURRENT_HELPER_SOURCE_REVIEW = "+repr(current_review_ref)+"\nCURRENT_HELPER_COMPILE = "+repr(compile_ref)+"\nENV_KEYS = {")
replace('def validate_staged_preparation(',"def validate_staged_closure(closure, label, invocation_ref, before_resume):\n    require(closure.get('schema') == 'researchos.staged-native-owned-closure.v1' and closure.get('label') == label and closure.get('invocation_ref') == invocation_ref and closure.get('closed') is True, 'staged invocation closure binding differs')\n    identity = closure.get('identity')\n    require(type(identity) is dict and all(type(identity.get(k)) is int and identity[k] > 0 for k in ('owner_pid', 'runner_pid', 'creation_time_100ns')) and all(type(identity.get(k)) is str and identity[k] for k in ('run_uuid', 'job_binding_id')), 'staged original held identity is incomplete')\n    require(type(before_resume) is dict and json.dumps(before_resume.get('identity'), sort_keys=True) == json.dumps(identity, sort_keys=True), 'staged closure identity differs from original before-resume record')\n    start, end = closure.get('observed_monotonic_start'), closure.get('observed_monotonic_end')\n    require(type(start) in (int, float) and type(end) in (int, float) and math.isfinite(start) and math.isfinite(end), 'staged closure original timing missing')\n    require(matching_idle_proof(closure.get('actual_fresh_cleanup'), closure.get('identity'), start, end), 'staged closure held identity or original fresh idle proof differs')\n    watchdog, producer = closure.get('watchdog_cleanup'), closure.get('duplicate_producer_cleanup')\n    require(type(watchdog) is dict and watchdog.get('duplicate_handle_closed') is True and watchdog.get('errors') == [], 'staged watchdog duplicate remains open')\n    require(type(producer) is dict and producer.get('closed') is True and producer.get('errors') == [], 'staged producer duplicate remains open')\n\n"+'def validate_staged_preparation(')
insert="""        require(doc['trusted_host_current_source_review_ref'] == CURRENT_HELPER_SOURCE_REVIEW and doc['trusted_host_current_compile_ref'] == CURRENT_HELPER_COMPILE, 'current staged helper evidence differs')
        helper_review = read_json(doc['trusted_host_current_source_review_ref'])
        helper_compile = read_json(doc['trusted_host_current_compile_ref'])
        require(helper_review.get('schema') == 'researchos.trusted-host-source-delta-review.v1' and helper_review.get('decision') == 'READY_SOURCE_FOR_ZERO_PROVIDER_PREPARATION' and helper_review.get('actor_id') not in AUTHORS | {'', None} and helper_review.get('formal_acceptance') is False and helper_review.get('execution_authority') is False, 'independent current staged helper review required')
        require(helper_compile.get('status') == 'COMPILED_SOURCE_ONLY' and helper_compile.get('all_owned_jobs_closed') is True, 'current helper compilation incomplete')
        for a, b in ((helper_review['binary_ref'], self.fixed['trusted_host_binary']), (helper_compile['binary_ref'], self.fixed['trusted_host_binary']), (helper_compile['source_members_ref'], helper_review['source_members_ref'])):
            require(Path(a['path']) == Path(b['path']) and a['sha256'] == b['sha256'] and type(a['bytes']) is int and a['bytes'] == b['bytes'], 'current helper reviewed/build tuple differs')
        helper_members = read_json(helper_review['source_members_ref'])
        require(type(helper_members) is list and len(helper_members) == 8 and {Path(r['path']).name for r in helper_members} == {'main.go', 'hostapi.go', 'prepare.go', 'execute.go', 'prepare_runtime.go', 'seed.template.json', 'profile.template.json', 'go.authority.template.json'}, 'current staged helper Source members differ')
        self.helper_refs = [doc['trusted_host_current_source_review_ref'], doc['trusted_host_current_compile_ref'], helper_review['source_members_ref']] + helper_members
"""
replace('        for ref in self.fixed.values():\n',insert+'        for ref in self.fixed.values():\n')
replace("+ self.bootstrap_refs\n","+ self.bootstrap_refs + self.helper_refs\n")
replace("'runtime_prepare_invocation_ref', 'finalize_prepare_invocation_ref')])","'runtime_prepare_invocation_ref', 'finalize_prepare_invocation_ref', 'runtime_prepare_closure_ref', 'finalize_prepare_closure_ref')])")
needle="        validate_staged_preparation(seed, self.prepared, runtime, self.bootstrap, self.input, self.fixed['trusted_host_binary'], read_json(self.input['runtime_prepare_invocation_ref']), read_json(self.input['finalize_prepare_invocation_ref']))\n"
replacement=needle+"""        lifecycle = read_json(self.input['bootstrap_lifecycle_ref'])
        closure_refs = [self.input['runtime_prepare_closure_ref'], self.input['finalize_prepare_closure_ref']]
        require(lifecycle.get('prepare_closed_refs') == closure_refs, 'bootstrap continuation omitted the staged preparation closures')
        for label, closure_key, invocation_key in (('runtime-prepare', 'runtime_prepare_closure_ref', 'runtime_prepare_invocation_ref'), ('finalize-prepare', 'finalize_prepare_closure_ref', 'finalize_prepare_invocation_ref')):
            closure = read_json(self.input[closure_key])
            self._guard([closure['before_resume_ref']])
            validate_staged_closure(closure, label, self.input[invocation_key], read_json(closure['before_resume_ref']))
"""
replace(needle,replacement)
compile(after,str(OUT/'root_coordinator.py'),'exec')
inverse=after
for old,new in reversed(edits):
    assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse==first
before=(OLD/'root_coordinator.py').read_text(encoding='utf-8')
def methods(code):
    tree=ast.parse(code);return {n.name:ast.dump(n,include_attributes=False) for cl in tree.body if isinstance(cl,ast.ClassDef) for n in cl.body if isinstance(n,ast.FunctionDef)}
om,nm=methods(before),methods(after)
assert set(nm)-set(om)=={'_verify_prepared_database'} and {k for k in om if om[k]!=nm[k]}=={'open','prepare'}
# Extend original control 1 only; no new control groups or model claims.
tree=ast.parse(after);scope={'math':math,'json':json}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','matching_idle_proof','validate_staged_closure')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<closure-only-pure-control>','exec'),scope)
identity={'run_uuid':'SYNTHETIC','owner_pid':101,'runner_pid':102,'creation_time_100ns':10001,'job_binding_id':'JOB'}
proof={'schema':'researchos.held-job-cleanup-observation.v1','observed_monotonic':10.2,**identity,**{k:True for k in ('captured_before_resume','held_job_handle','held_primary_handle','pid_match','creation_match','primary_exit_confirmed')},'active_processes':0,'errors':[]}
iref={'path':'D:/synthetic/invocation.json','sha256':'f'*64,'bytes':200}
closure={'schema':'researchos.staged-native-owned-closure.v1','label':'runtime-prepare','invocation_ref':iref,'closed':True,'identity':identity,'observed_monotonic_start':10.,'observed_monotonic_end':10.4,'actual_fresh_cleanup':proof,'watchdog_cleanup':{'duplicate_handle_closed':True,'errors':[]},'duplicate_producer_cleanup':{'closed':True,'errors':[]}}
before_resume={'identity':copy.deepcopy(identity)}
scope['validate_staged_closure'](closure,'runtime-prepare',iref,before_resume)
obs=[]
for name,mutate in [('foreign_invocation',lambda c:c['invocation_ref'].update(sha256='e'*64)),('foreign_held_identity',lambda c:c['identity'].update(runner_pid=999)),('stale_original_observation',lambda c:c['actual_fresh_cleanup'].update(observed_monotonic=9.)),('job_still_active',lambda c:c['actual_fresh_cleanup'].update(active_processes=1)),('watchdog_open',lambda c:c['watchdog_cleanup'].update(duplicate_handle_closed=False)),('producer_open',lambda c:c['duplicate_producer_cleanup'].update(closed=False)),('timing_bool',lambda c:c.update(observed_monotonic_start=True))]:
    c=copy.deepcopy(closure);mutate(c)
    try:scope['validate_staged_closure'](c,'runtime-prepare',iref,before_resume)
    except RuntimeError:obs.append({'case':name,'rejected':True})
    else:raise AssertionError('closure false accept '+name)
controls=json.loads((OUT/'delta-controls.json').read_bytes())
controls['controls'][0]['extra_owned_closure_positive']=True;controls['controls'][0]['extra_owned_closure_negative_cases']=obs
controls['controls'][1]['AST_final_revision_prior_pipeline_unchanged']=True
(OUT/'root_coordinator.py').write_text(after,encoding='utf-8',newline='')
source_ref=pin(OUT/'root_coordinator.py')
controls_ref=put('delta-controls.json',controls)
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json'):
    obj=json.loads((OUT/name).read_bytes())
    if 'coordinator_source_ref' in obj:obj['coordinator_source_ref']=source_ref
    if 'source_ref' in obj:obj['source_ref']=source_ref
    if obj.get('mode')=='MODEL_TRIAL' and name.startswith('input.'):
        for key in ('runtime_prepare_closure_ref','finalize_prepare_closure_ref'):obj[key]={'path':'ROOT_MUST_SUPPLY_ACTUAL_ABSOLUTE_PATH','sha256':'ROOT_MUST_SUPPLY_EXACT_SHA256','bytes':0}
        obj['trusted_host_current_source_review_ref']=current_review_ref;obj['trusted_host_current_compile_ref']=compile_ref
    put(name,obj)
(OUT/'source.forward.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/'root_coordinator.py'),tofile=str(OUT/'root_coordinator.py'))),encoding='utf-8',newline='')
(OUT/'source.inverse.diff').write_text(''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile=str(OUT/'root_coordinator.py'),tofile=str(OLD/'root_coordinator.py'))),encoding='utf-8',newline='')
put('input-intake.json',{'input_refs':inputs,'input_drift':0})
reuse.update({'current_helper_source_review_ref':current_review_ref,'current_helper_source_members_ref':members_ref,'current_helper_source_members':members})
put('reuse-evidence.json',reuse)
put('build-result.json',{'source_ref':source_ref,'fixed_pins_ref':pin(OUT/'fixed-pins.json'),'controls_ref':controls_ref,'new_controls':2,'passed':2,'constructors':2,'first_constructor_snapshot':str(snapshot),'candidate_module_imported':False,'actual_WinAPI_SQL_provider_calls':0,'new_tool_failures_before_build':[739],'nonfailure_observation':[740],'formal_acceptance':False,'execution_grant_issued':False})
print(json.dumps({'source_ref':source_ref,'new_controls':2,'passed':2,'closure_negative_cases':len(obs),'input_count':len(inputs)},ensure_ascii=True))

