import pathlib,json,hashlib,subprocess,sqlite3
OUT=pathlib.Path(__file__).resolve().parent; ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-runtime-host-20261012'
SOURCE=ROOT/'execution/v2.4/receipts/W05/W05-99/normal_runtime_host_setup_codex/20261012-current-chat'
checks=[]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def ck(name,v):checks.append({'check':name,'passed':bool(v)})
m=load(SOURCE/'source-bundle-final.json');ck('source-bundle-final',sha(SOURCE/'source-bundle-final.json')=='61202522d7bd44b0a86dc66f2a8a394e6e0cd66e4d34d226f83b66f6f30ad95c')
ck('HEAD',subprocess.check_output(['git','-C',str(WT),'rev-parse','HEAD'],text=True).strip()==m['candidate'])
changed=subprocess.check_output(['git','-C',str(WT),'diff','--name-only',m['base'],m['candidate']],text=True).splitlines()
ck('exact18',len(m['source_files'])==18 and sorted(changed)==sorted(x['path'] for x in m['source_files']))
for row in m['source_files']:
 p=WT/row['path'];ck('source:'+row['path'],sha(p)==row['sha256']);ck('commit:'+row['path'],p.read_bytes().replace(b'\r\n',b'\n')==subprocess.check_output(['git','-C',str(WT),'show',m['candidate']+':'+row['path']]).replace(b'\r\n',b'\n'))
for row in m['evidence_files']:ck('evidence:'+row['path'],sha(SOURCE/row['path'])==row['sha256'])
resource=ROOT/'execution/v2.4/receipts/W05/W05-99/runtime_assets_resource_codex/20261012-current-chat'
r=load(resource/'manifest.json');ck('resource-manifest',sha(resource/'manifest.json')=='7440d892f14704d50e184685ce71ddeb570fd77e1c9c7ac4d826ebb18ec00ca3')
for row in r['assets']:ck('asset:'+row['path'],sha(row['path'])==row['sha256'] and pathlib.Path(row['path']).stat().st_size==row['bytes'])
ck('mu-source',sha(WT/'adapters/runtime/mu/worker.mjs')==r['build_meta']['source_sha256'])
invocation=load(resource/'build-invocation.json')
ck('resource_producer',sha(WT/'adapters/runtime/mu/build.mjs')==invocation['source_sha256'] and invocation['exit_code']==0 and invocation['worker_source_sha256']==r['build_meta']['source_sha256'])
ck('resource_node_identity',sha(invocation['argv'][0])==invocation['node_sha256']==r['assets'][0]['sha256'])
ck('mu_pins',r['build_meta']['mu_commit']=='8dfebe36508ac0c2508735bb866756dab9283e74' and r['build_meta']['vendored_files_verified']==5083 and r['build_meta']['sdk_version']==r['build_meta']['ai_version']=='0.87.1' and r['build_meta']['esbuild_version']=='0.28.2')
vendor=load(ROOT/'third_party/mu.MANIFEST.json')
ck('vendor_manifest_count',len(vendor['entries'])==5083)
for name,row in vendor['entries'].items():ck('vendor:'+name,sha(ROOT/name)==row['sha256'] and (ROOT/name).stat().st_size==row['size'])
smoke=load(SOURCE/'control-cold-session-smoke.json');db=sqlite3.connect((pathlib.Path(smoke['data_root'])/'researchos.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
census={}
for table in ['runtime_bindings','runtime_qualification_plans','client_sessions','resource_effects','runtime_dispatches']:census[table]=db.execute('select count(*) from '+table).fetchone()[0]
for kind in ['Run','AcceptanceReceipt','BudgetLedgerEntry']:census[kind]=db.execute('select count(*) from domain_objects where kind=?',(kind,)).fetchone()[0]
expected=load(SOURCE/'control-cold-session-db-census.json')['counts'];ck('retained_DB_census',census==expected)
reg=[load for (body,) in db.execute("select body from domain_objects where kind='RuntimeRegistration'") for load in [json.loads(body)]]
ck('REGISTERED_no_qualification',len(reg)==1 and reg[0]['status']=='REGISTERED' and not reg[0]['qualification_ids'])
identities=db.execute('select principal,root,parent from orchestration_identity order by principal').fetchall();ck('three_identity_lineages',len(identities)==3 and len(set(x[1] for x in identities))==1)
ck('no_VERIFIER',db.execute("select count(*) from auth_principals where roles like '%VERIFIER%'").fetchone()[0]==0)
commands=db.execute("select operation,json_extract(body,'$.status'),count(*) from idempotency where operation in ('v2:host.configure','v2:workspace.register','v2:project.bootstrap','v2:session.create') group by operation,json_extract(body,'$.status') order by operation").fetchall()
ck('cold_creation_journal_completed',len(commands)==4 and all(status=='COMPLETED' and count==1 for _,status,count in commands))
ck('retained_control_binary',sha(ROOT/'.local/builds/normal-runtime-host-candidate-20261012/researchos-control.exe')==smoke['binary_sha256'])
db.close()
(OUT/'source_verification.json').write_text(json.dumps({'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'retained_db_counts':census,'identity_lineages':identities,'cold_typed_command_journal':commands},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':sum(x['passed'] for x in checks),'failed':[x['check'] for x in checks if not x['passed']]}))
