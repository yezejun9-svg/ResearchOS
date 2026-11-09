"""Only Source transformations and two isolated pure delta controls."""
import ast,difflib,hashlib,json,types
from pathlib import Path,PureWindowsPath
OLD=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_v2_codex/6d87bf2c319543ca95b92efc8d2a3b58')
REVIEW=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_v2_independent_review_codex/813337f875114e3b97ceccb0acb897fc')
OUT=Path(__file__).resolve().parent
inputs=[]
def pin(path):
    raw=Path(path).read_bytes();return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
    raw=Path(ref['path']).read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
    inputs.append(ref);return raw
def put(name,doc):
    with (OUT/name).open('xb') as f:f.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
def rawput(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name)
rh={'path':str(REVIEW/'handoff.json'),'sha256':'631741c3d9d3c91923550d0ede989a89cca359f1d59673c12cee07c5840f8a5b','bytes':3418}
review_handoff=json.loads(read(rh));review=json.loads(read(review_handoff['review_ref']));read(review_handoff['manifest_ref']);read(review_handoff['counterexamples_ref'])
assert {f['id'] for f in review['findings']}=={'R01','R02'}
old_h_ref={'path':str(OLD/'handoff.json'),'sha256':'70a9d95611f15207a7c43aebe6e6d1bbfdf735e9824c465794d296c4b22ff15a','bytes':4467}
old_h=json.loads(read(old_h_ref));old_m=json.loads(read(old_h['manifest_ref']))
for ref in old_m['members']:read(ref)
before=read(old_h['source_ref']).decode()
edits=[]
def replace(old,new):
    global after
    assert after.count(old)==1
    after=after.replace(old,new);edits.append((old,new))
after=before
once_insert="""        # Prepare only the directory; v9 exclusively consumes the absent file.
        once_dir = Path(self.bootstrap['data_root']) / 'trial-once'
        once_dir.mkdir(exist_ok=True)
        require(once_dir.is_dir() and not once_dir.is_symlink() and not once_dir.is_junction() and once_dir.resolve() == once_dir, 'canonical isolated once directory required')
        once_path = once_dir / (self.run_uuid + '.json')
        require(once_path.parent == once_dir and not once_path.exists() and not once_path.is_symlink(), 'Root once file already consumed or foreign')
"""
replace("        self.state = 'PREPARE_ATTEMPTED'\n",once_insert+"        self.state = 'PREPARE_ATTEMPTED'\n")
replace("'once_path': str(self.output / 'c7-execute.once.json')","'once_path': str(Path(self.bootstrap['data_root']) / 'trial-once' / (self.run_uuid + '.json'))")
replace("'qualification_profile_hash': self.admitted['profile_hash']","'qualification_profile_hash': self.engine.go_hash(self.profile_entity_ref)")
method="""    def _verify_admitted_profile_binding(self):
        # Host profile_hash remains the Artifact content digest; C7 expects Hash(ArtifactRef).
        project = self.bootstrap['project_id']
        runtime_id = self.admitted['runtime_id']
        profile_digest = self.engine.go_hash(self.profile_entity_ref)
        require(self.profile_entity_ref['content_hash'] == self.prepared['profile_hash'] == self.admitted['profile_hash'], 'actual profile content digest changed')
        with self._read_db() as db:
            actual_ref = self.engine.exact_artifact_ref(db, project, self.prepared['profile_artifact_id'])
            runtime = self.engine.object_by_id(db, 'RuntimeRegistration', runtime_id, project)
            bindings = db.execute('SELECT profile_ref,profile_hash,technical_hash FROM runtime_bindings WHERE project=? AND runtime=?', (project, runtime_id)).fetchall()
            markers = db.execute('SELECT task,run,runtime,epoch,profile_hash FROM runtime_qualification_runs WHERE project=? AND run=?', (project, self.admitted['qualification_run_id'])).fetchall()
        require(actual_ref == self.profile_entity_ref and runtime['id'] == runtime_id and runtime['project_id'] == project, 'current ArtifactRef or runtime registration differs')
        technical_hash = self.engine.go_hash([runtime[k] for k in ('adapter', 'adapter_revision', 'capabilities', 'platform', 'measurement_mode', 'credential_ref')])
        require(len(bindings) == 1 and json.loads(bindings[0][0]) == actual_ref and bindings[0][1] == profile_digest and bindings[0][2] == technical_hash, 'actual runtime profile binding differs')
        expected_marker = (self.admitted['qualification_task_id'], self.admitted['qualification_run_id'], runtime_id, self.admitted['qualification_epoch'], profile_digest)
        require(type(self.admitted['qualification_epoch']) is int and len(markers) == 1 and markers[0] == expected_marker, 'actual qualification profile marker differs')

"""
replace('    def issue_go(self):\n',method+'    def issue_go(self):\n')
replace("        self.state = 'GO_ATTEMPTED'\n","        self._verify_admitted_profile_binding()\n        self.state = 'GO_ATTEMPTED'\n")
restored=after
for old,new in reversed(edits):
    assert restored.count(new)==1;restored=restored.replace(new,old)
