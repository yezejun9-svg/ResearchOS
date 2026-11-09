"""Public old21 bootstrap leaf. Import performs no process, SQL or native API work.

A separately reviewed Root caller supplies a live scope. This Source creates no
registration, lease, Root issuer proof, runtime qualification or AcceptanceReceipt.
The qualified old Control creates the only database. No SQL writer or fake ledger
is used by this leaf. Its generated Owner file is retained privately and never read.
"""
from __future__ import annotations
import hashlib, json, ntpath, os, re, stat, time, types
from pathlib import Path

AUTHOR = 'codex:/root/backup_regression_resources'
ROOT = 'codex:/root'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
PHASES = ('prepare', 'bootstrap21', 'inspect21', 'complete')
RESOURCE_KEYS = {'input_manifest_ref','source_review_ref','resource_qualification_ref','runtime_manifest_ref','outer_host_binding_ref','source_author','reviewer_actor'}
REF_KEYS = {'path','sha256','bytes'}

class BoundaryError(RuntimeError): pass
def require(ok, code):
    if not ok: raise BoundaryError(code)

def strict(raw):
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result,'DUPLICATE_JSON_KEY'); result[key] = value
        return result
    def nonfinite(value): raise BoundaryError('NONFINITE_JSON_NUMBER')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)

