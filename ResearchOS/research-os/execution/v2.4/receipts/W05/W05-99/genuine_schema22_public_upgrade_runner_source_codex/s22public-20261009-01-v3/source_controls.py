"""Pure Source controls. These do not execute the public runner, SQLite or Win32."""
from pathlib import Path
import ast, copy, hashlib, json, types

O=Path(__file__).resolve().parent
source=(O/'public22_runner.py').read_bytes()
module=types.ModuleType('public22_runner_source_controls')
exec(compile(source,str(O/'public22_runner.py'),'exec'),module.__dict__)
contract=json.loads((O/'contract.json').read_bytes())
rows=[]
def check(name,ok):
    rows.append({'id':name,'passed':bool(ok),'scope':'PURE_SOURCE_CONTROL_NOT_RUNTIME'})
    if not ok:raise AssertionError(name)
def reject(name,call,expected):
    try:call()
    except module.BoundaryError as exc:check(name,str(exc)==expected)
    else:check(name,False)
check('v3-contract-pins-exact-runner',contract['source_runner_ref']['sha256']==hashlib.sha256(source).hexdigest() and contract['source_runner_ref']['bytes']==len(source))
check('v3-author-not-v2-native-author',contract['source_author']==module.AUTHOR and module.AUTHOR!='codex:/root/native_temp_independent_review')
check('v3-recheck-no-original1025-reclassification',contract['existing_public22_recheck_contract']['original1025_remains_failure'] is True and contract['existing_public22_recheck_contract']['no_new_output_or_child'] is True)
request={'case_id':'a'*32,'output_root':contract['output_parent']+'/schema22-public-'+'a'*32,'end_version':22}
projection=module.compile_case(contract,request)
check('finite22-four-public-commands',len(projection['phases'])==4)
check('bootstrap-authentic-old-control-only',projection['phases'][0]['argv'][0]==contract['old22_control']['path'] and projection['phases'][0]['argv'][1]=='--bootstrap-owner')
check('public-backup-create-restore-no-invented-verify-verb',[p['argv'][1] for p in projection['phases'][1:]]==['keygen','create','restore'])
check('recovery-key-outside-backup',projection['paths']['key'].startswith(projection['paths']['private']) and not projection['paths']['key'].startswith(projection['paths']['backup22']))
for version in [21,24,True]:
    bad={**request,'end_version':version}
    reject('reject-version-'+str(version),lambda bad=bad:module.compile_case(contract,bad),'MAIN_PUBLIC_23_TO_24_NOT_ADOPTED')
for label,path in [('parent-segment',contract['output_parent']+'/child/../schema22-public-'+'a'*32),('sibling',contract['output_parent']+'/another-run'),('drive-relative','D:case'),('ADS',request['output_root']+':stream'),('UNC','//server/share/case')]:
    bad={**request,'output_root':path}
    try:module.compile_case(contract,bad)
    except module.BoundaryError:check('reject-output-'+label,True)
    else:check('reject-output-'+label,False)
reject('reject-bool-case-id',lambda:module.compile_case(contract,{**request,'case_id':True}),'CASE_ID_INVALID')
reject('reject-extra-request-field',lambda:module.compile_case(contract,{**request,'authorized':True}),'REQUEST_FIELDS_INVALID')
reject('reject-author-substitution',lambda:module.compile_case({**contract,'source_author':'/root'},request),'SOURCE_AUTHOR_BINDING_MISMATCH')
for ref in [{'path':'D:/test','sha256':'0'*64,'size':1},{'path':'D:/test','sha256':'0'*64,'bytes':True},{'path':'D:/test','sha256':'0'*64,'bytes':1,'approved':True}]:
    try:module.exact_ref(ref)
    except module.BoundaryError:check('reject-invalid-exact-ref-'+str(len(rows)),True)
    else:check('reject-invalid-exact-ref-'+str(len(rows)),False)
