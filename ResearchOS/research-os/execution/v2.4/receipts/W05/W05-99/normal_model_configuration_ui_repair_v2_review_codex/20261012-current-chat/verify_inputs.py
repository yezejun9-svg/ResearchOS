from pathlib import Path
import hashlib, json, subprocess

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v2-20261012'
AUTHOR=OUT.parents[1]/'normal_model_configuration_ui_repair_v2_codex/20261012-current-chat'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(kind,path,want,size=None):
    p=Path(path)
    actual=digest(p) if p.is_file() else None
    checks.append(dict(kind=kind,path=str(p),expected=want,actual=actual,pass_=actual==want and (size is None or p.stat().st_size==size)))
m=AUTHOR/'receipt_manifest.json'
check('author-manifest',m,'48673f91653c39a273d9a3dfe7a93c3180271ea245fee413c16d711ac9453dcb')
for row in json.loads(m.read_text(encoding='utf-8'))['files']:
    check('author-receipt',AUTHOR/row['path'],row['sha256'],row.get('bytes'))
for row in json.loads((AUTHOR/'validator-inputs.after.json').read_text(encoding='utf-8')):
    check('validator-input',row['path'],row['sha256'],row.get('bytes'))
APP=WT/'.local/w05-ui-repair-validator-final3/apps/desktop'
descriptor=json.loads((APP/'resources/client-wire/descriptor.json').read_text(encoding='utf-8'))
check('descriptor',APP/'resources/client-wire/descriptor.json',digest(AUTHOR/'validator-descriptor.json'))
check('binary',APP/'resources/client-wire/researchos-client-wire-validator.exe',descriptor['binary_sha256'],descriptor['binary_bytes'])
for row in descriptor['exact_module_source_inventory']:
    check('built-module',APP/row['path'],row['sha256'])
    check('candidate-module',WT/'apps/desktop'/row['path'],row['sha256'])
commit='9602f61c05325fc9bd1b523398a8f9721eded72e'
base='292ad860f9e76cf2795d5a3010da1d114d01ff56'
files=subprocess.check_output(['git','diff','--name-only',base,commit],cwd=WT,text=True).splitlines()
for name in files:
    expected=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=WT)
    check('candidate-git',WT/name,hashlib.sha256(expected).hexdigest())
    copy=OUT/'source'/name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes((WT/name).read_bytes())
result=dict(candidate=commit,base=base,checks=len(checks),passed=sum(c['pass_'] for c in checks),failures=[c for c in checks if not c['pass_']],all_checks=checks)
(OUT/'input-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
raise SystemExit(bool(result['failures']))
