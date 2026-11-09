from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v3_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v3-20261012'
V2APP=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v2-20261012/.local/w05-ui-repair-validator-final3/apps/desktop'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
def check(kind,p,expected,size=None):
    actual=sha(p) if p.is_file() else None
    rows.append(dict(kind=kind,path=str(p),expected=expected,actual=actual,passed=actual==expected and (size is None or p.stat().st_size==size)))
manifest=AUTHOR/'receipt_manifest.json'
check('v3-author-manifest',manifest,'9534ebd09aa3959b9eae1d7e338943c352ebf1b0e25231fc4410eef4e7598189')
for row in json.loads(manifest.read_text(encoding='utf-8'))['files']:
    check('v3-author-receipt',AUTHOR/row['path'],row['sha256'],row['bytes'])
commit='2f48ad7d4cd3cececf06a2a9a059a36ba157032c'
files=subprocess.check_output(['git','diff','--name-only','9602f61c05325fc9bd1b523398a8f9721eded72e',commit],cwd=WT,text=True).splitlines()
for name in files:
    raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=WT)
    check('v3-candidate-git',WT/name,hashlib.sha256(raw).hexdigest())
    dest=OUT/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((WT/name).read_bytes())
descriptor=json.loads((V2APP/'resources/client-wire/descriptor.json').read_text(encoding='utf-8'))
check('v2-validator-binary',V2APP/'resources/client-wire/researchos-client-wire-validator.exe',descriptor['binary_sha256'],descriptor['binary_bytes'])
for row in descriptor['exact_module_source_inventory']:
    check('v2-validator-resource-module',V2APP/row['path'],row['sha256'])
result=dict(candidate=commit,checks=len(rows),passed=sum(r['passed'] for r in rows),failures=[r for r in rows if not r['passed']],current_v3_full_build_binding=False,evidence_class='V3_SOURCE_COMPONENTS_WITH_FROZEN_V2_GO_VALIDATOR',all_checks=rows)
(OUT/'input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for source,target in [('index.html','index.html'),('test-entry.jsx','test-entry.jsx'),('reviewer-dom.mjs','baseline-dom.mjs')]:
    (OUT/target).write_bytes((AUTHOR/source).read_bytes())
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
raise SystemExit(bool(result['failures']))
