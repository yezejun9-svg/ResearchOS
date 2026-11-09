from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'desktop_managed_qualification_client_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-20261012'
BUILD=WT/'.local/managed-client-bound-final3'
APP=BUILD/'apps/desktop'
CANDIDATE='fc350c97cddbf7d54e37b88ece25b0e8be8f1d87'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
checks=[]
def check(kind,p,expected,size=None):
    actual=sha(p) if p.is_file() else None
    checks.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
check('author-manifest',AUTHOR/'receipt-manifest-final.json','31579e9e4c48d9e16719c3d78ea1eca8f9a161156ee64d6856f5bf8083ca2620')
check('author-source-bundle',AUTHOR/'source-bundle-final.json','f8024bfb5d835d5cf9b9584970988e6c818b413e5362d592166c518faea81617')
for row in read(AUTHOR/'receipt-manifest-final.json')['artifacts']:check('author-artifact',AUTHOR/row['path'],row['sha256'],row['bytes'])
for row in read(AUTHOR/'source-bundle-final.json')['source_files']:
    name=row['path'];raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{name}'],cwd=WT)
    expected=hashlib.sha256(raw).hexdigest();assert expected==row['sha256']
    check('candidate-source',WT/name,expected);check('author-source',AUTHOR/'source'/name,expected)
    if (BUILD/name).is_file():check('bound-source',BUILD/name,expected)
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
descriptor=read(APP/'resources/client-wire/descriptor.json')
check('bound-validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',descriptor['binary_sha256'],descriptor['binary_bytes'])
for row in descriptor['exact_module_source_inventory']:check('bound-module',APP/row['path'],row['sha256'])
for row in descriptor['compiled_React_asset_inventory']:check('compiled-react',BUILD/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in descriptor['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
ref=descriptor['full_input_manifest_ref'];inputs=Path(ref['path']);check('full-input-manifest',inputs,ref['sha256'],ref['bytes'])
for row in read(inputs):check('full-build-input',Path(row['path']),row['sha256'],row['bytes'])
openapi='spec/v2.0/contracts/openapi.json'
raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{openapi}'],cwd=WT)
base_raw=subprocess.check_output(['git','show',f'1c17662c4e4cc7058cd1d045ae0d55d9f75c3633:{openapi}'],cwd=WT)
assert raw==base_raw
check('public-openapi-bound-copy',BUILD/openapi,hashlib.sha256(raw).hexdigest())
assert descriptor['public_openapi_sha256']==hashlib.sha256(raw).hexdigest()
(OUT/'bound-descriptor.json').write_bytes((APP/'resources/client-wire/descriptor.json').read_bytes())
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff','1c17662c4e4cc7058cd1d045ae0d55d9f75c3633',CANDIDATE],cwd=WT))
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-baseline.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon),indent=2)+'\n',encoding='utf-8')
(OUT/'main-tracked-status.txt').write_bytes(subprocess.check_output(['git','status','--short','-uno'],cwd=ROOT))
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(r['passed'] for r in checks),failures=[r for r in checks if not r['passed']],build_input_digest=descriptor['build_input_digest'],full_build_input_count=len(read(inputs)),all_checks=checks)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
raise SystemExit(bool(result['failures']))
