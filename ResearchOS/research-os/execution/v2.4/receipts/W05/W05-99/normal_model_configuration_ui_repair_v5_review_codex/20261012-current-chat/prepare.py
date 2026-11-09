from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v5_codex/20261012-current-chat'
V4=OUT.parents[1]/'normal_model_configuration_ui_repair_v4_review_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v5-20261012'
BUILD=WT/'.local/v5-bound-build-1'
APP=BUILD/'apps/desktop'
CANDIDATE='1c761174cabdd5be6fc95218eeaa502cd8c6c3f1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
checks=[]
def check(kind,p,expected,size=None):
    actual=sha(p) if p.is_file() else None
    checks.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
manifest=AUTHOR/'receipt_manifest.json'
check('author-manifest',manifest,'0a9143a104ab913ed2c759c1f3ec5ff6d9662083a20fd751570f67e41ef35e13')
for row in read(manifest)['files']:check('author-member',AUTHOR/row['path'],row['sha256'],row['bytes'])
descriptor=read(APP/'resources/client-wire/descriptor.json')
check('bound-validator',APP/'resources/client-wire/researchos-client-wire-validator.exe',descriptor['binary_sha256'],descriptor['binary_bytes'])
for row in descriptor['exact_module_source_inventory']:
    check('bound-module',APP/row['path'],row['sha256']);check('candidate-module',WT/'apps/desktop'/row['path'],row['sha256'])
for row in descriptor['compiled_React_asset_inventory']:check('compiled-react',BUILD/'apps/web/dist'/row['path'],row['sha256'],row['bytes'])
for row in descriptor['tools']:check('build-tool',Path(row['path']),row['sha256'],row.get('bytes'))
ref=descriptor['full_input_manifest_ref'];inputs=Path(ref['path']);check('full-input-manifest',inputs,ref['sha256'],ref['bytes'])
for row in read(inputs):check('full-build-input',Path(row['path']),row['sha256'],row['bytes'])
source=[]
for name in subprocess.check_output(['git','diff','--name-only','292ad860f9e76cf2795d5a3010da1d114d01ff56',CANDIDATE],cwd=WT,text=True).splitlines():
    raw=subprocess.check_output(['git','show',f'{CANDIDATE}:{name}'],cwd=WT);expected=hashlib.sha256(raw).hexdigest()
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    check('author-cumulative-snapshot',AUTHOR/'source'/name,expected)
    if (WT/name).is_file():check('candidate-cumulative-source',WT/name,expected)
    if (BUILD/name).is_file():check('bound-cumulative-source',BUILD/name,expected)
    source.append(dict(path=name,sha256=expected,worktree_present=(WT/name).is_file(),bound_present=(BUILD/name).is_file()))
(OUT/'cumulative-source-verification.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
(OUT/'candidate-full.diff').write_bytes(subprocess.check_output(['git','diff','292ad860f9e76cf2795d5a3010da1d114d01ff56',CANDIDATE],cwd=WT))
(OUT/'candidate-v5-delta.diff').write_bytes(subprocess.check_output(['git','diff','57ec9b4408835483bf0c4c30397968d7a11a0b2c',CANDIDATE],cwd=WT))
(OUT/'bound-descriptor.json').write_bytes((APP/'resources/client-wire/descriptor.json').read_bytes())
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
(OUT/'main-canon-baseline.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon),indent=2)+'\n',encoding='utf-8')
(OUT/'main-tracked-status.txt').write_bytes(subprocess.check_output(['git','status','--short','-uno'],cwd=ROOT))
for name in ['index.html','test-entry.jsx','baseline-dom.mjs','host-race-dom.mjs','status-race.mjs']:
    raw=(V4/name).read_text(encoding='utf-8').replace('w05-normal-model-ui-repair-v4-20261012','w05-normal-model-ui-repair-v5-20261012').replace('.local/v4-bound-build-6','.local/v5-bound-build-1').replace('V4_SOURCE_COMPONENT_ACTUAL_DOM_BOUND_V4_GO_VALIDATOR_SYNTHETIC_HTTP','V5_SOURCE_COMPONENT_ACTUAL_DOM_BOUND_V5_GO_VALIDATOR_SYNTHETIC_HTTP').replace('current_v4_full_build_binding','current_v5_full_build_binding').replace('BOUND_V4_IPC','BOUND_V5_IPC')
    (OUT/name).write_text(raw,encoding='utf-8')
result=dict(candidate=CANDIDATE,checks=len(checks),passed=sum(r['passed'] for r in checks),failures=[r for r in checks if not r['passed']],build_input_digest=descriptor['build_input_digest'],full_build_input_count=len(read(inputs)),all_checks=checks)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
raise SystemExit(bool(result['failures']))
