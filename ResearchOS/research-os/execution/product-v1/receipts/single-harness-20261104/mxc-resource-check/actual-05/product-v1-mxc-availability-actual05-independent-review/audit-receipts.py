import hashlib,json,pathlib,shutil
BASE=pathlib.Path(r'C:\Users\yqyyds\Documents\Codex\2026-11-04\task')
OUT=BASE/'product-v1-mxc-availability-actual05-independent-review'
CONTROL=BASE/'product-v1-owned-verification-20261104'
RUN=CONTROL/'runs/mxc_availability_20261105_f602'
PRIOR=CONTROL/'runs/mxc_availability_20261105_e91c'
PREP=BASE/'product-v1-mxc-availability-prepare-rev05-20261105-f602'
REG=BASE/'product-v1-mxc-availability-registration05/REGISTRATION.json'
SCOPE=CONTROL/'scopes/mxc_availability_20261105_f602.json'
INNER=PREP/'mxc.scope.json'
SOURCE=BASE/'product-v1-mxc-availability-security-review-rev05/REVIEW.json'
REGISTRAR=BASE/'register_product_v1_mxc_echo05.py'
def raw(p):return pathlib.Path(p).read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def obj(p):return json.loads(raw(p))
def norm(p):return str(p).replace('\\','/').lower()
def write(p,v):pathlib.Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
reg,outer,inner,job,native,launch=[obj(p) for p in [REG,SCOPE,INNER,RUN/'RESULT.json',RUN/'mxc/RESULT.json',RUN/'mxc/launch-plan.json']]
outer_sha='3ffc1d09651685066da6c4fa277d27f67f4d94efe3742975de38a4f419e342a2'
inner_sha='39edf2f23fbb3c39a20c1a5cf765bf696314d4c4144f794d68a5df2d3809ac97'
review_sha='9a0f1f8cf60eaaeaa330ad25bc5c85d99519530945f6319d4dfaa831f5025d79'
origin='mxc_availability_20261105_e91c:local-command-syntax-error'
assert sha(SCOPE)==reg['scope_sha256']==job['scope_sha256']==outer_sha
assert sha(INNER)==reg['inner_scope_sha256']==outer['argv'][2]==launch['scope_sha256']==inner_sha
assert sha(SOURCE)==reg['source_review_sha256']==inner['independent_review_sha256']==review_sha
assert outer['authorization']==inner['state']=='ROOT_REVIEWED_EXACT_COMMAND'
assert outer['scope_id']==inner['scope_id']==job['scope_id']=='mxc_availability_20261105_f602'
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
assert job['status']=='COMPLETED_OWNED_JOB_STOPPED' and job['root_exit_code']==0 and job['job_total_processes']==7
assert all(job[k] is True for k in ['job_assigned','resumed','root_signaled','job_active_zero','stop_proved'])
assert all(job[k] is False for k in ['timed_out','raw_limit_exceeded','input_drift'])
assert job['terminate_job_attempts']==job['terminate_original_root_attempts']==0 and job['errors']==[]
assert native['status']=='MXC_ECHO_CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF' and native['exit_code']==0
assert native['spawn_error'] is None and native['exit_signal'] is None and native['observation_errors']==[]
assert all(native[k] is False for k in ['timed_out','input_drift','resource_ready','product_can_submit','automatic_retry'])
assert native['exact_echo'] is True and native['child_close_observed'] is True
for e in job['raw']:
 p=RUN/e['file'];assert len(raw(p))==e['bytes'] and sha(p)==e['sha256']
assert obj(RUN/'stdout.raw')=={'status':'MXC_ECHO_CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF','resource_ready':False,'model_tasks':0}
for stream in native['streams']:
 name=stream['stream'];p=RUN/'mxc'/f'{name}.prefix.bin'
 assert obj(RUN/'mxc'/f'{name}.progress.json')==stream
 assert stream['stream_complete'] and stream['stream_end_observed'] and stream['child_close_observed']
 assert stream['errors']==[] and not stream['limit_reached'] and not stream['persistence_failed']
 assert len(raw(p))==stream['ingested_bytes']==stream['delivered_bytes']==stream['durable_prefix_bytes']
 assert sha(p)==stream['prefix_sha256']==stream['ingested_sha256']==stream['complete_stream_sha256']
 assert stream['discarded_tail_bytes']==0
