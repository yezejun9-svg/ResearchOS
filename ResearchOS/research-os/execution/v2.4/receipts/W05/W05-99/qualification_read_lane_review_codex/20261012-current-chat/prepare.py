import datetime,hashlib,json,os,pathlib,subprocess,sys
OUT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
BUILD=SRC/'.local/qualification-build-output-03/apps/desktop'
BUNDLE=SRC/'.local/readlane-sourcebundle-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,x):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def capture(n,args):
    p=subprocess.run(args,cwd=SRC,capture_output=True)
    (OUT/(n+'.stdout.raw')).write_bytes(p.stdout);(OUT/(n+'.stderr.raw')).write_bytes(p.stderr)
    put(n+'.invocation.json',{'argv':args,'cwd':str(SRC),'exit':p.returncode})
    assert p.returncode==0,(n,p.returncode)
    return p.stdout
manifest=read(BUNDLE/'manifest.json')
assert sha(BUNDLE/'manifest.json')=='4ad8f3053b2620a2af6a5fd6c41f6003ab5916bca404c4322dd71fd646089a19'
assert sha(BUNDLE/'matrix.json')=='ff91f710f8b2e074d5574071e6553787e78bcea50ed7f4245c16899c41d37292'
assert sha(BUNDLE/'postcommit-binding-02.json')=='f11095479b53dbd8b5eaa385684d93acf40e229fe5475e17607db2609ac966e4'
assert capture('git-status',['git','status','--porcelain'])==b''
identity=capture('git-identity',['git','rev-parse','HEAD','HEAD^{tree}']).decode().splitlines()
assert identity[0]==manifest['source_commit']
names=capture('git-changed',['git','diff','--name-only',manifest['base_commit'],manifest['source_commit']]).decode().splitlines()
assert names==['apps/desktop/main/lib/ipc.js','apps/desktop/main/main.js','tests/ui/desktop/http-wire-boundary.test.mjs']
capture('candidate-diff',['git','diff',manifest['base_commit'],manifest['source_commit'],'--',*names])
refs=[]
for n in ['manifest.json','matrix.json','postcommit-binding-02.json']:
    refs.append(row(BUNDLE/n))
for entry in manifest['source']:
    p=pathlib.Path(entry['path']); assert row(p)==entry
    relative=p.relative_to(SRC)
    raw=subprocess.run(['git','show',f"{identity[0]}:{relative.as_posix()}"],cwd=SRC,capture_output=True,check=True).stdout
    assert hashlib.sha256(raw).hexdigest()==entry['sha256']
    dest=OUT/'source'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    refs.append(row(p))
descriptor=read(BUILD/'resources/client-wire/descriptor.json')
assert sha(BUILD/'resources/client-wire/descriptor.json')==manifest['descriptor']['sha256']
refs.append(row(BUILD/'resources/client-wire/descriptor.json'))
exe=BUILD/'resources/client-wire/researchos-client-wire-validator.exe'
assert sha(exe)==descriptor['binary_sha256'];refs.append(row(exe))
for module in descriptor['exact_module_source_inventory']:
    p=BUILD/module['path'];assert sha(p)==module['sha256'];refs.append(row(p))
for key in ['compile_invocation_ref','full_input_manifest_ref','compiler_generated_importcfg_archives_ref']:
    p=pathlib.Path(descriptor[key]['path']);assert sha(p)==descriptor[key]['sha256'];refs.append(row(p))
inputs=read(pathlib.Path(descriptor['full_input_manifest_ref']['path']))
digest=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert digest==descriptor['build_input_digest']
input_drift=[]
for entry in inputs:
    p=pathlib.Path(entry['path'])
    if not p.is_file() or sha(p)!=entry['sha256']:input_drift.append(entry['path'])
assert not input_drift,input_drift
for n in ['apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/v2.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/preload/preload.js']:
    refs.append(row(SRC/n))
for item in manifest['logs']:
    p=pathlib.Path(item['path']);assert sha(p)==item['sha256'];refs.append(row(p))
put('binding-before.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':identity[0],'source_tree':identity[1],'exact_paths':names,'refs':refs,'full_input_count':len(inputs),'full_input_digest':digest,'drift':input_drift,'precommit_build_metadata_preserved':True,'new_git_worktree_created':False,'D_writes':0,'product_calls':0})
print(json.dumps({'source_commit':identity[0],'full_inputs':len(inputs),'refs':len(refs),'drift':len(input_drift)}))