reject('reject-unrebound-main23-candidate',lambda:module.upgrade23_phases(contract,projection,contract['main23_candidate_only']),'UNREBOUND_MAIN23_CANDIDATE_PROHIBITED')
fresh={'path':'D:/RootRegistered/fresh-main23.exe','sha256':'1'*64,'bytes':100}
phases=module.upgrade23_phases(contract,projection,fresh)
check('upgrade23-real-public-plan',phases[0]['argv'][1]=='upgrade-local' and phases[0]['argv'][-1]=='schema22-to23-host-model-configuration-v1')
check('upgrade23-exact-working22-input',phases[0]['argv'][phases[0]['argv'].index('--db')+1]==projection['paths']['workdb22'])
check('upgrade23-never-writes-baseline-as-input',projection['paths']['db22'] not in phases[0]['argv'])
check('upgrade23-old-program-identity-stays22',phases[0]['argv'][phases[0]['argv'].index('--source-program')+1]==contract['old22_control']['path'])
check('upgrade23-output-public-verification',[p['argv'][1] for p in phases[1:]]==['create','restore'])
module.same_json({'status':'x'},{'status':'x'})
reject('reject-emitted-persisted-mismatch',lambda:module.same_json({'status':'x'},{'status':'y'}),'PUBLIC_EMITTED_PERSISTED_RECEIPT_MISMATCH')
base={'actual_exit':0,'timed_out':False,'error':None,'owned_child_pid':123,'creation_time_100ns':123456,'resumed':True,'job_cleanup':{'unnamed_exclusive_job':True,'kill_on_job_close_configured':True,'assigned_before_resume':True,'job_idle_confirmed':True,'primary_exit_confirmed':True,'handles_closed':True,'active_processes_last_observed':0,'errors':[]}}
check('positive-cleanup-observation-shape',module.closed_job(base))
for field,value,code in [('actual_exit',None,'PUBLIC_CHILD_FAILED'),('actual_exit',False,'PUBLIC_CHILD_FAILED'),('timed_out',True,'PUBLIC_CHILD_FAILED'),('creation_time_100ns',None,'CHILD_CREATION_FILETIME_NOT_OBSERVED')]:
    bad={**base,field:value}
    reject('reject-child-'+field+'-'+str(value),lambda bad=bad:module.closed_job(bad),code)
for field in ['assigned_before_resume','job_idle_confirmed','handles_closed']:
    bad=copy.deepcopy(base);bad['job_cleanup'][field]=False
    reject('reject-cleanup-'+field,lambda bad=bad:module.closed_job(bad),'OWNED_JOB_CLEANUP_UNCONFIRMED')
bad=copy.deepcopy(base);bad['job_cleanup']['active_processes_last_observed']=1
reject('reject-surviving-descendant',lambda:module.closed_job(bad),'OWNED_JOB_NOT_EMPTY')
empty={'count':0,'rows_sha256':'0'*64}
db={'versions':list(range(1,23)),'integrity':['ok'],'foreign_key_violations':0,'tables':{'client_sessions':empty,'client_command_queue':empty}}
check('positive-exact22-ledger',module.validate_ledger(db,22))
reject('reject-labelled21-as22',lambda:module.validate_ledger({**db,'versions':list(range(1,22))},22),'EXACT_SCHEMA_LEDGER_REQUIRED')
reject('reject-boolean-ledger',lambda:module.validate_ledger({**db,'versions':[True]+list(range(2,23))},22),'EXACT_SCHEMA_LEDGER_REQUIRED')
pop=copy.deepcopy(db);pop['tables']['client_sessions']={'count':1}
reject('reject-nonempty-scope-inflation',lambda:module.validate_ledger(pop,22),'BOOTSTRAP_ONLY_TYPED_EMPTY_SCOPE_REQUIRED')
reject('reject-numbered23-without-configuration-tables',lambda:module.validate_ledger({**db,'versions':list(range(1,24))},23),'EMPTY_CONFIGURATION_PROFILE_REQUIRED')
db23=copy.deepcopy(db);db23['versions']=list(range(1,24))
for name in ['client_command_identities','host_model_configurations','host_model_config_heads']:db23['tables'][name]=empty
check('positive23-required-tables',module.validate_ledger(db23,23))
dummy={'path':'D:/Unopened/input.json','sha256':'0'*64,'bytes':1}
reject('no-scope-no-file-or-process',lambda:module.run_registered_case(dummy,dummy,None),'LIVE_ROOT_SCOPE_REQUIRED')
reject('json-is-not-live-Root-scope',lambda:module.run_registered_case(dummy,dummy,{'actor':'Root','approved':True}),'LIVE_ROOT_SCOPE_REQUIRED')
class Revoked:
    def require_registered(self,*a,**kw):raise module.BoundaryError('ROOT_LEASE_REVOKED')
    def require_phase(self,*a,**kw):raise AssertionError('must not reach phase')
    def receipt_context(self):raise AssertionError('must not read context')
    def qualified_current_main23(self,*a):raise AssertionError('must not reach binding')
