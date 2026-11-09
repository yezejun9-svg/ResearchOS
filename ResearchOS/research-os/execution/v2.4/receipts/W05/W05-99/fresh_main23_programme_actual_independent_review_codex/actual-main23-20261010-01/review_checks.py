"""Read-only factual validators for future actual Main23 build receipts.

No subprocess, Win32 process launch, SQL, registration or qualification publisher.
Root authority and complete original host records are separate required inputs.
"""
from pathlib import Path
import hashlib,json,ntpath

PHASES=('go-version','list-declared','list-export','build-main23','inspect-binary')
REF_KEYS={'path','sha256','bytes'}
def need(value,label):
    if not value:raise ValueError(label)
def canonical(path):return ntpath.normcase(ntpath.normpath(str(path)))
def ref_key(ref):return canonical(ref['path']),ref['sha256'],ref['bytes']
def exact(ref):
    need(type(ref) is dict and set(ref)==REF_KEYS,'EXACT_REF_FIELDS')
    need(type(ref['bytes']) is int and 0<=ref['bytes']<=512*1024*1024,'REF_SIZE')
    p=Path(ref['path']);need(p.is_absolute() and p.is_file() and not p.is_symlink() and not p.is_junction(),'REGULAR_ABSOLUTE_REF')
    raw=p.read_bytes()
    need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'REF_DRIFT')
    return raw
def doc(ref):return json.loads(exact(ref))
def clean_guard(observed):
    need(observed['verification']=='PASSED' and observed['closed'] is True and type(observed['retained_handles_count']) is int and observed['retained_handles_count']==0 and observed['errors']==[],'GUARD_CLOSED_ZERO')
def typed_owned(observed):
    need(type(observed['owned_child_pid']) is int and 0<observed['owned_child_pid']<=0xffffffff,'EXACT_UINT32_PID')
    need(type(observed['creation_time_100ns']) is int and 0<observed['creation_time_100ns']<2**64,'EXACT_UINT64_FILETIME')
    need(type(observed['actual_exit']) is int and observed['actual_exit']==0,'ACTUAL_GO_EXIT_ZERO')
    job=observed['job_cleanup']
    need(type(job['active_processes_last_observed']) is int and job['active_processes_last_observed']==0 and job['errors']==[],'JOB_IDLE_ZERO')
    for key in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'):
        need(job[key] is True,'JOB_'+key)
