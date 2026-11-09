import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
OLD=HERE/'product-v1-desktop-smoke-02-20261104';NEW=HERE/'product-v1-desktop-smoke-03-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not NEW.exists();r=json.loads((CONTROL/'runs/product-v1-build-04/RESULT.json').read_bytes())
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['stop_proved'] and not r['errors'] and not r['input_drift'] and r['terminate_job_attempts']==0
assert sha(OLD/'smoke.mjs')=='9398af77f03409379c051240d9a3e59f3b0cb795a5ef43d0e33fc72140b80716'
bundle=ROOT/'.local/worktrees/product-v1-build-04-20261104/.local/desktop-v1-build-04';manifest=bundle/'development-manifest.json';m=json.loads(manifest.read_bytes())
reg=json.loads((ROOT/'execution/product-v1/receipts/single-harness-20261104/build04-scope/registration.json').read_bytes());assert m['source']['head']==reg['main_head'] and m['source']['candidate_delta']==[]
for row in m['files']:
 p=bundle/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
assert sha(bundle/'apps/desktop/main/lib/ipc.js')=='6ceac6a835bb10fb40f14a3dc5a10d46937346424e5166e24952e9960c76d584'
text=(OLD/'smoke.mjs').read_text(encoding='utf8');oldbundle='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104/.local/desktop-v1-build-03';assert text.count(oldbundle)==1;text=text.replace(oldbundle,bundle.as_posix()).replace('a800bca4a7fe808a85c6b175547c5e1788e7d4f10b59fe58e17a94f7f4a713fa',sha(manifest))
NEW.mkdir();(NEW/'smoke.mjs').write_bytes(text.encode('utf8'))
scope=json.loads((CONTROL/'scopes/product-v1-desktop-smoke-02.json').read_bytes());scope.update(scope_id='product-v1-desktop-smoke-03',argv=[str(NEW/'smoke.mjs'),'--state',str(NEW/'smoke-state-01')],cwd=str(NEW))
files=[NEW/'smoke.mjs',manifest,bundle/'launch-development.mjs',bundle/'apps/desktop/main/main.js',bundle/'apps/desktop/main/lib/ipc.js',bundle/'runtime/electron/electron.exe',bundle/'apps/desktop/resources/control/researchos-control.exe',bundle/'apps/desktop/resources/control/runtime-verifier.exe'];scope['inputs']=[dict(path=str(p),sha256=sha(p)) for p in files]
sp=CONTROL/'scopes/product-v1-desktop-smoke-03.json';put(sp,scope)
review=dict(reviewer='codex:/root',decision='APPROVED_ONE_FRESH_ZERO_MODEL_GUI_SMOKE',source_head=reg['main_head'],scope_sha256=sha(sp),wrapper_sha256=sha(NEW/'smoke.mjs'),prior_wrapper_sha256=sha(OLD/'smoke.mjs'),change='Only immutable bundle path+manifest binding and new owned state changed. Public-health exact2 independently reviewed and integrated; all134 bundle files verified against manifest. Actual visual health still to be observed.',models_submitted=0,formal_increment=0,business_acceptance=False,outer_job_required=True)
put(NEW/'ROOT-REVIEW.json',review)
out=ROOT/'execution/product-v1/receipts/single-harness-20261104/desktop-smoke-03';assert not out.exists();out.mkdir()
for name,p in [('scope.json',sp),('smoke.mjs',NEW/'smoke.mjs'),('ROOT-REVIEW.json',NEW/'ROOT-REVIEW.json')]:(out/name).write_bytes(p.read_bytes())
print(json.dumps(dict(scope_path=str(sp),scope_sha256=sha(sp),wrapper_sha256=sha(NEW/'smoke.mjs'),models_submitted=0)))