assert restored==before
source_ref=rawput('root_coordinator.py',after.encode())
for name,a,b in [('source.forward.diff',before,after),('source.inverse.diff',after,before)]:
    rawput(name,''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='coordinator-before',tofile='coordinator-after')).encode())
tree=ast.parse(after);compile(tree,str(OUT/'root_coordinator.py'),'exec')
old_tree=ast.parse(before)
def methods(t):
    c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='RootResidentCoordinator')
    return {n.name:n for n in c.body if isinstance(n,ast.FunctionDef)}
old_methods=methods(old_tree);new_methods=methods(tree)
allowed={'prepare','issue_go','execute_c7','_verify_admitted_profile_binding'}
assert all(ast.dump(node,include_attributes=False)==ast.dump(new_methods[name],include_attributes=False) for name,node in old_methods.items() if name not in allowed)
old_other=[ast.dump(n,include_attributes=False) for n in old_tree.body if not isinstance(n,ast.ClassDef)]
new_other=[ast.dump(n,include_attributes=False) for n in tree.body if not isinstance(n,ast.ClassDef)]
assert old_other==new_other
fixed=json.loads(read(old_h['fixed_pins_ref']))
engine_tree=ast.parse(read(fixed['runner']))
hash_fn=next(n for n in engine_tree.body if isinstance(n,ast.FunctionDef) and n.name=='go_hash')
hash_ns={'json':json,'hashlib':hashlib};exec(compile(ast.Module(body=[hash_fn],type_ignores=[]),'<pinned-v9-pure-hash>','exec'),hash_ns)
go_hash=hash_ns['go_hash']
doc_node=next(n for n in ast.walk(new_methods['execute_c7']) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='doc' for t in n.targets)).value
doc_values={k.value:v for k,v in zip(doc_node.keys,doc_node.values)}
data=PureWindowsPath('D:/review-only-isolated/data');run_uuid='0123456789abcdef0123456789abcdef'
fake=types.SimpleNamespace(bootstrap={'data_root':str(data)},run_uuid=run_uuid)
once_value=eval(compile(ast.Expression(doc_values['once_path']),'<once-path-expression>','eval'),{'Path':PureWindowsPath,'self':fake})
once=PureWindowsPath(once_value)
prepare_source=ast.get_source_segment(after,new_methods['prepare'])
once_control=(once.is_absolute() and once.parent==data/'trial-once' and once.name==run_uuid+'.json' and prepare_source.index('once_dir.mkdir(exist_ok=True)')<prepare_source.index("self.state = 'PREPARE_ATTEMPTED'") and 'not once_path.exists()' in prepare_source and 'not once_dir.is_junction()' in prepare_source and 'once_path.open' not in prepare_source)
assert once_control

# Exact new method with synthetic rows; FakeDB executes no SQL.
profile={'entity_type':'Artifact','id':'synthetic-artifact','revision':7,'content_hash':'sha256:'+'a'*64}
runtime={'id':'synthetic-runtime','project_id':'synthetic-project','adapter':'mu-sdk','adapter_revision':'windows-appcontainer-v1','capabilities':['start','context_rebuild'],'platform':'windows-amd64','measurement_mode':'LIVE','credential_ref':'synthetic-credential-reference'}
digest=go_hash(profile);technical=go_hash([runtime[k] for k in ('adapter','adapter_revision','capabilities','platform','measurement_mode','credential_ref')])
valid_binding=(json.dumps(profile),digest,technical)
valid_marker=('synthetic-task','synthetic-run','synthetic-runtime',1,digest)
method_ns={'json':json,'require':lambda ok,message:None if ok else (_ for _ in ()).throw(RuntimeError(message))}
exec(compile(ast.Module(body=[new_methods['_verify_admitted_profile_binding']],type_ignores=[]),'<profile-binding-pure-control>','exec'),method_ns)
cases=[]
for case in ('valid','content_hash_as_binding_hash','content_hash_as_marker_hash','registration_technical_drift','ArtifactRef_revision_drift'):
    binding=list(valid_binding);marker=list(valid_marker);actual_ref=dict(profile);actual_runtime=dict(runtime)
    if case=='content_hash_as_binding_hash':binding[1]=profile['content_hash']
    if case=='content_hash_as_marker_hash':marker[4]=profile['content_hash']
    if case=='registration_technical_drift':actual_runtime['adapter_revision']='foreign'
    if case=='ArtifactRef_revision_drift':actual_ref['revision']=8
    class FakeDB:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def execute(self,query,args):
            if query.startswith('SELECT profile_ref,profile_hash,technical_hash'):
                assert args==('synthetic-project','synthetic-runtime');return types.SimpleNamespace(fetchall=lambda:[tuple(binding)])
            assert query.startswith('SELECT task,run,runtime,epoch,profile_hash') and args==('synthetic-project','synthetic-run')
            return types.SimpleNamespace(fetchall=lambda:[tuple(marker)])
    engine=types.SimpleNamespace(go_hash=go_hash,exact_artifact_ref=lambda *_:actual_ref,object_by_id=lambda *_:actual_runtime)
    fake=types.SimpleNamespace(bootstrap={'project_id':'synthetic-project'},prepared={'profile_hash':profile['content_hash'],'profile_artifact_id':'synthetic-artifact'},admitted={'runtime_id':'synthetic-runtime','profile_hash':profile['content_hash'],'qualification_task_id':'synthetic-task','qualification_run_id':'synthetic-run','qualification_epoch':1},profile_entity_ref=profile,engine=engine,_read_db=lambda:FakeDB())
    accepted=True
    try:method_ns['_verify_admitted_profile_binding'](fake)
    except RuntimeError:accepted=False
    assert accepted==(case=='valid')
    cases.append({'case':case,'accepted':accepted,'expected':case=='valid'})
