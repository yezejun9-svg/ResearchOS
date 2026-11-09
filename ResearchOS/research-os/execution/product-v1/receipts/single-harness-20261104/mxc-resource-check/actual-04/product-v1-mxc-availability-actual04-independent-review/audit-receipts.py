import hashlib,json,pathlib,shutil
BASE=pathlib.Path(r'C:\Users\yqyyds\Documents\Codex\2026-11-04\task')
OUT=BASE/'product-v1-mxc-availability-actual04-independent-review'
RUN=BASE/'product-v1-owned-verification-20261104/runs/mxc_availability_20261105_e91c'
PREP=BASE/'product-v1-mxc-availability-prepare-rev04-20261105-e91c'
REG=BASE/'product-v1-mxc-availability-registration04/REGISTRATION.json'
SCOPE=BASE/'product-v1-owned-verification-20261104/scopes/mxc_availability_20261105_e91c.json'
INNER=PREP/'mxc.scope.json'
SOURCE=BASE/'product-v1-mxc-availability-security-review-rev04/REVIEW.json'
def raw(p): return pathlib.Path(p).read_bytes()
def sha(p): return hashlib.sha256(raw(p)).hexdigest()
def obj(p): return json.loads(raw(p))
def write(p,v): pathlib.Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(p):return str(p).replace('\\','/').lower()
outer=obj(SCOPE);inner=obj(INNER);reg=obj(REG);job=obj(RUN/'RESULT.json');native=obj(RUN/'mxc/RESULT.json');launch=obj(RUN/'mxc/launch-plan.json')
outer_sha='32ef862e06e3664ab2354ea1508c2ba4885cfd70e63c41d80e97f6fb20c1d466'
inner_sha='51132f2e7b3ec9a9be82b881b7f5db383ed4f41a70054e6af0bccdf514785810'
assert sha(SCOPE)==reg['scope_sha256']==job['scope_sha256']==outer_sha
assert sha(INNER)==reg['inner_scope_sha256']==outer['argv'][2]==launch['scope_sha256']==inner_sha
assert sha(SOURCE)==reg['source_review_sha256']==inner['independent_review_sha256']=='650d24d091a86aa52b6c9779e3f7aff9fcf24dc58ded095af5b012aabd999025'
assert outer['authorization']==inner['state']=='ROOT_REVIEWED_EXACT_COMMAND'
assert outer['scope_id']==inner['scope_id']==job['scope_id']=='mxc_availability_20261105_e91c'
assert obj(RUN/'CONSUMED.json')['scope_sha256']==outer_sha
consumed=obj(RUN/'mxc/CONSUMED.json')
assert consumed['scope_sha256']==inner_sha and consumed['invocation_budget_consumed']==1
assert inner['argv']==launch['argv']==obj(PREP/'mxc.scope.template.json')['argv']
assert len(inner['argv'])==12 and norm(inner['executable'])==norm(launch['executable'])
assert norm(launch['cwd'])==norm(RUN/'mxc/cwd')
assert inner['model_tasks']==native['model_tasks']==0
assert inner['native_invocations']==1 and inner['automatic_retries']==0
assert native['automatic_retry'] is False and job['automatic_retry'] is False
assert outer['timeout_seconds']==45 and outer['cleanup_seconds']==5 and outer['process_limit']==16 and outer['memory_mib']==2048
assert inner['timeout_ms']==35000 and inner['stream_limit_bytes']==1048576 and inner['retained_prefix_bytes']==65536
assert job['status']=='CHILD_NONZERO_STOPPED' and job['root_exit_code']==1 and job['job_total_processes']==7
assert all(job[k] is True for k in ['job_assigned','resumed','root_signaled','job_active_zero','stop_proved'])
assert all(job[k] is False for k in ['timed_out','raw_limit_exceeded','input_drift'])
assert job['terminate_job_attempts']==job['terminate_original_root_attempts']==0 and job['errors']==[]
assert native['status']=='FAILED_OR_UNKNOWN_NO_RETRY' and native['exit_code']==1
assert native['spawn_error'] is None and native['exit_signal'] is None and native['observation_errors']==[]
assert all(native[k] is False for k in ['exact_echo','timed_out','input_drift','resource_ready','product_can_submit','automatic_retry'])
assert native['child_close_observed'] is True
for e in job['raw']:
 p=RUN/e['file'];assert len(raw(p))==e['bytes'] and sha(p)==e['sha256']
