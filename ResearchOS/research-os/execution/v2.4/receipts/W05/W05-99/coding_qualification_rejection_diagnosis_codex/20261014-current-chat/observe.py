import datetime,hashlib,json,pathlib,sqlite3,subprocess
E=pathlib.Path(__file__).resolve().parent;R=E.parents[6]
A=R/'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry10_codex/20261014-current-chat'
O=R/'execution/v2.4/receipts/W05/W05-99/coding_model_observer_codex/20261014-current-chat'
P='a7ebcf2a322c6abcf87e043f601ee804';S='a09d4435036b2b32a0d7076bfc53fd93';Q='1b4a119026c64f0347984bbc69862763';MC='mc-3f9329b391eaca14d82e7c4d3b9b6f34';RT='db26746ff0420ca156d315f0de00fb53'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
pins=[]
def pin(p):pins.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
historical=[]
for name,digest in [('new-config-qualification-1b4a119-preconfirm.json','3e7445fb6976a99f6d3d263ec3ba340845dc40873968c841d02a65cec5d76cf5'),('new-config-qualification-1b4a119-after-confirm.json','b17b1616c10a71b9b449d655de2beccd46f466fefb03238851a9c168d675d65f')]:
    p=O/name;assert sha(p)==digest;pin(p);d=read(p)
    selected={k:v for k,v in d.items() if k in ['at','session','stage','current_session_hash_matches_request','qualification_request_time_valid_now','preconfirm_goals_and_refs_current','observation_bound','qualification_requests','qualification_consumption','runtime_qualification_runs','qualification_request','task','runtime','coding_installation']}
    if 'qualification_request' in selected:
        value=selected['qualification_request'];selected['qualification_request']={k:v for k,v in value.items() if k!='body'} if isinstance(value,dict) else value
    historical.append(dict(source=str(p),keys=list(d),selected=selected))
put('historical-safe-fields.json',historical)
for p in A.iterdir():
    if p.is_file():pin(p)
core='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';desktop='c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
files=['internal/host/desktop_management_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/domain/runtime_qualification_execution_windows.go','internal/domain/client_session_fence.go','internal/domain/runtime_qualification_fence_windows_test.go','internal/domain/runtime_qualification_confirmation_windows_test.go','internal/domain/runtime_qualification_execution_windows_test.go','internal/domain/client_protocol_sessions.go','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/main.js']
captures=[]
for rel in files:
    commit=desktop if rel.startswith('apps/desktop/') else core
    proc=subprocess.run(['git','show',commit+':'+rel],cwd=R,capture_output=True)
    assert proc.returncode==0,(rel,proc.stderr)
    dest=E/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(proc.stdout)
    captures.append(dict(commit=commit,path=rel,capture=str(dest),sha256=sha(dest),bytes=len(proc.stdout),git_show_exit=proc.returncode))
put('source-captures.json',captures)
db=R/'.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite'
c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN');queries=[]
def query(sql,args=()):
    queries.append(dict(sql=sql,parameters=list(args)))
    return [dict(row) for row in c.execute(sql,args)]
result=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),database=str(db),database_uri_mode='ro',query_only=c.execute('PRAGMA query_only').fetchone()[0],transaction='BEGIN/ROLLBACK',mutations=0,api_requests=0,model_requests=0)
result['session']=query('SELECT id,project_id,revision,writer_epoch,writer_client_id,lease_expires_at,workspace_ref,model_config_ref,run_id,sealed_at,archived_at FROM client_sessions WHERE project_id=? AND id=?',(P,S))
result['qualification_request']=query("SELECT key,request_hash,created_at,json_extract(body,'$.request_id') AS request_id,json_extract(body,'$.session_id') AS session_id,json_extract(body,'$.model_config_ref') AS model_config_ref,json_extract(body,'$.session_hash') AS session_hash,json_extract(body,'$.client_id') AS client_id,json_extract(body,'$.writer_epoch') AS writer_epoch,json_extract(body,'$.expected_revision') AS expected_revision,json_extract(body,'$.issued_at') AS issued_at,json_extract(body,'$.expires_at') AS expires_at FROM idempotency WHERE project=? AND operation='host:qualification-confirmation' AND key=?",(P,Q))
result['consumption']=query("SELECT key,request_hash,created_at,json_extract(body,'$.run_id') AS run_id,json_extract(body,'$.state') AS state FROM idempotency WHERE project=? AND operation='host:managed-runtime-qualification' AND key=?",(P,Q))
result['all_new_config_requests']=query("SELECT key,created_at,json_extract(body,'$.issued_at') AS issued_at,json_extract(body,'$.expires_at') AS expires_at FROM idempotency WHERE project=? AND operation='host:qualification-confirmation' AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.model_config_ref')=? ORDER BY created_at",(P,S,MC))
result['runtime_runs']=query('SELECT project,task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle FROM runtime_qualification_runs WHERE project=? AND runtime=?',(P,RT))
result['coding_installation']=query("SELECT key,created_at,json_extract(body,'$.state') AS state,json_extract(body,'$.model_config_ref') AS model_config_ref,json_extract(body,'$.runtime_id') AS runtime_id FROM idempotency WHERE project=? AND operation='host:coding-installation' AND key=?",(P,'c671505efdffbb538c998cb7ca0265e1'))
result['newconfig_metadata']=query('SELECT model_config_ref,config_revision,config_hash,created_at FROM host_model_configurations WHERE model_config_ref=?',(MC,))
result['task']=query("SELECT id,revision,json_extract(body,'$.status') AS status,json_extract(body,'$.active_run_id') AS active_run_id FROM domain_objects WHERE project=? AND kind='Task' AND id=?",(P,'0469d97b91b04fd7fdeed77770ea1bed'))
result['window_tables']=query("SELECT name,sql FROM sqlite_master WHERE type='table' AND (name LIKE '%qualification%' OR name LIKE '%host_%')")
c.rollback();c.close();result['queries']=queries;put('live-readonly-observation.json',result);put('input-pins.json',pins)
print(json.dumps({k:v for k,v in result.items() if k not in ['queries','window_tables']},ensure_ascii=False))
