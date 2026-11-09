import json,sqlite3,pathlib
p=pathlib.Path(__file__).parent
row=json.loads((p/'control-cold-session-smoke.json').read_text(encoding='utf-8-sig'))
db=sqlite3.connect('file:'+row['data_root']+'/researchos.sqlite?mode=ro',uri=True)
runtimes=[json.loads(x[0]) for x in db.execute("SELECT body FROM domain_objects WHERE kind='RuntimeRegistration'")]
tasks=[json.loads(x[0]) for x in db.execute("SELECT body FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.task_type')='runtime_qualification'")]
counts={k:db.execute('SELECT count(*) FROM domain_objects WHERE kind=?',(k,)).fetchone()[0] for k in ['Run','AcceptanceReceipt','BudgetLedgerEntry']}
counts.update({k:db.execute('SELECT count(*) FROM '+k).fetchone()[0] for k in ['resource_effects','runtime_dispatches','runtime_bindings','runtime_qualification_plans','client_sessions']})
assert len(runtimes)==1 and runtimes[0]['status']=='REGISTERED'
assert len(tasks)==1 and tasks[0]['status']=='DRAFT'
assert all(counts[k]==0 for k in ['Run','AcceptanceReceipt','BudgetLedgerEntry','resource_effects','runtime_dispatches'])
assert all(counts[k]==1 for k in ['runtime_bindings','runtime_qualification_plans','client_sessions'])
out={'candidate':'a57ca3e33b4e9d7c9351cd4143f8914c936f6bda','cold_start_real_control':True,'real_shell_chooser':True,'session_create':row['session_create'],'runtime_status':runtimes[0]['status'],'qualification_task_status':tasks[0]['status'],'counts':counts,'passed':True}
(p/'control-cold-session-db-census.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
db.close()
