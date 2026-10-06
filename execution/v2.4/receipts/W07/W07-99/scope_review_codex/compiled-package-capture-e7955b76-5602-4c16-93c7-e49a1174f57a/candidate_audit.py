import ast,hashlib,importlib.util,io,json,os,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WORK=ROOT/'.local/worktrees/codex-w0799'
PREFIX=Path('execution/v2.4/receipts/W07/W07-99/source_executor_codex')
REC=WORK/PREFIX/'complete-package-freeze-47ff332401e24eb8bb43964dcf79a113'
HEAD='80dadb8e707d3e83bda8f48874c7f5ff899e01c3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def git(*args):return subprocess.check_output(['git','-C',str(WORK),*args])
def walk_refs(o):
    if isinstance(o,dict):
        if 'path' in o and 'sha256' in o:yield o
        for v in o.values():yield from walk_refs(v)
    elif isinstance(o,list):
        for v in o:yield from walk_refs(v)
result={'candidate':HEAD,'mode':'INDEPENDENT_SOURCE_AND_ACTUAL_MAIN_INVENTORY_REVIEW','formal_acceptance':False,'new_LIVE_capture':False}
assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain').strip()
changed=git('diff-tree','--no-commit-id','--name-only','-r',HEAD).decode().splitlines()
result['blobs']=[]
for name in changed:
    raw=git('show',HEAD+':'+name)
    assert raw==(WORK/name).read_bytes()
    result['blobs'].append({'path':name,'sha256':hashlib.sha256(raw).hexdigest()})
result['source_paths']=[p for p in changed if not p.startswith(PREFIX.as_posix()+'/')]
assert result['source_paths']==['ops/ci/sources.py','tests/sources/check/parent_gate_test.py']
assert sha(REC/'handoff.json')=='c5bb4c35815fd460eeea85119778b098bc76f4e4421ba2be6f1fb89e080640fc'
assert sha(REC/'qualification.json')=='20465e41fa2caf0ff03af329ea9ef09158beca3361ce54f7fef83b2f8279ef2b'
refs=[]
for name in changed:
    if not name.endswith('.json'):continue
    for entry in walk_refs(load(WORK/name)):
        p=Path(entry['path']);p=p if p.is_absolute() else WORK/p
        assert sha(p)==entry['sha256'].removeprefix('sha256:')
        refs.append(ref(p))
result['verified_json_refs']=refs
qualification=load(REC/'qualification.json');proof_path=Path(qualification['proof_ref']['path']);capture=proof_path.parent
before=load(capture/'source-before.json');after=load(capture/'source-after.json')
assert before==after and all(sha(WORK/p)==h.removeprefix('sha256:') for p,h in before.items())
events=[json.loads(line) for line in (capture/'fixture.stdout').read_text(encoding='utf-8').splitlines()]
counts={action:sum(e.get('Action')==action and 'Test' in e for e in events) for action in ['pass','fail','skip']}
assert counts['fail']==counts['skip']==0
assert sum(e.get('Action')=='pass' and 'Test' in e and '/' not in e['Test'] for e in events)==47
assert 'Ran 8 tests' in (capture/'parent-unit.stderr').read_text() and '\nOK' in (capture/'parent-unit.stderr').read_text()
result['executor_fixture']={'proof':ref(proof_path),'source_count':len(before),'before_after_and_current':True,'events':counts,'top_level_pass':47,'parent_tests':8,'H07_snapshots':len(load(proof_path)['h07_invocations'][0]['db_snapshots']),'scope':'isolated pre-S6 worktree; not current main collector'}
result['retained_initial_failure']=ref(REC/'qualification-initial-failure.json')
source=(WORK/'ops/ci/sources.py').read_bytes()
namespace={'__file__':str(ROOT/'ops/ci/sources.py'),'__name__':'independent_candidate_collector'}
exec(compile(source,str(WORK/'ops/ci/sources.py'),'exec'),namespace)
candidate=type('Candidate',(),namespace)
tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='decoder' for t in n.targets))
stop=next(i for i,n in enumerate(main.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='SOURCE_FILES' for t in n.targets))
fragment=compile(ast.Module(body=main.body[start:stop+1],type_ignores=[]),str(WORK/'ops/ci/sources.py'),'exec')
base_files=list(namespace['SOURCE_FILES']);vectors={};envs={}
go=Path(qualification['go_ref']['path'])
for mode in ['fixture','live']:
    inherited=dict(os.environ)
    for name in ['GOPATH','GOCACHE','GOMODCACHE']:inherited.pop(name,None)
    inherited.update({'RESEARCHOS_SOURCE_MODE':mode,'GOROOT':str(go.parents[1]),'GOTOOLCHAIN':'local','GOENV':'off'})
    with patch.dict(os.environ,inherited,clear=True):
        namespace['prepare_go_environment']()
        command=[str(go),'env','-json','GOPATH','GOCACHE','GOMODCACHE','GOROOT','GOTOOLCHAIN','GOENV']
        done=subprocess.run(command,cwd=ROOT,capture_output=True,env=dict(os.environ))
        (OUT/(mode+'-go-env.stdout')).write_bytes(done.stdout);(OUT/(mode+'-go-env.stderr')).write_bytes(done.stderr)
        assert done.returncode==0
        envs[mode]=json.loads(done.stdout)
    working=dict(namespace,dep_out=REC/(mode+'-go-list.stdout'),SOURCE_FILES=list(base_files))
    exec(fragment,working)
    vectors[mode]={name:namespace['sha256'](ROOT/name) for name in working['SOURCE_FILES']}
