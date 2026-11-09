import hashlib,json,pathlib,subprocess
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os')
C='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419';BASE='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e'
def git(*args):return subprocess.run(['git','--no-optional-locks','-C',str(R),*args],capture_output=True,check=True).stdout
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
paths=git('diff-tree','--no-commit-id','--name-status','-r',C).decode().splitlines()
status=git('status','--porcelain=v1','--untracked-files=no').decode().splitlines()
assert git('rev-parse','HEAD').decode().strip()==BASE and git('rev-parse',C+'^').decode().strip()==BASE
assert not git('diff','--cached','--name-only')
rows=[]
for item in paths:
    kind,name=item.split('\t');p=R/name
    staged=git('ls-files','--stage','--',name).decode().strip()
    pathstatus=git('status','--porcelain=v1','--untracked-files=all','--',name).decode().strip()
    target=git('show',C+':'+name)
    row={'change':kind,'path':name,'main_exists':p.exists(),'index_entry':staged,'path_status':pathstatus,'candidate_sha256':hashlib.sha256(target).hexdigest(),'candidate_bytes':len(target)}
    if kind=='A':assert not p.exists() and not staged and not pathstatus;row['mergeability']='NEW_PATH_NO_MAIN_OR_INDEX_COLLISION'
    else:
        before=git('show',BASE+':'+name);assert p.read_bytes()==before and not pathstatus
        row.update({'main_sha256':sha(p),'base_sha256':hashlib.sha256(before).hexdigest(),'mergeability':'MAIN_BYTES_EQUAL_DIRECT_PARENT_BLOB'})
    rows.append(row)
assert len(rows)==7 and len(status)==20
rules=[];out=E/'rules';out.mkdir(exist_ok=False)
locations=[R.parent/'AGENTS.md',R/'AGENTS.md']
for dirname in ['apps','apps/desktop','apps/desktop/main','tests','tests/ui','tests/ui/desktop','docs','docs/installation']:
    locations.append(R/dirname/'AGENTS.md')
for i,p in enumerate(locations):
    row={'path':str(p),'exists':p.is_file()}
    if p.is_file():
        raw=p.read_bytes();name=f'{i:02d}-AGENTS.md';(out/name).write_bytes(raw);row.update({'copy':str(out/name),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)});print(str(p));print(raw.decode('utf-8'))
    rules.append(row)
rootgate=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/CP554-live-Main-integration-preflight.json'
assert sha(rootgate)=='b2e8abf34d43d253cac77a8d22394c4f065af6695b48fbab855335b62cc91ca2'
(E/'ROOT-CP554-LIVE-GATE.json').write_bytes(rootgate.read_bytes())
put('MAIN-SEVEN-PATHS-INDEPENDENT.json',{'head':BASE,'candidate':C,'direct_parent':True,'index_empty':True,'tracked_dirty_count':len(status),'tracked_dirty_paths':status,'seven_paths':rows,'rules':rules,'root_gate_sha256':sha(rootgate)})
print(json.dumps({'tracked_dirty_count':len(status),'index_empty':True,'seven':rows,'rules_locations':rules},ensure_ascii=False))
