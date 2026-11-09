import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104'
PREP=HERE/'product-v1-mxc-availability-prepare-rev05-20261105-f602';OUT=HERE/'product-v1-mxc-availability-registration05';ID='mxc_availability_20261105_f602'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists(),str(p)
 p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists() and not (CONTROL/'runs'/ID).exists()
cp=read(ROOT/'execution/v2.4/checkpoint.json');assert cp['revision']==657 and cp['current_Main_HEAD']=='5956907bd640d2d4f4abcb583aeb2520883e97c8'
prior_id='mxc_availability_20261105_e91c';prior=CONTROL/'runs'/prior_id
assert sorted(p.name for p in (CONTROL/'runs').iterdir() if p.is_dir() and p.name.startswith('mxc_availability_'))==[prior_id]
assert sha(prior/'RESULT.json')=='6903454745a9ee821497e9a2f172fd00a736a07165316800a0129a28ff8442fd'
pr=read(prior/'RESULT.json');assert pr['root_exit_code']==1 and pr['stop_proved'] and pr['job_active_zero'] and pr['terminate_job_attempts']==0
review=BASE/'mxc-resource-check/preparation-05/product-v1-mxc-availability-security-review-rev05/REVIEW.json';assert sha(review)=='9a0f1f8cf60eaaeaa330ad25bc5c85d99519530945f6319d4dfaa831f5025d79';rv=read(review)
assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
mf=PREP/'MANIFEST.json';assert sha(mf)=='f104973eb1ccd5f4009bb6424553f2ec683df2bb0022e8254ca36fbadd15285e'
for row in read(mf)['files']:assert sha(PREP/row['name'])==row['sha256']
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
inner=read(PREP/'mxc.scope.template.json');assert inner['scope_id']==ID and inner['model_tasks']==0 and inner['native_invocations']==1 and inner['automatic_retries']==0
assert inner['diagnostic_origin']=='mxc_availability_20261105_e91c:local-command-syntax-error' and inner['diagnostic_attempt']==2
assert inner['argv']==['-c','windows.sandbox=mxc','sandbox','--include-managed-config','--permission-profile',':workspace','--','C:\\Windows\\System32\\cmd.exe','/d','/c','echo','MXC_OK']
inner['state']='ROOT_REVIEWED_EXACT_COMMAND';inner['independent_review_sha256']=sha(review);inner['purpose']='LOCAL_STARTUP_AVAILABILITY_ONLY_NOT_PERMISSION_QUALIFICATION_OR_MODEL'
ip=PREP/'mxc.scope.json';assert not ip.exists();put(ip,inner)
outer=read(PREP/'f13.scope.template.json');outer['authorization']='ROOT_REVIEWED_EXACT_COMMAND';outer['argv']=[str(PREP/'mxc-echo.mjs'),str(ip),sha(ip)]
assert outer['scope_id']==ID and outer['timeout_seconds']==45 and outer['process_limit']==16 and outer['memory_mib']==2048
paths=[Path(v['path']) for v in outer['inputs']]+[review,mf,Path(__file__)];outer['inputs']=[dict(path=str(p),sha256=sha(p)) for p in paths]
sp=CONTROL/'scopes'/f'{ID}.json';assert not sp.exists();put(sp,outer);OUT.mkdir()
registration=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),inner_scope_path=str(ip),inner_scope_sha256=sha(ip),source_review_sha256=sha(review),model_tasks=0,local_native_echo_invocations=1,automatic_retry=0,product_profile_unchanged=True,os_setup_authorized=False,resource_ready=False,availability_only=True,formal_increment=0,product_increment=0)
registration.update(diagnostic_origin=inner['diagnostic_origin'],diagnostic_attempt=2,prior_consumed_scope=prior_id,prior_failure_result_sha256=sha(prior/'RESULT.json'),prior_failure_retained=True,prior_local_native_invocations=1,total_planned_local_native_invocations=2,max_local_native_invocations=2,change='Only target CMD executable token path separators; no model, permission, environment or configuration change')
put(OUT/'REGISTRATION.json',registration)
target=BASE/'mxc-resource-check/registered-05';assert not target.exists();target.mkdir()
for name,p in [('inner.scope.json',ip),('outer.scope.json',sp),('REGISTRATION.json',OUT/'REGISTRATION.json'),('register_product_v1_mxc_echo05.py',Path(__file__))]:(target/name).write_bytes(p.read_bytes())
print(json.dumps(registration))