def check_factual_build(contract,request,state,leaf,base):
    """Read actual pinned receipts and recompute closure; never run programme."""
    need(state['status']=='BUILT_CANDIDATE_PENDING_NONAUTHOR_PROGRAMME_REVIEW' and state['first_failure'] is None,'BUILT_CANDIDATE_ONLY')
    need(state['case_id']==request['case_id'] and state['phase']=='inspect-binary','CASE_FINAL_PHASE')
    need(state['formal_acceptance'] is False and state['product_program_executions']==0 and state['model_calls']==0 and state['database_calls']==0,'BUILD_ONLY_BOUNDARY')
    need(state['automatic_retry'] is False and not state.get('cleanup_errors'),'NO_RETRY_OR_CLEANUP_FAILURE')
    projection=leaf.compile_request(contract,request,base);paths=projection['paths']
    need(tuple(call['phase'] for call in state['calls'])==PHASES,'EXACT_FIVE_GO_CALLS')
    need(state['root_created'] is True and len(state['prepared_directories'])==7,'PREPARE_PHASE_EVIDENCE')
    environment=doc(state['environment_ref'])
    need(environment['GOROOT']==contract['goroot'] and environment['GOTOOLCHAIN']=='local' and environment['GOPROXY']==environment['GOSUMDB']=='off' and environment['CGO_ENABLED']=='0','ISOLATED_LOCKED_ENVIRONMENT')
    calls=[]
    for phase,call in zip(projection['phases'],state['calls']):
        need(call['argv']==phase['argv'] and canonical(call['cwd'])==canonical(paths['frozen_main']) and call['timeout_seconds']==phase['timeout'] and call['env']==environment,'EXACT_INVOCATION')
        need(type(call['actual_exit']) is int and call['actual_exit']==0,'INVOCATION_EXIT_ZERO')
        typed_owned(call['observation'])
        need(call['individual_descendant_exit_codes'] is None,'DESCENDANT_EXITS_REMAIN_UNKNOWN')
        need(type(call['started_at_unix_ns']) is int and type(call['ended_at_unix_ns']) is int and call['started_at_unix_ns']<=call['ended_at_unix_ns'],'EXACT_TIME_INTS')
        observed=doc(call['result_ref']);need(observed=={k:v for k,v in call.items() if k!='result_ref'},'ORIGINAL_RESULT_EXACT')
        before=doc(call['before_ref'])
        for key in ('phase','argv','cwd','env','timeout_seconds','started_at_unix_ns'):need(before[key]==call[key],'BEFORE_BINDING_'+key)
        need(before['observation'] is None and before['actual_exit'] is None,'BEFORE_HAS_NO_FUTURE_RESULT')
        stdout,stderr=exact(call['stdout_ref']),exact(call['stderr_ref'])
        need(len(stdout)<=16*1024*1024 and len(stderr)<=16*1024*1024,'COMPLETE_BOUNDED_STREAMS')
        calls.append((call,stdout,stderr))
    need(calls[0][1].decode().strip()=='go version go1.27.1 windows/amd64','ACTUAL_LOCKED_GO_VERSION')
    manifest=doc(contract['input_manifest_ref'])
    before=doc(state['source_before_ref'])['refs'];after=doc(state['source_after_ref'])['refs']
    frozen=doc(state['frozen_before_ref'])['refs'];frozen_after=doc(state['frozen_after_ref'])['refs']
    need([ref_key(r) for r in before]==[ref_key(r) for r in after],'ORIGINAL_SOURCE_VECTOR_NO_DRIFT')
    need([ref_key(r) for r in frozen]==[ref_key(r) for r in frozen_after],'FROZEN_VECTOR_NO_DRIFT')
    original={ref_key(r) for r in before}
    need(all(ref_key(item['ref']) in original for item in manifest['items']),'ALL_MAIN_MODULE_TOOLCHAIN_INPUTS_ORIGINALLY_HELD')
    need(len([item for item in manifest['items'] if item['kind']=='main'])==572,'FROZEN_572_MAIN_INPUTS')
    allowed=frozen+[item['ref'] for item in manifest['items'] if item['kind']=='toolchain']
    declared=leaf.declared_closure(leaf.parse_json_stream(calls[1][1]),allowed,paths,contract,base,False)
    exports=leaf.declared_closure(leaf.parse_json_stream(calls[2][1]),allowed,paths,contract,base,True)
    need(declared==doc(state['declared_closure_ref']),'COMPLETE_DECLARED_CLOSURE_RECOMPUTED')
    recorded_exports=doc(state['export_closure_ref'])
    need(exports['packages']==declared['packages'] and exports['input_refs']==declared['input_refs'],'DECLARED_EXPORT_GRAPH_AND_INPUTS_EQUAL')
    need(recorded_exports['packages']==exports['packages'] and recorded_exports['input_refs']==exports['input_refs'],'RECORDED_EXPORT_GRAPH_EXACT')
    need([{k:v for k,v in item.items() if k!='ref'} for item in recorded_exports['exports']]==exports['exports'],'ALL_EXPORT_RECORDS_BOUND')
    cache_before=doc(state['cache_before_build_ref'])['refs'];cache_after=doc(state['cache_after_build_ref'])['refs']
    cache_after_keys={ref_key(r) for r in cache_after}
    need(all(ref_key(r) in cache_after_keys for r in cache_before),'BUILD_CACHE_INPUTS_NO_DRIFT')
    for item in recorded_exports['exports']:
        need(canonical(item['ref']['path'])==canonical(item['path']) and ref_key(item['ref']) in {ref_key(r) for r in cache_before},'EXPORT_PIN_BEFORE_BUILD')
        exact(item['ref'])
    leaf.verify_binary_metadata(calls[4][1],contract)
    candidate=state['candidate_for_independent_review']
    need(candidate['program_ref']==state['program_ref'] and candidate['source_refs']==contract['current_main_source_refs'] and candidate['qualification_ref'] is None,'CANDIDATE_NOT_SELF_QUALIFIED')
    need(canonical(state['program_ref']['path'])==canonical(paths['program']),'EXACT_PROGRAM_PATH')
    binary=exact(state['program_ref']);need(binary[:2]==b'MZ','WINDOWS_PE_BINARY')
    need(set(state['guard_cleanup'])=={'original_inputs','frozen_inputs','export_inputs','program'},'ALL_FOUR_BUILD_GUARDS_PRESENT')
    for guard in state['guard_cleanup'].values():clean_guard(guard)
    return dict(five_actual_Go_jobs_checked=True,prepare_and_five_phase_provenance_checked=True,declared_and_export_closures_recomputed=True,programme_qualification=None,formal_acceptance=False)
