from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'product_coding_client_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-product-coding-client-20261012';BUILD=WT/'.local/coding-client-bound-final3';APP=BUILD/'apps/desktop'
CANDIDATE='eb7f712d21268c87f9af9428048313c9361c52d6';BASE='b3ebbbfd03d3c32f9238403317ce29718e31d321'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def check(kind,p,expected,size=None):
 actual=sha(p) if p.is_file() else None
 checks.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
check('author-manifest',AUTHOR/'manifest.json','277d3d8885470dfd031d356e0273d384839fa2d3e871ce612f1d734bb03d1118')
check('author-bundle',AUTHOR/'source-bundle-final.json','a30bf849cfd9f707ddcd188af15d17df012aeb58db9e93bb64129e38f62016b6')
m=read(AUTHOR/'manifest.json');b=read(AUTHOR/'source-bundle-final.json')
check('author-census',AUTHOR/'raw-census.json',m['raw_census_sha256']);check('author-readme',AUTHOR/'README.md',m['readme_sha256'])
census=read(AUTHOR/'raw-census.json');assert len(census['entries'])==1699
for row in census['entries']:check('author-raw',AUTHOR/row['path'],row['sha256'],row['bytes'])
scopepath=ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp424/coding-client-scope.json'
check('scope',scopepath,b['scope_sha256']);scope=read(scopepath)
for key in ['private_contract_ref','core_source_bundle_ref']:
 row=scope[key];check(key,ROOT/row['path'],row['sha256'],row['bytes'])
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip();(OUT/'candidate-tracked-status.txt').write_bytes(status)
changed=subprocess.check_output(['git','diff','--name-only',BASE,CANDIDATE],cwd=WT,text=True).splitlines();assert len(changed)==7 and set(changed)=={r['path'] for r in b['source_files']} and set(changed)<=set(scope['paths'])
for row in b['source_files']:
 name=row['path'];raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{name}'],cwd=WT);assert hashlib.sha256(raw).hexdigest()==row['sha256']
 check('source',WT/name,row['sha256'],row['bytes'])
 if (BUILD/name).is_file():check('bound-source',BUILD/name,row['sha256'],row['bytes'])
 p=OUT/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
descriptorpath=APP/'resources/client-wire/descriptor.json';d=read(descriptorpath)
check('descriptor',descriptorpath,b['bound_build']['descriptor_sha256']);check('author-descriptor',AUTHOR/'raw/bound-descriptor.json',b['bound_build']['descriptor_sha256'])
check('validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',d['binary_sha256'],d['binary_bytes'])
for row in d['exact_module_source_inventory']:check('bound-module',APP/row['path'],row['sha256'])
for row in d['compiled_React_asset_inventory']:check('compiled-react',BUILD/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in d['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
ref=d['full_input_manifest_ref'];inputs=Path(ref['path']);check('full-input-manifest',inputs,ref['sha256'],ref['bytes'])
for row in read(inputs):check('build-input',Path(row['path']),row['sha256'],row['bytes'])
assert len(read(inputs))==6439 and d['build_input_digest']=='cd58b95dac4f960b5c17f210c1a1d195b78a773d9645ff4b4a5dae5d9d9bdf0a'
(OUT/'bound-descriptor.json').write_bytes(descriptorpath.read_bytes());(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff',BASE,CANDIDATE],cwd=WT))
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status']})
write('main-canon-baseline.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon))
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(x['passed'] for x in checks),failures=[x for x in checks if not x['passed']],author_files=1699,full_build_inputs=6439,source_files=7,registered_paths=8,build_input_digest=d['build_input_digest'],all_checks=checks)
write('input-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='all_checks'}));assert not result['failures']
