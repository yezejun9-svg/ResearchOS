from pathlib import Path
import hashlib,json,ntpath
R=Path(__file__).resolve().parent;T=R.parent.parent
run=T/'product-v1-cli-same-host-caps-run-02/receipts'
outer=T/'product-v1-owned-verification-20261104/runs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['result.json','owned-core-and-discovery.before.json','owned-core-and-discovery.after.json','cli-caps.json','cli-streams.json','CONSUMED.json']
paths=[run/n for n in names]+[outer/'product-v1-cli-same-host-caps-02/RESULT.json',outer/'product-v1-cli-same-host-caps-01/RESULT.json',outer/'product-v1-cli-same-host-caps-01/stderr.raw']
v=[json.loads(p.read_text(encoding='utf-8-sig')) for p in paths[:-1]]
result,before,after,caps,streams,consumed,job,oldjob=v
assert before==after and result['owned_core_identity']==before['core']==result['main_reports'][0]['owned_core_identity']
core=before['core'];discovery=before['discovery']
assert core['pid']==discovery['pid']==60528 and core['host_id']==discovery['host_instance_id']=='host-8ad74c022e79'
assert core['image_sha256']=='9822351e13584757e3122d5f78ae0ba3d98cc6eb5e33c9b51a0710146804cb98'
assert discovery['url']==result['main_reports'][0]['host_url']=='http://127.0.0.1:38209'
assert ntpath.normcase(ntpath.normpath(discovery['data_dir']))==ntpath.normcase(ntpath.normpath(str(T/'product-v1-cli-same-host-caps-run-02/data')))
assert result['status']=='SAME_HOST_CLI_CAPS_OBSERVED_PENDING_OUTER_JOB_STOP' and result['caps_invocations']==1
assert result['cli_close']=={'code':0,'signal':None} and result['cli_original_handle_close_observed'] and result['close']['app_close_resolved']
assert result['task_submissions']==result['model_requests']==0 and caps['response']['data']=={'harness_id':'codex','can_submit':True,'reason_code_count':0}
assert streams['exit_code']==0 and not streams['overflow'] and streams['spawn_error'] is None
assert job['status']=='COMPLETED_OWNED_JOB_STOPPED' and job['root_exit_code']==0 and job['stop_proved'] and job['job_active_zero'] and job['terminate_job_attempts']==job['terminate_original_root_attempts']==0
assert oldjob['root_exit_code']==2 and oldjob['status']=='CHILD_NONZERO_STOPPED' and oldjob['stop_proved']
assert paths[-1].read_text().strip()=='FRESH_C_ROOT_REQUIRED' and not (T/'product-v1-cli-same-host-caps-run-01').exists()
report={
 'schema':'researchos.independent-receipt-readback.v1','decision':'OBSERVATION_CONFIRMED_NOT_PRODUCT_ACCEPTANCE','formal_increment':0,'product_increment':0,
 'inputs':[{'path':str(p),'sha256':sha(p)} for p in paths],
 'confirmed':{'caps_invocations':1,'cli_exit_code':0,'cli_close_observed':True,'task_submissions':0,'model_requests':0,'app_close_resolved':True,'same_before_after_core_and_public_discovery':True,'core_identity':core,'public_discovery':discovery,'capability_summary':caps['response']['data'],'outer_status':job['status'],'outer_exit_code':0,'stop_proved':True,'job_active_zero':True,'forced_termination_attempts':0,'source_bundle_manifest_sha256':result['bundle_manifest_sha256'],'cli_sha256':result['cli_sha256']},
 'identity_evidence_boundary':{'basis':result['identity_basis'],'independent_native_server_pid_observed':False,'cli_output_identity_fields':result['cli_output_identity_fields'],'meaning':'Successful fixed CLI caps request under explicit same-data/discovery environment, validated original Main Core identity and unchanged public snapshots. No network/pipe PID interception or independent CLI-reported server PID was observed.'},
 'prior_run01':{'status':oldjob['status'],'exit_code':oldjob['root_exit_code'],'reason':'FRESH_C_ROOT_REQUIRED','run_root_exists':False,'classification':'ROOT_SCOPE_PATH_FORMAT_PRELAUNCH_METADATA_FAILURE','carryforward_only':True,'count_again':False,'original_evidence_preserved':True,'fix':'Root used a new scope/run02 with canonical Windows separators; original guards and reviewed source unchanged.'},
 'limits':['can_submit true and reason count zero are only the public summary returned by Host. Authentication kind, login method, model availability and task execution qualification are not established.','This readback neither launched App/CLI/native/model nor ran new tests or rehashed the full bundle. It read existing exact C receipts only.','No task was submitted; product acceptance, planning/review/patch-application journeys and Windows write enforcement remain unqualified.','The outer Job receipt supplies stop evidence separately from the inner pending-outer-stop status; no forced-stop or retry is inferred.'],
 'diagnostic_events':[],'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
}
p=R/'report.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selection=R/'archive-file-list.json';assert not selection.exists();selection.write_text(json.dumps([str(R/'readback.py'),str(p)],indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(p),'report_sha256':sha(p),'archive_file_list_sha256':sha(selection)}))
