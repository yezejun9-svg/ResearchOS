from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v4_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v4-20261012'
BUILD=WT/'.local/v4-bound-build-6'
APP=BUILD/'apps/desktop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
rows=[]
def check(kind,p,expected,size=None):
    actual=sha(p) if p.is_file() else None
    rows.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
manifest=AUTHOR/'receipt_manifest.json'
check('author-manifest',manifest,'ece814f27447a2ec1e23acb2fcd2d18e214e858117b16206c51ee5aff448a0be')
for row in read(manifest)['files']:check('author-member',AUTHOR/row['path'],row['sha256'],row['bytes'])
candidate='57ec9b4408835483bf0c4c30397968d7a11a0b2c'
for name in subprocess.check_output(['git','diff','--name-only','2f48ad7d4cd3cececf06a2a9a059a36ba157032c',candidate],cwd=WT,text=True).splitlines():
    raw=subprocess.check_output(['git','show',f'{candidate}:{name}'],cwd=WT)
    check('candidate-source',WT/name,hashlib.sha256(raw).hexdigest())
    dest=OUT/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
descriptor=read(APP/'resources/client-wire/descriptor.json')
check('bound-descriptor',APP/'resources/client-wire/descriptor.json',sha(AUTHOR/'final-bound-descriptor.json'))
check('bound-validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',descriptor['binary_sha256'],descriptor['binary_bytes'])
for row in descriptor['exact_module_source_inventory']:
    check('bound-module',APP/row['path'],row['sha256'])
    check('candidate-module',WT/'apps/desktop'/row['path'],row['sha256'])
for row in descriptor['compiled_React_asset_inventory']:check('compiled-react',BUILD/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in descriptor['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name
    canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-baseline.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon),indent=2)+'\n',encoding='utf-8')
(OUT/'main-tracked-status.txt').write_bytes(subprocess.check_output(['git','status','--short','-uno'],cwd=ROOT))
(OUT/'candidate-delta.diff').write_bytes(subprocess.check_output(['git','diff','2f48ad7d4cd3cececf06a2a9a059a36ba157032c',candidate],cwd=WT))
for name in ['index.html','test-entry.jsx','baseline-dom.mjs','host-race-dom.mjs']:(OUT/name).write_bytes((AUTHOR/name).read_bytes())
result=dict(candidate=candidate,checks=len(rows),passed=sum(r['passed'] for r in rows),failures=[r for r in rows if not r['passed']],build_root=str(BUILD),build_input_digest=descriptor['build_input_digest'],all_checks=rows)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
print('FULL_INPUT_MANIFEST_REF',descriptor['full_input_manifest_ref'])
raise SystemExit(bool(result['failures']))
