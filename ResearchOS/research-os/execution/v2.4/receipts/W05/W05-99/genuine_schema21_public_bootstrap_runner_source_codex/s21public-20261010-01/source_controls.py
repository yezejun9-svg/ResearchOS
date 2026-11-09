"""Finite new Task87 pure/AST controls. No leaf execution, native child or SQL."""
import ast, copy, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    p=Path(p); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
    with (Q/name).open('xb') as f: f.write((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def need(ok,code):
    if not ok: raise AssertionError(code)
def main():
    contract=json.loads((Q/'contract.json').read_bytes())
    m=types.ModuleType('task87_public21_pure')
    raw=(Q/'public21_runner.py').read_bytes(); tree=ast.parse(raw)
    exec(compile(raw,str(Q/'public21_runner.py'),'exec'),m.__dict__)
    guard_module=m.load_module(contract['source_guard'],'task87_controls_guard')
    guard=guard_module.SourceReadGuard()
    refs=[pin(Q/'public21_runner.py'),pin(Q/'contract.json'),pin(Q/'input-manifest.json'),pin(__file__),contract['old21_qualification_ref'],contract['public22_helpers_ref'],contract['source_guard']]
    checks=[]; failure=None
    def yes(name,fn):
        need(fn() is True,name); checks.append(dict(id=name,passed=True,kind='PURE_SYNTHETIC_OR_AST_NO_AUTHORITY'))
    def reject(name,fn):
        try: fn()
        except (m.BoundaryError,ValueError,AssertionError): checks.append(dict(id=name,passed=True,kind='PURE_REJECTION_NO_AUTHORITY')); return
        raise AssertionError(name+' accepted')
    def changed(obj,key,value):
        x=copy.deepcopy(obj); x[key]=value; return x
    try:
        guard.acquire(refs)
        request={'case_id':'a'*32,'output_root':ntpath.join(contract['output_parent'],'schema21-public-'+'a'*32)}
        projection=m.compile_case(contract,request)
        yes('PUBLIC_CLI_EXACT_FROZEN_FLAGS_CWD_EXIT90',lambda:projection['child']['argv']==[contract['old21_control']['path'],'--bootstrap-owner','--credential-file',projection['paths']['owner_file']] and projection['child']['cwd']==contract['old21_root'] and projection['child']['timeout_seconds']==90 and tuple(projection['phase_order'])==m.PHASES)
        text=raw.decode('utf-8')
        yes('OLD_CONTROL_ALONE_CREATES_DATABASE',lambda:"for name in ('private','raw','tmp'):" in text and "Path(paths['data21']).mkdir" not in text and "sqlite3" not in text)
        for name,key,val in [('REQUEST_EXTRA','end_version',21),('CASE_UPPER','case_id','A'*32),('CASE_BOOL','case_id',True),('CASE_SHORT','case_id','a'*31),('FOREIGN_ROOT','output_root','D:/foreign/schema21-public-'+'a'*32)]:
            reject(name,lambda key=key,val=val:m.compile_case(contract,changed(request,key,val)))
        for path in ('D:/ok/.local/child','D:\\ok\\.local\\child'):
            yes('LOCAL_DOT_DIRECTORY_'+str(len(checks)),lambda path=path:type(m.regular_path(path)) is str)
        for name,path in [('PATH_DEVICE','\\\\.\\C:\\bad'),('PATH_EXTENDED','\\\\?\\C:\\bad'),('PATH_UNC','\\\\server\\share\\bad'),('PATH_ADS','D:/tmp/a:stream'),('PATH_TRAVERSAL','D:/tmp/../bad'),('PATH_RESERVED','D:/tmp/NUL'),('PATH_NUL','D:/tmp/\x00bad')]:
            reject(name,lambda path=path:m.regular_path(path))
        yes('NORMALIZED_REF_SPELLING',lambda:m.same_ref(contract['old21_control'],changed(contract['old21_control'],'path',contract['old21_control']['path'].replace('\\','/'))))
        reject('REF_BOOL_BYTES',lambda:m.exact_ref(changed(contract['old21_control'],'bytes',True)))
        reject('REF_BAD_SHA',lambda:m.exact_ref(changed(contract['old21_control'],'sha256','bad')))
        document=m.strict(m.read_exact(contract['old21_qualification_ref']))
        binding={'qualification_ref':contract['old21_qualification_ref'],'program_refs':{'control':contract['old21_control'],'backup':contract['old21_backup']},'source_commit':contract['source_commit'],'source_tree':contract['source_tree'],'source_schema_version':21,'outer_host_binding_ref':document['root_issuance_binding_ref']}
        yes('PINNED_REAL_PROGRAMME_DATA_PURE_VALIDATION_ONLY',lambda:m.validate_programme(binding,document,contract))
        reject('PROGRAMME_SCHEMA22',lambda:m.validate_programme(changed(binding,'source_schema_version',22),document,contract))
        reject('PROGRAMME_SOURCE_COMMIT',lambda:m.validate_programme(changed(binding,'source_commit','0'*40),document,contract))
        reject('PROGRAMME_FOREIGN_PROGRAM_BYTES',lambda:m.validate_programme(changed(binding,'program_refs',{'control':changed(contract['old21_control'],'sha256','0'*64),'backup':contract['old21_backup']}),document,contract))
        reject('PROGRAMME_WRONG_ROOT_ISSUER',lambda:m.validate_programme(binding,changed(document,'issued_by','codex:/root/foreign'),contract))
        reject('PROGRAMME_SCHEMA_BOOL',lambda:m.validate_programme(binding,changed(document,'source_schema_version',True),contract))
        reject('PROGRAMME_EXECUTION_GRANT_CONFUSION',lambda:m.validate_programme(binding,changed(document,'execution_grant',True),contract))
        reject('PROGRAMME_SELF_REVIEW',lambda:m.validate_programme(binding,changed(document,'review_author',m.AUTHOR),contract))
        placeholder=contract['input_manifest_ref']
        resources={key:placeholder for key in m.RESOURCE_KEYS-{'source_author','reviewer_actor'}}
        resources.update(source_author=m.AUTHOR,reviewer_actor='codex:/root/independent_test_only')
        yes('RESOURCE_SHAPE_SYNTHETIC_NEVER_LIVE_CAPABILITY',lambda:m.validate_resources(resources,contract))
        reject('RESOURCE_SELF_REVIEW',lambda:m.validate_resources(changed(resources,'reviewer_actor',m.AUTHOR),contract))
        reject('RESOURCE_UNKNOWN_ACTOR',lambda:m.validate_resources(changed(resources,'reviewer_actor','unknown'),contract))
        reject('RESOURCE_FOREIGN_SOURCE_AUTHOR',lambda:m.validate_resources(changed(resources,'source_author','codex:/root/native_temp_independent_review'),contract))
        reject('RESOURCE_EXTRA_KEY',lambda:m.validate_resources(changed(resources,'secret','synthetic'),contract))
        reject('RESOURCE_WRONG_MANIFEST',lambda:m.validate_resources(changed(resources,'input_manifest_ref',changed(placeholder,'sha256','0'*64)),contract))
        observation={'versions':list(range(1,22)),'integrity':['ok'],'foreign_key_violations':0,'schema_sha256':'a'*64,'tables':{name:{'count':count,'rows_sha256':'b'*64} for name,count in [('auth_principals',1),('auth_credentials',1),('domain_objects',0),('domain_versions',0),('client_sessions',0),('backup_restore_barriers',0)]},'mode':'ro,immutable,query_only','raw_rows_emitted':False}
        yes('ORACLE_SHAPE_SYNTHETIC_NOT_DATABASE_PROOF',lambda:m.validate_observation(observation))
        reject('ORACLE_LEDGER22',lambda:m.validate_observation(changed(observation,'versions',list(range(1,23)))))
        reject('ORACLE_LEDGER_GAP',lambda:m.validate_observation(changed(observation,'versions',[1,7,21])))
        reject('ORACLE_LEDGER_BOOL',lambda:m.validate_observation(changed(observation,'versions',[True]+list(range(2,22)))))
        reject('ORACLE_INTEGRITY',lambda:m.validate_observation(changed(observation,'integrity',['bad'])))
        reject('ORACLE_FOREIGN_KEY',lambda:m.validate_observation(changed(observation,'foreign_key_violations',1)))
        reject('ORACLE_RAW_ROWS',lambda:m.validate_observation(changed(observation,'raw_rows_emitted',True)))
        reject('ORACLE_WRITABLE_MODE',lambda:m.validate_observation(changed(observation,'mode','rw')))
        tables=copy.deepcopy(observation['tables']); tables['auth_credentials']['count']=0
        reject('ORACLE_MISSING_CREDENTIAL_ROW',lambda:m.validate_observation(changed(observation,'tables',tables)))
        tables=copy.deepcopy(observation['tables']); tables['domain_objects']['count']=1
        reject('ORACLE_NONEMPTY_BUSINESS',lambda:m.validate_observation(changed(observation,'tables',tables)))
        tables=copy.deepcopy(observation['tables']); tables['client_command_queue']={'count':0,'rows_sha256':'b'*64}
        reject('ORACLE_LATER_QUEUE_SCHEMA',lambda:m.validate_observation(changed(observation,'tables',tables)))
        functions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        run=functions['run_registered_case']; run_text=ast.get_source_segment(text,run)
        yes('FIRST_LIVE_REGISTERED_GATE_BEFORE_INPUT_READ',lambda:run_text.index("root_scope.require_registered(")<run_text.index("strict(read_exact(contract_ref))")<run_text.index("root.mkdir()"))
        yes('SINGLE_OWNED_CHILD_CALL_NO_SHELL_NO_SQL_WRITER',lambda:run_text.count('job_module.run_owned(')==1 and 'subprocess' not in text and 'taskkill' not in text and 'user_version' not in text and 'UPDATE schema_migrations' not in text)
        yes('OWNED_JOB_SUCCESS_BEFORE_READONLY_ORACLE',lambda:run_text.index('helpers.closed_job(observed)')<run_text.index('readonly_database_observation(db)'))
        yes('EXACT_FILE_INVENTORY_BEFORE_AFTER_CHILD',lambda:run_text.count('verify_frozen_inventory(contract)')==2)
        yes('DB_GUARD_BEFORE_IMMUTABLE_ORACLE_FINAL_BYTE_CHECK',lambda:run_text.index('baseline_guard.acquire([baseline_ref])')<run_text.index('readonly_database_observation(db)') and "FINAL_BASELINE_BYTES_UNCHANGED" in run_text)
        yes('NO_OWNER_BYTES_READ',lambda:"owner.read" not in text and "observed_ref(owner)" not in text and 'credential_bytes_read_or_emitted=False' in text)
        yes('FINITE_PHASE_LEASE_GATES',lambda:all("root_scope.require_phase('"+phase+"'" in run_text for phase in m.PHASES))
        yes('GUARD_CLOSE_FINALLY_BEFORE_RECEIPT',lambda:bool(run.body) and "finally:" in run_text and run_text.index("audit=guard.close()")<run_text.index("save_new(root/'case.closed.json',state)"))
        yes('NO_AUTO_ENTRY_OR_SOURCE_ACCEPTANCE',lambda:all(not isinstance(n,ast.If) or ast.get_source_segment(text,n).startswith('if ') for n in tree.body) and "'__main__'" not in text and 'formal_acceptance=False' in text and 'automatic_retry=False' in text)
        environment_source=ast.get_source_segment(text,functions['public_environment'])
        yes('FIVE_PUBLIC_ENV_ONLY',lambda:"('SystemRoot','WINDIR')" in environment_source and "TEMP=paths['tmp'],TMP=paths['tmp'],RESEARCHOS_DATA_DIR=paths['data21']" in environment_source and 'dict(os.environ)' not in environment_source)
        yes('REAL_21_PREFIX_AND_UNNUMBERED_ADDON',lambda:contract['schema_oracle']['numbered_ledger']==list(range(1,22)) and contract['schema_oracle']['addon_not_numbered'] is True and contract['public_cli']['native_child_limit']==1 and contract['public_cli']['backup_child_limit']==0)
        yes('NEW_SCOPE_NO_FUTURE_AUTHORITY',lambda:contract['scope_key']=='PUBLIC21_BOOTSTRAP_ONLY' and all(contract[key] is None for key in contract if key.startswith('future_')) and contract['runtime_grant'] is False and contract['execution_grant'] is False)
        result={'schema':'researchos.schema21-public-bootstrap-source-controls.v1','source_author':m.AUTHOR,'checks':checks,'passed':len(checks),'failed':0,'synthetic_controls_are_not_formal_or_native':True,'run_registered_case_called':False,'SQL_connections':0,'Native_Go_model_TP_calls':0,'Root_scope_or_qualification_created':False,'old_85_helpers_controls_rerun':False,'actual_outer_exit':None,'Python_exit_marker_required':True,'formal_acceptance':False,'execution_grant':False}
    except BaseException as exc:
        failure=exc
        result={'schema':'researchos.schema21-public-bootstrap-source-controls.v1','checks':checks,'passed':len(checks),'failed':1,'first_failure_type':type(exc).__name__,'first_failure':str(exc),'original_ordinal':None,'Root_assignment_required':True,'SQL_Native_Go_model_TP_called':False,'formal_acceptance':False}
    finally:
        closed=guard.close(); save('source-controls.guard.closed.json',closed)
        result['source_guard_ref']=pin(Q/'source-controls.guard.closed.json')
        controls_ref=save('source-controls.json',result)
    need(closed.get('closed') is True and closed.get('retained_handles_count')==0 and closed.get('verification')=='PASSED' and not closed.get('errors'),'CONTROLS_GUARD_CLOSURE')
    if failure is not None: raise failure
    print(json.dumps({'controls_ref':controls_ref,'controls':len(checks),'guard_closed':True,'retained_handles':0,'product_calls':0},ensure_ascii=False,sort_keys=True))
    return 0
if __name__=='__main__':
    code=1
    try: code=main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code)); sys.exit(code)
