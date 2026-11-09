import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
wrapper=HERE/'product-v1-cli-component-build-01.py';assert sha(wrapper)=='474838a3f75e2ce148943d3cfc92b62f97b7c03922b27366b4857f349081aa3c'
review=HERE/'product-v1-cli-build-independent-review-20261104/report.json'
rv=json.loads(review.read_bytes());assert rv['decision']=='APPROVED_BUILD_ONLY'
template=json.loads((CONTROL/'scopes/product-v1-build-03.json').read_bytes());scope=dict(template)
scope.update(scope_id='product-v1-cli-build-01',argv=['-B','-X','utf8',str(wrapper)],timeout_seconds=600,process_limit=8,memory_mib=4096,max_raw_bytes=16*1024*1024)
wt=ROOT/'.local/worktrees/product-v1-build-03-20261104';assert not (wt/'.local/cli-v1-artifact-01').exists()
scope['inputs']=[row for row in template['inputs'] if row['path'].endswith(('go.mod','go.sum','build-development.py','go.exe','apps\\cli\\main.go','apps\\cli\\productv1.go','apps\\cli\\productv1_test.go'))]
for p in [wrapper,review,wt/'execution/toolchains/locked.json']:
 scope['inputs'].append(dict(path=str(p),sha256=sha(p)))
assert len(scope['inputs'])>=10
sp=CONTROL/'scopes/product-v1-cli-build-01.json';put(sp,scope)
out=ROOT/'execution/product-v1/receipts/single-harness-20261104/cli-artifact-build-01';assert not out.exists();out.mkdir()
for name,p in [('scope.json',sp),('wrapper.py',wrapper),('independent-review.json',review)]: (out/name).write_bytes(p.read_bytes())
put(out/'ROOT-REVIEW.json',dict(decision='APPROVED_BUILD_ONLY',reviewer='codex:/root',wrapper_sha256=sha(wrapper),independent_review_sha256=sha(review),scope_sha256=sha(sp),source_head='c4029c0b57599e1aafed6d01ea4034b0cf465ccd',review='Read complete wrapper and existing helper behavior. Fixed clean WT; fresh CLI output/cache/profile. Offline Go closure, metadata/build only; no CLI application/Host/auth/model execution. f13 owned Job required.',formal_increment=0,model_requests=0))
print(json.dumps(dict(scope=str(sp),scope_sha256=sha(sp))))