assert obj(RUN/'stdout.raw')=={'status':'FAILED_OR_UNKNOWN_NO_RETRY','resource_ready':False,'model_tasks':0}
for stream in native['streams']:
 name=stream['stream'];p=RUN/'mxc'/f'{name}.prefix.bin'
 assert obj(RUN/'mxc'/f'{name}.progress.json')==stream
 assert stream['stream_complete'] and stream['stream_end_observed'] and stream['child_close_observed']
 assert stream['errors']==[] and not stream['limit_reached'] and not stream['persistence_failed']
 assert len(raw(p))==stream['ingested_bytes']==stream['delivered_bytes']==stream['durable_prefix_bytes']
 assert sha(p)==stream['prefix_sha256']==stream['ingested_sha256']==stream['complete_stream_sha256']
 assert stream['discarded_tail_bytes']==0
stderr=raw(RUN/'mxc/stderr.prefix.bin')
assert stderr.hex()=='c3fcc1eed3efb7a8b2bbd5fdc8b7a1a30d0a' and len(stderr)==18
assert stderr.decode('gbk')=='命令语法不正确。\r\n'
assert raw(RUN/'mxc/stdout.prefix.bin')==b''
assert sorted(launch['env_keys_only'])==sorted(['APPDATA','COMSPEC','HOME','LOCALAPPDATA','OS','PATH','PATHEXT','SystemDrive','SystemRoot','TEMP','TMP','USERPROFILE','WINDIR'])
pin_checks=[];deferred=[]
for pin in outer['inputs']:
 if norm(pin['path']).startswith('c:/'):
  assert sha(pin['path'])==pin['sha256'];pin_checks.append(pin)
 else:
  assert norm(pin['path']).startswith('d:/') and pin['sha256']==sha(SOURCE)
  deferred.append({'path':pin['path'],'sha256':pin['sha256'],'verification':'NOT_DIRECTLY_READ_C_ONLY; controller input_drift=false; C source review same SHA'})
assert len(pin_checks)==10 and len(deferred)==1
assert sha(outer['executable'])==outer['executable_sha256']
manifest=obj(PREP/'MANIFEST.json')
for f in manifest['files']:
 assert sha(PREP/f['name'])==f['sha256'] and len(raw(PREP/f['name']))==f['bytes']
runfiles=sorted(p for p in RUN.rglob('*') if p.is_file())
assert len(runfiles)==11
selection=[]
for p in runfiles+[REG,SCOPE,INNER,SOURCE,PREP/'MANIFEST.json']:
 relative=('run/'+p.relative_to(RUN).as_posix()) if p.is_relative_to(RUN) else ('support/'+('outer.scope.json' if p==SCOPE else 'inner.scope.json' if p==INNER else 'source-REVIEW.json' if p==SOURCE else p.name))
 target=OUT/'evidence'/relative;target.parent.mkdir(parents=True,exist_ok=True)
 assert not target.exists()
 shutil.copyfile(p,target)
 assert sha(target)==sha(p)
 selection.append({'source':str(p),'archive_file':'evidence/'+relative,'bytes':len(raw(p)),'sha256':sha(p)})
