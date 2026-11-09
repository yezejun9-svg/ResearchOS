import hashlib,json,secrets
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';CONTROL=HERE/'product-v1-owned-verification-20261104'
PREP=HERE/'product-v1-real-electron-single-task-prepare-04';OUT=HERE/'product-v1-single-task-flow-01-registration';WT=ROOT/'.local/worktrees/product-v1-build-07-20261104';BUNDLE=WT/'.local/desktop-v1-build-07'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists(),str(p)
 p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert not OUT.exists()
cp=read(ROOT/'execution/v2.4/checkpoint.json');assert cp['revision']==643 and cp['current_Main_HEAD']=='2b39fe3a6e8d69981a4079bb585086dca98b283e'
progress=read(BASE/'progress-cp643/RESUME.json');assert progress['real_model_requests']==0 and progress['historical_records']==len(cp['failure_counters'])==2544
freeze=PREP/'FROZEN.json';assert sha(freeze)=='297cb3a7e8f0fb5e1af8fa5bcce31d15ee5077fcaa48607f4c51e656ce5c6111';frozen=read(freeze)
for ref,digest in frozen['files'].items():assert sha(PREP/ref)==digest
review=BASE/'one-task-controller04/reviews/REVIEW.json';assert sha(review)=='509372d819c522feb214ce35352d64d59fcf3c1def95bb68060736e86167095d';rv=read(review)
assert rv['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and rv['formal_increment']==0 and not rv['pending_blockers']
for ref in ['FROZEN.json','real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json']:assert sha(PREP/ref)==rv['source_sha256'][ref]
pre=progress['prerequisite'];native=Path(pre['runner_result_path']);job=Path(pre['root_result_path']);nr=Path(pre['independent_actual_review_path']);post=HERE/'product-v1-build07-post-native-flow04-root-readback.json'
assert sha(native)==pre['runner_result_sha256']=='0a81b047fa46464ee3f97f0613ba44b4f885a77b8f9a865fcb0ed6ee77535548'
assert sha(job)==pre['root_result_sha256']=='16dfca2a599409e15fa0099ddb61f660292a061d7010430320b2696cacf43d72'
assert sha(nr)==pre['independent_actual_review_sha256']=='1cec87e65f97025a88122b33e5f6d7f7c4e84652e0d39703727645ee5408304f'
assert read(nr)['decision']=='VERIFIED_REAL_NATIVE_PATH_ENTRY_AND_MAIN_BINDING_FUNCTIONAL_OBSERVATION_ONLY'
n=read(native);j=read(job);assert n['status']=='REAL_NATIVE_PATH_ENTRY_AND_PROJECT_BINDING_OBSERVED_NOT_PRODUCT_ACCEPTED' and n['native_workspace_authorization']=='REAL_MAIN_ACTIVE_PROJECT_WORKSPACE_BINDING_OBSERVED' and n['actual_dom_submit_attempts']==0 and n['close']['app_close_resolved']
assert j['status']=='COMPLETED_OWNED_JOB_STOPPED' and j['root_exit_code']==0 and j['stop_proved'] and j['job_active_zero'] and j['terminate_job_attempts']==0 and not j['errors'] and not j['input_drift']
assert sha(post)==pre['postbundle_sha256']=='9585660b85246cc9dbf92dc024acd40d00e4a90d18cb3876b59ad17891324523'
manifest=BUNDLE/'development-manifest.json';assert sha(manifest)=='ba4fbefa07e1ba9597ee54c894949edb5d33847e38b10d3f53ee8704d84fd6e7';m=read(manifest)
assert m['source']['head']==cp['current_Main_HEAD'] and not m['source']['candidate_delta']
for row in m['files']:assert sha(BUNDLE/row['path'])==row['sha256']
assert {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob('*') if p.is_file()}=={row['path'] for row in m['files']}|{'development-manifest.json'}
reg=read(BASE/'build07-scope/registration.json');scope=read(PREP/'scope.template.json')
scope.update(status='ROOT_APPROVED_REAL_RUN',scope_nonce=secrets.token_hex(24),run_root=str(HERE/'product-v1-single-task-中文-run-01'),project_display_name='ResearchOS one real readonly Harness task')
assert not Path(scope['run_root']).exists() and scope['budget']['task_submissions']==scope['budget']['model_calls']==1 and scope['budget']['automatic_retries']==0
pins={row['path']:row['sha256'] for row in scope['source']['pins']};pins.update(reg['source_sha256'])
assert 'execution/product-v1/contracts/harness.v1.interface.rev2.json' not in pins
for ref,digest in pins.items():assert sha(WT/ref)==digest
scope['source']['pins']=[dict(path=k,sha256=v) for k,v in pins.items()]
assert Path(scope['source']['root'])==WT and scope['source']['head']==cp['current_Main_HEAD']
scope['harness'].update(runner_sha256=sha(PREP/'real-electron-flow.mjs'),folder_helper_sha256=sha(PREP/'choose-owned-folder.ps1'))
scope['prerequisite']['native_zero_flow'].update(runner_result_path=str(native),runner_result_sha256=sha(native),root_result_path=str(job),root_result_sha256=sha(job),independent_actual_review_path=str(nr),independent_actual_review_sha256=sha(nr),postbundle_path=str(post),postbundle_sha256=sha(post))
selector=scope['native_picker']['validation_warning']['dismiss_selector'];evidence=Path(selector['evidence_path']);assert sha(evidence)==selector['evidence_sha256']=='392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423' and selector['expected_control_id']==2
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
OUT.mkdir();contract=dict(schema='researchos.root-real-flow-launch-contract/1',decision='APPROVED_ONE_FRESH_READONLY_NATIVE_HARNESS_TASK',reviewer='codex:/root',controller_sha256=sha(CONTROL/'owned_run.py'),source_review_sha256=sha(review),native_actual_review_sha256=sha(nr),source_head=cp['current_Main_HEAD'],bundle_manifest_sha256=sha(manifest),runner_sha256=scope['harness']['runner_sha256'],helper_sha256=scope['harness']['folder_helper_sha256'],run_root=scope['run_root'],task_budget=1,native_harness_invocations=1,internal_model_api_calls='NOT_MEASURED',automatic_retry=0,
 root_supervision='Exact f13 original unnamed Job assigned and membership checked before Resume; original handles retained; no breakaway; final accounting/activezero required.',
 account_policy='Actual typed Host caps LOGGED_IN and kind chatgpt immediately before one normal DOM submit; no API/paid/login fallback or manual auth/config/credential reads/copies.',
 task_policy='Only fresh own readonly canary fixture; original stable request/task/run identities across all snapshots/events/reconciliation; no new ID or resubmit after UNKNOWN. Require actual result/events canary and unchanged fixture hashes.',
 native_policy='Real Shell invalid/valid UI only; exact owned source-pinned warning sole actualButtonID2; actual Main ACTIVE same fixture binding. No text-as-grant, arbitrary path API or activation/keyboard fallback.',formal_increment=0,product_acceptance_increment=0)
cf=OUT/'ROOT-LAUNCH-CONTRACT.json';put(cf,contract);scope['root_supervision'].update(controller_sha256=contract['controller_sha256'],launch_contract_sha256=sha(cf));inner=OUT/'real-flow.scope.json';put(inner,scope)
outer=read(CONTROL/'scopes/product-v1-desktop-smoke-02.json');outer.update(scope_id='product-v1-single-task-flow-01',argv=[str(PREP/'real-electron-flow.mjs'),'--execute','--scope',str(inner),'--scope-sha256',sha(inner)],cwd=str(PREP),timeout_seconds=scope['root_supervision']['outer_deadline_ms']//1000,max_raw_bytes=16*1024*1024)
files=[inner,cf,review,freeze,PREP/'real-electron-flow.mjs',PREP/'choose-owned-folder.ps1',Path(scope['playwright']['inventory_path']),manifest,Path(scope['launcher']['path']),BUNDLE/'runtime/electron/electron.exe',BUNDLE/'apps/desktop/resources/control/researchos-control.exe',Path(scope['codex']['executable']),Path(scope['windows']['powershell']),Path(scope['contract_path']),native,job,nr,post,evidence]
outer['inputs']=[dict(path=str(p),sha256=sha(p)) for p in files];sp=CONTROL/'scopes/product-v1-single-task-flow-01.json';put(sp,outer)
registration=dict(status='REGISTERED_NOT_EXECUTED',scope_path=str(sp),scope_sha256=sha(sp),inner_scope_sha256=sha(inner),source_head=cp['current_Main_HEAD'],bundle_manifest_sha256=sha(manifest),task_budget=1,prior_model_tasks_submitted=0,native_harness_invocation_budget=1,internal_model_api_calls='NOT_MEASURED',formal_increment=0,product_acceptance_increment=0);put(OUT/'REGISTRATION.json',registration)
archive=BASE/'single-task-flow-01';assert not archive.exists();archive.mkdir()
for name,p in [('outer.scope.json',sp),('inner.scope.json',inner),('ROOT-LAUNCH-CONTRACT.json',cf),('independent-controller-review.json',review),('independent-native-review.json',nr),('REGISTRATION.json',OUT/'REGISTRATION.json'),('register_product_v1_single_task_flow01.py',Path(__file__))]:(archive/name).write_bytes(p.read_bytes())
print(json.dumps(registration))
