import argparse,hashlib,json,secrets,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
PREP=HERE/'product-v1-real-electron-tree-diagnostic-revision-02';OUT=HERE/'product-v1-tree-diagnostic-04-registration'
WT=ROOT/'.local/worktrees/product-v1-build-06-20261104';BUNDLE=WT/'.local/desktop-v1-build-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):assert not p.exists();p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists()
ap=argparse.ArgumentParser();ap.add_argument('--review',required=True);ap.add_argument('--review-sha',required=True);a=ap.parse_args();review=Path(a.review);assert sha(review)==a.review_sha
rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and not rv['pending_blockers']
manifest=BUNDLE/'development-manifest.json';m=read(manifest)
registration=ROOT/'execution/product-v1/receipts/single-harness-20261104/build06-scope/registration.json';reg=read(registration)
r=read(CONTROL/'runs/product-v1-build-06/RESULT.json')
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['stop_proved'] and not r['errors'] and not r['input_drift'] and r['terminate_job_attempts']==0
assert m['source']['head']==reg['main_head'] and m['source']['candidate_delta']==[]
for row in m['files']:
 p=BUNDLE/row['path'];assert p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
for ref,pin in reg['source_sha256'].items():assert sha(WT/ref)==pin
scope=read(PREP/'scope.template.json');scope.update(status='ROOT_APPROVED_REAL_RUN',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-tree-diagnostic-run-04'))
assert not Path(scope['run_root']).exists()
pins={row['path']:sha(WT/row['path']) for row in scope['source']['pins'] if row['path']!='execution/product-v1/contracts/harness.v1.interface.rev2.json'}
pins.update(reg['source_sha256'])
scope['source'].update(root=str(WT),head=reg['main_head'],pin_status='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE',pins=[dict(path=k,sha256=v) for k,v in pins.items()])
scope['bundle'].update(root=str(BUNDLE),manifest_sha256=sha(manifest),electron_sha256=sha(BUNDLE/'runtime/electron/electron.exe'),control_sha256=sha(BUNDLE/'apps/desktop/resources/control/researchos-control.exe'),source_binding_review='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE')
scope['selector_reference']=dict(scope['selector_binding'])
scope['selector_binding'].update(source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest))
scope['launcher'].update(path=str(BUNDLE/'launch-development.mjs'),sha256=sha(BUNDLE/'launch-development.mjs'))
assert scope['harness']['runner_sha256']==sha(PREP/'real-electron-flow.mjs')=='32bbc82cebcc1d6693588639bfc3dd81eb685c7ed4c856f512dc42aa61c4c40a'
assert scope['harness']['folder_helper_sha256']==sha(PREP/'choose-owned-folder.ps1')=='d3e37e333fa85fe57b6951292a458f73b08a2f801a2e9b997089599ec044ade4'
OUT.mkdir()
launch_contract=dict(schema='researchos.root-real-flow-launch-contract/1',decision='APPROVED_OWNED_DIALOG_TREE_METADATA_ONLY_CANCEL',reviewer='codex:/root',controller_sha256=sha(CONTROL/'owned_run.py'),independent_review_sha256=sha(review),source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest),runner_sha256=sha(PREP/'real-electron-flow.mjs'),helper_sha256=sha(PREP/'choose-owned-folder.ps1'),run_root=scope['run_root'],root_supervision='Existing f13 exact unnamed Job assigned and membership checked before Resume; original handles retained, no breakaway, bounded timeout and final accounting. Runner fields are not kernel proof.',task_budget=0,automatic_retry=0,payment_policy='Dedicated diagnostic has no capabilities/task/submit/model path; budget0.',directory_policy='Only owned dialog Tree metadata, then mandatory owned IDCANCEL. No TreeItem navigation, OK, workspace authorization or task.',auth_policy='Normal native account use by CLI; no manual credential/config reads or copies.',unknown_policy='No second submit/cancel mutation; retain exact task/request/run evidence and stop.',formal_increment=0,product_acceptance_increment=0)
contract=OUT/'ROOT-LAUNCH-CONTRACT.json';put(contract,launch_contract)
scope['root_supervision'].update(controller_sha256=launch_contract['controller_sha256'],launch_contract_sha256=sha(contract))
inner=OUT/'real-flow.scope.json';put(inner,scope)
outer=read(CONTROL/'scopes/product-v1-desktop-smoke-02.json')
outer.update(scope_id='product-v1-tree-diagnostic-04',argv=[str(PREP/'real-electron-flow.mjs'),'--execute','--scope',str(inner),'--scope-sha256',sha(inner)],cwd=str(PREP),timeout_seconds=360,max_raw_bytes=16*1024*1024)
files=[inner,contract,review,PREP/'real-electron-flow.mjs',PREP/'choose-owned-folder.ps1',PREP/'SDK_INVENTORY.json',manifest,BUNDLE/'launch-development.mjs',BUNDLE/'runtime/electron/electron.exe',BUNDLE/'apps/desktop/resources/control/researchos-control.exe',Path(scope['codex']['executable']),Path(scope['windows']['powershell']),ROOT/'execution/product-v1/contracts/harness.v1.interface.rev2.json']
outer['inputs']=[dict(path=str(p),sha256=sha(p)) for p in files]
sp=CONTROL/'scopes/product-v1-tree-diagnostic-04.json';put(sp,outer)
put(OUT/'REGISTRATION.json',dict(status='REGISTERED_NOT_EXECUTED',scope_sha256=sha(sp),inner_scope_sha256=sha(inner),source_head=reg['main_head'],bundle_manifest_sha256=sha(manifest),formal_increment=0,model_tasks_submitted=0))
archive=ROOT/'execution/product-v1/receipts/single-harness-20261104/tree-diagnostic-04';assert not archive.exists();archive.mkdir()
for name,p in [('outer.scope.json',sp),('inner.scope.json',inner),('ROOT-LAUNCH-CONTRACT.json',contract),('independent-controller-review.json',review),('REGISTRATION.json',OUT/'REGISTRATION.json')]: (archive/name).write_bytes(p.read_bytes())
print(json.dumps(dict(scope=str(sp),scope_sha256=sha(sp),new_run_root=scope['run_root'],task_budget=0)))
