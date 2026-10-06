import hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[6]
WORK = ROOT / '.local/worktrees/codex-w0799'
COMMIT = '2da28a73e2ef8b8fea62eac5c68a4397c9d7a3f9'
REL = Path('execution/v2.4/receipts/W07/W07-99/source_executor_codex')
HAND = REL / 'relocation-fix-2ee66f6d875f496f863ceb477d1c026e/handoff.json'
COL = REL / 'run-8017e0f7e4384703b223c3dbc542a057'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(WORK),*args])
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def walk_refs(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value: yield value
        for item in value.values(): yield from walk_refs(item)
    elif isinstance(value,list):
        for item in value: yield from walk_refs(item)

result = {'candidate':COMMIT,'network_calls':0,'formal_increment':0}
assert git('rev-parse','HEAD').decode().strip()==COMMIT
result['status_before']=git('status','--porcelain').decode()
assert not result['status_before']
changed=git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).decode().splitlines()
result['changed_blobs']=[]
for name in changed:
    blob=git('show',COMMIT+':'+name)
    current=(WORK/name).read_bytes()
    assert blob==current
    result['changed_blobs'].append({'path':name,'sha256':hashlib.sha256(blob).hexdigest()})
source=[name for name in changed if not name.startswith(REL.as_posix()+'/')]
assert source==['ops/ci/sources.py','tests/sources/check/parent_gate_test.py']
handoff=json.loads((WORK/HAND).read_text(encoding='utf-8'))
assert sha(WORK/HAND)=='e199361aa0d573cbf5f6ac4526acc069105227174e96560216ee2d81fba53fce'
result['handoff']=ref(WORK/HAND)
result['handoff_refs']=[]
for entry in walk_refs(handoff):
    assert sha(WORK/entry['path'])==entry['sha256'].removeprefix('sha256:')
    result['handoff_refs'].append(entry)
proof=json.loads((WORK/COL/'proof.json').read_text(encoding='utf-8'))
assert sha(WORK/COL/'proof.json')=='be55cec5bb18e285ad5d933e784fac8d04b8035fe5c0f0bc81c8d8769a2a454c'
result['retained_proof']=ref(WORK/COL/'proof.json')
prior=git('ls-tree','-r','--name-only',COMMIT+'^','--',COL.as_posix()).decode().splitlines()
for name in prior: assert git('show',COMMIT+'^:'+name)==git('show',COMMIT+':'+name)
result['old_collection_unchanged_blobs']=len(prior)
result['executor_tests']=[]
for attempt in handoff['test_attempts']:
    invocation=json.loads((WORK/attempt['invocation']['path']).read_text(encoding='utf-8'))
    assert invocation['exit_code']==attempt['actual_exit']
    result['executor_tests'].append({'exit_code':invocation['exit_code'],'stderr':attempt['stderr']})

# Isolate even temporary test writes from the peer's candidate worktree.
with tempfile.TemporaryDirectory(prefix='w07-relocation-review-',dir=ROOT/'.local') as temp:
    snap=Path(temp)
    for name in ['ops/ci/sources.py','tests/sources/check/parent_gate_test.py','tests/sources/check/main.py']:
        target=snap/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(WORK/name,target)
    target=snap/COL; target.mkdir(parents=True)
    for name in ['proof.json','fixture.stdout','fixture.stderr','h07-assertions.json']:
        shutil.copyfile(WORK/COL/name,target/name)
    shutil.copytree(WORK/COL/'h07-db',target/'h07-db')
    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,'-B','-X','utf8','tests/sources/check/parent_gate_test.py','-v']
    completed=subprocess.run(command,cwd=snap,env=env,capture_output=True)
    (OUT/'independent_units.stdout').write_bytes(completed.stdout)
    (OUT/'independent_units.stderr').write_bytes(completed.stderr)
    result['independent_units']={'argv':command,'isolated_cwd':str(snap),'exit_code':completed.returncode,'stdout':ref(OUT/'independent_units.stdout'),'stderr':ref(OUT/'independent_units.stderr')}
    assert completed.returncode==0
    assert b'Ran 7 tests' in completed.stderr and b'\nOK' in completed.stderr

spec=importlib.util.spec_from_file_location('review_relocation_gate',WORK/'ops/ci/sources.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
gate.ROOT=ROOT
collection=ROOT/COL
assert sha(collection/'proof.json')==sha(WORK/COL/'proof.json')
snapshots=proof['h07_invocations'][0]['db_snapshots']
before={item['path']:sha(ROOT/item['path']) for item in snapshots}
opened=[]
original_connect=gate.sqlite3.connect
def local_only(database,**kwargs):
    assert database.startswith(collection.as_uri()+'/h07-db/')
    assert database.endswith('?mode=ro&immutable=1') and kwargs=={'uri':True}
    opened.append(database)
    return original_connect(database,**kwargs)
gate.sqlite3.connect=local_only
try: actual=gate.verify_h07_evidence(collection,proof)
finally: gate.sqlite3.connect=original_connect
after={item['path']:sha(ROOT/item['path']) for item in snapshots}
assert actual and len(opened)==13 and before==after
result['independent_main_replay']={'actual':actual,'opened':opened,'before':before,'after':after,'mode':'READ_ONLY_H07_RELOCATION_ONLY'}
result['status_after']=git('status','--porcelain').decode()
assert result['status_after']==result['status_before']
result['limitations']=['No LIVE or full product proof qualification; old proof vector is historical after reader source change.','No parent/A05/global CURRENT acceptance.']
(OUT/'audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'audit':ref(OUT/'audit.json'),'source_paths':source,'changed_blobs':len(changed),'retained_collection':len(prior),'independent_units':completed.returncode,'main_snapshot_count':len(opened),'main_replay':actual}))
