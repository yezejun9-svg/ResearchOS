from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v4-20261012'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
descriptor=read(WT/'.local/v4-bound-build-6/apps/desktop/resources/client-wire/descriptor.json')
ref=descriptor['full_input_manifest_ref']
manifest=Path(ref['path'])
assert sha(manifest)==ref['sha256']
checks=[]
for row in read(manifest):
    p=Path(row['path']);actual=sha(p) if p.is_file() else None
    checks.append(dict(path=str(p),expected=row['sha256'],actual=actual,passed=actual==row['sha256'] and p.stat().st_size==row['bytes']))
result=dict(manifest_sha256=sha(manifest),checks=len(checks),passed=sum(r['passed'] for r in checks),failures=[r for r in checks if not r['passed']],all_checks=checks)
(OUT/'full-input-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='all_checks'},ensure_ascii=True))
# Keep the first copied-harness run intact: it selected the author's old build-5.
old=OUT/'baseline-legacy-build5';old.mkdir(exist_ok=True)
for name in ['baseline-dom.mjs','baseline-dom.stdout','baseline-dom.stderr','baseline-dom.invocation.json','reviewer-dom-results.json','raw-http']:
    if (OUT/name).exists():(OUT/name).rename(old/name)
source=(old/'baseline-dom.mjs').read_text(encoding='utf-8').replace("process.env.RESEARCHOS_DESKTOP_WIRE_ROOT=path.join(WT,'.local/v4-bound-build-5/apps/desktop')", "assert.equal(process.env.RESEARCHOS_DESKTOP_WIRE_ROOT,path.join(WT,'.local/v4-bound-build-6/apps/desktop'))")
(OUT/'baseline-dom.mjs').write_text(source,encoding='utf-8')
race=(OUT/'host-race-dom.mjs').read_text(encoding='utf-8').replace("V4_IPC_AND_ACTUAL_DOM_WITH_FROZEN_V2_GO_VALIDATOR_SYNTHETIC_HTTP", "V4_SOURCE_COMPONENT_ACTUAL_DOM_BOUND_V4_GO_VALIDATOR_SYNTHETIC_HTTP").replace('current_v4_full_build_binding:false','current_v4_full_build_binding:true')
(OUT/'host-race-dom.mjs').write_text(race,encoding='utf-8')
raise SystemExit(bool(result['failures']))