fake=types.SimpleNamespace(engine=types.SimpleNamespace(go_hash=go_hash),profile_entity_ref=profile)
qualification_hash=eval(compile(ast.Expression(doc_values['qualification_profile_hash']),'<C7-profile-hash-expression>','eval'),{'self':fake})
assert qualification_hash==digest and qualification_hash!=profile['content_hash']
issue=ast.get_source_segment(after,new_methods['issue_go'])
assert issue.index('self._verify_admitted_profile_binding()')<issue.index("self.state = 'GO_ATTEMPTED'")<issue.index('self.pipe_write.write(frame)')
old_issue=ast.get_source_segment(before,old_methods['issue_go'])
assert issue.replace('        self._verify_admitted_profile_binding()\n','')==old_issue
control_ref=put('delta-controls.json',{'schema':'researchos.root-sdk-coordinator-v3-delta-controls.v1','controls':[{'finding':'R01','passed':once_control,'once_path_expression_result':once_value,'provider_free_directory_setup_before_prepare':True,'once_file_created_by_coordinator':False},{'finding':'R02','passed':True,'synthetic_content_hash':profile['content_hash'],'synthetic_ArtifactRef_hash':digest,'synthetic_binding_matrix':cases,'actual_pinned_v9_go_hash_AST_used':True,'pre_GO_binding_check':True,'Host_GO_content_hash_semantics_unchanged':True}],'passed':2,'total':2,'only_expected_AST_methods_changed':True,'full_bytes_inverse_roundtrip':True,'prior_40_plus_1_controls_reused_not_rerun':True,'candidate_imports':0,'actual_native_SQL_provider_calls':0,'synthetic_rows_are_not_qualification_evidence':True,'source_ref':source_ref})
fixed_ref=rawput('fixed-pins.json',read(old_h['fixed_pins_ref']))
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json'):
    original=next(r for r in old_m['members'] if Path(r['path']).name==name)
    d=json.loads(read(original));d['source_ref' if name=='independent-source-review.template.json' else 'coordinator_source_ref']=source_ref
    if 'fixed_pins_ref' in d:d['fixed_pins_ref']=fixed_ref
    put(name,d)
put('reuse-evidence.json',{'input_refs':inputs,'prior_Source_manifest_members':len(old_m['members']),'old_source_ref':old_h['source_ref'],'independent_review_handoff_ref':rh,'fixed_24_role_pins_reused_not_rehashed':True,'prior_controls_reused_not_rerun':[40,1],'historical_review_failures_not_recounted':[724,726],'new_tool_failures':0})
rawput('REPORT.md',b'# Root coordinator v3 narrow Source repair\n\nStatus: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_DELTA_REVIEW.\n\nR01: provider-free prepare creates or validates the real isolated data_root/trial-once directory, refuses symlink/junction/canonical-path drift, and checks the UUID-specific file is absent. C7 once_path is data_root/trial-once/<run_uuid>.json. The coordinator does not create, delete, overwrite, or reset that file; pinned v9 exclusively consumes it.\n\nR02: C7 qualification_profile_hash is engine.go_hash(actual profile_entity_ref). Before GO the actual read-only registration, current ArtifactRef, runtime binding, and admitted qualification marker are checked for matching project/runtime/task/run/epoch/ref digest and technical registration hash. Host profile_hash and all GO content-hash fields retain their existing Artifact content-digest meaning. This Source contains future read-only DB queries but none were executed for this repair.\n\nTwo isolated delta controls passed, including synthetic digest mismatch/registration/ref-drift cases. Original 24 role pins and 40+1 prior controls are reused, not rerun. Forward/inverse full-byte restoration is verified; other Source behavior is unchanged. No actual native/SQL/provider calls or canonical/Main edits were made. This does not create bootstrap or qualification facts. Successful bootstrap is still unavailable, and the separate normal-Host draft/runtime issue remains outside this repair. No API or source Head changes, execution grant, READY, or formal acceptance are issued.\n')
put('build-result.json',{'source_ref':source_ref,'fixed_pins_ref':fixed_ref,'control_ref':control_ref,'closed_in_Source_pending_independent_review':['R01','R02'],'controls':2,'passed':2,'new_failures':0,'candidate_native_SQL_provider_calls':0,'Main_canonical_writes':0})
print(json.dumps({'source_ref':source_ref,'controls_ref':control_ref,'controls':2,'passed':2,'inverse_roundtrip':True,'new_failures':0}))