assert envs['fixture']==envs['live']
assert Path(envs['fixture']['GOPATH'])==ROOT/'.local/gopath' and Path(envs['fixture']['GOCACHE'])==ROOT/'.local/gocache'
assert vectors['fixture']==vectors['live']
missing=load(OUT/'gap_audit.json')['missing_files']
assert all(e['path'] in vectors['fixture'] for e in missing)
newvector=vectors['fixture'];old=load(ROOT/PREFIX/'run-c495292dee2d4e4fba7bb11a06979907/source-before.json')
assert set(newvector)-set(old)=={e['path'] for e in missing}
(OUT/'actual-main-logic-vector.json').write_text(json.dumps(newvector,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result['actual_main_candidate_logic']={'source_count':len(newvector),'all_27_included':True,'both_modes_equal':True,'environments':envs,'vector':ref(OUT/'actual-main-logic-vector.json'),'execution':'Unmodified candidate AST inventory statements run on actual MAIN with hash-checked recorded actual MAIN Go-list. Actual go env run separately in both modes. No collector/fixture/LIVE execution on MAIN. Vector hashes existing main bytes; candidate not integrated.'}
testtree=ast.parse((WORK/'tests/sources/check/parent_gate_test.py').read_bytes())
cls=next(n for n in testtree.body if isinstance(n,ast.ClassDef) and n.name=='ParentGateTests')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_filtered_go_cache_environment_has_project_defaults')
testclass=ast.ClassDef(name='IndependentEnvironmentTest',bases=[ast.Attribute(value=ast.Name(id='unittest',ctx=ast.Load()),attr='TestCase',ctx=ast.Load())],keywords=[],body=[method],decorator_list=[])
testglobals={'unittest':unittest,'gate':candidate,'ROOT':ROOT,'os':os,'patch':patch}
exec(compile(ast.fix_missing_locations(ast.Module(body=[testclass],type_ignores=[])),'candidate_environment_test','exec'),testglobals)
stream=io.StringIO();tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(testglobals['IndependentEnvironmentTest']))
(OUT/'independent_environment_test.raw').write_text(stream.getvalue(),encoding='utf-8')
assert tested.wasSuccessful() and not tested.skipped
result['independent_environment_test']={'tests':tested.testsRun,'skipped':0,'successful':True,'raw':ref(OUT/'independent_environment_test.raw')}
# Invoke the unchanged strict reader against MAIN, using only the inventory
# argument in memory. This is a coverage assertion, not a new or edited proof.
def module(name):
    path=ROOT/'execution/v2.4'/name;spec=importlib.util.spec_from_file_location('ind_'+name,path);m=importlib.util.module_from_spec(spec);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
api=module('formal_case_index.py');profile=module('formal_profile_w07.py')
col=ROOT/PREFIX/'run-c495292dee2d4e4fba7bb11a06979907';proof=load(col/'proof.json')
tools=load(ROOT/proof['version_vector_ref']['path'])['tool'];context={'compilation_invocation_ref':ref(col/'go-list.invocation.json')}
reader=api.Reader(ROOT)
profile._compiled_inputs(api,reader,context,proof,newvector,tools,api.interval(proof,'historical proof'))
reader.finish()
result['actual_main_strict_coverage']={'result':'PASS','reader':ref(ROOT/'execution/v2.4/formal_profile_w07.py'),'read_files':len(reader.read_hashes),'argument':'proposed inventory only in memory; historical proof files unchanged','formal_acceptance':False}
assert not git('status','--porcelain').strip()
(OUT/'candidate_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit':ref(OUT/'candidate_audit.json'),'source_count':len(newvector),'all_27':True,'mode_vectors_equal':True,'strict_main_coverage':'PASS','candidate_sources':result['source_paths']}))
