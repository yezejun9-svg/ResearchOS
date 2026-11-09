import argparse, hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
base='3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    tmp=path.with_name(path.name+'.new')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(tmp,path)
def git(directory,*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=directory,stderr=subprocess.STDOUT).decode('utf-8').strip()
parser=argparse.ArgumentParser()
parser.add_argument('--host-review',required=True)
parser.add_argument('--host-review-sha',required=True)
args=parser.parse_args()
review_paths={'routing':out/'reviews/routing-review.json','host':out/args.host_review}
assert sha(review_paths['routing'])=='e18aa5c64df24486c08917c66d58691640130a8a545116211513cbaf3ea2a38f'
assert sha(review_paths['host'])==args.host_review_sha
assert git(root,'rev-parse','HEAD')==base
assert not (out/'integration-journal.json').exists(), 'Inspect previous journal, do not replay uncertain writes'
scope=json.loads((out/'scope-and-baseline.json').read_bytes())
for path,expected in scope['protected_tracked_before'].items():
    if path in ['execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md']:continue
    actual=sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE'
    assert actual==expected, path
assert (root/'execution/v2.4/commands.json').read_bytes()==(out/'commands.before.json').read_bytes()
routing=json.loads((out/'routing-author/author-summary.json').read_bytes())['source_sha256']
host={r['path']:r['sha256'] for r in json.loads((out/'host-author/source-manifest.json').read_bytes())['files']}
assert not set(routing).intersection(host)
records=[]
for name,folder,files,message in [
    ('routing','w05-runtime-routing-20261104',routing,'fix(runtime): route v2.4 selectors and verify locked Python'),
    ('host','shared-host-discovery-20261104',host,'feat(clients): discover the owned Desktop host across working directories')]:
    wt=root/'.local/worktrees'/folder
    assert git(wt,'rev-parse','HEAD')==base
    assert not git(wt,'diff','--cached','--name-only')
    for path,digest in files.items(): assert sha(wt/path)==digest,path
    git(wt,'diff','--check')
    records.append({'scope':name,'status':'VERIFIED_BEFORE_COMMIT','files':files,'worktree':str(wt)})
put(out/'integration-journal.json',{'started_at':datetime.now(timezone.utc).isoformat(),'base':base,'records':records,'formal_increment':0})
for record in records:
    wt=Path(record['worktree'])
    git(wt,'add','--',*record['files'])
    assert set(git(wt,'diff','--cached','--name-only').splitlines())==set(record['files'])
    message='fix(runtime): route v2.4 selectors and verify locked Python' if record['scope']=='routing' else 'feat(clients): discover the owned Desktop host across working directories'
    record['commit_output']=git(wt,'commit','-m',message)
    record['candidate_commit']=git(wt,'rev-parse','HEAD');record['status']='COMMITTED'
    put(out/'integration-journal.json',{'base':base,'records':records,'formal_increment':0})
git(root,'merge','--ff-only',records[0]['candidate_commit'])
records[0]['main_commit']=git(root,'rev-parse','HEAD');records[0]['status']='INTEGRATED'
put(out/'integration-journal.json',{'base':base,'records':records,'formal_increment':0})
git(root,'cherry-pick',records[1]['candidate_commit'])
records[1]['main_commit']=git(root,'rev-parse','HEAD');records[1]['status']='INTEGRATED'
put(out/'integration-journal.json',{'base':base,'records':records,'formal_increment':0})
for files in [routing,host]:
    for path,digest in files.items(): assert sha(root/path)==digest,path
candidate=out/'registry-candidate.json'
assert sha(candidate)=='dc5f7fe16ce55d1fd1d9c50df4df96e266f454a76416d817ed7e62406226f279'
registry=root/'execution/v2.4/commands.json'
assert registry.read_bytes()==(out/'commands.before.json').read_bytes()
temporary=registry.with_name(registry.name+'.cp580.new')
assert not temporary.exists()
temporary.write_bytes(candidate.read_bytes());os.replace(temporary,registry)
assert sha(registry)==sha(candidate)
preserved={}
for path,expected in scope['protected_tracked_before'].items():
    if path in ['execution/v2.4/checkpoint.json','execution/v2.4/HANDOFF_RESUME_PACK.md','execution/v2.4/commands.json']:continue
    actual=sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE'
    assert actual==expected,path
    preserved[path]=actual
result={'status':'SOURCE_INTEGRATED_DEVELOPMENT_EVIDENCE_ONLY','at':datetime.now(timezone.utc).isoformat(),'base_head':base,'main_head':git(root,'rev-parse','HEAD'),'main_tree':git(root,'rev-parse','HEAD^{tree}'),'records':records,'registry_revision':41,'registry_sha256':sha(registry),'review_refs':{name:{'path':str(path.relative_to(root)),'sha256':sha(path)} for name,path in review_paths.items()},'protected_preserved':preserved,'step_state_unchanged':True,'formal_increment':0,'native_executed':False,'provider_executed':False,'original_data_migrated':False}
put(out/'integration.json',result)
print(json.dumps({k:result[k] for k in ['status','main_head','main_tree','registry_revision','registry_sha256','formal_increment']}))
