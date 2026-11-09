import hashlib,json,secrets,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
PREP=HERE/'product-v1-real-electron-harness-prepare-revision-03';OUT=HERE/'product-v1-real-electron-run-01-registration'
WT=ROOT/'.local/worktrees/product-v1-build-04-20261104';BUNDLE=WT/'.local/desktop-v1-build-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists()
review=HERE/'product-v1-real-electron-independent-review-20261104/revision03/review.json'
assert sha(review)=='97538836b6104c82c076d9d189eb0b4a485cebeab8d86f67e2a17b0364d582cf'
rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and not rv['pending_blockers']
manifest=BUNDLE/'development-manifest.json';m=read(manifest)
registration=ROOT/'execution/product-v1/receipts/single-harness-20261104/build04-scope/registration.json';reg=read(registration)
r=read(CONTROL/'runs/product-v1-build-04/RESULT.json')
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['stop_proved'] and not r['errors'] and not r['input_drift'] and r['terminate_job_attempts']==0
assert m['source']['head']==reg['main_head'] and m['source']['candidate_delta']==[]
for row in m['files']:
 p=BUNDLE/row['path'];assert p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
for ref,pin in reg['source_sha256'].items():assert sha(WT/ref)==pin
scope=read(PREP/'scope.template.json');scope.update(status='ROOT_APPROVED_REAL_RUN',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-real-electron-run-01'))
assert not Path(scope['run_root']).exists()
pins={row['path']:sha(WT/row['path']) for row in scope['source']['pins'] if row['path']!='execution/product-v1/contracts/harness.v1.interface.rev2.json'}
pins.update(reg['source_sha256'])
scope['source'].update(root=str(WT),head=reg['main_head'],pin_status='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE',pins=[dict(path=k,sha256=v) for k,v in pins.items()])
scope['bundle'].update(root=str(BUNDLE),manifest_sha256=sha(manifest),electron_sha256=sha(BUNDLE/'runtime/electron/electron.exe'),control_sha256=sha(BUNDLE/'apps/desktop/resources/control/researchos-control.exe'),source_binding_review='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE')
scope['selector_reference']=dict(scope['selector_binding'])
scope['selector_binding'].update(source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest))
scope['launcher'].update(path=str(BUNDLE/'launch-development.mjs'),sha256=sha(BUNDLE/'launch-development.mjs'))
assert scope['harness']['runner_sha256']==sha(PREP/'real-electron-flow.mjs')=='68458e0ff59d091d2481356f19bec7d557a3dc9924ee3f91cc8c47e77b1d450b'
assert scope['harness']['folder_helper_sha256']==sha(PREP/'choose-owned-folder.ps1')=='b5a826fab09c149f8affce7385c4d45efeb5ddc124a438fbb0677ee3f33bc38e'
OUT.mkdir()
launch_contract=dict(schema='researchos.root-real-flow-launch-contract/1',decision='APPROVED_ONE_FRESH_REAL_READONLY_GUI_TASK',reviewer='codex:/root',controller_sha256=sha(CONTROL/'owned_run.py'),independent_review_sha256=sha(review),source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest),runner_sha256=sha(PREP/'real-electron-flow.mjs'),helper_sha256=sha(PREP/'choose-owned-folder.ps1'),run_root=scope['run_root'],root_supervision='Existing f13 exact unnamed Job assigned and membership checked before Resume; original handles retained, no breakaway, bounded timeout and final accounting. Runner fields are not kernel proof.',task_budget=1,automatic_retry=0,payment_policy='Actual capabilities must report LOGGED_IN+chatgpt immediately before sole DOM submit. No API paid/login fallback.',directory_policy='Real owned Shell UIAutomation only; reliable absolute path proof or normal owned cancel, never fake selection.',auth_policy='Normal native account use by CLI; no manual credential/config reads or copies.',unknown_policy='No second submit/cancel mutation; retain exact task/request/run evidence and stop.',formal_increment=0,product_acceptance_increment=0)
contract=OUT/'ROOT-LAUNCH-CONTRACT.json';put(contract,launch_contract)
scope['root_supervision'].update(controller_sha256=launch_contract['controller_sha256'],launch_contract_sha256=sha(contract))
inner=OUT/'real-flow.scope.json';put(inner,scope)
outer=read(CONTROL/'scopes/product-v1-desktop-smoke-02.json')
outer.update(scope_id='product-v1-real-electron-flow-01',argv=[str(PREP/'real-electron-flow.mjs'),'--execute','--scope',str(inner),'--scope-sha256',sha(inner)],cwd=str(PREP),timeout_seconds=360,max_raw_bytes=16*1024*1024)
files=[inner,contract,review,PREP/'real-electron-flow.mjs',PREP/'choose-owned-folder.ps1',PREP/'SDK_INVENTORY.json',manifest,BUNDLE/'launch-development.mjs',BUNDLE/'runtime/electron/electron.exe',BUNDLE/'apps/desktop/resources/control/researchos-control.exe',Path(scope['codex']['executable']),Path(scope['windows']['powershell']),ROOT/'execution/product-v1/contracts/harness.v1.interface.rev2.json']
outer['inputs']=[dict(path=str(p),sha256=sha(p)) for p in files]
sp=CONTROL/'scopes/product-v1-real-electron-flow-01.json';put(sp,outer)
put(OUT/'REGISTRATION.json',dict(status='REGISTERED_NOT_EXECUTED',scope_sha256=sha(sp),inner_scope_sha256=sha(inner),source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest),formal_increment=0,model_tasks_submitted=0))
archive=ROOT/'execution/product-v1/receipts/single-harness-20261104/real-electron-flow-01';assert not archive.exists();archive.mkdir()
for name,p in [('outer.scope.json',sp),('inner.scope.json',inner),('ROOT-LAUNCH-CONTRACT.json',contract),('independent-controller-review.json',review),('REGISTRATION.json',OUT/'REGISTRATION.json')]: (archive/name).write_bytes(p.read_bytes())
print(json.dumps(dict(scope=str(sp),scope_sha256=sha(sp),new_run_root=scope['run_root'],task_budget=1)))
