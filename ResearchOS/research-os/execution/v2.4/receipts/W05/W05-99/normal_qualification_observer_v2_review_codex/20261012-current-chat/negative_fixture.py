import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util, json, pathlib, sqlite3, traceback

OUT = pathlib.Path(__file__).resolve().parent
SOURCE = pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/researchos-storage-continuation-cp441-20261012/observer-v2/observe.py')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '0360de13d900c0787ef5e44cb19f13041bb3622ca1d0faeb1181463a9eca1f64'
spec = importlib.util.spec_from_file_location('frozen_observer', SOURCE)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
observer.PROJECT, observer.SESSION, observer.OWNER = 'fixture-project', 'fixture-session', 'fixture-owner'
request = dict(request_id='fixture-request',project_id=observer.PROJECT,session_id=observer.SESSION,model_config_ref='fixture-config',runtime_id='fixture-runtime',task_id='fixture-task',plan_hash='sha256:'+'a'*64,profile_hash='sha256:'+'b'*64,authorize_purpose='mu_turn',purpose_seconds=60,owner_host='fixture-host',owner_principal=observer.OWNER,owner_root=observer.OWNER,session_hash='sha256:'+'c'*64,configuration_hash='sha256:'+'d'*64,issued_at='2026-10-12T00:00:00Z',expires_at='2026-10-12T00:01:00Z')
raw = json.dumps(request,separators=(',',':'))
canonical = json.dumps(request,separators=(',',':'),sort_keys=True)
digest = 'sha256:'+hashlib.sha256(canonical.encode()).hexdigest()
result=[]
for storage in ['BLOB','TEXT']:
    db=OUT/('synthetic-'+storage.lower()+'.sqlite')
    assert not db.exists(), 'Append-only fixture database'
    with sqlite3.connect(db) as c:
        c.executescript('''CREATE TABLE client_sessions(id,project_id,revision,writer_epoch,writer_client_id,lease_expires_at,workspace_ref,model_config_ref,core_build_id,sealed_at,archived_at);
        CREATE TABLE runtime_qualification_plans(project,task,runtime,plan,plan_hash,author,author_root);
        CREATE TABLE domain_objects(project,kind,id,revision,body);
        CREATE TABLE runtime_qualification_runs(project);
        CREATE TABLE runtime_dispatches(project);
        CREATE TABLE resource_effects(project);
        CREATE TABLE idempotency(principal,project,operation,key,request_hash,body BLOB,created_at,PRIMARY KEY(principal,project,operation,key));''')
        c.execute('INSERT INTO client_sessions VALUES(?,?,?,?,?,?,?,?,?,?,?)',(observer.SESSION,observer.PROJECT,1,1,'fixture-client','2026-10-12T01:00:00Z','fixture-workspace','fixture-model','fixture-build',None,None))
        for scope in ['GLOBAL','PROJECT','GOAL']:
            c.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',(observer.PROJECT,'BudgetPolicy','fixture-'+scope,1,json.dumps({'scope_type':scope})))
        c.execute('INSERT INTO idempotency VALUES(?,?,?,?,?,?,?)',(observer.OWNER,observer.PROJECT,'host:qualification-confirmation','fixture-request',digest,raw.encode() if storage=='BLOB' else raw,'2026-10-12T00:00:00Z'))
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    observer.DATABASE=db
    assert observer.DATABASE.parent==OUT and observer.DATABASE.drive.upper()=='C:'
    try:
        observer.observe('fixture-request')
        entry={'storage':storage,'unexpected':'OBSERVATION_SUCCEEDED'}
    except Exception as error:
        entry={'storage':storage,'error':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    entry['database_unchanged']=before==hashlib.sha256(db.read_bytes()).hexdigest()
    entry['database_override']=str(observer.DATABASE)
    result.append(entry)
print(json.dumps({'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'fixture_only':True,'real_database_opened':False,'field_count':len(request),'domain_hash':digest,'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'canonical_sha256':hashlib.sha256(canonical.encode()).hexdigest(),'results':result},indent=2))
assert result[0]['error']=='AssertionError'
assert result[1]['message']=='ORIGINAL_REQUEST_HASH_MISMATCH'
assert all(r['database_unchanged'] for r in result)
