import argparse,hashlib,json,secrets
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104';PREP=HERE/'product-v1-cli-same-host-caps-prepare-revision-03-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
p=argparse.ArgumentParser();p.add_argument('--review',required=True);p.add_argument('--review-sha',required=True);a=p.parse_args();review=Path(a.review);assert sha(review)==a.review_sha
rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and not rv['pending_blockers']
assert sha(PREP/'same-host-caps.mjs')=='834ce474f5f62bab79d7908395efec6dbdd57856b2448dd74d71205bdf8a109f'
assert sha(PREP/'MANIFEST.json')=='09d300b1859b966febfc61d50bb744b9fc357670130d64c07eb59c28ba04e9be'
scope=read(PREP/'scope.template.json');scope.update(status='ROOT_APPROVED_SINGLE_CAPS',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-cli-same-host-caps-run-02'));assert not Path(scope['run_root']).exists()
bundle=Path(scope['bundle']['root']);manifest=bundle/'development-manifest.json';assert sha(manifest)=='b3f62e359609b8cc698ddc4934e2f9e6cf2b3e1ddfb0a454ac315a70968a4f39'
for row in read(manifest)['files']:
 f=bundle/row['path'];assert f.stat().st_size==row['bytes'] and sha(f)==row['sha256']
out=HERE/'product-v1-cli-same-host-caps-02-registration';assert not out.exists();out.mkdir();inner=out/'inner.scope.json';put(inner,scope)
outer=read(CONTROL/'scopes/product-v1-desktop-smoke-03.json');outer.update(scope_id='product-v1-cli-same-host-caps-02',argv=[str(PREP/'same-host-caps.mjs'),'--scope',str(inner),'--scope-sha256',sha(inner)],cwd=str(PREP),timeout_seconds=180,max_raw_bytes=16*1024*1024)
files=[inner,review,PREP/'same-host-caps.mjs',PREP/'MANIFEST.json',HERE/'product-v1-real-electron-harness-prepare-revision-04/real-electron-flow.mjs',Path(scope['playwright']['inventory_path']),manifest,bundle/'launch-development.mjs',bundle/'runtime/electron/electron.exe',bundle/'apps/desktop/resources/control/researchos-control.exe',Path(scope['cli']['path'])]
outer['inputs']=[dict(path=str(f),sha256=sha(f)) for f in files]
sp=CONTROL/'scopes/product-v1-cli-same-host-caps-02.json';put(sp,outer)
rootreview=dict(decision='APPROVED_ONE_SAME_HOST_CAPS_QUERY_NO_TASK_MODEL',reviewer='codex:/root',source_head='71396f932d0ccc7035f3fdb4896e3c7ecc8f6343',independent_review_sha256=sha(review),wrapper_sha256=sha(PREP/'same-host-caps.mjs'),scope_sha256=sha(sp),review='Read complete wrapper, P2 no-raw-stream fix and new derivedSystemDrive/ownedElectroncwd diff with actual discovery producer DTO. Fixed[harness,caps] once, no picker/project/task/model, native credentials handled only by CLI, public discovery versus original Core identity before/after, bounded normal close and f13 original Job accounting required. Core cwd remains REPO; no independent pipePID/network interception claim.',task_submissions=0,model_requests=0,formal_increment=0)
put(out/'ROOT-REVIEW.json',rootreview)
archive=ROOT/'execution/product-v1/receipts/single-harness-20261104/cli-same-host-caps-02';assert not archive.exists();archive.mkdir()
for name,f in [('outer.scope.json',sp),('inner.scope.json',inner),('wrapper.mjs',PREP/'same-host-caps.mjs'),('independent-review.json',review),('ROOT-REVIEW.json',out/'ROOT-REVIEW.json')]:(archive/name).write_bytes(f.read_bytes())
print(json.dumps(dict(scope=str(sp),scope_sha256=sha(sp),new_run_root=scope['run_root'],task_budget=0,model_budget=0)))
