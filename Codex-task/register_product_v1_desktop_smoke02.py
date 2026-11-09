import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
OLD=HERE/'product-v1-desktop-smoke-20261104';NEW=HERE/'product-v1-desktop-smoke-02-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not NEW.exists();r=json.loads((CONTROL/'runs/product-v1-build-03/RESULT.json').read_bytes());assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['stop_proved'] and not r['errors'] and not r['input_drift'] and r['terminate_job_attempts']==0
assert sha(OLD/'smoke.mjs')=='e19cf3cde84643a5f473ea94dc266ad9856ed7f3e3c2aa2add99692237a57979'
bundle=ROOT/'.local/worktrees/product-v1-build-03-20261104/.local/desktop-v1-build-03';manifest=bundle/'development-manifest.json';assert sha(manifest)=='a800bca4a7fe808a85c6b175547c5e1788e7d4f10b59fe58e17a94f7f4a713fa'
text=(OLD/'smoke.mjs').read_text(encoding='utf8');oldbundle='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-20261104/.local/desktop-v1-build-02';assert text.count(oldbundle)==1;text=text.replace(oldbundle,bundle.as_posix());text=text.replace('716ed8b0f4591ff1cb8e4f5d90975345c6963ebfa5f5d8e6ea9635c4d6ab92cf',sha(manifest));NEW.mkdir();(NEW/'smoke.mjs').write_bytes(text.encode('utf8'))
oldscope=json.loads((CONTROL/'scopes/product-v1-desktop-smoke-01.json').read_bytes());scope=dict(oldscope);scope.update(scope_id='product-v1-desktop-smoke-02',argv=[str(NEW/'smoke.mjs'),'--state',str(NEW/'smoke-state-01')],cwd=str(NEW))
files=[NEW/'smoke.mjs',manifest,bundle/'launch-development.mjs',bundle/'apps/desktop/main/main.js',bundle/'runtime/electron/electron.exe',bundle/'apps/desktop/resources/control/researchos-control.exe',bundle/'apps/desktop/resources/control/runtime-verifier.exe'];scope['inputs']=[dict(path=str(p),sha256=sha(p)) for p in files]
sp=CONTROL/'scopes/product-v1-desktop-smoke-02.json';put(sp,scope)
review=dict(reviewer='codex:/root',decision='APPROVED_ONE_FRESH_ZERO_MODEL_GUI_SMOKE',source_head='c4029c0b57599e1aafed6d01ea4034b0cf465ccd',scope_sha256=sha(sp),wrapper_sha256=sha(NEW/'smoke.mjs'),prior_wrapper_sha256=sha(OLD/'smoke.mjs'),change='Only immutable bundle path+manifest binding and new owned state changed. Underlying reviewed wrapper unchanged; newly reviewed Main uses private AUTHORITY_READ probe and validated actual Host health, fresh dark default.',models_submitted=0,formal_increment=0,business_acceptance=False,outer_job_required=True)
put(NEW/'ROOT-REVIEW.json',review)
out=ROOT/'execution/product-v1/receipts/single-harness-20261104/desktop-smoke-02';assert not out.exists();out.mkdir();(out/'scope.json').write_bytes(sp.read_bytes());(out/'smoke.mjs').write_bytes((NEW/'smoke.mjs').read_bytes());(out/'ROOT-REVIEW.json').write_bytes((NEW/'ROOT-REVIEW.json').read_bytes())
print(json.dumps(dict(scope_path=str(sp),scope_sha256=sha(sp),wrapper_sha256=sha(NEW/'smoke.mjs'),new_state=scope['argv'][-1],models_submitted=0)))
