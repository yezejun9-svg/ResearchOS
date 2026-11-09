import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
artifact=ROOT/'.local/worktrees/product-v1-build-03-20261104/.local/cli-v1-artifact-01';manifest=artifact/'artifact-manifest.json';m=read(manifest)
assert sha(manifest)=='ef603e5dc373d01a67f5a0d9b6b2c56e82bd03b89f58d3dbb10bfcc6feb5b3b9'
binary=Path(m['binary']['path']);assert sha(binary)==m['binary']['sha256']=='881e26a2784cab412c21e3f6b3e562d031d9f10479911953a83ef5888a7a4da7'
r=read(CONTROL/'runs/product-v1-cli-build-01/RESULT.json');assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['stop_proved'] and r['terminate_job_attempts']==0 and not r['errors'] and not r['input_drift']
scope=read(CONTROL/'scopes/product-v1-cli-build-01.json');scope.update(scope_id='product-v1-cli-help-01',executable=str(binary),executable_sha256=sha(binary),argv=['harness','help'],cwd=str(HERE),timeout_seconds=20,process_limit=4,memory_mib=256,max_raw_bytes=1024*1024,env={})
scope['inputs']=[dict(path=str(p),sha256=sha(p)) for p in [binary,manifest]]
sp=CONTROL/'scopes/product-v1-cli-help-01.json';put(sp,scope)
out=ROOT/'execution/product-v1/receipts/single-harness-20261104/cli-help-01';assert not out.exists();out.mkdir();(out/'scope.json').write_bytes(sp.read_bytes())
put(out/'ROOT-REVIEW.json',dict(decision='APPROVED_USAGE_ONLY',reviewer='codex:/root',scope_sha256=sha(sp),binary_sha256=sha(binary),review='Actual source main dispatches harness; runCLIHarness help returns before prompt/deps.connectHost. Run exact harness help with f13 fresh minimal profile, no inherited Host/auth/env/old working directory. This verifies namespace usage only, not Host/model task completion.',formal_increment=0,business_acceptance=False,model_requests=0))
print(json.dumps(dict(scope=str(sp),scope_sha256=sha(sp))))
