import datetime,hashlib,json,pathlib,sqlite3,subprocess
P=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
D=R/'execution/v2.4/receipts/W05/W05-99/normal_desktop_actual_qualification_preparation_codex/20261012-current-chat/preparation-draft-01.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
assert sha(D)=='831f3f509e0b0067ebc8cf3ba7f936da8ded72c2c96b60bf12c0f317c05739d2'
draft=json.loads(D.read_text('utf-8-sig'))
sources=['apps/web/src/workbench.jsx','apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/ipc.js','apps/desktop/preload/preload.js','apps/control/main.go','internal/host/desktop_management_windows.go','internal/host/runtime_setup_windows.go','internal/host/runtime_qualification_windows.go','internal/host/runtime_verifier_process_windows.go','internal/domain/client_runtime_setup_windows.go','internal/domain/runtime_qualification_confirmation_windows.go','internal/domain/runtime_qualification_execution_windows.go','internal/domain/runtime_qualification.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_model_unknown_verification.go','internal/domain/runtime_drain_windows.go','internal/verifier/client.go','adapters/runtime/bridge_windows.go','adapters/runtime/mu/worker.mjs','adapters/runtime/mu/package.json','ops/experiment_sandbox/sandbox_windows.go','ops/experiment_sandbox/async_windows.go']
write('source-binding.json',dict(head=subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD']).decode().strip(),draft_sha256=sha(D),sources=[dict(path=x,sha256=sha(R/x),bytes=(R/x).stat().st_size) for x in sources],metadata=[dict(path=x['path'],sha256=sha(R/x['path']),matches=sha(R/x['path'])==x['sha256']) for x in draft['resource_metadata']]))
dbpath=pathlib.Path(draft['data_root'])/'researchos.sqlite'
db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True)
db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
def query(sql,args=()):
 c=db.execute(sql,args);return [dict(zip([v[0] for v in c.description],r)) for r in c.fetchall()]
tables={r['name'] for r in query("SELECT name FROM sqlite_master WHERE type='table'")}
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),path=str(dbpath),mode='ro',query_only=db.execute('PRAGMA query_only').fetchone()[0])
out['kind_counts']=query("SELECT kind,count(*) AS count FROM domain_objects WHERE kind IN ('Task','Run','Goal','RuntimeRegistration','BudgetLedgerEntry','BudgetPolicy','WorkspaceBinding','AcceptanceReceipt') GROUP BY kind ORDER BY kind")
out['table_counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['client_sessions','resource_effects','runtime_dispatches','runtime_qualification_runs','runtime_qualification_plans','runtime_bindings','runtime_observations','uploaded_content'] if t in tables}
out['private_qualification_receipt_counts']=query("SELECT operation,count(*) AS count FROM idempotency WHERE operation IN ('host:qualification-confirmation','host:managed-runtime-qualification','host:managed-verifier-lineage') GROUP BY operation")
out['workspaces']=query("SELECT id,revision,json_extract(body,'$.principal_id') AS principal_id,json_extract(body,'$.project_id') AS project_id,json_extract(body,'$.status') AS status,json_extract(body,'$.access') AS access FROM domain_objects WHERE kind='WorkspaceBinding'")
out['budget_policies']=[json.loads(r['body']) for r in query("SELECT body FROM domain_objects WHERE kind='BudgetPolicy'")]
out['orchestration_identity']=query('SELECT principal,root,parent FROM orchestration_identity')
if 'host_model_configurations' in tables:
 cols=[r['name'] for r in query('PRAGMA table_info(host_model_configurations)')]
 safe=[c for c in ['model_config_ref','owner_host_ref','principal','config_revision','provider_id','model_id','base_url','credential_ref','config_hash','configuration_hash','body'] if c in cols and c!='body']
 out['model_configurations']=query('SELECT '+','.join(safe)+' FROM host_model_configurations')
out['sessions_columns']=[r['name'] for r in query('PRAGMA table_info(client_sessions)')]
safe=[c for c in ['id','project_id','revision','writer_epoch','writer_client_id','writer_expires_at','workspace_ref','model_config_ref','sealed','archived'] if c in out['sessions_columns']]
out['sessions']=query('SELECT '+','.join(safe)+' FROM client_sessions')
db.rollback();db.close()
write('current-safe-state.json',out)
print(json.dumps(dict(head=json.loads((P/'source-binding.json').read_text('utf-8'))['head'],counts=out['table_counts'],kind_counts=out['kind_counts'],draft_bound=True,queries_readonly=True)))
