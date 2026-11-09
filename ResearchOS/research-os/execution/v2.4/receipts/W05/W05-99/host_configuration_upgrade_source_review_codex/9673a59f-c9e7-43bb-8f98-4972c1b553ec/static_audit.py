from pathlib import Path
import json,hashlib,sqlite3,sys,datetime
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).parent;L=json.loads((O/'locations.json').read_bytes());R=Path(L['root']);W=Path(L['worktree']);P=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/handoff-5375496dd2b24206b5db17fc9bc358c3';H=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':H(b),'bytes':len(b)}
def save(n,j):(O/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=[]
def read(p):
 b=p.read_bytes();audit.append(ref(p));return json.loads(b)
handoff=read(P/'handoff.json');final=read(P/'final_handoff.json');gates=read(P/'gates.json')
verified={}
def verify(e,root=W):
 if not isinstance(e,dict):return
 if 'path' in e and 'sha256' in e:
  p=root/e['path'];r=ref(p);assert r['sha256']==e['sha256'],str(p);verified[str(p)]=r
for j in [handoff,final]:
 for e in j.values():verify(e)
raw_cache={};gate_summary=[]
for g in gates:
 for e in g['raw_test_refs']:
  verify(e['raw']);p=W/e['raw']['path']
  if str(p) not in raw_cache:raw_cache[str(p)]=p.read_text(encoding='utf-8').splitlines()
  raw=raw_cache[str(p)];loc=e['raw']['locator'];lines=raw[loc['line_start']-1:loc['line_end']]
  found=[json.loads(x) for x in lines];assert any(x.get('Test')==e['test'] and x.get('Action')==e['action'] for x in found),(g['id'],e['test'])
 gate_summary.append({'id':g['id'],'executor_status':g['status'],'claim':g['claim'],'verified_raw_locators':len(g['raw_test_refs'])})
dbs=[]
for e in handoff['closed_sqlite_snapshots']:
 verify(e);p=W/e['path'];before=ref(p);db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  tables={n for n, in db.execute("SELECT name FROM sqlite_master WHERE type='table'")};counts={}
  for n in ['host_model_configurations','host_model_config_heads','client_command_identities','idempotency','client_sessions','client_command_queue','client_control_requests','client_control_receipts','resource_effects']:
   counts[n]=db.execute('SELECT count(*) FROM '+n).fetchone()[0] if n in tables else None
  versions=[v for v, in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
  states=list(db.execute("SELECT json_extract(body,'$.state'),count(*) FROM resource_effects GROUP BY json_extract(body,'$.state')"))
  dbs.append({'ref':before,'versions':versions,'counts':counts,'effect_states':states,'readonly_immutable':True})
 finally:db.close()
 assert before==ref(p)
fnd=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json';f=read(fnd)
for e in f['independent_tests']:
 for key in ['result_ref','stdout_ref','invocation_ref']:verify(e[key],R)
summary={'status':'STATIC_FROZEN10_AUDIT_ONLY_FINAL11_PENDING','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':'125ea34ca0878f18c4dce47f9259ab5e9e77c2eb','source_freeze':ref(O/'static_source_freeze.json'),'reference_checks':list(verified.values()),'top_reads':audit,'gate_locators':gate_summary,'closed_public_databases':dbs,'foundation_review':ref(fnd),'foundation_review_identity':{'reviewer':f['reviewer_id'],'executor':f['executor_id']},'independent_tests_this_review':0,'product_source_changes':0,'formal_increment':0}
save('static_receipt_audit.json',summary);print(json.dumps({'verified_refs':len(verified),'gates':len(gates),'closed_DBs':len(dbs),'foundation_review_hash':ref(fnd)['sha256'],'static_only':True}))
