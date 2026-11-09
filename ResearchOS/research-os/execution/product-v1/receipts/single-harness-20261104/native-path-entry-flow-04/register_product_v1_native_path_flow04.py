import argparse,hashlib,json,secrets
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104'
WT=ROOT/'.local/worktrees/product-v1-build-07-20261104';BUNDLE=WT/'.local/desktop-v1-build-07'
OUT=HERE/'product-v1-native-path-entry-run-04-registration'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 assert not p.exists(),str(p)
 p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--manifest-sha',required=True);p.add_argument('--review',required=True);p.add_argument('--review-sha',required=True);a=p.parse_args()
PREP=Path(a.prepare).resolve();assert PREP.is_relative_to(HERE) and not OUT.exists()
manifest=PREP/'MANIFEST.json';assert sha(manifest)==a.manifest_sha
for row in read(manifest)['files']:assert sha(PREP/row['path'])==row['sha256']
review=Path(a.review);assert sha(review)==a.review_sha
rv=read(review);assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
assert rv['approved_revision']=='05' and Path(rv['source_root'])==PREP
for ref,digest in rv['source_sha256'].items():assert sha(PREP/ref)==digest
cp=read(ROOT/'execution/v2.4/checkpoint.json');assert cp['revision']==641 and cp['current_Main_HEAD']=='2b39fe3a6e8d69981a4079bb585086dca98b283e'
mf=BUNDLE/'development-manifest.json';assert sha(mf)=='ba4fbefa07e1ba9597ee54c894949edb5d33847e38b10d3f53ee8704d84fd6e7'
m=read(mf);reg=read(ROOT/'execution/product-v1/receipts/single-harness-20261104/build07-scope/registration.json')
r=read(CONTROL/'runs/product-v1-build-07/RESULT.json')
assert r['root_exit_code']==0 and r['stop_proved'] and not r['errors'] and not r['input_drift'] and r['terminate_job_attempts']==0
assert m['source']['head']==reg['main_head']==cp['current_Main_HEAD'] and m['source']['candidate_delta']==[]
for row in m['files']:assert sha(BUNDLE/row['path'])==row['sha256']
assert {f.relative_to(BUNDLE).as_posix() for f in BUNDLE.rglob('*') if f.is_file()}=={v['path'] for v in m['files']}|{'development-manifest.json'}
for ref,digest in reg['source_sha256'].items():assert sha(WT/ref)==digest
scope=read(PREP/'scope.template.json');scope.update(status='ROOT_APPROVED_REAL_RUN',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-native-path-entry-中文-run-04'))
assert not Path(scope['run_root']).exists() and scope['budget']['task_submissions']==scope['budget']['model_calls']==0
assert scope['source']['head']==cp['current_Main_HEAD'] and Path(scope['source']['root'])==WT
pins={row['path']:row['sha256'] for row in scope['source']['pins']};pins.update(reg['source_sha256'])
assert 'execution/product-v1/contracts/harness.v1.interface.rev2.json' not in pins
for ref,digest in pins.items():assert sha(WT/ref)==digest
scope['source']['pins']=[dict(path=k,sha256=v) for k,v in pins.items()]
assert scope['bundle']['manifest_sha256']==sha(mf) and Path(scope['bundle']['root'])==BUNDLE
assert sha(BUNDLE/'apps/desktop/resources/control/researchos-control.exe')==scope['bundle']['control_sha256']=='4e1c951b65ef325a8d9e842d0e21e7a05ad6b49b631db6030353ce0f28380cce'
assert scope['harness']['runner_sha256']==sha(PREP/'real-electron-flow.mjs')
assert scope['harness']['folder_helper_sha256']==sha(PREP/'choose-owned-folder.ps1')
selector=scope['native_picker']['validation_warning']['dismiss_selector'];evidence=Path(selector['evidence_path'])
assert selector['expected_control_id']==2 and selector['expected_button_count']==1 and selector['message_box_result_is_control_id'] is False
assert evidence==HERE/'product-v1-native-path-entry-中文-run-03/receipts/native-folder-automation.json'
assert sha(evidence)==selector['evidence_sha256']=='392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423'
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
OUT.mkdir()
contract=dict(schema='researchos.root-real-flow-launch-contract/1',decision='APPROVED_ZERO_MODEL_NATIVE_INVALID_VALID_PATH_FLOW',reviewer='codex:/root',controller_sha256=sha(CONTROL/'owned_run.py'),independent_review_sha256=sha(review),source_head=reg['main_head'],bundle_manifest_sha256=sha(mf),runner_sha256=scope['harness']['runner_sha256'],helper_sha256=scope['harness']['folder_helper_sha256'],run_root=scope['run_root'],task_budget=0,model_budget=0,automatic_retry=0,
 root_supervision='Exact f13 original unnamed Job assigned and membership checked before Resume; original handles retained; no breakaway; bounded outer deadline; final accounting. Runner fields are not kernel proof.',
 directory_policy='Only new own fixture: real chooser invalid input, exact owned warning, retain chooser, valid input and real Shell confirm. Typed text and chooser closure are not authority; require actual Main ACTIVE exact fixture binding. No arbitrary path API.',
 payment_policy='No capability/task/submit/model path in this zero-budget controller.',auth_policy='Normal native platform account; no manual auth/config/credential reads/copies.',unknown_policy='No repeated post or input after uncertain action. Retain actual phase and known authorization; Root original Job accounts any pending process.',formal_increment=0,product_acceptance_increment=0)
cf=OUT/'ROOT-LAUNCH-CONTRACT.json';put(cf,contract)
scope['root_supervision'].update(controller_sha256=contract['controller_sha256'],launch_contract_sha256=sha(cf))
inner=OUT/'real-flow.scope.json';put(inner,scope)
outer=read(CONTROL/'scopes/product-v1-desktop-smoke-02.json')
outer.update(scope_id='product-v1-native-path-entry-flow-04',argv=[str(PREP/'real-electron-flow.mjs'),'--execute','--scope',str(inner),'--scope-sha256',sha(inner)],cwd=str(PREP),timeout_seconds=360,max_raw_bytes=16*1024*1024)
files=[inner,cf,review,manifest,PREP/'real-electron-flow.mjs',PREP/'choose-owned-folder.ps1',Path(scope['playwright']['inventory_path']),mf,Path(scope['launcher']['path']),BUNDLE/'runtime/electron/electron.exe',BUNDLE/'apps/desktop/resources/control/researchos-control.exe',Path(scope['codex']['executable']),Path(scope['windows']['powershell']),Path(scope['contract_source']['path']),evidence]
outer['inputs']=[dict(path=str(f),sha256=sha(f)) for f in files]
sp=CONTROL/'scopes/product-v1-native-path-entry-flow-04.json';put(sp,outer)
registration=dict(status='REGISTERED_NOT_EXECUTED',scope_path=str(sp),scope_sha256=sha(sp),inner_scope_sha256=sha(inner),source_head=reg['main_head'],bundle_manifest_sha256=sha(mf),prepare_manifest_sha256=sha(manifest),task_budget=0,model_budget=0,formal_increment=0,product_acceptance_increment=0)
put(OUT/'REGISTRATION.json',registration)
archive=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-path-entry-flow-04';assert not archive.exists();archive.mkdir()
for name,f in [('outer.scope.json',sp),('inner.scope.json',inner),('ROOT-LAUNCH-CONTRACT.json',cf),('independent-controller-review.json',review),('REGISTRATION.json',OUT/'REGISTRATION.json'),('register_product_v1_native_path_flow04.py',Path(__file__))]:(archive/name).write_bytes(f.read_bytes())
print(json.dumps(registration))
