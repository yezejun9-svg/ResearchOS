"""One Source constructor; two isolated pure contract controls; no candidate module import."""
import ast,copy,difflib,hashlib,json,types
from pathlib import Path,PureWindowsPath
OLD=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v3_codex/f02d7bbd33534835985bfd5a87f6bd67")
OUT=Path(__file__).resolve().parent
HELPER=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_v4_codex/staged-root-69e7c3008fd968419f4d4072c3c8")
INITIAL=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/actual_cli_bootstrap_v3_component_independent_review_codex/d391a2e49cf24d559e7d58016b8eb41e/review.json")
inputs=[]
def pin(p):
    raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
    raw=Path(ref['path']).read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];inputs.append(ref);return raw
def put(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    return rawput(name,raw)
def rawput(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name)
oldh=json.loads(read({'path':str(OLD/'handoff.json'),'sha256':'ea647d52aa4a1fba8ffb33f2561a39e528afaf3cf14cd5ddf3c7a89446d80af5','bytes':4934}))
oldm=json.loads(read(oldh['manifest_ref']))
for ref in oldm['members']:read(ref)
initialref={'path':str(INITIAL),'sha256':'ce0691c2776d2ab6e95e19a019bb2f424c15b5aafc3b9ff2f20907cfda43cec4','bytes':3194}
initial=json.loads(read(initialref))
initialh=json.loads(read(initial['source_handoff_ref']))
initialsnapshot=json.loads(read(initialh['partial_bootstrap_snapshot_ref']))
for name in ('main.go','prepare_runtime.go'):read(pin(HELPER/name))
compile_ref={'path':str(OLD.parent.parent/'integration_codex/trusted-host-v4-build-staged-root-69e7c3008fd968419f4d4072c3c8/compile.closed.json'),'sha256':'d35e59bfc79bb724891754a2461a7ecfc62aaaf72ed73f9cc796d7b2f84837cb','bytes':1741}
read(compile_ref)
binary={'path':'D:/作品集/ResearchOS/research-os/.local/trusted-host-build-staged-85f7c8eccfaf4499b6c80261409ae2d2/trusted-qualification-host.exe','sha256':'117638d8215a20516693dc1b6380723e3d968c17220c918f3051f16b43560099','bytes':32129536}
read(binary)
before=read(oldh['source_ref']).decode()
after=before
edits=[]
def replace(old,new):
    global after
    assert after.count(old)==1,old[:100]
    after=after.replace(old,new);edits.append((old,new))
replace("NO_PROVIDER validates existing bootstrap evidence only. MODEL_TRIAL prepares\nthe trusted Host before one shared 300-second admission/qualification/C7 window.","NO_PROVIDER validates existing staged bootstrap evidence only. MODEL_TRIAL consumes\nthe prepared Host before one shared 300-second admission/qualification/C7 window.")
replace("AUTHORS = {'codex:/root', 'codex:/root/command_queue_impl'}","AUTHORS = {'codex:/root', 'codex:/root/command_queue_impl'}\nINITIAL_COMPONENT_REVIEW = "+repr(initialref))
start=after.index('def validate_bootstrap(');end=after.index('class RootResidentCoordinator:',start)
replace(after[start:end],"def validate_bootstrap(result, lifecycle, guard_cleanup, initial_review, initial_snapshot):\n    require(result.get('stage') == 'BOOTSTRAP_ONLY' and result.get('actor_id') == 'codex:/root', 'actual Root bootstrap required')\n    require(type(result.get('provider_requests')) is int and result['provider_requests'] == 0 and result.get('qualification') is None and result.get('formal_acceptance') is None, 'bootstrap is not runtime qualification')\n    require(lifecycle.get('schema') == 'researchos.actual-cli-staged-continuation-lifecycle.v1' and lifecycle.get('all_owned_jobs_cleanup_confirmed') is True and lifecycle.get('error') is None and type(lifecycle.get('provider_requests')) is int and lifecycle['provider_requests'] == 0, 'continuation lifecycle incomplete')\n    jobs = lifecycle.get('jobs')\n    require(type(jobs) is list and len(jobs) == 2 and {j.get('label') for j in jobs} == {'normal-host', 'cli-goal'} and all(j.get('closed') is True for j in jobs), 'exact continuation cleanup set required')\n    require(guard_cleanup.get('closed') is True and type(guard_cleanup.get('retained_handles_count')) is int and guard_cleanup['retained_handles_count'] == 0 and guard_cleanup.get('errors') == [], 'bootstrap Source guard cleanup incomplete')\n    expected = {'Task': 1, 'Run': 0, 'BudgetLedgerEntry': 0, 'resource_effects': 0}\n    require(type(result.get('db_counts')) is dict and set(result['db_counts']) == set(expected) and all(type(result['db_counts'][k]) is int and result['db_counts'][k] == v for k, v in expected.items()), 'staged bootstrap database count mismatch')\n    require(type(result.get('qualification_task_id')) is str and result['qualification_task_id'] and result.get('qualification_task_status') == 'DRAFT' and type(result.get('ordinary_goal_tasks')) is int and result['ordinary_goal_tasks'] == 0, 'qualification must be the only DRAFT Task')\n    require(initial_review.get('schema') == 'researchos.actual-cli-bootstrap-component-independent-review.v1' and initial_review.get('actor_id') == 'codex:/root/command_queue_impl' and initial_review.get('source_author') == 'codex:/root' and initial_review.get('decision') == 'PASS_COMPONENT_EVIDENCE_WITH_GOAL_BLOCKED' and initial_review.get('failed_checks') == [], 'prior actual init independent component review required')\n    require({'ACTUAL_CLI_INIT_EXIT_ZERO', 'ACTUAL_HOST_OWNED_GUI_PICKER_AND_UNIQUE_DURABLE_BINDING', 'THREE_OWNED_JOBS_AND_DUPLICATES_CONFIRMED_CLOSED_IN_ORIGINAL_RUN', 'SOURCE_GUARD_TEN_ENTRIES_ZERO_RETAINED'} <= set(initial_review.get('verified_scope', [])), 'prior init/workspace/cleanup review scope missing')\n    require(initial_review['project_id'] == initial_snapshot['project_id'] == result['project_id'] and initial_snapshot['actual_cli_init_exit'] == 0, 'continuation differs from actual initialized project')\n    require(initial_snapshot['config']['workspace_ref'] == result['workspace_ref'], 'continuation workspace binding differs')\n    for key in ('data_root', 'workspace', 'discovery_file', 'cli_config_file'):\n        require(Path(initial_snapshot[key]) == Path(result[key]), 'continuation initial layout differs')\n    for key in ('project_id', 'goal_id', 'workspace_ref', 'workspace_witness'):\n        require(type(result.get(key)) is str and result[key], 'bootstrap identity missing')\n    data = Path(result['data_root'])\n    require(data.is_absolute() and ROOT / '.local' in data.parents and Path(result['workspace']) == data / 'workspace', 'bootstrap isolation layout')\n    for key in ('discovery_file', 'cli_config_file'):\n        require(data in Path(result[key]).parents, 'bootstrap consumed path outside data root')\n\ndef validate_staged_preparation(seed, prepared, runtime, bootstrap, doc, binary, runtime_invocation, finalize_invocation):\n    require(seed.get('draft_goal_id') == '', 'staged seed must precede the ordinary CLI draft')\n    shared = ('project_id', 'qualification_goal_id', 'qualification_task_id', 'runtime_id', 'profile_artifact_id', 'profile_hash', 'model_ref', 'host_instance_id')\n    require(all(type(prepared.get(k)) is str and prepared[k] and prepared[k] == runtime.get(k) for k in shared), 'staged preparation tuple mismatch')\n    require(prepared['project_id'] == bootstrap['project_id'] and prepared['qualification_task_id'] == bootstrap['qualification_task_id'] and prepared.get('draft_goal_id') == bootstrap['goal_id'] and prepared['qualification_goal_id'] != bootstrap['goal_id'], 'staged preparation Goal/Task differs')\n    require(runtime.get('qualification_task_status') == 'DRAFT', 'runtime preparation Task was admitted')\n    for obj, fields in ((runtime, {'qualification_goals': 1, 'qualification_tasks': 1, 'ordinary_goals': 0, 'ordinary_tasks': 0, 'runs': 0}), (prepared, {'qualification_tasks': 1, 'ordinary_goal_tasks': 0, 'runs': 0})):\n        require(all(type(obj.get(k)) is int and obj[k] == v for k, v in fields.items()), 'staged preparation business counts differ')\n    for receipt, phase, status, ref_key, invocation in ((runtime, 'prepare-runtime', 'RUNTIME_READY', 'runtime_prepare_receipt_ref', runtime_invocation), (prepared, 'finalize-prepare', 'PREPARED', 'prepare_receipt_ref', finalize_invocation)):\n        require(receipt.get('schema') == 'researchos.trusted-qualification-host.v1' and receipt.get('phase') == phase and receipt.get('status') == status and receipt.get('source_seed_sha256') == doc['host_seed_ref']['sha256'] and type(receipt.get('provider_requests')) is int and receipt['provider_requests'] == 0, 'actual staged receipt differs')\n        argv = [binary['path'], '-phase', phase, '-seed', doc['host_seed_ref']['path'], '-receipt', doc[ref_key]['path']]\n        if phase == 'finalize-prepare':\n            argv.extend(['-draft-goal-id', bootstrap['goal_id']])\n        require(invocation.get('argv') == argv and Path(invocation.get('cwd', '')) == ROOT, 'staged owned invocation differs')\n        result = invocation.get('result')\n        require(native_closed(result) and result.get('error') is None and type(result.get('actual_exit')) is int and result['actual_exit'] == 0 and result.get('timed_out') is False and invocation.get('error') is None, 'staged owned invocation did not close successfully')\n\n")
replace("doc.get('schema') == 'researchos.root-sdk-coordinator-input.v1'","doc.get('schema') == 'researchos.root-sdk-coordinator-input.v2'")
oldbootstrap="""        self.bootstrap = read_json(doc['bootstrap_result_ref'])
        validate_bootstrap(self.bootstrap, read_json(doc['bootstrap_lifecycle_ref']), read_json(doc['bootstrap_guard_cleanup_ref']))
"""
newbootstrap="""        self.bootstrap = read_json(doc['bootstrap_result_ref'])
        require(doc['initial_cli_init_component_review_ref'] == INITIAL_COMPONENT_REVIEW, 'actual initial component review pin differs')
        initial_review = read_json(doc['initial_cli_init_component_review_ref'])
        initial_handoff = read_json(initial_review['source_handoff_ref'])
        initial_snapshot = read_json(initial_handoff['partial_bootstrap_snapshot_ref'])
        self.bootstrap_refs = [doc[k] for k in ('bootstrap_result_ref', 'bootstrap_lifecycle_ref', 'bootstrap_guard_cleanup_ref', 'initial_cli_init_component_review_ref')] + [initial_review['source_handoff_ref'], initial_handoff['partial_bootstrap_snapshot_ref']]
        validate_bootstrap(self.bootstrap, read_json(doc['bootstrap_lifecycle_ref']), read_json(doc['bootstrap_guard_cleanup_ref']), initial_review, initial_snapshot)
"""
replace(oldbootstrap,newbootstrap)
replace("refs = list(self.fixed.values()) + [self.input_ref, self.review_ref, doc['coordinator_source_ref'], doc['fixed_pins_ref'], doc['bootstrap_result_ref'], doc['bootstrap_lifecycle_ref'], doc['bootstrap_guard_cleanup_ref']]","refs = list(self.fixed.values()) + [self.input_ref, self.review_ref, doc['coordinator_source_ref'], doc['fixed_pins_ref']] + self.bootstrap_refs")
replace("validate_bootstrap(self.bootstrap, json.loads(self.source_guard.get_buffer(doc['bootstrap_lifecycle_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['bootstrap_guard_cleanup_ref']['path'])))","validate_bootstrap(self.bootstrap, json.loads(self.source_guard.get_buffer(doc['bootstrap_lifecycle_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['bootstrap_guard_cleanup_ref']['path'])), json.loads(self.source_guard.get_buffer(doc['initial_cli_init_component_review_ref']['path'])), json.loads(self.source_guard.get_buffer(initial_handoff['partial_bootstrap_snapshot_ref']['path'])))")
replace("self._guard([self.input['root_execution_authority_ref'], self.input['host_seed_ref'], self.input['intake_review_ref'], self.input['public_route_manifest_ref']])","self._guard([self.input[k] for k in ('root_execution_authority_ref', 'host_seed_ref', 'intake_review_ref', 'public_route_manifest_ref', 'runtime_prepare_receipt_ref', 'prepare_receipt_ref', 'runtime_prepare_invocation_ref', 'finalize_prepare_invocation_ref')])")
replace("pairs = {'project_id': 'project_id', 'draft_goal_id': 'goal_id',","pairs = {'project_id': 'project_id',")
oldprepare="""        self.state = 'PREPARE_ATTEMPTED'
        receipt = self.output / 'host.prepare.json'
        self._host_phase('prepare', receipt, time.monotonic()+90)
        self.prepared = read_json(pin(receipt))
        require(self.prepared.get('status') == 'PREPARED' and self.prepared.get('provider_requests') == 0 and self.prepared['project_id'] == self.bootstrap['project_id'], 'Host preparation result mismatch')
"""
newprepare="""        self.state = 'PREPARATION_CONSUMPTION_ATTEMPTED'
        self.prepared = read_json(self.input['prepare_receipt_ref'])
        runtime = read_json(self.input['runtime_prepare_receipt_ref'])
        validate_staged_preparation(seed, self.prepared, runtime, self.bootstrap, self.input, self.fixed['trusted_host_binary'], read_json(self.input['runtime_prepare_invocation_ref']), read_json(self.input['finalize_prepare_invocation_ref']))
"""
replace(oldprepare,newprepare)
replace("self._guard([self.profile_ref, pin(receipt)])\n        self.state = 'PREPARED'","self._guard([self.profile_ref])\n        self._verify_prepared_database()\n        self.state = 'PREPARED'")
replace("    def _wait_receipt(self, path):\n","    def _verify_prepared_database(self):\n        project = self.bootstrap['project_id']\n        with self._read_db() as db:\n            counts = {}\n            for kind in ('Task', 'Run', 'BudgetLedgerEntry'):\n                counts[kind] = db.execute('SELECT count(*) FROM domain_objects WHERE project=? AND kind=?', (project, kind)).fetchone()[0]\n            counts['resource_effects'] = db.execute('SELECT count(*) FROM resource_effects WHERE project=?', (project,)).fetchone()[0]\n            expected = {'Task': 1, 'Run': 0, 'BudgetLedgerEntry': 0, 'resource_effects': 0}\n            require(all(type(counts[k]) is int and counts[k] == v for k, v in expected.items()), 'current staged database counts changed')\n            task = self.engine.object_by_id(db, 'Task', self.prepared['qualification_task_id'], project)\n            require(task['id'] == self.prepared['qualification_task_id'] and task['project_id'] == project and task['goal_id'] == self.prepared['qualification_goal_id'] and task['status'] == 'DRAFT' and task['task_type'] == 'runtime_qualification' and task.get('active_run_id') is None, 'current qualification Task is not the unique unadmitted DRAFT')\n            goal = self.engine.object_by_id(db, 'Goal', self.bootstrap['goal_id'], project)\n            require(goal['id'] == self.bootstrap['goal_id'] and goal['project_id'] == project and goal['status'] == 'DRAFT' and goal['id'] != task['goal_id'], 'ordinary Goal is not the actual independent DRAFT')\n            ordinary = db.execute(\"SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=?\", (project, goal['id'])).fetchone()[0]\n            require(type(ordinary) is int and ordinary == 0, 'ordinary Goal already has a Task')\n            runtime = self.engine.object_by_id(db, 'RuntimeRegistration', self.prepared['runtime_id'], project)\n            actual_ref = self.engine.exact_artifact_ref(db, project, self.prepared['profile_artifact_id'])\n            bindings = db.execute('SELECT profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=? AND runtime=?', (project, self.prepared['runtime_id'])).fetchall()\n        require(runtime['id'] == self.prepared['runtime_id'] and runtime['project_id'] == project and actual_ref == self.profile_entity_ref and actual_ref['content_hash'] == self.prepared['profile_hash'], 'prepared runtime or sealed profile changed')\n        technical = self.engine.go_hash([runtime[k] for k in ('adapter', 'adapter_revision', 'capabilities', 'platform', 'measurement_mode', 'credential_ref')])\n        require(len(bindings) == 1 and json.loads(bindings[0][0]) == actual_ref and bindings[0][1] == self.engine.go_hash(actual_ref) and bindings[0][2] == technical, 'prepared formal runtime binding changed')\n\n"+"    def _wait_receipt(self, path):\n")
compile(after,str(OUT/'root_coordinator.py'),'exec')
oldast=ast.parse(before);newast=ast.parse(after)
def methods(tree):
    return {n.name:ast.dump(n,include_attributes=False) for cl in tree.body if isinstance(cl,ast.ClassDef) for n in cl.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
om,nm=methods(oldast),methods(newast)
assert set(nm)-set(om)=={'_verify_prepared_database'}
assert {k for k in om if om[k]!=nm[k]}=={'open','prepare'}
assert 'self._host_phase(' not in ast.get_source_segment(after,next(n for cl in newast.body if isinstance(cl,ast.ClassDef) for n in cl.body if getattr(n,'name',None)=='prepare'))
inverse=after
for old,new in reversed(edits):
    assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse.encode()==before.encode()
source_ref=rawput('root_coordinator.py',after.encode())
fixed=json.loads(read(oldh['fixed_pins_ref']));originalfixed=copy.deepcopy(fixed);fixed['trusted_host_binary']=binary
assert {k for k in fixed if fixed[k]!=originalfixed[k]}=={'trusted_host_binary'}
fixed_ref=put('fixed-pins.json',fixed)
rawput('source.forward.diff',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/'root_coordinator.py'),tofile=str(OUT/'root_coordinator.py'))).encode())
rawput('source.inverse.diff',''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile=str(OUT/'root_coordinator.py'),tofile=str(OLD/'root_coordinator.py'))).encode())
placeholder={'path':'ROOT_MUST_SUPPLY_ACTUAL_ABSOLUTE_PATH','sha256':'ROOT_MUST_SUPPLY_EXACT_SHA256','bytes':0}
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json'):
    obj=json.loads((OLD/name).read_bytes())
    if 'coordinator_source_ref' in obj:obj['coordinator_source_ref']=source_ref
    if 'source_ref' in obj:obj['source_ref']=source_ref
    if 'fixed_pins_ref' in obj:obj['fixed_pins_ref']=fixed_ref
    if name.startswith('input.'):
        obj['schema']='researchos.root-sdk-coordinator-input.v2'
        obj['initial_cli_init_component_review_ref']=initialref
        if obj['mode']=='MODEL_TRIAL':
            for k in ('runtime_prepare_receipt_ref','prepare_receipt_ref','runtime_prepare_invocation_ref','finalize_prepare_invocation_ref'):obj[k]=placeholder
    put(name,obj)