def regular_path(path):
    require(type(path) is str and path and not any(ord(c)<32 for c in path),'REGULAR_PATH_STRING')
    regular = path.replace('/','\\'); drive,tail = ntpath.splitdrive(regular)
    require(re.fullmatch('[A-Za-z]:',drive) is not None and tail.startswith('\\') and not tail.startswith('\\\\') and ':' not in tail,'ABSOLUTE_LOCAL_NON_ADS_PATH')
    parts = tail[1:].split('\\')
    require(all(part and part not in ('.','..') and not part.endswith((' ','.')) and re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?',part) is None for part in parts),'REGULAR_COMPONENTS')
    return ntpath.normcase(ntpath.normpath(regular))

def exact_ref(ref):
    require(type(ref) is dict and set(ref)==REF_KEYS and type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None and type(ref['bytes']) is int and 0<=ref['bytes']<=512*1024*1024,'EXACT_REF')
    regular_path(ref['path']); return ref

def same_ref(left,right):
    exact_ref(left); exact_ref(right)
    return regular_path(left['path'])==regular_path(right['path']) and left['sha256']==right['sha256'] and left['bytes']==right['bytes']

def read_exact(ref):
    exact_ref(ref); raw = Path(ref['path']).read_bytes()
    require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'REF_DRIFT')
    return raw

def observed_ref(path):
    raw=Path(path).read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def save_new(path,value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with Path(path).open('xb') as handle: handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    return observed_ref(path)

def load_module(ref,name):
    module=types.ModuleType(name); module.__file__=ref['path']
    exec(compile(read_exact(ref),ref['path'],'exec'),module.__dict__); return module

def compile_case(contract,request):
    """Pure argv projection; no filesystem observation or authority."""
    require(type(request) is dict and set(request)=={'case_id','output_root'},'EXACT_CASE_REQUEST_FIELDS')
    require(type(request['case_id']) is str and re.fullmatch('[0-9a-f]{32}',request['case_id']) is not None,'CASE_ID')
    require(contract['schema']=='researchos.schema21-public-bootstrap-contract.v1' and contract['source_author']==AUTHOR,'EXACT_SOURCE_CONTRACT')
    require(regular_path(request['output_root'])==regular_path(ntpath.join(contract['output_parent'],'schema21-public-'+request['case_id'])),'DISTINCT_ONE_SHOT_NAMESPACE')
    for key in ('old21_control','old21_backup','old21_qualification_ref','source_guard','owned_job','public22_helpers_ref','input_manifest_ref'):
        exact_ref(contract[key])
    root=request['output_root']; child=lambda name: ntpath.join(root,name)
    paths=dict(root=root,data21=child('source21'),db21=child('source21\\researchos.sqlite'),private=child('private'),owner_file=child('private\\owner.json'),raw=child('raw'),tmp=child('tmp'))
    return dict(paths=paths,phase_order=PHASES,child=dict(id='bootstrap21',argv=[contract['old21_control']['path'],'--bootstrap-owner','--credential-file',paths['owner_file']],cwd=contract['old21_root'],timeout_seconds=90))

def validate_programme(binding,document,contract):
    require(type(binding) is dict and set(binding)=={'qualification_ref','program_refs','source_commit','source_tree','source_schema_version','outer_host_binding_ref'},'ROOT_OLD21_BINDING_SHAPE')
    require(same_ref(binding['qualification_ref'],contract['old21_qualification_ref']),'EXACT_OLD21_QUALIFICATION_REF')
    exact_ref(binding['outer_host_binding_ref'])
    require(type(binding['program_refs']) is dict and set(binding['program_refs'])=={'control','backup'},'TWO_QUALIFIED_PROGRAMMES')
    require(document['schema']=='researchos.root-old21-programme-qualification.v1' and document['issued_by']==ROOT and document['root_thread_id']==ROOT_THREAD and document['status']=='QUALIFIED_OLD21_BUILD' and document['programme_qualification'] is True and document['independent_non_author'] is True,'ROOT_BOUND_OLD21_PROGRAMME')
    require(document['review_author']!=document['source_author'] and document['review_author']!=document['build_executor'] and document['review_author']!=AUTHOR,'INDEPENDENT_PROGRAMME_REVIEWER')
    for key,expected in (('control',contract['old21_control']),('backup',contract['old21_backup'])):
        require(same_ref(binding['program_refs'][key],expected) and same_ref(document['program_refs'][key],expected),'EXACT_OLD21_PROGRAMME_BYTES')
    require(type(binding['source_schema_version']) is int and type(document['source_schema_version']) is int and binding['source_schema_version']==document['source_schema_version']==21,'SOURCE_SCHEMA21_NOT_FAKE_LEDGER')
    require(binding['source_commit']==document['source_commit']==contract['source_commit'] and binding['source_tree']==document['source_tree']==contract['source_tree'],'FROZEN_GIT_SOURCE_BINDING')
    require(document['formal_acceptance'] is False and document['execution_grant'] is False,'PROGRAMME_QUALIFICATION_NOT_EXECUTION_GRANT')
    return True

def validate_resources(binding,contract):
    require(type(binding) is dict and set(binding)==RESOURCE_KEYS,'EXACT_RUNTIME_RESOURCE_BINDING')
    for key in RESOURCE_KEYS-{'source_author','reviewer_actor'}: exact_ref(binding[key])
    require(same_ref(binding['input_manifest_ref'],contract['input_manifest_ref']) and binding['source_author']==AUTHOR,'CURRENT_RUNNER_RESOURCE_BINDING')
    reviewer=binding['reviewer_actor']
    require(type(reviewer) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',reviewer) is not None and reviewer!=AUTHOR,'NONAUTHOR_RUNTIME_REVIEWER')
    return True

def validate_observation(observation):
    """Pure oracle checks. Values are produced by immutable SQLite only at runtime."""
    require(type(observation) is dict and type(observation.get('versions')) is list and all(type(x) is int for x in observation['versions']) and observation['versions']==list(range(1,22)),'EXACT_NUMBERED_SCHEMA21_LEDGER')
    require(observation.get('integrity')==['ok'] and type(observation.get('foreign_key_violations')) is int and observation['foreign_key_violations']==0,'IMMUTABLE_DATABASE_VALIDATION')
    require(type(observation.get('schema_sha256')) is str and re.fullmatch('[0-9a-f]{64}',observation['schema_sha256']) is not None and observation.get('mode')=='ro,immutable,query_only' and observation.get('raw_rows_emitted') is False,'REAL_SCHEMA_ORACLE_REQUIRED')
    tables=observation.get('tables'); require(type(tables) is dict,'TABLE_MANIFEST')
    for name,value in tables.items():
        require(type(name) is str and type(value) is dict and set(value)=={'count','rows_sha256'} and type(value['count']) is int and value['count']>=0 and type(value['rows_sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['rows_sha256']) is not None,'TYPED_TABLE_COUNT_HASH')
    for name,count in (('auth_principals',1),('auth_credentials',1),('domain_objects',0),('domain_versions',0),('client_sessions',0),('backup_restore_barriers',0)):
        require(name in tables and tables[name]['count']==count,'FRESH_OWNER_AND_REAL_EMPTY_SESSION_ADDON')
    require(not ({'client_command_queue','client_command_identities','host_model_configurations','host_model_config_heads','runtime_prepared_abandonments'} & set(tables)),'NO_LATER_NUMBERED_SCHEMA_TABLES')
    return True

def public_environment(paths):
    """Only public Windows roots plus this case's temporary/data roots."""
    env={key:os.environ[key] for key in ('SystemRoot','WINDIR') if key in os.environ}
    require(set(env)=={'SystemRoot','WINDIR'} and all(type(value) is str and value and '\x00' not in value for value in env.values()),'PUBLIC_WINDOWS_ENVIRONMENT_REQUIRED')
    env.update(TEMP=paths['tmp'],TMP=paths['tmp'],RESEARCHOS_DATA_DIR=paths['data21'])
    return env

def verify_frozen_inventory(contract):
    directory=Path(contract['old21_root'])/'migrations/sqlite'
    actual=[path for path in directory.iterdir() if re.fullmatch('[0-9]{4}_.+\\.sql',path.name)]
    expected=[ref for relative,ref in contract['frozen_runtime_refs'].items() if re.fullmatch('[0-9]{4}_.+\\.sql',ntpath.basename(relative))]
    require(sorted(regular_path(str(path)) for path in actual)==sorted(regular_path(ref['path']) for ref in expected),'EXACT_FROZEN_NUMBERED_FILE_MEMBERSHIP')
    require(sorted(int(path.name[:4]) for path in actual)==list(range(1,22)),'EXACT_FROZEN_FILES_1_TO21')
    require('migrations/sqlite/next_v24_sessions.sql' in contract['frozen_runtime_refs'],'REAL_UNNUMBERED_SESSION_ADDON_REQUIRED')

def run_registered_case(contract_ref,request_ref,root_scope):
    """One true public Control bootstrap, then a held immutable database oracle.

    The live Root caller authenticates full original peer/Root host records,
    new scope/owner/current4/finite lease and the complete Python/SQLite/native
    runtime resource closure. JSON binding shape here never substitutes for it.
    """
    require(root_scope is not None and not isinstance(root_scope,dict),'LIVE_ROOT_SCOPE_REQUIRED')
    for name in ('require_registered','require_phase','receipt_context','require_resources','qualified_old21_programmes'):
        require(callable(getattr(root_scope,name,None)),'LIVE_ROOT_SCOPE_INTERFACE')
    # No input read, directory, SQL connection or child before this live gate.
    root_scope.require_registered(contract_ref,request_ref,source_author=AUTHOR)
    contract=strict(read_exact(contract_ref)); request=strict(read_exact(request_ref)); projection=compile_case(contract,request)
    paths=projection['paths']; root=Path(paths['root'])
    resources=root_scope.require_resources(contract_ref,contract['input_manifest_ref']); validate_resources(resources,contract)
    programme=root_scope.qualified_old21_programmes(contract_ref,contract['old21_qualification_ref'])
    validate_programme(programme,strict(read_exact(contract['old21_qualification_ref'])),contract)
    state=dict(schema='researchos.schema21-public-bootstrap-observation.v1',case_id=request['case_id'],contract_ref=contract_ref,request_ref=request_ref,root_context=None,
        status='STARTED',phase='prepare',programme_binding=programme,resource_binding=resources,calls=[],observations={},first_failure=None,
        preparation=dict(root_created=False,created_directories=[]),closed_receipt=dict(status='NOT_ATTEMPTED',ref=None,error=None),
        public_bootstrap_observed=False,backup_restore_executed=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
        full20to24='OPEN',original_data_touched=False,credential_bytes_read_or_emitted=False,automatic_retry=False)
    source_guard=baseline_guard=None; helpers=None; baseline_ref=None
    try:
        root_scope.require_phase('prepare',request_ref,paths['root']); state['root_context']=root_scope.receipt_context()
        helpers=load_module(contract['public22_helpers_ref'],'reviewed_public22_helpers')
        helpers._assert_output_ancestors(paths['root'])
        root.mkdir(); state['preparation']['root_created']=True
        for name in ('private','raw','tmp'):
            Path(paths[name]).mkdir(); state['preparation']['created_directories'].append(paths[name])
        guard_module=load_module(contract['source_guard'],'reviewed_source_guard')
        source_guard=guard_module.SourceReadGuard()
        manifest=strict(read_exact(contract['input_manifest_ref']))
        refs=manifest['references']+[contract_ref,request_ref,contract['input_manifest_ref'],*resources_ref_values(resources),programme['outer_host_binding_ref']]
        source_guard.acquire(refs)
        job_module=load_module(contract['owned_job'],'reviewed_windows_owned_job')
        verify_frozen_inventory(contract)
        state['phase']='bootstrap21'; root_scope.require_phase('bootstrap21',request_ref,paths['root'])
        require(root_scope.require_resources(contract_ref,contract['input_manifest_ref'])==resources,'ROOT_RESOURCE_BINDING_CHANGED')
        child=projection['child']; stdout=Path(paths['raw'])/'bootstrap21.stdout'; stderr=Path(paths['raw'])/'bootstrap21.stderr'
        invocation=dict(phase='bootstrap21',argv=child['argv'],cwd=child['cwd'],env=public_environment(paths),timeout_seconds=90,started_at_unix_ns=time.time_ns(),actual_exit=None,observation=None)
        state['calls'].append(invocation)
        invocation['before_ref']=save_new(Path(paths['raw'])/'bootstrap21.before.json',dict(invocation))
        with stdout.open('xb') as out, stderr.open('xb') as err:
            observed=job_module.run_owned(invocation['argv'],invocation['cwd'],invocation['env'],out,err,90,creation_flags=0x08000000)
        invocation.update(observation=observed,actual_exit=observed.get('actual_exit'),ended_at_unix_ns=time.time_ns(),stdout_ref=observed_ref(stdout),stderr_ref=observed_ref(stderr))
        invocation['result_ref']=save_new(Path(paths['raw'])/'bootstrap21.result.json',{key:value for key,value in invocation.items() if key!='result_ref'})
        helpers.closed_job(observed)
        require(stdout.stat().st_size<=4*1024*1024 and stderr.stat().st_size<=4*1024*1024,'PUBLIC_OUTPUT_SIZE_CAP')
        state['phase']='inspect21'; root_scope.require_phase('inspect21',request_ref,paths['root'])
        verify_frozen_inventory(contract)
        db=helpers.quiescent_database(paths['db21']); baseline_ref=observed_ref(db)
        os.chmod(db,stat.S_IREAD)
        require(bool(db.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY),'BASELINE_READONLY_ATTRIBUTE')
        baseline_guard=guard_module.SourceReadGuard(); baseline_guard.acquire([baseline_ref])
        observation=helpers.readonly_database_observation(db); validate_observation(observation)
        require(same_ref(observation['database_ref'],baseline_ref) and same_ref(observed_ref(db),baseline_ref),'IMMUTABLE_BASELINE_BYTES_UNCHANGED')
        owner=Path(paths['owner_file']); require(owner.is_file() and not owner.is_symlink() and not owner.is_junction() and owner.stat().st_size>0,'PRIVATE_GENERATED_OWNER_FILE_METADATA')
        state['observations']['created21']=observation
        state['private_owner_metadata']=dict(path=str(owner),exists=True,bytes_read=False,bytes_recorded=False,opaque_generated_fixture_only=True)
        state['baseline_manifest_ref']=save_new(root/'baseline21.manifest.json',dict(database_ref=baseline_ref,readonly_attribute=True,source_guard_share='FILE_SHARE_READ_ONLY',created_by='Root-qualified old21 Control --bootstrap-owner',numbered_migrations=list(range(1,22)),unnumbered_session_addon='migrations/sqlite/next_v24_sessions.sql',formal_acceptance=False))
        state['phase']='complete'; root_scope.require_phase('complete',request_ref,paths['root'])
        require(root_scope.require_resources(contract_ref,contract['input_manifest_ref'])==resources,'ROOT_RESOURCE_CLOSURE_CHANGED')
        require(same_ref(observed_ref(db),baseline_ref),'FINAL_BASELINE_BYTES_UNCHANGED')
        state['public_bootstrap_observed']=True; state['status']='PUBLIC21_BOOTSTRAP_OBSERVED_PENDING_INDEPENDENT_REVIEW'
    except BaseException as exc:
        state['status']='STOPPED_AT_FIRST_FAILURE'; state['first_failure']=dict(phase=state['phase'],type=type(exc).__name__,message=str(exc),original_ordinal=None,Root_assignment_required=True,last_child_exit=state['calls'][-1]['actual_exit'] if state['calls'] else None)
    finally:
        state['guard_cleanup']={}
        for name,guard in (('baseline',baseline_guard),('source',source_guard)):
            if guard is not None:
                try:
                    audit=guard.close(); state['guard_cleanup'][name]=audit
                    if audit.get('verification')!='PASSED' or audit.get('closed') is not True or audit.get('retained_handles_count')!=0 or audit.get('errors'):
                        state['status']='STOPPED_GUARD_CLEANUP_UNCONFIRMED'
                except BaseException as exc:
                    state['guard_cleanup'][name]=dict(error_type=type(exc).__name__,error=str(exc),closed=None,retained_handles_count=None)
                    state['status']='STOPPED_GUARD_CLEANUP_UNCONFIRMED'
        state['baseline_ref']=baseline_ref
        state['publication']={key:Path(paths[key]).exists() for key in ('root','data21','db21','private','raw','tmp','owner_file')}
        state['recoverability']=dict(new_public_fixture_retained=state['publication']['db21'],private_generated_owner_retained=state['publication']['owner_file'],recovery_requires_new_Root_registration=True,automatic_retry_or_deletion_performed=False)
        if state['preparation']['root_created']:
            try:
                state['closed_receipt']['status']='PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF'
                ref=save_new(root/'case.closed.json',state)
                state['closed_receipt'].update(status='PUBLISHED',ref=ref)
            except BaseException as exc:
                state['closed_receipt'].update(status='FAILED_ROOT_MUST_PERSIST_RETURNED_STATE',error=dict(type=type(exc).__name__,message=str(exc)))
                state['status']='STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED'
        else:
            state['closed_receipt']['status']='ROOT_NOT_CREATED_ROOT_MUST_PERSIST_RETURNED_STATE'
    return state

def resources_ref_values(resources):
    return [resources[key] for key in sorted(RESOURCE_KEYS-{'source_author','reviewer_actor'})]