reject('Root-denial-before-any-read-or-create',lambda:module.run_registered_case(dummy,dummy,Revoked()),'ROOT_LEASE_REVOKED')
tree=ast.parse(source)
check('no-standalone-activation-entrypoint',not any(isinstance(x,ast.If) and '__name__' in ast.unparse(x.test) for x in tree.body))
check('sqlite-import-is-lazy-read-observer-only',not any(isinstance(x,(ast.Import,ast.ImportFrom)) and 'sqlite3' in ast.unparse(x) for x in tree.body))
check('no-sql-DML-in-source',not any(isinstance(n,ast.Constant) and isinstance(n.value,str) and reword in n.value.upper() for n in ast.walk(tree) for reword in ['INSERT INTO','UPDATE AUTH_','CREATE TABLE','DELETE FROM']))
check('explicit-readonly-observer',b'?mode=ro&immutable=1' in source and b'PRAGMA query_only=ON' in source)
check('explicit-baseline-readonly-attribute',b'os.chmod(baseline["path"], stat.S_IREAD)' in source)
check('Sourceguard-finally-close-present',b'audit = guard.close()' in source)

# F1: the production verify22 primitive, with synthetic digests and no database.
go_source=Path(contract['old22_recovery_source']['path']).read_text(encoding='utf-8')
trigger=module.expected_restore_trigger_sql(go_source)
check('F1-exact-frozen-Go-restore-trigger-extracted',trigger.startswith('CREATE TRIGGER backup_require_fresh_observation BEFORE UPDATE ON domain_objects\n'))
schema=[['table','auth_credentials','auth_credentials','CREATE TABLE auth_credentials(token_hash TEXT PRIMARY KEY,revoked INTEGER)'],['table','auth_principals','auth_principals','CREATE TABLE auth_principals(id TEXT PRIMARY KEY)']]
schema.sort(key=lambda r:(r[0],r[1]))
sealed=copy.deepcopy(db)
sealed['schema_rows']=schema
sealed['schema_sha256']=module.schema_digest(schema)
sealed['tables'].update(auth_principals={'count':1,'rows_sha256':'b'*64},auth_credentials={'count':1,'rows_sha256':'c'*64},domain_objects={'count':1,'rows_sha256':'d'*64})
for i in range(78):sealed['tables']['synthetic_%02d'%i]={'count':0,'rows_sha256':'0'*64}
assert len(sealed['tables'])==83
sealed['credentials']={'columns':['token_hash','revoked'],'pk_columns':['token_hash'],'count':1,'all_revoked_zero':True,'all_revoked_one':False,'source_rows_sha256':'c'*64,'expected_revoked_rows_sha256':'e'*64}
restored=copy.deepcopy(sealed)
restored['schema_rows']=sorted(schema+[['trigger','backup_require_fresh_observation','domain_objects',trigger]],key=lambda r:(r[0],r[1]))
restored['schema_sha256']=module.schema_digest(restored['schema_rows'])
restored['tables']['auth_credentials']['rows_sha256']='e'*64
restored['credentials'].update(all_revoked_zero=False,all_revoked_one=True,source_rows_sha256='e'*64)
manifest={'migrations':list(range(1,23)),'schema_hash':'sha256:'+sealed['schema_sha256']}
check('F1-exact-public-restore-delta-accepted',module.validate_restore22(restored,sealed,manifest,trigger))
def changed_schema(row_change):
    altered=copy.deepcopy(restored);row_change(altered['schema_rows']);altered['schema_rows'].sort(key=lambda r:(r[0],r[1]));altered['schema_sha256']=module.schema_digest(altered['schema_rows']);return altered
