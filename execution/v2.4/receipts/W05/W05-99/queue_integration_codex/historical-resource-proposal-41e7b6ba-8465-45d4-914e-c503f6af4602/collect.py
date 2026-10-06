from pathlib import Path
import hashlib,json,subprocess,re,os,base64,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
go=read(ROOT/'execution/toolchains/locked.json')['tools']['go'];assert sha(Path(go['path']))==go['sha256']
env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(Path(go['path']).parents[1]))
commands=[]
def run(name,argv):
    if (HERE/(name+'.stdout.raw')).exists():name='second-'+name
    assert not (HERE/(name+'.stdout.raw')).exists()
    p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
    (HERE/(name+'.stdout.raw')).write_bytes(p.stdout);(HERE/(name+'.stderr.raw')).write_bytes(p.stderr)
    commands.append({'name':name,'argv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'environment':{k:env[k] for k in ('GOTOOLCHAIN','GOENV','GOROOT')},'stdout':ref(HERE/(name+'.stdout.raw')),'stderr':ref(HERE/(name+'.stderr.raw'))})
    return p.stdout.decode('utf-8',errors='replace')
binaries=[]
for p in sorted((ROOT/'.local').glob('*/*.exe')):
    if any(x in p.as_posix().lower() for x in ('private','secrets','holdout')):continue
    if p.parent.name not in ('bin','current-control-attempt05','current-control-attempt06','current-control-attempt07','current-control-attempt08','current-control-attempt09','current-control-attempt10'):continue
    info=run('buildinfo-'+str(len(binaries)),[go['path'],'version','-m',str(p)])
    rev=re.search(r'vcs.revision=(\w+)',info)
    binaries.append({**ref(p),'go_buildinfo':info,'revision':rev.group(1) if rev else None})
public=ROOT/'execution/receipts/W16/control-business-proof/104b83f'
bundles=[]
for test in ('TestW16ControlReplayNative','TestW16ControlBusinessNoGain'):
    p=public/(test+'-public-bundle.json');b=read(p)
    fs=b.get('files',b.get('Files',{}))
    assert 'snapshot.sqlite' in fs,list(b)
    snapshot=base64.b64decode(fs['snapshot.sqlite'])
    # sqlite3.deserialize cannot attach a WAL-mode image without a backing path.
    # Read only a derived in-memory view with header journal-mode bytes switched
    # to rollback mode; the public artifact bytes/hash are never changed.
    view=bytearray(snapshot);view[18]=view[19]=1
    db=sqlite3.connect(':memory:');db.deserialize(bytes(view));db.execute('PRAGMA query_only=ON')
    versions=[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    db.close()
    hashes={k:hashlib.sha256(base64.b64decode(v)).hexdigest() for k,v in fs.items()}
    bundles.append({'test':test,'bundle':ref(p),'suite':ref(public/(test+'-public-suite.json')),'binding':b.get('binding',b.get('Binding')),'versions':versions,'tables':tables,'file_sha256':hashes})
source_paths=['internal/domain/backup_upgrade_test.go','internal/domain/backup_upgrade_final_test.go','internal/domain/durability.go','internal/domain/evolution_control_test.go','internal/domain/evolution_control_projection.go','evaluation/evolution/control_release.go','migrations/sqlite/0017_runtime_dispatch.sql','.local/releases/schema14-09a6a5e/internal/domain/durability.go','.local/releases/schema14-09a6a5e/internal/domain/backup_upgrade_test.go','.local/releases/schema14-09a6a5e/apps/control/main.go','execution/receipts/W16/control-business-proof/manifest.json','execution/receipts/W17/local-upgrade/integration-10cbc005-9ccd-4c20-8517-fac98e08d454/report.json','execution/receipts/W17/local-upgrade/actual-20260930T142007Z/upgrade.stdout.json','execution/v2.4/receipts/W07/W07-99/integration_codex/resume-r240/legacy14-resource-mapping.json']
inputs=[ref(ROOT/p) for p in source_paths]
history={}
for rev in ('09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0','104b83f0f4a6634a1367938da2bbf7b496483da2'):
    history[rev]=run('migrations-'+rev[:7],['git','ls-tree','-r','--name-only',rev,'migrations/sqlite']).splitlines()
    run('legacy-tests-'+rev[:7],['git','show',rev+':internal/domain/'+('backup_upgrade_test.go' if rev.startswith('09a') else 'evolution_control_test.go')])
write(HERE/'resource_audit.json',{'mode':'READ_ONLY_RESOURCE_AND_PUBLIC_FIXTURE_INSPECTION_NO_PRODUCT_EXECUTION','binaries':binaries,'public_schema20_bundles':bundles,'inputs':inputs,'historical_migration_inventory':history,'commands':commands,'existing_database_opened':False,'public_fixture_sqlite_in_memory_only':True,'inspection_view':'Derived in-memory SQLite header bytes18/19 set1 solely to inspect WAL-mode standalone image; artifact unchanged. Not an executable restored fixture.','historical_control_started':False,'external_model_calls':0,'investigation_failures':['First collect.py stopped at sqlite3.deserialize WAL-mode query: OperationalError unable to open database file. First read-only buildinfo stdout/stderr retained; second prefixed calls do not overwrite them.','Pre-collector rg Windows wildcard arguments and nonexistent evolution_control.go/routes.go returned missing-path errors; corrected to directory plus -g without source writes.']})
print(json.dumps({'binaries':[{k:b[k] for k in ('path','sha256','revision')} for b in binaries],'bundles':[{k:b[k] for k in ('test','versions')} for b in bundles]},indent=2))
