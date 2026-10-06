"""Execute the eleven real registered W04 bindings once, reusing frozen proof."""
from pathlib import Path
import datetime as dt, hashlib, json, os, subprocess, sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]; EXEC=HERE.parent/'executor_codex'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def canon(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
registry=load(ROOT/'execution/v2.4/commands.json'); assert registry['revision']==38
index_ref=load(EXEC/'current_execution.json')['execution_index_ref']; index=load(ROOT/index_ref['path'])
assert index_ref['sha256']==sha(ROOT/index_ref['path'])=='fd482ccc186bf557118e252741b2e1ee785d35e0c3873955c037d242849de464'
expected=load(EXEC/'expected.json'); commands=expected['case_entries']+expected['gate_entries']
bindings=[]; invocations=[]
directory=HERE/'registered_dispatches'; directory.mkdir()
env={name:value for name,value in os.environ.items() if name.upper() in ['SYSTEMROOT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PATH']}
env.update(PYTHONUTF8='1',RESEARCHOS_MODE='FIXTURE',RESEARCHOS_MEASUREMENT_MODE='FIXTURE')
for binding in commands:
    selector='case_id' if 'case_id' in binding else 'check_id'; ident=binding[selector]; key=binding['command_key']
    folder=directory/(ident+'-'+key.replace('.','_')); folder.mkdir()
    argv=[sys.executable,'-B','-X','utf8',str(ROOT/'execution/command_dispatcher/dispatch.py'),key,'--spec','v2.4','--task-id','W04','--'+selector.replace('_','-'),ident]
    start=now()
    r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
    (folder/'runner.stdout').write_bytes(r.stdout); (folder/'runner.stderr').write_bytes(r.stderr)
    response=json.loads(r.stdout); actual_path=Path(response['receipt']); actual=load(actual_path)
    save(folder/'runner_receipt.json',{'schema':'researchos.root-dispatch-invocation.v1','actual_argv':argv,'cwd':str(ROOT),'environment_variable_names':sorted(env),
        'executable_sha256':sha(Path(sys.executable)),'started_at':start,'ended_at':now(),'exit_code':r.returncode,
        'stdout':ref(folder/'runner.stdout'),'stderr':ref(folder/'runner.stderr'),'original_dispatch_receipt':ref(actual_path)})
    (folder/'receipt.json').write_bytes(actual_path.read_bytes())
    assert r.returncode==0 and actual['status']=='PASS' and type(actual['exit_code']) is int and actual['exit_code']==0 and type(actual['child_exit_code']) is int and actual['child_exit_code']==0,(binding,response)
    assert actual['registered_command_revision']==sha(ROOT/'execution/v2.4/commands.json')
    ids=expected['cases'][ident] if selector=='case_id' else [ident]
    assert sorted(actual['assertion_ids'])==sorted(ids)
    child=load(ROOT/actual['stdout']['path']); assert child['execution_index_ref']==index_ref and child['mode']=='FIXTURE'
    bindings.append({'command_key':key,selector:ident,'mode':'FIXTURE','receipt_ref':ref(folder/'receipt.json')})
    invocations.append({'command_key':key,selector:ident,'original':ref(actual_path),'runner':ref(folder/'runner_receipt.json')})
    print(json.dumps({'status':'PASS_REGISTERED','key':key,selector:ident,'invocation_id':actual['invocation_id']},ensure_ascii=False),flush=True)
vector_ref=load(ROOT/index['cases']['A01']['version_manifest']['path'])['version_vector_ref']; vector=load(ROOT/vector_ref['path'])
source_snapshot=load(ROOT/index['cases']['A01']['version_manifest']['path'])
suffixes=['*.go','*.json','*.sql','*.md','*.txt','*.yaml','*.yml']
roots=['internal','adapters','migrations','tests/contracts/fixtures','tests/context/parent','spec/v2.0/contracts']
exact=[reference['path'] for reference in vector['source_files'] if not any(reference['path'].startswith(root+'/') for root in roots)]
coverage={'roots':[{'path':root,'patterns':suffixes} for root in roots],'exact_files':sorted(exact),'paths_sha256':canon(sorted(reference['path'] for reference in vector['source_files']))}
save(HERE/'current_context_codex.json',{'schema':'researchos.w04.current-context.v1','scope':'ROOT_CURRENT_APPLICABILITY','task_id':'W04','step_id':'W04-99',
    'execution_index':index_ref,'version_vector':vector,'execution_source_snapshot':{'code_revision':source_snapshot['code_revision'],'dirty':source_snapshot['dirty'],'version_vector_sha256':canon(vector)},
    'source_coverage':coverage,'registry_ref':ref(ROOT/'execution/v2.4/commands.json'),'registry_snapshot_ref':ref(HERE/'commands_snapshot_r38.json'),'registered_dispatches':bindings})
save(HERE/'registered_dispatch_summary_codex.json',{'schema':'researchos.root-registered-dispatch-summary.v1','status':'PASS','task_id':'W04','step_id':'W04-99',
    'registry_revision':38,'case_bindings':6,'parent_gate_bindings':5,'actual_registered_invocations':invocations,'execution_index':index_ref,
    'current_context':ref(HERE/'current_context_codex.json'),'formal_case_count_delta':0,'parent_accepted':False,'product_go_reexecutions':0})
print(json.dumps({'status':'PASS_ELEVEN_REAL_REGISTERED_DISPATCHES','context':ref(HERE/'current_context_codex.json'),'formal_accepted':0}))
