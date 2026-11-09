import datetime,hashlib,json,pathlib,subprocess
OUT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
BUILD=SRC/'.local/qualification-build-output-v2-02/apps/desktop'
BUNDLE=SRC/'.local/readlane-v2-wip-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,x):
 with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def capture(n,args):
 p=subprocess.run(args,cwd=SRC,capture_output=True);(OUT/(n+'.stdout.raw')).write_bytes(p.stdout);(OUT/(n+'.stderr.raw')).write_bytes(p.stderr)
 put(n+'.invocation.json',{'argv':args,'cwd':str(SRC),'exit':p.returncode});assert p.returncode==0;return p.stdout
manifest=read(BUNDLE/'manifest.json');assert sha(BUNDLE/'manifest.json')=='5db8663b96cabab59fcc4138b9abcf8aca22c400bbe213d46bff845065582439'
status=capture('git-status',['git','status','--porcelain']).decode().splitlines()
assert status==[' M apps/desktop/main/lib/ipc.js',' M tests/ui/desktop/http-wire-boundary.test.mjs'],status
identity=capture('git-identity',['git','rev-parse','HEAD','HEAD^{tree}']).decode().splitlines();assert identity[0]==manifest['frozen_base_commit']
capture('candidate-wip-diff',['git','diff','--',*manifest['allowed_paths']])
refs=[row(BUNDLE/'manifest.json')]
for item in manifest['files']:
 p=BUNDLE/item['name'];assert sha(p)==item['sha256'];refs.append(row(p))
binding=read(BUNDLE/'source-binding.json')
for entry in binding:
 p=SRC/entry['path'];assert sha(p)==entry['sha256'];refs.append(row(p));dest=OUT/'source'/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 if entry['build_copy_sha256']:
  built=BUILD/pathlib.Path(entry['path']).relative_to('apps/desktop');assert sha(built)==entry['sha256'];refs.append(row(built))
dp=pathlib.Path(manifest['build']['descriptor']);assert sha(dp)==manifest['build']['descriptor_sha256'];descriptor=read(dp);refs.append(row(dp))
exe=BUILD/'resources/client-wire/researchos-client-wire-validator.exe';assert sha(exe)==descriptor['binary_sha256']==manifest['build']['binary_sha256'];refs.append(row(exe))
for entry in descriptor['exact_module_source_inventory']:
 p=BUILD/entry['path'];assert sha(p)==entry['sha256'];refs.append(row(p))
for key in ['compile_invocation_ref','full_input_manifest_ref','compiler_generated_importcfg_archives_ref']:
 p=pathlib.Path(descriptor[key]['path']);assert sha(p)==descriptor[key]['sha256'];refs.append(row(p))
inputs=read(pathlib.Path(descriptor['full_input_manifest_ref']['path']));digest=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert digest==descriptor['build_input_digest']==manifest['build']['input_digest'];assert len(inputs)==6444
input_drift=[]
for entry in inputs:
 p=pathlib.Path(entry['path'])
 if not p.is_file() or sha(p)!=entry['sha256']:input_drift.append(entry['path'])
assert not input_drift,input_drift
for entry in binding:
 matches=[x for x in inputs if pathlib.Path(x['path'])==SRC/entry['path']];assert len(matches)==1 and matches[0]['sha256']==entry['sha256'],entry
for n in ['apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/v2.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/preload/preload.js','tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/w13-react.test.js']:
 p=SRC/n;refs.append(row(p))
for item in read(BUNDLE/'test-invocations.json'):
 p=pathlib.Path(item['stdout']);assert sha(p)==item['stdout_sha256'];refs.append(row(p));text=p.read_text(encoding='utf-8-sig');assert '# pass '+str(item['pass']) in text and '# fail '+str(item['fail']) in text
put('binding-before.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':identity[0],'source_tree':identity[1],'wip_status':status,'exact_paths':manifest['allowed_paths'],'refs':refs,'full_input_count':len(inputs),'full_input_digest':digest,'drift':input_drift,'source_is_frozen_uncommitted_WIP':True,'D_writes':0,'product_calls':0})
print(json.dumps({'source_commit':identity[0],'full_inputs':len(inputs),'refs':len(refs),'drift':len(input_drift)}))
