import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104'
PREP=HERE/'product-v1-mxc-availability-prepare-rev03-20261105-d83a';OUT=HERE/'product-v1-mxc-availability-registration03';ID='mxc_availability_20261105_d83a'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists(),str(p)
 p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists() and not (CONTROL/'runs'/ID).exists()
review=BASE/'mxc-resource-check/preparation/product-v1-mxc-availability-security-review-rev03/REVIEW.json';assert sha(review)=='5c050272594be2815b4bbb17a7d94a18be431e49c8801af304cb2b5fbc273d34';rv=read(review)
assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
mf=PREP/'MANIFEST.json';assert sha(mf)=='6e0b74a1d62256c8c040ca5732f2ac09887effe784eca8f5dbcc5f8df57c7439'
for row in read(mf)['files']:assert sha(PREP/row['name'])==row['sha256']
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
inner=read(PREP/'mxc.scope.template.json');assert inner['scope_id']==ID and inner['model_tasks']==0 and inner['native_invocations']==1 and inner['automatic_retries']==0
assert inner['argv']==['-c','windows.sandbox=mxc','sandbox','--include-managed-config','--permission-profile',':workspace','--','C:/Windows/System32/cmd.exe','/d','/c','echo','MXC_OK']
inner['state']='ROOT_REVIEWED_EXACT_COMMAND';inner['independent_review_sha256']=sha(review);inner['purpose']='LOCAL_STARTUP_AVAILABILITY_ONLY_NOT_PERMISSION_QUALIFICATION_OR_MODEL'
ip=PREP/'mxc.scope.json';assert not ip.exists();put(ip,inner)
outer=read(PREP/'f13.scope.template.json');outer['authorization']='ROOT_REVIEWED_EXACT_COMMAND';outer['argv']=[str(PREP/'mxc-echo.mjs'),str(ip),sha(ip)]
assert outer['scope_id']==ID and outer['timeout_seconds']==45 and outer['process_limit']==16 and outer['memory_mib']==2048
paths=[Path(v['path']) for v in outer['inputs']]+[review,mf,Path(__file__)];outer['inputs']=[dict(path=str(p),sha256=sha(p)) for p in paths]
sp=CONTROL/'scopes'/f'{ID}.json';assert not sp.exists();put(sp,outer);OUT.mkdir()
registration=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),inner_scope_path=str(ip),inner_scope_sha256=sha(ip),source_review_sha256=sha(review),model_tasks=0,local_native_echo_invocations=1,automatic_retry=0,product_profile_unchanged=True,os_setup_authorized=False,resource_ready=False,availability_only=True,formal_increment=0,product_increment=0)
put(OUT/'REGISTRATION.json',registration)
target=BASE/'mxc-resource-check/registered-03';assert not target.exists();target.mkdir()
for name,p in [('inner.scope.json',ip),('outer.scope.json',sp),('REGISTRATION.json',OUT/'REGISTRATION.json'),('register_product_v1_mxc_echo03.py',Path(__file__))]:(target/name).write_bytes(p.read_bytes())
print(json.dumps(registration))