for label,altered,code in [
    ('missing-trigger',changed_schema(lambda rows:rows.pop()),'PUBLIC_RESTORE_TRIGGER_MISMATCH'),
    ('extra-trigger',changed_schema(lambda rows:rows.append(['trigger','unexpected','domain_objects','CREATE TRIGGER unexpected AFTER UPDATE ON domain_objects BEGIN SELECT 1; END'])),'PUBLIC_RESTORE_SCHEMA_MISMATCH'),
    ('altered-trigger',changed_schema(lambda rows:rows[-1].__setitem__(3,rows[-1][3]+' ')),'PUBLIC_RESTORE_TRIGGER_MISMATCH'),
]:reject('F1-reject-'+label,lambda altered=altered:module.validate_restore22(altered,sealed,manifest,trigger),code)
for label,change,code in [
    ('dropped-owner',lambda d:d['tables']['auth_principals'].update(count=0),'PUBLIC_RESTORE_OWNER_ROW_REQUIRED'),
    ('changed-owner-row',lambda d:d['tables']['auth_principals'].update(rows_sha256='f'*64),'PUBLIC_RESTORE_TABLE_STATE_MISMATCH'),
    ('changed-domain-row',lambda d:d['tables']['domain_objects'].update(rows_sha256='f'*64),'PUBLIC_RESTORE_TABLE_STATE_MISMATCH'),
    ('changed-other-table',lambda d:d['tables']['synthetic_77'].update(rows_sha256='f'*64),'PUBLIC_RESTORE_TABLE_STATE_MISMATCH'),
    ('wrong-auth-full-row',lambda d:d['tables']['auth_credentials'].update(rows_sha256='f'*64),'PUBLIC_CREDENTIAL_DIGEST_INCONSISTENT'),
    ('revoked-not-one',lambda d:d['credentials'].update(all_revoked_one=False),'PUBLIC_RESTORE_CREDENTIAL_REVOCATION_REQUIRED'),
    ('changed-auth-PK',lambda d:d['credentials'].update(pk_columns=['different']),'PUBLIC_RESTORE_CREDENTIAL_LAYOUT_MISMATCH'),
    ('dropped-table',lambda d:d['tables'].pop('domain_objects'),'PUBLIC_RESTORE_83_TABLES_REQUIRED'),
    ('extra-table',lambda d:d['tables'].update(unexpected=empty),'PUBLIC_RESTORE_83_TABLES_REQUIRED'),
    ('changed-table-count',lambda d:d['tables']['domain_objects'].update(count=2),'PUBLIC_RESTORE_TABLE_STATE_MISMATCH'),
    ('missing-schema-digest',lambda d:d.pop('schema_sha256'),'PUBLIC_RESTORE_SCHEMA_DIGEST_REQUIRED'),
    ('wrong-schema-digest',lambda d:d.update(schema_sha256='f'*64),'PUBLIC_RESTORE_SCHEMA_DIGEST_MISMATCH'),
]:
    altered=copy.deepcopy(restored);change(altered)
    reject('F1-reject-'+label,lambda altered=altered:module.validate_restore22(altered,sealed,manifest,trigger),code)
