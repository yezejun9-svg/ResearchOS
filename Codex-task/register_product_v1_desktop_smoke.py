import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104';PREP=HERE/'product-v1-desktop-smoke-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert sha(PREP/'smoke.mjs')=='e19cf3cde84643a5f473ea94dc266ad9856ed7f3e3c2aa2add99692237a57979'
assert sha(PREP/'MANIFEST.json')=='c2b780465b3f3d6a39f672b6c1932b58498499490e8b980e6d17bd4d425de49a'
assert sha(PREP/'SCOPE.template.json')=='38fb1e652f96f4dc7e8312ea465e13a2035e74de4cf7fdeccb9464ec788bb6f5'
dry=json.loads((CONTROL/'runs/product-v1-bundle-dryrun-01/RESULT.json').read_bytes());assert dry['status']=='COMPLETED_OWNED_JOB_STOPPED' and dry['stop_proved'] and not dry['input_drift'] and not dry['errors']
scope=json.loads((PREP/'SCOPE.template.json').read_bytes());scope.update(scope_id='product-v1-desktop-smoke-01',authorization='ROOT_REVIEWED_EXACT_COMMAND')
for entry in scope['inputs']:assert sha(Path(entry['path']))==entry['sha256']
state=Path(scope['argv'][-1]);assert not state.exists() and state.parent==PREP
bundle=ROOT/'.local/worktrees/product-v1-build-20261104/.local/desktop-v1-build-02'
for f in [bundle/'runtime/electron/electron.exe',bundle/'apps/desktop/resources/control/researchos-control.exe',bundle/'apps/desktop/resources/control/runtime-verifier.exe']:
 scope['inputs'].append(dict(path=str(f),sha256=sha(f)))
sp=CONTROL/'scopes/product-v1-desktop-smoke-01.json';put(sp,scope)
review=dict(reviewer='codex:/root',author='codex:/root/runtime_readiness',decision='APPROVED_FOR_ONE_FRESH_ZERO_MODEL_GUI_SMOKE',scope_sha256=sha(sp),wrapper_sha256=sha(PREP/'smoke.mjs'),review='Full wrapper and bundled validation functions read. ValidateBundle checks all134 files; normal Windows profile only for native metadata, no ambient secret/proxy inheritance; private fresh data/userData; actual Main capture and host.status; exact original ElectronPID/Core identity and normal shutdown verified by throw-on-failure validator; outer original-handle Job required before any acceptance. No directory choice/project/task submit, modelcalls0 by action scope.',limitations=['Wrapper arrays persist after child close; if outer timeout occurs, treat outcome UNKNOWN and preserve fresh state/screenshot; never infer success from image alone.','This verifies desktop startup and Host metadata only, not real model, permissions, cancel, project or business acceptance.'],product_acceptance_increment=0,formal_increment=0)
put(PREP/'ROOT-REVIEW.json',review)
out=ROOT/'execution/product-v1/receipts/single-harness-20261104/desktop-smoke-01';assert not out.exists();out.mkdir()
for name in ['smoke.mjs','ROOT-REVIEW.json']:(out/name).write_bytes((PREP/name).read_bytes())
(out/'scope.json').write_bytes(sp.read_bytes());(out/'bundle-dryrun.RESULT.json').write_bytes((CONTROL/'runs/product-v1-bundle-dryrun-01/RESULT.json').read_bytes())
print(json.dumps(dict(scope_path=str(sp),scope_sha256=sha(sp),root_review_sha256=sha(PREP/'ROOT-REVIEW.json'),new_state=str(state),model_submission_actions=0)))