write(OUT/'SELECTION.json',{'schema':'researchos.readonly-evidence-selection.v1','files':selection,'original_evidence_modified':False})
report={
 'schema':'researchos.independent-actual-audit.v1',
 'decision':'VERIFIED_LOCAL_COMMAND_FAILED_MXC_CAPABILITY_UNDETERMINED_NO_REPLAY',
 'formal_increment':0,'product_increment':0,'model_increment':0,'pending_review_blockers':[],
 'scope_id':inner['scope_id'],'outer_scope_sha256':outer_sha,'inner_scope_sha256':inner_sha,
 'evidence_selection':'SELECTION.json',
 'source_sha256':{str(p):sha(p) for p in [REG,SCOPE,INNER,SOURCE,PREP/'MANIFEST.json',RUN/'RESULT.json',RUN/'mxc/RESULT.json']},
 'input_integrity':{'outer_input_pins':11,'C_input_pins_independently_hashed':10,'C_input_pin_checks':pin_checks,'other_pins':deferred,'node_executable_hash_verified':True,'frozen_manifest_members_verified':8,'controller_reports_input_drift':False,'wrapper_reports_input_drift':False},
 'measurements':{'actual_local_native_command_invocations_in_this_scope':1,'scope_invocation_budget_consumed':1,'actual_reviewer_invocations':0,'actual_model_tasks':0,'retry_observed':False,'model_or_internal_API_calls':'NOT_INDEPENDENTLY_MEASURED; fixed command is local sandbox echo, not model execution'},
 'observations':{'outer_status':job['status'],'root_exit_code':1,'native_exit_code':1,'native_spawn_error':None,'native_stdout_bytes':0,'native_stderr_bytes':18,'native_stderr_hex':stderr.hex(),'native_stderr_GBK':stderr.decode('gbk'),'native_stderr_sha256':sha(RUN/'mxc/stderr.prefix.bin'),'echo_observed':False,'stdout_stderr_complete':True,'timeout_or_output_limit':False,'observation_errors':[],'job_total_processes':7,'job_assigned_before_reported_resume':True,'job_active_zero':True,'root_signaled':True,'stop_proved':True,'forced_termination_attempts':0,'controller_errors':[],'elapsed_seconds':job['elapsed_seconds']},
 'diagnostic_events':[{'origin_key':'mxc_availability_20261105_e91c:local-command-syntax-error','classification':'ACTUAL_LOCAL_COMMAND_FAILURE_CAPABILITY_UNDETERMINED','detail':'The single fixed local sandbox command returned exit 1; complete native stderr contains 18 bytes decoding as GBK 命令语法不正确。 and stdout is empty. The retained diagnostic does not identify which internal component emitted it or establish MXC initialization success/failure. Preserve the consumed scope and original failure; no replay performed by this audit.'}],
 'interpretation':{
 'supported':['The registered fixed local command was attempted once and failed with exit 1; MXC_OK was not observed.','The wrapper completed stream capture without timeout, quota, persistence or observation errors.','The original f13 controller reports 7 total processes and final Job zero with normal root exit, no forced termination, no errors and no input drift.'],
 'not_established':['MXC available or unavailable','MXC isolation/container initialization completed','Cause or emitting component of the command syntax error','Split-read filesystem enforcement or permission qualification','Product READY/business acceptance or permission to retry a model','Actual network/API activity from independent telemetry'],
 'registration_status_note':'REGISTRATION.json REGISTERED_NOT_EXECUTED is a registration-time receipt; later consumed/result receipts establish this completed failed execution.',
 'consumed_status_note':'PRELAUNCH and CONSUMED_LAUNCH_OUTCOME_UNKNOWN are retained prelaunch markers, superseded for outcome by final results; they do not license replay.'},
 'runtime_disposition':'Preserve original failure and consumed scope. No automatic retry or additional command chain; any future investigation requires separate authorization and scope.',
 'review_activity':{'Native_or_Echo_started':0,'model_started':0,'candidate_entrypoint_imported':False,'D_reads':0,'D_writes':0,'original_receipt_modifications':0,'public_C_pins_hash_read_only':True}}
write(OUT/'REVIEW.json',report)
print(json.dumps({'decision':report['decision'],'run_receipts_verified':len(runfiles),'selection_files':len(selection),'C_pins_verified':len(pin_checks),'D_pins_directly_read':0,'stderr_hex':stderr.hex(),'formal_increment':0,'product_increment':0,'review_sha256':sha(OUT/'REVIEW.json')},ensure_ascii=True,indent=2))

