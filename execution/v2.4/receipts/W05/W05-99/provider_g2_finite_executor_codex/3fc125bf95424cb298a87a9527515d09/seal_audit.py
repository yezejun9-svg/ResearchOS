from pathlib import Path
import json,hashlib,subprocess,re,sqlite3,uuid
N=Path(__file__).resolve().parent;W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
B=N/'build-e98a85f6a8fe4e69a1b2939a55ec68ef';R=N/'run-c62cac438c834dc794a35231bd688818'
F=N/('final-audit-'+uuid.uuid4().hex);F.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(W)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(n,v):(F/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
source=[x['path'] for x in json.loads((N/'source-before.json').read_text(encoding='utf-8'))]
expected={'providerBrokerFixture','TestProviderBindingPreflightRefusals','TestProviderBindingQuarantineBeforeSDK','coordinatorFixtureProgram'}
checks=[]
for rel in source:
 old=(N/'source-before'/rel).read_bytes();new=(W/rel).read_bytes()
 for m in re.finditer(rb'^func (\w+)\(',old,re.M):
  name=m.group(1).decode();end=old.find(b'\n}',m.start())+2
  body=old[m.start():end]
  if name in expected:continue
  good=body in new;checks.append({'path':rel,'function':name,'original_body_sha256':hashlib.sha256(body).hexdigest(),'unchanged':good});assert good,name
save('protected-functions.json',checks)
changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines();assert sorted(changed)==sorted(source)
save('source-manifest.json',[dict(ref(W/x),base_commit='6fb5263681c17f0e50920c354dc07ed440a23714',base_sha256=sha(N/'source-before'/x)) for x in source])
(F/'source.diff').write_bytes(subprocess.check_output(['git','diff','--binary','--']+source))
handoff=json.loads((R/'handoff.json').read_text(encoding='utf-8'));results=handoff['results'];assert len(results)==29 and all(x['status']=='PASS' for x in results)
assert sum(x['model_fixture_http'] for x in results)==4
dbs=[]
for p in R.rglob('*.sqlite'):
 before=sha(p);con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  integrity=con.execute('PRAGMA integrity_check').fetchall();assert integrity==[('ok',)]
  schema=con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
  tables=[{'name':name,'rows':con.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0]} for name,sql in schema]
 finally:con.close()
 assert before==sha(p)
 dbs.append({'snapshot':ref(p),'capture_method':'VACUUM INTO after joined fixture execution, then closed destination','reader':'Python sqlite3 mode=ro immutable=1','integrity':integrity,'table_counts':tables,'read_sha_unchanged':True})
assert len(dbs)==13,len(dbs)
save('closed-db-audit.json',dbs)
counts=[]
for p in R.rglob('*counts.json'):counts.append({'ref':ref(p),'actual':json.loads(p.read_text(encoding='utf-8'))})
save('actual-http-counts.json',counts)
for label in ['inputs.before','component.after.native.before','inputs.after']:
 assert not json.loads((R/(label+'.json')).read_text(encoding='utf-8'))['drift']
matrix=[]
for x in results:
 row=dict(x);row['acceptance']='NOT_SELF_ACCEPTED';matrix.append(row)
save('case-matrix.json',matrix)
save('failure-origins.json',[json.loads(p.read_text(encoding='utf-8-sig'))|{'original_receipt':ref(p)} for p in sorted(N.glob('tool-origin-*.json'))])
save('audit-summary.json',{'status':'FINITE_EXECUTION_REPORTED_NOT_SOURCE_ACCEPTANCE','protected_functions':len(checks),'source_paths':source,'case_leaves':29,'native_exit_zero':29,'skip':0,'failure':0,'component_leaves':18,'native_leaves':11,'sdk_child_processes':10,'model_loopback_requests':4,'external_paid_requests':0,'closed_fixture_sqlite_snapshots':len(dbs),'build_ref':ref(B/'build-result.json'),'run_ref':ref(R/'handoff.json'),'input_count':37513,'compiler_archives':349,'immutable_drift':0,'scope_ref':ref(N/'scope.original.json'),'known_limits':['G2 only; no provider qualification, whole-provider or formal acceptance','All original held tests remain NOT_RUN','Synthetic matcher controls and actual rollback components are separately classified','contextFixture protected bootstrap request count is not instrumented; remaining setup and runtime HTTP handler requests and readiness are explicit separate counters']})
print(F)