assert raw(RUN/'mxc/stdout.prefix.bin')==b'MXC_OK\r\n'
assert raw(RUN/'mxc/stderr.prefix.bin')==b''
old_launch=obj(PRIOR/'mxc/launch-plan.json')
assert [i for i,(a,b) in enumerate(zip(old_launch['argv'],launch['argv'])) if a!=b]==[7]
assert norm(old_launch['argv'][7])==norm(launch['argv'][7])
assert old_launch['env_keys_only']==launch['env_keys_only']
old_inner=obj(BASE/'product-v1-mxc-availability-prepare-rev04-20261105-e91c/mxc.scope.json')
assert old_inner['windows']==inner['windows'] and old_inner['executable']==inner['executable']
assert reg['diagnostic_origin']==inner['diagnostic_origin']==origin
assert reg['diagnostic_attempt']==inner['diagnostic_attempt']==2
assert inner['prior_attempt_retained'] is True and reg['prior_failure_retained'] is True
assert reg['prior_local_native_invocations']==1 and reg['total_planned_local_native_invocations']==reg['max_local_native_invocations']==2
assert sha(PRIOR/'RESULT.json')==reg['prior_failure_result_sha256']=='6903454745a9ee821497e9a2f172fd00a736a07165316800a0129a28ff8442fd'
assert obj(PRIOR/'RESULT.json')['root_exit_code']==1 and obj(PRIOR/'mxc/CONSUMED.json')['invocation_budget_consumed']==1
prior_sel=BASE/'product-v1-mxc-availability-actual04-independent-review/SELECTION.json'
assert sha(prior_sel)=='f90ede448c2943dda68b47e015c3d4e67586f0286d5d59f760eb6ec6dadfe11d'
for f in obj(prior_sel)['files']:assert sha(f['source'])==f['sha256']
observed_scopes=sorted(p.name for p in (CONTROL/'runs').iterdir() if p.is_dir() and p.name.startswith('mxc_availability_'))
assert observed_scopes==['mxc_availability_20261105_e91c','mxc_availability_20261105_f602']
registrar_text=raw(REGISTRAR).decode('utf-8')
assert "==[prior_id]" in registrar_text and "prior/'RESULT.json'" in registrar_text and "max_local_native_invocations=2" in registrar_text
pin_checks=[];D_report=None
for pin in outer['inputs']:
 if not norm(pin['path']).startswith('c:/'):
  assert norm(pin['path']).startswith('d:/')
  assert norm(pin['path']).endswith('/mxc-resource-check/preparation-05/product-v1-mxc-availability-security-review-rev05/review.json')
  assert pin['sha256']==review_sha and D_report is None
  D_report=pathlib.Path(pin['path'])
 assert sha(pin['path'])==pin['sha256'];pin_checks.append(pin)
assert len(pin_checks)==11 and D_report is not None
assert sha(outer['executable'])==outer['executable_sha256']
manifest=obj(PREP/'MANIFEST.json')
for f in manifest['files']:assert sha(PREP/f['name'])==f['sha256'] and len(raw(PREP/f['name']))==f['bytes']
assert len(manifest['files'])==7
runfiles=sorted(p for p in RUN.rglob('*') if p.is_file())
assert len(runfiles)==11
support=[(REG,'REGISTRATION.json'),(SCOPE,'outer.scope.json'),(INNER,'inner.scope.json'),(SOURCE,'source-REVIEW.json'),(PREP/'MANIFEST.json','MANIFEST.json'),(REGISTRAR,'registrar.py'),(PRIOR/'RESULT.json','prior-RESULT.json'),(prior_sel,'prior-SELECTION.json'),(D_report,'archived-source-REVIEW.json')]
selection=[]
for p,name in [(p,'run/'+p.relative_to(RUN).as_posix()) for p in runfiles]+[(p,'support/'+name) for p,name in support]:
 target=OUT/'evidence'/name;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
 shutil.copyfile(p,target);assert sha(target)==sha(p)
 selection.append({'source':str(p),'archive_file':'evidence/'+name,'bytes':len(raw(p)),'sha256':sha(p)})