# Pure control 1: extract only free validation functions; all fixtures synthetic.
scope={'Path':PureWindowsPath,'ROOT':PureWindowsPath('D:/作品集/ResearchOS/research-os')}
nodes=[n for n in newast.body if isinstance(n,ast.FunctionDef) and n.name in ('require','native_closed','validate_bootstrap','validate_staged_preparation')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<isolated-validation>','exec'),scope)
root=scope['ROOT'];data=root/'.local'/'synthetic';bootstrap={'stage':'BOOTSTRAP_ONLY','actor_id':'codex:/root','provider_requests':0,'qualification':None,'formal_acceptance':None,'project_id':'P','goal_id':'G','workspace_ref':'W','workspace_witness':'witness','data_root':str(data),'workspace':str(data/'workspace'),'discovery_file':str(data/'discovery.json'),'cli_config_file':str(data/'config.json'),'db_counts':{'Task':1,'Run':0,'BudgetLedgerEntry':0,'resource_effects':0},'qualification_task_id':'T','qualification_task_status':'DRAFT','ordinary_goal_tasks':0}
review=copy.deepcopy(initial);review['project_id']='P'
snapshot={'project_id':'P','actual_cli_init_exit':0,'config':{'workspace_ref':'W'},**{k:bootstrap[k] for k in ('data_root','workspace','discovery_file','cli_config_file')}}
lifecycle={'schema':'researchos.actual-cli-staged-continuation-lifecycle.v1','all_owned_jobs_cleanup_confirmed':True,'error':None,'provider_requests':0,'jobs':[{'label':n,'closed':True} for n in ('normal-host','cli-goal')]}
guard={'closed':True,'retained_handles_count':0,'errors':[]}
scope['validate_bootstrap'](bootstrap,lifecycle,guard,review,snapshot)
common={'schema':'researchos.trusted-qualification-host.v1','source_seed_sha256':'SEED','project_id':'P','qualification_goal_id':'QG','qualification_task_id':'T','runtime_id':'R','profile_artifact_id':'A','profile_hash':'CONTENT','model_ref':'M','host_instance_id':'H','provider_requests':0,'qualification_tasks':1,'runs':0}
runtime={**common,'phase':'prepare-runtime','status':'RUNTIME_READY','qualification_task_status':'DRAFT','qualification_goals':1,'ordinary_goals':0,'ordinary_tasks':0}
prepared={**common,'phase':'finalize-prepare','status':'PREPARED','draft_goal_id':'G','ordinary_goal_tasks':0}
doc={'host_seed_ref':{'path':'D:/seed.json','sha256':'SEED'},'runtime_prepare_receipt_ref':{'path':'D:/runtime.json'},'prepare_receipt_ref':{'path':'D:/prepared.json'}}
closed={'error':None,'actual_exit':0,'timed_out':False,'job_cleanup':{'errors':[],'active_processes_last_observed':0,**{k:True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')}}}
inv=[]
for phase,key in (('prepare-runtime','runtime_prepare_receipt_ref'),('finalize-prepare','prepare_receipt_ref')):
    argv=[binary['path'],'-phase',phase,'-seed',doc['host_seed_ref']['path'],'-receipt',doc[key]['path']]
    if phase=='finalize-prepare':argv+=['-draft-goal-id','G']
    inv.append({'argv':argv,'cwd':str(root),'result':copy.deepcopy(closed),'error':None})
seed={'draft_goal_id':''}
scope['validate_staged_preparation'](seed,prepared,runtime,bootstrap,doc,binary,*inv)
observations=[]
def rejected(name,call):
    try:call()
    except (RuntimeError,KeyError,TypeError):observations.append({'case':name,'rejected':True})
    else:raise AssertionError('false accept: '+name)
for name,mutate in [('old_global_task_zero',lambda b,l,r,s:b['db_counts'].update(Task=0)),('bool_task_count',lambda b,l,r,s:b['db_counts'].update(Task=True)),('old_three_jobs',lambda b,l,r,s:l['jobs'].append({'label':'cli-init','closed':True})),('foreign_prior_project',lambda b,l,r,s:r.update(project_id='FOREIGN')),('foreign_prior_workspace',lambda b,l,r,s:s['config'].update(workspace_ref='FOREIGN'))]:
    b,l,r,s=map(copy.deepcopy,(bootstrap,lifecycle,review,snapshot));mutate(b,l,r,s)
    rejected(name,lambda:scope['validate_bootstrap'](b,l,guard,r,s))
for name,mutate in [('seed_contains_goal',lambda s,p,r,i:s.update(draft_goal_id='G')),('foreign_prepared_goal',lambda s,p,r,i:p.update(draft_goal_id='X')),('runtime_tuple_drift',lambda s,p,r,i:r.update(runtime_id='X')),('source_seed_drift',lambda s,p,r,i:r.update(source_seed_sha256='X')),('native_handles_open',lambda s,p,r,i:i[0]['result']['job_cleanup'].update(handles_closed=False)),('wrong_phase_argv',lambda s,p,r,i:i[1]['argv'].__setitem__(2,'prepare'))]:
    s,p,r,i=map(copy.deepcopy,(seed,prepared,runtime,inv));mutate(s,p,r,i)
    rejected(name,lambda:scope['validate_staged_preparation'](s,p,r,bootstrap,doc,binary,*i))
control1={'id':'V4-01_STAGED_CHAIN','positive_bootstrap_and_staged_receipts':True,'negative_cases':observations,'passed':True}
# Pure control 2: the new method receives only explicit in-memory fake DB/engine.
method=next(n for cl in newast.body if isinstance(cl,ast.ClassDef) for n in cl.body if getattr(n,'name',None)=='_verify_prepared_database')
method=copy.deepcopy(method);method.decorator_list=[]
dbscope={'json':json,'require':scope['require']}
exec(compile(ast.Module(body=[method],type_ignores=[]),'<isolated-db-contract>','exec'),dbscope)
artifact={'id':'A','content_hash':'CONTENT'}
registration={'id':'R','project_id':'P',**{k:k for k in ('adapter','adapter_revision','capabilities','platform','measurement_mode','credential_ref')}}
task={'id':'T','project_id':'P','goal_id':'QG','status':'DRAFT','task_type':'runtime_qualification','active_run_id':None}
goal={'id':'G','project_id':'P','status':'DRAFT'}
def h(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
technical=h([registration[k] for k in ('adapter','adapter_revision','capabilities','platform','measurement_mode','credential_ref')])
class Rows:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return self.rows[0]
    def fetchall(self):return self.rows
class DB:
    def __init__(self):self.counts=dict(bootstrap['db_counts']);self.ordinary=0;self.binding=[(json.dumps(artifact),h(artifact),technical)]
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def execute(self,sql,args):
        if 'runtime_bindings' in sql:return Rows(self.binding)
        if 'resource_effects' in sql:return Rows([(self.counts['resource_effects'],)])
        if 'json_extract' in sql:return Rows([(self.ordinary,)])
        assert args[0]=='P' and len(args)==2;return Rows([(self.counts[args[1]],)])
def fixture():
    db=DB();objects={'Task':copy.deepcopy(task),'Goal':copy.deepcopy(goal),'RuntimeRegistration':copy.deepcopy(registration)}
    engine=types.SimpleNamespace(object_by_id=lambda db,kind,objid,project:objects[kind],exact_artifact_ref=lambda *a:copy.deepcopy(artifact),go_hash=h)
    obj=types.SimpleNamespace(bootstrap=copy.deepcopy(bootstrap),prepared=copy.deepcopy(prepared),profile_entity_ref=copy.deepcopy(artifact),engine=engine,_read_db=lambda:db)
    return obj,db,objects
obj,db,objects=fixture();dbscope['_verify_prepared_database'](obj)
observations=[]
for name,mutate in [('global_extra_task',lambda d,o:d.counts.update(Task=2)),('ordinary_task_exists',lambda d,o:setattr(d,'ordinary',1)),('qualification_admitted',lambda d,o:o['Task'].update(status='READY')),('wrong_qualification_goal',lambda d,o:o['Task'].update(goal_id='G')),('run_exists',lambda d,o:d.counts.update(Run=1)),('binding_content_digest_instead_of_ref',lambda d,o:setattr(d,'binding',[(json.dumps(artifact),'CONTENT',technical)])),('registration_technical_drift',lambda d,o:o['RuntimeRegistration'].update(adapter_revision='DRIFT'))]:
    obj,db,objects=fixture();mutate(db,objects);rejected(name,lambda:dbscope['_verify_prepared_database'](obj))
control2={'id':'V4-02_CURRENT_DB_CONTRACT','positive_unique_DRAFT_task_and_formal_binding':True,'negative_cases':observations,'AST_unchanged_prior_R01_R02_retained_parent_and_300s_pipeline':True,'full_bytes_inverse_verified':True,'passed':True}
controls_ref=put('delta-controls.json',{'schema':'researchos.pure-delta-controls.v1','controls':[control1,control2],'new_controls':2,'passed':2,'candidate_module_imported':False,'actual_WinAPI_SQL_provider_calls':0})
put('input-intake.json',{'input_refs':inputs,'input_drift':0})
put('reuse-evidence.json',{'prior_handoff_ref':pin(OLD/'handoff.json'),'prior_controls_reused_not_rerun':[40,1,2],'fixed_roles_total':len(fixed),'fixed_roles_changed':['trusted_host_binary'],'unchanged_roles_reused_not_rehashed':len(fixed)-1,'inherited_trusted_host_source_and_review_roles_are_historical_not_new_v4_review':True,'new_helper_source_refs':[pin(HELPER/n) for n in ('main.go','prepare_runtime.go')],'helper_compile_ref':compile_ref,'initial_component_review_ref':initialref})
put('build-result.json',{'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'controls_ref':controls_ref,'new_controls':2,'passed':2,'new_tool_failures_before_build':[739],'nonfailure_observation':[740],'actual_WinAPI_SQL_provider_calls':0,'formal_acceptance':False,'execution_grant_issued':False})
print(json.dumps({'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'new_controls':2,'passed':2,'input_count':len(inputs)},ensure_ascii=False))

