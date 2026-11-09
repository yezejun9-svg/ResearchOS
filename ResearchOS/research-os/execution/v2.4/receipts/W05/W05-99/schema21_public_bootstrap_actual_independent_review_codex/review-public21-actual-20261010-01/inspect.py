import json,hashlib,sqlite3
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
s=json.loads((R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public21-caller-9690cc6324834ded8781ce8a2233fa82/runner-returned-state.root.json').read_bytes())
c=json.loads(Path(s['contract_ref']['path']).read_bytes())
q=json.loads(Path(s['root_context']['resource_qualification_ref']['path']).read_bytes())
db=Path(s['baseline_ref']['path'])
con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
con.execute('PRAGMA query_only=ON')
out={'ledger_columns':[r[1] for r in con.execute('PRAGMA table_info(schema_migrations)')],'session_columns':[r[1] for r in con.execute('PRAGMA table_info(client_sessions)')],'trigger_names':[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'")],'qkeys':list(q),'guards':{k:{x:v.get(x) for x in ('verification','closed','retained_handles_count','errors')} for k,v in s['guard_cleanup'].items()}}
con.close()
for name,ref in [('facts',json.loads(Path(s['root_context']['registration_result_ref']['path']).read_bytes())['facts_ref']),('qualification_peer',q['review_hostpair_binding_ref']),('qualification_root',q['root_issuance_binding_ref'])]:
 out[name]=json.loads(Path(ref['path']).read_bytes())
print(json.dumps(out,ensure_ascii=False))