write(OUT/'SELECTION.json',{'schema':'researchos.readonly-evidence-selection.v1','files':selection,'original_evidence_modified':False})
report={
 'schema':'researchos.independent-actual-audit.v1',
 'decision':'VERIFIED_FIXED_LOCAL_MXC_ECHO_STARTUP_ONLY_NOT_PRODUCT_ACCEPTANCE',
 'formal_increment':0,'product_increment':0,'model_increment':0,'pending_review_blockers':[],
 'scope_id':inner['scope_id'],'outer_scope_sha256':outer_sha,'inner_scope_sha256':inner_sha,'evidence_selection':'SELECTION.json',
 'source_sha256':{str(p):sha(p) for p in [REG,SCOPE,INNER,SOURCE,PREP/'MANIFEST.json',REGISTRAR,RUN/'RESULT.json',RUN/'mxc/RESULT.json',D_report]},
 'input_integrity':{'outer_input_pins':11,'independently_hashed':11,'C_input_pins':10,'exact_D_archived_review_pins':1,'pin_checks':pin_checks,'node_executable_hash_verified':True,'frozen_manifest_members_verified':7,'controller_input_drift':False,'wrapper_input_drift':False},
 'observations':{'outer_status':job['status'],'root_exit_code':0,'native_exit_code':0,'native_spawn_error':None,'stdout_bytes':8,'stdout_hex':raw(RUN/'mxc/stdout.prefix.bin').hex(),'stdout_text':'MXC_OK\r\n','stdout_sha256':sha(RUN/'mxc/stdout.prefix.bin'),'stderr_bytes':0,'exact_echo':True,'both_streams_complete':True,'job_assigned':True,'resumed':True,'job_total_processes':7,'job_active_zero':True,'root_signaled':True,'stop_proved':True,'forced_termination_attempts':0,'controller_errors':[],'observation_errors':[],'timeout':False,'output_limit':False,'elapsed_seconds':job['elapsed_seconds']},
 'lineage':{'diagnostic_origin':origin,'diagnostic_attempt':2,'actual_local_invocations_this_scope':1,'prior_actual_local_invocations':1,'cumulative_local_invocations_in_known_diagnostic_scopes':2,'registered_cumulative_max':2,'observed_owned_mxc_scope_directories':observed_scopes,'prior_failure_preserved':True,'prior_failure_result_sha256':sha(PRIOR/'RESULT.json'),'prior_evidence_files_unchanged':16,'registrar_unique_prior_scope_guard_statically_verified':True,'registrar_prior_failure_pin_guard_statically_verified':True,'automatic_retry':False,'budget_remaining':0},
 'diagnostic_events':[{'origin_key':origin,'classification':'KNOWN_DIAGNOSTIC_SECOND_ATTEMPT_ECHO_OBSERVED','new_diagnostic_increment':0,'detail':'The separately registered second local diagnostic scope changed only argv[7] path spelling plus fresh scope paths and produced exact MXC_OK CRLF with exit 0. The failed consumed first attempt remains byte-identical. This supports current fixed-command startup success; the path-spelling change is associated with the different result but does not conclusively prove the internal root cause.'}],
 'interpretation':{'supported':['The pinned local command explicitly selecting windows.sandbox=mxc completed and produced exact MXC_OK CRLF under the original f13 Job.','Current fixed local MXC echo startup availability is observed for this scope.','The original Job ended with 7 total processes, active zero, no forced termination, no errors and no input drift.'],
 'not_established':['Product split-read/root-deny/minimal-read policy enforcement','Filesystem/network isolation security qualification or adversarial capability tests','Product READY or business acceptance','Permission to retry the consumed product/model task','Conclusive root cause of the first command syntax error','Independent measurement of network/internal API activity'],
 'configuration_boundary':'Compared registered fixed argv, windows profile fields and environment key lists; no private user configuration/authentication was read and no saved-configuration immutability claim is made.',
 'registration_status_note':'REGISTERED_NOT_EXECUTED is the retained registration-time state; final consumed/result receipts establish this completed execution.',
 'wrapper_status_note':'REQUIRES_ROOT_STOP_PROOF is satisfied here only by independently checked original f13 final Job-zero receipt.'},
 'measurements':{'actual_model_tasks':0,'reviewer_native_echo_invocations':0,'reviewer_model_invocations':0,'model_or_internal_API_calls':'NOT_INDEPENDENTLY_MEASURED; the reviewed fixed command is a local sandbox echo, not model execution'},
 'disposition':'Two known local diagnostic attempts are consumed. No further run performed or authorized by this audit; retain both attempts and current scope. Echo success does not authorize a model retry.',
 'review_activity':{'candidate_entrypoint_imported':False,'Native_Echo_model_started':0,'private_userdata_auth_config_read':False,'exact_D_archived_review_files_read':1,'D_writes':0,'original_receipt_modifications':0}}
write(OUT/'REVIEW.json',report)
print(json.dumps({'decision':report['decision'],'run_receipts':11,'selection_files':len(selection),'pins_verified':11,'job_processes':7,'prior_evidence_unchanged':16,'cumulative_local_attempts':2,'review_sha256':sha(OUT/'REVIEW.json')},indent=2))

