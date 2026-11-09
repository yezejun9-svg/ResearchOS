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
result={'schema':'researchos.schema22-public-runner-source-controls.v1','scope':'PURE_SOURCE_ONLY_NO_NATIVE_NO_SQLITE_NO_CHILD_PROCESS','count':len(rows),'pass':sum(r['passed'] for r in rows),'fail':sum(not r['passed'] for r in rows),'controls':rows,'runtime_verified':False,'process_calls':0,'database_calls':0,'native_calls':0}
p=O/'source-controls.json'
with p.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'count':result['count'],'pass':result['pass'],'fail':result['fail'],'process_calls':0,'database_calls':0,'native_calls':0,'ref':{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}},ensure_ascii=False))

