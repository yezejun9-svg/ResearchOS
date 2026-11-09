import hashlib,json,stat
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
CONTROL=HERE/'product-v1-owned-verification-20261104'
ID='product-v1-native-synthetic-flow-01'
OUT=HERE/'product-v1-native-synthetic-flow01-cleanup-postcheck.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists()
result_path=CONTROL/'runs'/ID/'RESULT.json';r=read(result_path)
assert r['scope_id']==ID and r['scope_sha256']=='181da91b8024cc2d222092950d16705945ed77b667259ba8f04297cd9da3045c'
assert r['status']=='TIMED_OUT_STOPPED' and r['timed_out'] and r['stop_proved'] and r['job_active_zero'] and r['root_signaled'] and r['terminate_job_attempts']==1 and r['terminate_original_root_attempts']==0 and r['errors']==[] and not r['input_drift'] and not r['raw_limit_exceeded']
scope_path=CONTROL/'scopes'/(ID+'.json');assert sha(scope_path)==r['scope_sha256']
scope=read(scope_path)
for item in scope['inputs']:assert sha(Path(item['path']))==item['sha256'],item['path']
for row in r['raw']:
 p=result_path.parent/row['file'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
registration=read(HERE/'product-v1-native-synthetic-flow-01-registration/REGISTRATION.json')
inner=read(Path(registration['inner_scope_path']));run=Path(inner['run_root']);receipts=run/'receipts'
observed=read(receipts/'result.json');task=read(receipts/'final-task.json');events=read(receipts/'events.json')
assert observed['actual_dom_submit_attempts']==1 and task['terminal'] and task['status']=='FAILED' and task['result'] is None
assert task['task_ref']['task_id']=='c9fc3e4dc1ea5d34a0ca003a983b43c6' and task['run']=={'run_id':'a46af22fb058915f9f7119b2d7d73f8f','epoch':'1'}
assert not any(e['kind']=='ASSISTANT_MESSAGE' for e in events)
bundle=Path(inner['bundle']['root']);manifest=read(bundle/'development-manifest.json')
assert sha(bundle/'development-manifest.json')=='5d9277b3d7be35f8577325859c2033d612dbad0b6077902964be15637533ad85'
for row in manifest['files']:assert sha(bundle/row['path'])==row['sha256']
assert {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}=={row['path'] for row in manifest['files']}|{'development-manifest.json'}
fixture=HERE/'product-v1-native-qualification-中文-root-01';source=fixture/'S'
prepared=read(HERE/'product-v1-first-native-fixture-canaries-preparation.json')
assert {p.name for p in source.iterdir()}==set(prepared['exact_initial_inventory'])
for name,row in prepared['exact_initial_inventory'].items():assert sha(source/name)==row['sha256']
fixed_receipt=fixture/'receipts'/(hashlib.sha256((task['run']['run_id']+'/'+task['run']['epoch']).encode()).hexdigest()+'.json')
assert not fixed_receipt.exists() and not fixed_receipt.parent.exists()
diagnostic=HERE/'product-v1-native-synthetic-flow01-home-diagnostic/REVIEW.json'
assert sha(diagnostic)=='a5c0bd2a3910646cef88f373fc836b4bd43328402056d05935b4ddfed24a1ae0'
out=dict(status='ORIGINAL_OWNED_JOB_STOPPED_FORCE_TIMEOUT_NOT_NORMAL_APP_CLOSE',at=datetime.now(timezone.utc).isoformat(),scope_id=ID,scope_sha256=r['scope_sha256'],original_result_path=str(result_path),original_result_sha256=sha(result_path),original_job_stop_proved=True,job_active_processes=0,job_cumulative_processes=r['job_total_processes'],root_signaled=True,original_root_pid=r['root_pid'],original_creation_filetime=r['creation_filetime'],original_job_termination_attempts=1,manual_pid_or_name_kills=0,elapsed_seconds=r['elapsed_seconds'],normal_app_close_confirmed=False,scope_replay_allowed=False,dom_submit_attempts=1,task_ref=task['task_ref'],run=task['run'],request_id=task['request_id'],task_status='FAILED',assistant_message_events=0,qualification_current_fixed_receipt=str(fixed_receipt),qualification_receipt_exists=False,qualification_receipt_parent_exists=False,preparation_reason='SOURCE_PROVEN_SAME_HOME_SEPARATOR_MISMATCH_BEFORE_PRIVATE_DIRECTORY_OR_QUALIFICATION_LAUNCH',preparation_reason_evidence=str(diagnostic),preparation_reason_evidence_sha256=sha(diagnostic),reason_claim_limit='Actual Task DTO is generic; concrete guard mismatch is established by exact executed-source and recorded launch environment, not by a missing receipt alone or a runtime guard trace.',model_delegation='PRODUCT_REPORTED_NONE; SOURCE_CHAIN_RETURNS_BEFORE_QUALIFICATION_LAUNCH',internal_api_calls='NOT_MEASURED',bundle_files_postchecked=len(manifest['files']),bundle_drift=False,source_canaries_unchanged=True,formal_increment=0,product_increment=0)
OUT.write_bytes((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(postcheck=str(OUT),sha256=sha(OUT),job_active_processes=0,original_job_termination_attempts=1,normal_app_close=False,task_status='FAILED',bundle_files=len(manifest['files']),replay_allowed=False)))