bad=copy.deepcopy(sealed);bad['credentials']['all_revoked_zero']=False
reject('F1-reject-invalid-source-credential-baseline',lambda:module.validate_restore22(restored,bad,manifest,trigger),'PUBLIC_RESTORE_CREDENTIAL_REVOCATION_REQUIRED')
bad=copy.deepcopy(manifest);bad['schema_hash']='sha256:'+'f'*64
reject('F1-reject-manifest-schema-digest-drift',lambda:module.validate_restore22(restored,sealed,bad,trigger),'PUBLIC_BACKUP_MANIFEST_SCHEMA_MISMATCH')
weak=copy.deepcopy(sealed);weak['tables']['auth_principals']['count']=0
check('F1-legacy-ledger-alone-counterexample-still-demonstrated',module.validate_ledger(weak,22))
reject('F1-reject-invalid-sealed-owner',lambda:module.validate_restore22(restored,weak,manifest,trigger),'PUBLIC_RESTORE_OWNER_ROW_REQUIRED')
verify_arm=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="phase['id'] == 'verify22'")
check('F1-production-verify22-invokes-strong-validator',any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='validate_restore22' for n in ast.walk(verify_arm)))
reject('existing-recheck-denied-without-live-Root-scope',lambda:module.recheck_existing_public22(dummy,dummy,{},None),'LIVE_ROOT_EXISTING_OBSERVATION_SCOPE_REQUIRED')
recheck_arm=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recheck_existing_public22')
check('existing-recheck-has-no-owned-child-invocation',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run_owned' for n in ast.walk(recheck_arm)))

# F2: run the real orchestration function with in-memory filesystem boundaries.
# No OS mkdir/save, guard API, SQLite observer, or process dispatcher is invoked.
def prepare_failure_control(fail_name,publication_fails=False):
    original={name:getattr(module,name) for name in ['Path','read_exact','save_new','_assert_output_ancestors','_load_pinned_module']}
    created=set();attempts=[];saved=[];loaded=[]
    norm=module.regular_absolute
    root_key=norm(projection['paths']['root'])
    fail_key=norm(projection['paths'][fail_name])
    class MemoryPath:
        def __init__(self,path):self.path=str(path)
        def __str__(self):return self.path
        def __truediv__(self,name):return MemoryPath(module.ntpath.join(self.path,name))
        def mkdir(self):
            key=norm(self.path);attempts.append(key)
            if key==fail_key:raise OSError('INJECTED_PREPARE_MKDIR_FAILURE:'+fail_name)
            created.add(key)
        def exists(self):return norm(self.path) in created
        def is_dir(self):return self.exists()
        def is_file(self):return False
    class Scope:
        def require_registered(self,*a,**kw):pass
        def require_phase(self,phase,*a):assert phase=='prepare'
        def receipt_context(self):return {'scope':'SYNTHETIC_SOURCE_ONLY_NOT_AUTHORITY'}
        def qualified_current_main23(self,*a):raise AssertionError('unexpected Main qualification')
    c_ref={'path':'D:/Unopened/contract.json','sha256':'1'*64,'bytes':1}
    q_ref={'path':'D:/Unopened/request.json','sha256':'2'*64,'bytes':1}
    def save(path,value):
        if publication_fails:raise OSError('INJECTED_CLOSED_RECEIPT_FAILURE')
        saved.append((str(path),copy.deepcopy(value)))
        return {'path':str(path),'sha256':'3'*64,'bytes':1}
    def forbidden_load(*a):loaded.append(a);raise AssertionError('NO_NATIVE_SOURCE_MODULE_ALLOWED')
    try:
        module.Path=MemoryPath
        module.read_exact=lambda ref:json.dumps(contract if ref==c_ref else request).encode()
        module.save_new=save
        module._assert_output_ancestors=lambda path:None
        module._load_pinned_module=forbidden_load
        result=module.run_registered_case(c_ref,q_ref,Scope())
    finally:
        for name,value in original.items():setattr(module,name,value)
    check('F2-'+fail_name+('-receipt-failure' if publication_fails else '')+'-first-failure-retained',result['first_failure']['phase']=='prepare' and result['first_failure']['type']=='OSError' and result['first_failure']['message']=='INJECTED_PREPARE_MKDIR_FAILURE:'+fail_name and result['first_failure']['last_child_exit'] is None and result['first_failure']['original_ordinal'] is None)
    check('F2-'+fail_name+('-receipt-failure' if publication_fails else '')+'-no-child-no-retry',result['calls']==[] and not loaded and attempts[-1]==fail_key and len(attempts)==len(set(attempts)) and result['recoverability']['automatic_retry_or_recovery_performed'] is False)
    check('F2-'+fail_name+('-receipt-failure' if publication_fails else '')+'-partial-preparation',set(norm(x) for x in result['preparation']['created_directories'])==created and norm(result['preparation']['attempted_path'])==fail_key and result['publication']['root']==(root_key in created))
    if fail_name=='root':
        check('F2-root-uncreated-explicit-Root-return-receipt',not saved and result['closed_receipt']['status']=='ROOT_NOT_CREATED_ROOT_MUST_PERSIST_RETURNED_STATE')
    elif publication_fails:
        check('F2-close-write-failure-preserves-original-and-return-state',not saved and result['status']=='STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED' and result['closed_receipt']['status']=='FAILED_ROOT_MUST_PERSIST_RETURNED_STATE' and result['closed_receipt']['error']['message']=='INJECTED_CLOSED_RECEIPT_FAILURE')
    else:
        check('F2-'+fail_name+'-closed-receipt-produced',len(saved)==1 and saved[0][0].endswith('case.closed.json') and saved[0][1]['first_failure']==result['first_failure'] and saved[0][1]['publication']==result['publication'] and result['status']=='STOPPED_AT_FIRST_FAILURE' and result['closed_receipt']['status']=='PUBLISHED')
for name in ['root','private','raw','tmp','work22']:prepare_failure_control(name)
prepare_failure_control('raw',publication_fails=True)

result={'schema':'researchos.schema22-public-runner-source-controls.v1','scope':'PURE_SOURCE_ONLY_NO_NATIVE_NO_SQLITE_NO_CHILD_PROCESS','count':len(rows),'pass':sum(r['passed'] for r in rows),'fail':sum(not r['passed'] for r in rows),'controls':rows,'runtime_verified':False,'process_calls':0,'database_calls':0,'native_calls':0}
p=O/'source-controls.json'
with p.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'count':result['count'],'pass':result['pass'],'fail':result['fail'],'process_calls':0,'database_calls':0,'native_calls':0,'ref':{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}},ensure_ascii=False))

