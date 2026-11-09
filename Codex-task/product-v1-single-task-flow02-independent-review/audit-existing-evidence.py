"""Read existing public C receipts and the authorized two-file fixture only."""
import hashlib, json, stat
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inner_file=ROOT/'product-v1-single-task-flow-02-registration/real-flow.scope.json'
outer_file=ROOT/'product-v1-owned-verification-20261104/scopes/product-v1-single-task-flow-02.json'
inner,outer=read(inner_file),read(outer_file)
runroot=Path(inner['run_root']); receipts=runroot/'receipts'
control=ROOT/'product-v1-owned-verification-20261104'
jobroot=control/'runs/product-v1-single-task-flow-02'
job,consumed=read(jobroot/'RESULT.json'),read(jobroot/'CONSUMED.json')
result,task,events=read(receipts/'result.json'),read(receipts/'final-task.json'),read(receipts/'events.json')
launch=read(receipts/'launch-input.json')
assert job['scope_sha256']==consumed['scope_sha256']==sha(outer_file)
assert outer['argv'][-1]==result['scope_sha256']==sha(inner_file)
assert consumed['controller_sha256']==sha(control/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
for raw in job['raw']:
    f=jobroot/raw['file'];assert f.stat().st_size==raw['bytes'] and sha(f)==raw['sha256']
assert job['status']=='CHILD_NONZERO_STOPPED' and job['root_exit_code']==2
assert job['job_assigned'] and job['resumed'] and job['root_signaled'] and job['stop_proved'] and job['job_active_zero']
assert job['job_total_processes']==59 and job['terminate_job_attempts']==job['terminate_original_root_attempts']==0
assert not job['errors'] and not job['input_drift'] and not job['automatic_retry'] and not job['timed_out']
assert result['close']['app_close_resolved'] and result['actual_dom_submit_attempts']==1
assert result['status']=='BLOCKED_OR_FAILED' and result['phase']=='AUTHORITATIVE_TASK_TERMINAL_OBSERVED'
assert result['error']['code']=='REAL_READ_RESULT_NOT_CONFIRMED'
assert task==result['task'] and task['status']=='FAILED' and task['terminal'] is True
assert task['failure']['code']=='HARNESS_UNAVAILABLE' and task['failure']['retryable'] is False
assert task['result']['assistant_text']=='' and task['result']['cli_thread_id'] is None
request='15a8196b-9109-4633-a851-76e2d51aaf87'
ref={'project_id':'3c2851162463a31281fc21678e12636a','task_id':'449cdce6ba09adefcbaa57e95e2e9411'}
run={'run_id':'d15274806ec0f89e26077c195ef93e59','epoch':'1'}
assert result['request_id']==task['request_id']==request and result['task_ref']==task['task_ref']==ref
assert result['run_ref']==task['run']==run and result['identity_provenance']=='FIRST_VALID_PENDING_SUBMIT'
sources=[receipts/'pending-1.json',*sorted(receipts.glob('observation-*.json')),*sorted(receipts.glob('events-page-*.json')),receipts/'events.json',receipts/'final-task.json']
requests=set();runs=set();taskrefs=set();tasks=[]
def inspect(value):
    if isinstance(value,dict):
        if isinstance(value.get('request_id'),str):requests.add(value['request_id'])
        if 'run_id' in value and 'epoch' in value:runs.add((value['run_id'],value['epoch']))
        if isinstance(value.get('task_ref'),dict):taskrefs.add((value['task_ref']['project_id'],value['task_ref']['task_id']))
        if 'request_id' in value and 'harness_id' in value:
            assert value['workspace_ref']==task['workspace_ref'] and value['prompt']==task['prompt']
            assert value['scope']=='workspace-read' and value['ephemeral'] is True and value['harness_id']=='codex'
            tasks.append(value)
        for child in value.values():inspect(child)
    elif isinstance(value,list):
        for child in value:inspect(child)
for f in sources:inspect(read(f))
assert requests=={request} and runs=={(run['run_id'],run['epoch'])} and taskrefs=={(ref['project_id'],ref['task_id'])}
pending=read(receipts/'pending-1.json')['pending']
assert pending['ok'] and pending['data']['kind']=='submit' and pending['data']['state']=='SENDING'
assert pending['data']['request_id']==request and pending['data']['workspace_ref']==task['workspace_ref']
assert pending['data']['prompt']==task['prompt']
page_events={};cursor=0;pages=[]
for f in sorted(receipts.glob('events-page-*.json')):
    page=read(f);assert page['task_ref']==ref and page['reset'] is False
    assert int(page['next_cursor'])>=cursor
    for e in page['events']:
        assert e['task_ref']==ref and (e['run'] is None or e['run']==run)
        assert int(e['sequence'])<=int(page['next_cursor'])
        if e['event_id'] in page_events:assert page_events[e['event_id']]==e
        page_events[e['event_id']]=e
    cursor=int(page['next_cursor']);pages.append({'file':f.name,'cursor':page['next_cursor'],'end':page['end'],'event_count':len(page['events'])})
assert sorted(page_events.values(),key=lambda x:int(x['sequence']))==events
assert len({e['event_id'] for e in events})==len(events)==6
assert [e['kind'] for e in events]==['TASK_QUEUED','RUN_STARTED','RUN_STATE','LOG','LOG','TASK_TERMINAL']
assert events[-1]['payload']['task']==task and pages[-1]['end'] is True
assert not any(e['kind'] in ['ASSISTANT_MESSAGE','TOOL_EVENT'] for e in events)
logs=[{'event_id':e['event_id'],'sequence':e['sequence'],'text':e['payload']['text']} for e in events if e['kind']=='LOG']
failure_phrase='windows unelevated restricted-token sandbox cannot enforce split filesystem read restrictions directly; refusing to run unsandboxed'
assert len(logs)==2 and all(failure_phrase in e['text'] for e in logs)
assert 'Failed to create session' in logs[0]['text'] and 'thread/start failed' in logs[1]['text']
caps=read(receipts/'capabilities-immediately-before-submit.json')
assert caps['authentication']['state']=='LOGGED_IN' and caps['authentication']['kind']=='chatgpt'
assert caps['can_submit'] and caps['harness_id']=='codex' and caps['security_scope']['mode']=='workspace-read'
assert caps['security_scope']['native_auth']=='CLI_OWNED' and caps['capabilities']['write'] is False
assert caps['installation']['version']=='0.166.0' and caps['installation']['executable_sha256']=='sha256:'+inner['codex']['sha256']
assert sha(receipts/'capabilities-before.json')==sha(receipts/'capabilities-immediately-before-submit.json')
assert sha(ROOT/'product-v1-real-electron-single-task-prepare-04/real-electron-flow.mjs')==inner['harness']['runner_sha256']=='e14f9d287398b432f6e3a55918fb73be747b8b446d1e7f032ddfdfd925627a5b'
assert sha(ROOT/'product-v1-real-electron-single-task-prepare-04/choose-owned-folder.ps1')==inner['harness']['folder_helper_sha256']
assert inner['bundle']['source_binding_review']=='ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE'
failed=[g for g in result['guard_history'] if not g['passed']]
assert len(failed)==1 and failed[0]['code']=='REAL_READ_RESULT_NOT_CONFIRMED'
assert any(g['code']=='SOURCE_BOUND_BUILD_REQUIRED' and g['passed'] for g in result['guard_history'])
assert result['source_head']==inner['source']['head'] and result['bundle_manifest_sha256']==inner['bundle']['manifest_sha256']
main=read(receipts/'main-current-project-observation.json');after=read(receipts/'main-context-after-open.json')
assert main['context']==after['context']=={'project_id':ref['project_id'],'session_id':None}
binding=main['listed']['result']['items'];assert len(binding)==1
assert binding[0]['status']=='ACTIVE' and binding[0]['project_id']==ref['project_id']
assert binding[0]['authorized_workspace_ref']==task['workspace_ref'] and binding[0]['display_path']==main['displayed_path']==launch['workspace']
native_receipt=read(receipts/'native-folder-automation.json');native= json.loads(native_receipt['stdout'])
assert native_receipt['exit']==0 and native['clicked_ok'] and native['invalid_kept_chooser_open'] and native['valid_ok_attempted'] and not native['outcome_uncertain']
assert native['actual_task_submissions']==0 and native['model_outcome']=='NOT_RUN_ZERO_BUDGET'
workspace=runroot/'workspace';assert workspace==Path(launch['workspace'])
actual=[]
for f in workspace.iterdir():
    assert not f.is_symlink() and not (f.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    assert f.is_file() and f.name in {'README.md','probe.txt'}
    actual.append({'path':f.name,'sha256':sha(f),'bytes':f.stat().st_size})
assert sorted(actual,key=lambda x:x['path'])==sorted(launch['original_files'],key=lambda x:x['path'])
assert hashlib.sha256(task['prompt'].encode()).hexdigest()==launch['prompt_sha256']
token=(workspace/'probe.txt').read_text().strip();assert token not in task['prompt'] and not task['result']['assistant_text']
evidence=[inner_file,outer_file,jobroot/'RESULT.json',jobroot/'CONSUMED.json',jobroot/'stdout.raw',receipts/'result.json',receipts/'final-task.json',receipts/'events.json',receipts/'pending-1.json',receipts/'capabilities-immediately-before-submit.json',receipts/'launch-input.json',receipts/'main-current-project-observation.json',receipts/'main-context-after-open.json',receipts/'native-folder-automation.json',*sources]
print(json.dumps({'status':'VERIFIED_ACTUAL_SINGLE_TASK_RESOURCE_BLOCKED_NO_REPLAY','request_id':request,'task_ref':ref,'run_ref':run,'identity_observation_files':len(sources),'observed_task_snapshots':len(tasks),'distinct_requests':len(requests),'distinct_tasks':len(taskrefs),'distinct_runs':len(runs),'events':[{'event_id':e['event_id'],'sequence':e['sequence'],'kind':e['kind'],'run':e['run']} for e in events],'pages':pages,'failure_logs':logs,'measurement':{'actual_dom_submit_attempts':1,'native_harness_invocations_observed':1,'model_inference':'NOT_CONFIRMED','session_start':'FAILED_BEFORE_THREAD_ESTABLISHED','internal_api_calls':'NOT_MEASURED','transport_post_count':'NOT_INSTRUMENTED','assistant_messages':0,'tool_events':0,'cli_thread_id':None},'fixture_after_independent_readonly_audit':actual,'fixture_unchanged':True,'canary_in_prompt':False,'runner_success_only_fixture_receipt_present':(receipts/'workspace-unchanged.json').exists(),'source_pin_entries':len(inner['source']['pins']),'source_preflight_guards_passed':True,'job_processes':job['job_total_processes'],'job_active_zero':True,'normal_app_close':True,'evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in evidence},'formal_increment':0},indent=2))
