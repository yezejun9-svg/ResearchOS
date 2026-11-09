"""Independent read-only NF5 actual facts. Never issue Mode or formal authority."""
import ast
import hashlib
import json
import ntpath
import os
import platform
import re
import sys
import traceback
import types
from datetime import datetime,timezone
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
ROOT_ACTOR='codex:/root'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
TEMP_PARENT=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
BASE=R/'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-05'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
GUARD_SHA='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
SOURCE_PINS={
 'HDF.json':('7c5defa472a1d1165095fb8c0346063f14ef4a95174f70eba32e7eaeded80694',21485),
 'MF.json':('9c3563d40496edd99c94bba582aafe7b80dd307992b66c56bfd4093f8f28e990',4619),
 'full_w09_runtime.source.py':('3fa9468a620366860ed1ba0d55c9f8079351e20426eb01ea6642d36ec4b6ec87',42781),
 'root-calling-contract.json':('148c64c93a55b2f2d35b19a44e1385537397d3ccdccb7464064bd5197807c804',8064),
 'source.choice.json':('7366a710702d0e0a3190e1b29a2550b234df89edea602bc20ed48189ab93232c',18097),
 'compiler-source-blueprint.json':('b2a08658ff7431ca2c0673598c582293e2dda1a3a31f23e96029cb96d7ff6b21',1000801)}

def require(ok,code):
    if not ok:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def decode(raw):
    def pairs(items):
        out={}
        for k,v in items:
            require(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
def ref_shape(ref):
    require(type(ref)is dict and set(ref)=={'path','sha256','bytes'} and type(ref['path'])is str
        and type(ref['sha256'])is str and re.fullmatch('[0-9a-f]{64}',ref['sha256'])
        and type(ref['bytes'])is int and 0<=ref['bytes']<=128*1024*1024,'EXACT_TYPED_REF')
    p=Path(ref['path']);p=p if p.is_absolute()else R/p
    require(p.is_absolute() and not any(x in ('..','.')for x in p.parts)
        and not str(p).startswith(('\\\\','\\\\?\\','\\\\.\\')),'REGULAR_ABSOLUTE_PATH')
    require(p.is_relative_to(R)or p.is_relative_to(TEMP_PARENT),'PUBLIC_RESOURCE_NAMESPACE')
    require(p not in {R/'execution/v2.4/checkpoint.json',R/'execution/v2.4/path_ownership.json',R/'execution/v2.4/step_state.json',R/'execution/v2.4/commands.json'},'NO_LIVE_CANON_READ')
    require(not p.is_symlink() and not getattr(p,'is_junction',lambda:False)()
        and ntpath.normcase(str(p.resolve(strict=True)))==ntpath.normcase(str(p.absolute())),'NO_RESOURCE_ALIAS')
    return p
def key(ref):return(ntpath.normcase(str(ref_shape(ref))),ref['sha256'],ref['bytes'])
def same_ref(a,b):return key(a)==key(b)
def read_ref(ref):
    p=ref_shape(ref);raw=p.read_bytes()
    require(len(raw)==ref['bytes']and digest(raw)==ref['sha256'],'RESOURCE_PIN_CHANGED')
    return raw
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=digest(raw),bytes=len(raw))
def uint(value,bits,label):
    require(type(value)is int and 0<value<(1<<bits),'EXACT_UINT_'+label);return value
def job(record):
    result=record['result'];c=result['job_cleanup']
    pid=uint(result['owned_child_pid'],32,'PID');clock=uint(result['creation_time_100ns'],64,'FILETIME')
    require(record['creation_time_100ns_decimal']==str(clock),'FILETIME_DECIMAL_MISMATCH')
    require(type(result['actual_exit'])is int and result['actual_exit']==0 and record['actual_outer_exit']==0
        and type(record['actual_outer_exit'])is int and result['timed_out']is False and result['error']is None
        and record['exception']is None and record['evidence_errors']==[],'ACTUAL_JOB_FAILURE')
    require(type(c['active_processes_last_observed'])is int and c['active_processes_last_observed']==0 and c['errors']==[]
        and all(c[k]is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')),'JOB_NOT_CLOSED')
    require(record['individual_child_numeric_exit']is None,'UNOBSERVED_CHILD_EXIT_MUST_STAY_NULL')
    return dict(actual_exit=0,pid=pid,creation_time_100ns_decimal=str(clock),owned_job_closed=True,unknown_individual_child_exit=None)
def guard_receipt(doc):
    require(doc['closed']is True and type(doc['retained_handles_count'])is int and doc['retained_handles_count']==0
        and not doc['errors'] and doc['failure']is None,'GUARD_NOT_CLOSED')
    require(all(row['verified']is True and row['final_path_match']is True and row['closed']is True for row in doc['entries']),'GUARD_ENTRY_UNCLOSED')
    return {(ntpath.normcase(row['path']),row['sha256'],row['bytes'])for row in doc['entries']}
def load_module(raw,path):
    module=types.ModuleType('nf5_actual_readonly_closure');module.__file__=str(path)
    tree=ast.parse(raw)
    require(not any(isinstance(n,ast.If)or(isinstance(n,ast.Expr)and not(isinstance(n.value,ast.Constant)and type(n.value.value)is str))for n in tree.body),'INERT_CLOSURE_MODULE_REQUIRED')
    exec(compile(tree,str(path),'exec'),module.__dict__);return module
def clock(value,label='timestamp'):
    require(type(value)is str,'TEXT_'+label);dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(dt.tzinfo is not None,'OFFSET_'+label);return dt.astimezone(timezone.utc)
class API:
    InvalidEvidence=ValueError
    strict_json=staticmethod(decode)
    stamp=staticmethod(clock)
    @staticmethod
    def require(ok,code,detail=''):require(ok,code+': '+detail)
    @staticmethod
    def interval(doc,label):
        a,b=clock(doc['started_at'],label),clock(doc['ended_at'],label)
        require(a<=b,'REVERSED_INTERVAL');return a,b
def event_interval(profile_raw,stream,report,tests,label):
    tree=ast.parse(profile_raw);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_native_event_interval')
    scope={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'pinned_Main_native_event_interval','exec'),scope)
    return scope['_native_event_interval'](API,stream,report,tests,label)
def nested_documents(value):
    if type(value)in(dict,list):
        yield value
        for item in(value.values()if type(value)is dict else value):yield from nested_documents(item)
    elif type(value)is str:
        for text in dict.fromkeys((value,*value.splitlines())):
            try:parsed=decode(text)
            except(ValueError,TypeError):continue
            if parsed!=value:yield from nested_documents(parsed)
def has_ref(value,ref):
    wanted=(ntpath.normcase(str(Path(ref['path']).absolute())),ref['sha256'],ref['bytes'])
    for row in nested_documents(value):
        if type(row)is dict and set(row)=={'path','sha256','bytes'}and type(row.get('path'))is str:
            p=Path(row['path']);p=p if p.is_absolute()else R/p
            if(ntpath.normcase(str(p.absolute())),row['sha256'],row['bytes'])==wanted:return True
    return False
def root_pair(binding_ref):
    b=decode(read_ref(binding_ref))
    if b['schema']=='researchos.w09-native-producer.actual-audit.v1':
        require(b['actor_id']==ROOT_ACTOR and b['Root_thread_id']==ROOT_THREAD,'ROOT_BINDING_IDENTITY')
    else:
        require(b['schema']=='researchos.root-native-actual-host-pair.v1'and b['issued_by']==ROOT_ACTOR
            and b['root_thread_id']==ROOT_THREAD and b['formal_acceptance']is False and b['canonical_written']is False,'ROOT_HOST_PAIR_IDENTITY')
    raw=read_ref(b['original_capture_ref']);lines=raw.splitlines(keepends=True)
    require(len(lines)==3 and all(x.endswith(b'\n')for x in lines),'THREE_COMPLETE_ROOT_LINES')
    h,c,o=[decode(x)for x in lines];first,last=c['payload'],o['payload']
    require(h['type']=='session_meta'and h['ordinal']==0 and h['payload']['id']==ROOT_THREAD,'TRUE_ROOT_HEADER')
    require(c['type']==o['type']=='response_item'and first['type']in('function_call','custom_tool_call')
        and last['type']in('function_call_output','custom_tool_call_output')and type(first['call_id'])is str
        and first['call_id']==last['call_id']and type(c['ordinal'])is int and type(o['ordinal'])is int
        and 0<c['ordinal']<o['ordinal'],'TRUE_ROOT_TOOL_PAIR')
    offsets=b['source_line_offsets'];hashes=b['original_line_sha256'];size=b['source_prefix_size_observed']
    require(type(size)is int and size>0 and type(offsets)is list and len(offsets)==3 and offsets==sorted(set(offsets))
        and offsets[0]==0 and all(type(v)is int and v>=0 for v in offsets)
        and len(hashes)==3 and all(off+len(line)<=size and digest(line)==sha for off,line,sha in zip(offsets,lines,hashes)),'IMMUTABLE_CAPTURE_RANGE_BINDING')
    observed={}
    for doc in nested_documents(last):
        if type(doc)is dict and type(doc.get('chunk_id'))is str and'output'in doc:
            observed[doc['chunk_id']]=doc
    require(len(observed)==1,'EXACT_ONE_ACTUAL_HOST_RESULT')
    observation=next(iter(observed.values()))
    if b['schema']=='researchos.root-native-actual-host-pair.v1':
        require(b['source_line_bytes']==[len(x)for x in lines]and b['original_call_id']==first['call_id']
            and b['actual_host_chunk_id']==observation['chunk_id']and b['tool_call_timestamp']==c['timestamp']
            and b['tool_result_timestamp']==o['timestamp'],'ORIGINAL_HOST_PAIR_PUBLIC_FIELDS')
        require(b['actual_outer_exit']==observation.get('exit_code')and b['actual_exec_session_id']==observation.get('session_id'),'KNOWN_HOST_EXITS_SESSIONS')
    return dict(binding_ref=binding_ref,binding_schema=b['schema'],raw_ref=b['original_capture_ref'],binding_sha256=b.get('binding_sha256'),
        call_id=first['call_id'],call_ordinal=c['ordinal'],output_ordinal=o['ordinal'],call_payload=first,
        output_payload=last,actual_host_result=observation,immutable_capture_verified=True,live_Root_audit_read=False)
def root_capture(binding_ref,artifact_ref):
    pair=root_pair(binding_ref)
    require(((pair['binding_schema']=='researchos.w09-native-producer.actual-audit.v1'and pair['binding_sha256']==artifact_ref['sha256'])
        or(pair['binding_schema']=='researchos.root-native-actual-host-pair.v1'and pair['binding_sha256']is None))
        and has_ref(pair['output_payload'],artifact_ref),'STRUCTURED_ACTUAL_ROOT_ARTIFACT_REF_REQUIRED')
    return pair
def root_run_pair(initial_ref,completed_ref,invocation_ref,c,request_ref,expected_Root_exit=0):
    initial=root_pair(initial_ref);completed=root_capture(completed_ref,invocation_ref)
    first,last=initial['actual_host_result'],completed['actual_host_result']
    require(type(first.get('session_id'))is int and first['session_id']>0 and'write_stdin'in completed['call_payload'].get('input','')
        and re.search(r'session_id\s*:\s*'+str(first['session_id'])+r'\b',completed['call_payload']['input'])
        and initial['output_ordinal']<completed['call_ordinal'],'SAME_ACTUAL_RUNNING_HOST_SESSION')
    require(type(expected_Root_exit)is int and expected_Root_exit in(0,1)and type(last.get('exit_code'))is int
        and last['exit_code']==expected_Root_exit and('ROOT_ACTUAL_PYTHON_EXIT='+str(expected_Root_exit))in last['output'].splitlines(),
        'ACTUAL_ROOT_PYTHON_EXIT_EXACT')
    text=initial['call_payload'].get('input','')
    require('exec_command'in text and str(BASE/'run_full_w09.source.py')in text and c['selector_key']in text
        and request_ref['path']in text and request_ref['sha256']in text
        and re.search(r'\b'+str(request_ref['bytes'])+r'\b',text),'ACTUAL_REQUEST_AND_PRODUCER_CALL_ARGUMENTS')
    return [initial,completed]
def root_prepare_pair(initial_ref,completed_ref,ready,c,request_ref):
    initial=root_pair(initial_ref);completed=root_pair(completed_ref)
    first,last=initial['actual_host_result'],completed['actual_host_result']
    require(type(first.get('session_id'))is int and first['session_id']>0 and'write_stdin'in completed['call_payload'].get('input','')
        and re.search(r'session_id\s*:\s*'+str(first['session_id'])+r'\b',completed['call_payload']['input'])
        and initial['output_ordinal']<completed['call_ordinal'],'SAME_PREPARE_HOST_SESSION')
    require(type(last.get('exit_code'))is int and last['exit_code']==0
        and'ROOT_ACTUAL_PYTHON_EXIT=0'in last['output'].splitlines(),'ACTUAL_PREPARE_PYTHON_EXIT_ZERO')
    text=initial['call_payload'].get('input','')
    require('exec_command'in text and str(BASE/'prepare_full_w09.source.py')in text and c['selector_key']in text
        and request_ref['path']in text and request_ref['sha256']in text
        and re.search(r'\b'+str(request_ref['bytes'])+r'\b',text),'ACTUAL_PREPARE_CALL_ARGUMENTS')
    progress=[doc for doc in nested_documents(last['output'])if type(doc)is dict and doc.get('stage')=='prepare']
    require(len(progress)==1 and progress[0]['status']==ready['status']=='PREPARED_ALL_GUARDS_CLOSED'
        and progress[0]['receipt_root']==c['receipt_root']and progress[0]['error']is None
        and progress[0]['cleanup_errors']==[]and progress[0]['all_guards_closed']is True
        and progress[0]['all_owned_jobs_closed']is True and progress[0]['unsaved_stage_result']is None,'ACTUAL_PREPARE_READY_FILE_PUBLICATION')
    return [initial,completed]
def mode_facts(closure,ctx,report,c,native):
    facts=dict(required_mode=c['mode'],producer_id=ROOT_ACTOR,independent_fact_reviewer=ACTOR,
        run_id=c['run_id'],report_sha256=digest((R/Path(report['raw_evidence_references'][0]).parent/'report.json').read_bytes()),
        source_sha256=native['source_hashes'],go_executable=native['go'],final_mode_decision_issued=False,
        finalization='MODE_FINALIZATION_REQUIRES_TRUE_FULL_REVIEWER')
    if c['mode']=='FIXTURE':
        rows=ctx['events'].get('http-exchange',[])
        require(rows and all(row['value'].get('delivery')=='IN_PROCESS_HTTptest_RECORDER'for row in rows),'ACTUAL_FIXTURE_HTTP_RECORDER')
        states=[row for label,group in ctx['events'].items()if label.startswith('state-')for row in group]
        require(any(Path(row['value'].get('root_path','')).is_relative_to(TEMP_PARENT)for row in states),'ACTUAL_FIXTURE_ROOT_OUTSIDE_CONTROLLED_TEMP')
        facts.update(input_origin='OWNED_TEMP_DIR',http_delivery='IN_PROCESS_HTTptest_RECORDER',temp_common_parent=str(TEMP_PARENT),state_event_refs=[row['pin']for row in states])
    else:
        require(os.name=='nt'and platform.system()=='Windows'and platform.machine().casefold()in('amd64','x86_64')
            and sys.getwindowsversion().build>=22000,'ACTUAL_WINDOWS11_X64_REQUIRED')
        branch=closure.only(ctx['events'],'g02-os-branch','TestW09RootReplacementCannotFeedProduct')
        command=closure.only(ctx['events'],'g02-junction-command','TestW09RootReplacementCannotFeedProduct')
        require(branch['goos']=='windows'and branch['goarch']=='amd64'and branch['junction_branch']is True,'REAL_GO_WINDOWS_BRANCH')
        root,target=Path(command['root']),Path(command['target'])
        require(root.is_absolute()and target.is_absolute()and root!=target and type(command['exit_code'])is int
            and command['exit_code']==0 and command['command']==['cmd.exe','/c','mklink','/J',str(root),str(target)],'REAL_JUNCTION_COMMAND')
        closure._raw_pin(command['output'],ctx['members'],'TestW09RootReplacementCannotFeedProduct')
        facts.update(actual_platform='Windows11x64',os=platform.system(),os_release=platform.release(),junction_actual=command,
            go_branch_actual=branch,junction_event_ref=ctx['events']['g02-junction-command'][0]['pin'],host_event_ref=ctx['events']['g02-os-branch'][0]['pin'])
    return facts

def packet_artifacts(closed,c):
    packet=decode(read_ref(closed['native_packet_ref']))
    require(packet['schema']=='researchos.w09-four-selector-native-packet.v1'and packet['run_id']==c['run_id']
        and packet['consumer_source_root']==str(R)and packet['immutable_original_bytes']is True and packet['formal_acceptance']is False,
        'IMMUTABLE_ORIGINAL_PACKET')
    summary=closed['summary']
    if summary is not None:
        require(same_ref(summary['report_ref'],packet['original_report_ref'])and same_ref(summary['tool_run_ref'],packet['original_tool_run_ref']),
            'SUMMARY_MATCHES_ORIGINAL_PACKET')
        return summary
    require(c['selector_key']=='C19'and closed['status']=='FAILED_NO_AUTOMATIC_RETRY'
        and closed['error']=="ValueError('EXACT_NATIVE_ARGV')"and closed['original_exception_type']=='ValueError','ONLY_ORIGINAL_C19_REFUSAL')
    root=Path(c['receipt_root'])/'producer'
    inventory_ref=pin(root/'actual-compiler-input-inventory.json');permit_ref=pin(root/'launcher.permit.json')
    sets={item['label']:guard_receipt(decode(read_ref(item['ref'])))for item in closed['guard_cleanups']}
    require(key(inventory_ref)in sets['compiler-exports']and key(permit_ref)in sets['launcher-permit'],
        'FAILED_STAGE_ARTIFACTS_EXACT_ORIGINAL_GUARD_PINS')
    return dict(report_ref=packet['original_report_ref'],tool_run_ref=packet['original_tool_run_ref'],
        compiler_inventory_ref=inventory_ref,launcher_permit_ref=permit_ref,derived_for_readonly_review=True,success_summary_created=False)

def reviewed_runtime_closure(closed,ready,c,summary,bp):
    jobs=[];require(len(closed['invocation_observations'])==2,'EXACT_LIST_AND_PRODUCER_JOBS')
    for observed in closed['invocation_observations']:
        record=decode(read_ref(observed['ref']));require(record==observed['record']and observed['verified']is True and observed['job_closed']is True,'ORIGINAL_JOB_RECEIPT_BINDING')
        require(record['public_environment']==ready['environment']and record['cwd']==str(R),'ACTUAL_EXPLICIT_ENVIRONMENT')
        jobs.append(dict(label=observed['label'],ref=observed['ref'],**job(record)))
    require([row['label']for row in jobs]==['compiler-input-list','w09-selector-main-producer'],'EXACT_JOB_ORDER')
    guards={}
    for original in closed['guard_cleanups']:
        cleanup=decode(read_ref(original['ref']));require(cleanup==original['observation']and original['closed']is True and original['receipt_saved']is True,'ORIGINAL_CLOSED_GUARD_BINDING')
        require(original['label']not in guards,'DUPLICATE_GUARD_LABEL');guards[original['label']]=guard_receipt(cleanup)
    require(set(guards)=={'input','runtime','preparation','compiler-exports','launcher-permit'},'EXACT_RESOURCE_GUARDS')
    stable={(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in bp['stable_input_refs']}
    require(stable<=guards['input'],'ALL_3905_COMPILER_INPUTS_HELD_DURING_NATIVE')
    inv=decode(read_ref(summary['compiler_inventory_ref']))
    require(inv['actual_go_list_export']is True and inv['source21']==c['source21']and same_ref(inv['blueprint_ref'],c['compiler_blueprint_ref'])
        and len(inv['packages'])==len(set(inv['packages']))==inv['package_count']and set(inv['packages'])<=set(bp['allowed_package_roster'])
        and set(bp['required_test_packages'])<=set(inv['packages']),'ACTUAL_COMPILER_CLOSURE')
    require({(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in inv['stable_build_input_refs']}<=stable,'ACTUAL_STABLE_COMPILER_INPUTS_CHANGED')
    require({key(x)for x in inv['module_go_mod_refs']}=={key(x)for x in bp['module_go_mod_refs']},'EXACT_19_MODULE_CLOSURE')
    private=inv['private_generated_input_refs']+inv['private_export_refs']
    require(private and all(Path(x['path']).is_relative_to(Path(c['scratch_root'])/'gocache')for x in private)
        and {(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in private}<=guards['compiler-exports'],'PRIVATE_COMPILE_INPUTS_HELD')
    require(key(summary['compiler_inventory_ref'])in guards['compiler-exports']and key(summary['launcher_permit_ref'])in guards['launcher-permit'],
        'INVENTORY_AND_PERMIT_HELD_WITH_ACTUAL_NATIVE')
    root=Path(c['receipt_root'])/'producer';started_ref=pin(root/'launcher.started.json');ended_ref=pin(root/'launcher.closed.json')
    started=decode(read_ref(started_ref));ended=decode(read_ref(ended_ref));permit=decode(read_ref(summary['launcher_permit_ref']))
    require(same_ref(started['permit_ref'],summary['launcher_permit_ref'])and same_ref(ended['permit_ref'],summary['launcher_permit_ref'])
        and same_ref(started['runner_ref'],permit['runner_ref'])and same_ref(ended['runner_ref'],permit['runner_ref'])
        and same_ref(started['launcher_ref'],permit['launcher_ref'])and same_ref(ended['launcher_ref'],permit['launcher_ref']),
        'EXACT_PRIVATE_LAUNCHER_PROVENANCE')
    require(started['fixed_run_id']==c['run_id']and started['fixed_output_root']==c['output_root']and started['source_root']==str(R)
        and started['Source21']==c['source21']and started['adapter']=='RUNNER_PRIVATE_UUID_OBJECT_ONLY'
        and started['stdlib_uuid_modified']is False and started['Main_source_modified']is False,'SINGLE_EXACT_RUN_LAUNCHER')
    require(type(ended['runner_returned_exit'])is int and ended['runner_returned_exit']==0 and ended['error']is None
        and ended['one_uuid_consumed']is True and ended['cleanup_errors']==[]and ended['stdlib_uuid_modified']is False
        and ended['Main_source_modified']is False and ended['unknown_individual_descendant_exit']is None,'LAUNCHER_RETURN_CLOSED')
    return dict(jobs=jobs,compiler_inventory_ref=summary['compiler_inventory_ref'],compiler_input_refs_held=len(stable),
        actual_compiler_packages=inv['package_count'],module_count=len(bp['module_go_mod_refs']),private_generated_inputs=len(inv['private_generated_input_refs']),
        private_export_inputs=len(inv['private_export_refs']),launcher_started_ref=started_ref,launcher_closed_ref=ended_ref,
        inner_Go_separate_OwnedJob_receipt=None,inner_Go_lifetime='INHERITS_EXCLUSIVE_OUTER_OWNED_PYTHON_JOB',
        unknown_individual_child_exits=None,all_original_guards_closed=True)

def review_refused_c19(row,c,closure,profile_raw,bp):
    require(set(row)=={'prepare_ref','producer_closed_ref','prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref',
        'run_initial_Root_capture_ref','run_completed_Root_capture_ref'}and c['selector_key']=='C19','EXACT_REFUSED_C19_INPUT')
    ready=decode(read_ref(row['prepare_ref']));closed=decode(read_ref(row['producer_closed_ref']))
    require(ready['status']=='PREPARED_ALL_GUARDS_CLOSED'and ready['stage']=='prepare'and ready['error']is None
        and closed['stage']=='run'and closed['status']=='FAILED_NO_AUTOMATIC_RETRY'and closed['summary']is None
        and closed['error']=="ValueError('EXACT_NATIVE_ARGV')"and closed['original_exception_type']=='ValueError',
        'ORIGINAL_C19_STAGE_REFUSAL_RETAINED')
    for d in(ready,closed):
        require(d['cleanup_errors']==[]and d['all_guards_closed']is True and d['all_cleanup_receipts_saved']is True
            and d['all_owned_jobs_closed']is True and type(d['formal_case_accepted_delta'])is int and d['formal_case_accepted_delta']==0
            and d['actual_formal_consumers']is False and type(d['external_model_provider_requests'])is int and d['external_model_provider_requests']==0
            and type(d['paid_provider_requests'])is int and d['paid_provider_requests']==0 and d['Main_source_written']is False
            and d['Canon_written']is False and d['automatic_retry']is False,'C19_BOUNDARIES_AND_ALL_CLEANUP_CLOSED')
    require(closed['original_invocation_diagnostics']is None and closed['original_invocation_errors']==[],'C19_FAILURE_IS_POSTRUN_PACKET_GATE')
    require(ready['run_id']==c['run_id']and ready['source21']==c['source21']and ready['scratch_root']==c['scratch_root'],
        'C19_FROZEN_SOURCE_AND_SCRATCH')
    request=decode(read_ref(closed['request_ref']));require(same_ref(closed['request_ref'],ready['request_ref']),'C19_SAME_ROOT_REQUEST')
    scope=decode(read_ref(request['scope_ref']))
    require(scope['issued_by']==scope['executor']==ROOT_ACTOR and scope['generation']=='fullw09-20261010-05'
        and scope['run_id']==c['run_id']and scope['selector']==c['selector'],'C19_DISTINCT_ORIGINAL_ROOT_SCOPE')
    artifacts=packet_artifacts(closed,c);report=decode(read_ref(artifacts['report_ref']));tool=decode(read_ref(artifacts['tool_run_ref']))
    require(report['run_id']==tool['run_id']==c['run_id']and report['task_id']=='W09'and report['check_id']is None
        and report['case_id']=='C19'and report['scope']==c['native_scope'],'C19_ORIGINAL_ROUTE')
    require(type(report['exit_code'])is int and report['exit_code']==0 and type(tool['native_exit_code'])is int and tool['native_exit_code']==0
        and report['status']=='PASS'and report['timed_out']is False and type(report['formal_case_accepted_delta'])is int
        and report['formal_case_accepted_delta']==0 and report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING'
        and tool['formal_acceptance']=='NOT_RUN','C19_ACTUAL_NATIVE_ZERO_WITHOUT_FORMAL_ACCEPTANCE')
    expected=[c['tool_refs']['go']['path'],*c['go_test_argv_suffix']];actual=report['actual_invocation']
    require(actual==tool['actual_invocation']and len(actual)==len(expected)and actual!=expected,'C19_EXACT_ARGV_CONTRACT_REJECTED')
    different=[i for i,(a,b)in enumerate(zip(actual,expected))if a!=b]
    require(different==[5]and expected[4]==actual[4]=='-run'
        and expected[5]=='^(?:TestW09C19ExplicitOriginAndUnknown|TestW09C19ChainInvalidation)$'
        and actual[5]=='^(?:TestW09C19ChainInvalidation|TestW09C19ExplicitOriginAndUnknown)$','ONLY_OBSERVED_LITERAL_ARGV_ORDER_MISMATCH')
    require(report['selected_tests']==['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown']
        and c['selected_tests']==['TestW09C19ExplicitOriginAndUnknown','TestW09C19ChainInvalidation']
        and sorted(report['assertion_ids'])==sorted(c['expected_native_ids'])and len(report['assertion_ids'])==5,'C19_ACTUAL_TWO_TESTS_FIVE_IDS')
    require(report['version_manifest']['source_sha256']=={Path(ref['path']).relative_to(R).as_posix():'sha256:'+ref['sha256']for ref in c['source21']},
        'C19_ACTUAL_CURRENT_SOURCE21')
    require(clock(scope['lease_issued_at'])<=clock(report['started_at'])<=clock(report['ended_at'])<=clock(scope['lease_expires_at']),
        'C19_OBSERVED_NATIVE_WITHIN_ORIGINAL_LEASE')
    relative=Path(artifacts['report_ref']['path']).relative_to(R).as_posix();source=dict(report,report_reference=relative)
    require(tool['schema']=='researchos.w09-native-producer-tool-run.v1'and tool['report_ref']==relative
        and tool['report_sha256']==artifacts['report_ref']['sha256'],'C19_TOOL_BOUND_TO_ORIGINAL_REPORT')
    native=closure.verify_native(R,source,report,c['expected_native_ids'],report['selected_tests'])
    require(tool['stdout_sha256']==native['stdout']['sha256']and tool['stderr_sha256']==native['stderr']['sha256']
        and tool['stdout_ref']==report['raw_evidence_references'][0]and tool['stderr_ref']==report['raw_evidence_references'][1],
        'C19_ORIGINAL_NATIVE_STREAMS_BOUND')
    intervals=event_interval(profile_raw,read_ref(native['stdout']),report,report['selected_tests'],'C19_observed_refused_contract')
    owned=closure.verify_owned(R,source,report,report['selected_tests'],c['assertion_owner']);closure.verify_c19(owned)
    runtime=reviewed_runtime_closure(closed,ready,c,artifacts,bp)
    pairs=[*root_prepare_pair(row['prepare_initial_Root_capture_ref'],row['prepare_completed_Root_capture_ref'],ready,c,closed['request_ref']),
        *root_run_pair(row['run_initial_Root_capture_ref'],row['run_completed_Root_capture_ref'],closed['invocation_observations'][-1]['ref'],
            c,closed['request_ref'],expected_Root_exit=1)]
    return dict(selector='C19',run_id=c['run_id'],fact_status='OBSERVED_NATIVE_PASS_CONTRACT_REFUSED',qualified_for_main_formal_consumption=False,
        refusal='EXACT_NATIVE_ARGV',Root_original_failure_ordinal=1156,Root_outer_exit=1,Root_python_exit=1,actual_native_exit=0,
        producer_actual_exit=0,producer_closed_ref=row['producer_closed_ref'],report_ref=artifacts['report_ref'],tool_run_ref=artifacts['tool_run_ref'],
        expected_argv=expected,actual_argv=actual,differing_argv_indices=different,expected_selected_tests=c['selected_tests'],
        actual_selected_tests=report['selected_tests'],observed_native_ids=report['assertion_ids'],owned_members=len(owned['members']),
        native_event_interval=intervals,runtime_closure=runtime,Root_original_tool_pairs=pairs,
        mode_predicate_facts=mode_facts(closure,owned,report,c,native),C19_Mode_issuance_permitted=False,success_summary_created=False,
        formal_acceptance=False,formal_case_accepted_delta=0)

def collect_actual_refs(packet,choices):
    refs=[]
    def add(ref):
        ref_shape(ref);refs.append(ref);return decode(read_ref(ref))
    for name,row in packet['groups'].items():
        c=choices[name];ready=add(row['prepare_ref']);closed=add(row['producer_closed_ref'])
        request=add(closed['request_ref']);add(request['scope_ref']);add(request['canonical_vector_ref'])
        for label in('prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'):
            binding=add(row[label]);refs.append(binding['original_capture_ref'])
        for stage in(ready,closed):
            for original in stage['guard_cleanups']:add(original['ref'])
        summary=packet_artifacts(closed,c);report=add(summary['report_ref']);add(summary['tool_run_ref']);add(summary['compiler_inventory_ref'])
        add(summary['launcher_permit_ref']);packet_index=add(closed['native_packet_ref'])
        for rowmap in packet_index['raw_copy_mapping']:
            for value in rowmap.values():
                if type(value)is dict and set(value)=={'path','sha256','bytes'}:refs.append(value)
        for relative in report['raw_evidence_references']:refs.append(pin(R/relative))
        refs.extend(report['owned_export']['members'])
        for observed in closed['invocation_observations']:
            invocation=add(observed['ref']);refs.extend([invocation['stdout_ref'],invocation['stderr_ref']])
        root=Path(c['receipt_root'])/'producer'
        refs.extend([pin(root/'launcher.started.json'),pin(root/'launcher.closed.json')])
    return refs

def review_group(row,c,closure,profile_raw,bp):
    require(set(row)=={'prepare_ref','producer_closed_ref','prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'},'EXACT_SIX_ACTUAL_INPUT_REFS')
    ready=decode(read_ref(row['prepare_ref']));closed=decode(read_ref(row['producer_closed_ref']))
    require(ready['status']=='PREPARED_ALL_GUARDS_CLOSED'and closed['status']=='MAIN_SELECTOR_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW'
        and ready['stage']=='prepare'and closed['stage']=='run','ACTUAL_STAGE_NOT_PASS')
    for d in(ready,closed):
        require(d['error']is None and not d['cleanup_errors']and d['all_guards_closed']is True
            and d['all_cleanup_receipts_saved']is True and d['all_owned_jobs_closed']is True
            and type(d['formal_case_accepted_delta'])is int and d['formal_case_accepted_delta']==0
            and d['actual_formal_consumers']==0 and d['external_model_provider_requests']==0
            and d['paid_provider_requests']==0 and d['Main_source_written']is False and d['Canon_written']is False
            and d['automatic_retry']is False,'ACTUAL_BOUNDARY_OR_CLEANUP_FAILURE')
    require(ready['run_id']==c['run_id'] and ready['source21']==c['source21']and ready['scratch_root']==c['scratch_root']
        and closed['summary']['run_id']==c['run_id']and closed['summary']['selector']==c['selector'],'FIXED_SOURCE_RUN_ROUTE')
    request=decode(read_ref(closed['request_ref']));require(same_ref(closed['request_ref'],ready['request_ref']),'SAME_PREPARE_RUN_REQUEST')
    scope=decode(read_ref(request['scope_ref']));require(scope['issued_by']==scope['executor']==ROOT_ACTOR
        and scope['generation']=='fullw09-20261010-05'and scope['run_id']==c['run_id']and scope['selector']==c['selector'],'DISTINCT_ROOT_SCOPE')
    summary=closed['summary'];report=decode(read_ref(summary['report_ref']));tool=decode(read_ref(summary['tool_run_ref']))
    require(report['run_id']==tool['run_id']==c['run_id']and report['selected_tests']==c['selected_tests']
        and sorted(report['assertion_ids'])==sorted(c['expected_native_ids'])and report['scope']==c['native_scope']
        and report['task_id']=='W09'and report['check_id']==(c['selector']['check_id']or None)
        and report['case_id']==(c['selector']['case_id']or None),'EXACT_ACTUAL_NATIVE_SELECTION')
    require(type(report['exit_code'])is int and report['exit_code']==0 and type(tool['native_exit_code'])is int and tool['native_exit_code']==0
        and report['status']=='PASS'and report['timed_out']is False and type(report['formal_case_accepted_delta'])is int
        and report['formal_case_accepted_delta']==0 and report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING'
        and tool['formal_acceptance']=='NOT_RUN','ACTUAL_NATIVE_ZERO_NO_FORMAL')
    require(clock(scope['lease_issued_at'])<=clock(report['started_at'])<=clock(report['ended_at'])<=clock(scope['lease_expires_at']),'ACTUAL_NATIVE_WITHIN_ORIGINAL_LEASE')
    relative=Path(summary['report_ref']['path']).relative_to(R).as_posix();source=dict(report,report_reference=relative)
    require(tool['schema']=='researchos.w09-native-producer-tool-run.v1'and tool['report_ref']==relative
        and tool['report_sha256']==summary['report_ref']['sha256']and tool['actual_invocation']==report['actual_invocation']
        and report['actual_invocation']==[c['tool_refs']['go']['path'],*c['go_test_argv_suffix']],'ACTUAL_TOOL_RUN_BINDING')
    require(report['version_manifest']['source_sha256']=={Path(ref['path']).relative_to(R).as_posix():'sha256:'+ref['sha256']for ref in c['source21']},'EXACT_CURRENT_SOURCE21')
    native=closure.verify_native(R,source,report,c['expected_native_ids'],c['selected_tests'])
    require(tool['stdout_sha256']==native['stdout']['sha256']and tool['stderr_sha256']==native['stderr']['sha256']
        and tool['stdout_ref']==report['raw_evidence_references'][0]and tool['stderr_ref']==report['raw_evidence_references'][1],'TOOL_NATIVE_STREAMS')
    intervals=event_interval(profile_raw,read_ref(native['stdout']),report,c['selected_tests'],c['selector_key'])
    owned=closure.verify_owned(R,source,report,c['selected_tests'],c['assertion_owner'])
    if c['selector_key']in('W09-G01','C19'):closure.verify_c19(owned)
    if c['selector_key']in('W09-G01','W09-G02','A06'):closure.verify_a06(owned)
    jobs=[];require(len(closed['invocation_observations'])==2,'EXACT_LIST_AND_PRODUCER_JOBS')
    for observed in closed['invocation_observations']:
        record=decode(read_ref(observed['ref']));require(record==observed['record']and observed['verified']is True and observed['job_closed']is True,'ORIGINAL_JOB_RECEIPT_BINDING')
        require(record['public_environment']==ready['environment']and record['cwd']==str(R),'ACTUAL_EXPLICIT_ENVIRONMENT')
        jobs.append(dict(label=observed['label'],ref=observed['ref'],**job(record)))
    require([row['label']for row in jobs]==['compiler-input-list','w09-selector-main-producer'],'EXACT_JOB_ORDER')
    guards={}
    for original in closed['guard_cleanups']:
        cleanup=decode(read_ref(original['ref']));require(cleanup==original['observation']and original['closed']is True and original['receipt_saved']is True,'ORIGINAL_CLOSED_GUARD_BINDING')
        require(original['label']not in guards,'DUPLICATE_GUARD_LABEL');guards[original['label']]=guard_receipt(cleanup)
    require(set(guards)=={'input','runtime','preparation','compiler-exports','launcher-permit'},'EXACT_RESOURCE_GUARDS')
    stable={(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in bp['stable_input_refs']}
    require(stable<=guards['input'],'ALL_3905_COMPILER_INPUTS_HELD_DURING_NATIVE')
    inv=decode(read_ref(summary['compiler_inventory_ref']))
    require(inv['actual_go_list_export']is True and inv['source21']==c['source21']and same_ref(inv['blueprint_ref'],c['compiler_blueprint_ref'])
        and len(inv['packages'])==len(set(inv['packages']))==inv['package_count']and set(inv['packages'])<=set(bp['allowed_package_roster'])
        and set(bp['required_test_packages'])<=set(inv['packages']),'ACTUAL_COMPILER_CLOSURE')
    require({(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in inv['stable_build_input_refs']}<=stable,'ACTUAL_STABLE_COMPILER_INPUTS_CHANGED')
    require({key(x)for x in inv['module_go_mod_refs']}=={key(x)for x in bp['module_go_mod_refs']},'EXACT_19_MODULE_CLOSURE')
    private=inv['private_generated_input_refs']+inv['private_export_refs']
    require(private and all(Path(x['path']).is_relative_to(Path(c['scratch_root'])/'gocache')for x in private)
        and {(ntpath.normcase(x['path']),x['sha256'],x['bytes'])for x in private}<=guards['compiler-exports'],'PRIVATE_COMPILE_INPUTS_HELD')
    captures=[*root_prepare_pair(row['prepare_initial_Root_capture_ref'],row['prepare_completed_Root_capture_ref'],ready,c,closed['request_ref']),
        *root_run_pair(row['run_initial_Root_capture_ref'],row['run_completed_Root_capture_ref'],closed['invocation_observations'][-1]['ref'],c,closed['request_ref'])]
    return dict(selector=c['selector_key'],run_id=c['run_id'],report_ref=summary['report_ref'],tool_run_ref=summary['tool_run_ref'],
        actual_native_exit=0,assertions=c['expected_native_ids'],selected_tests=c['selected_tests'],owned_members=len(owned['members']),
        native_event_interval=intervals,jobs=jobs,Root_original_tool_pairs=captures,compiler_input_refs_held=len(stable),
        module_count=len(bp['module_go_mod_refs']),mode_predicate_facts=mode_facts(closure,owned,report,c,native),
        formal_case_accepted_delta=0,formal_acceptance=False)

def execute_review(args):
    require(len(args)==3,'THREE_TYPED_REVIEW_INPUT_ARGUMENTS')
    input_ref=dict(path=args[0],sha256=args[1],bytes=int(args[2]));packet=decode(read_ref(input_ref))
    require(set(packet)=={'schema','source_review_ref','groups'}and packet['schema']=='researchos.w09-nf5-four-actual-review-input.v1'
        and set(packet['groups'])=={'W09-G01','W09-G02','A06','C19'},'ALL_FOUR_ACTUAL_GROUPS_REQUIRED')
    previous=decode(read_ref(packet['source_review_ref']));require(previous['actor_id']==ACTOR
        and previous['decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE','REAL_PRIOR_SOURCE_REVIEW')
    for name,(sha,size)in SOURCE_PINS.items():read_ref(dict(path=str(BASE/name),sha256=sha,bytes=size))
    all_choices=decode((BASE/'source.choice.json').read_bytes());choices={name:dict(all_choices['common'],**partial)for name,partial in all_choices['selectors'].items()};bp=decode((BASE/'compiler-source-blueprint.json').read_bytes())
    closure_path=R/'ops/ci/w09_evidence_closure.py';closure_ref=next(x for x in choices['W09-G02']['source21']if Path(x['path'])==closure_path)
    closure=load_module(read_ref(closure_ref),closure_path);profile_path=R/'execution/v2.4/formal_profile_w09.py'
    profile_raw=read_ref(dict(path=str(profile_path),sha256='d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f',bytes=71397))
    refs=[input_ref,packet['source_review_ref'],dict(path=str(profile_path),sha256=digest(profile_raw),bytes=len(profile_raw)),closure_ref,
        *[dict(path=str(BASE/name),sha256=sha,bytes=size)for name,(sha,size)in SOURCE_PINS.items()],*choices['W09-G02']['source21'],
        pin(R/'execution/toolchains/locked.json'),*collect_actual_refs(packet,choices)]
    unique={key(ref):ref for ref in refs}
    guard_raw=GUARD.read_bytes();require(digest(guard_raw)==GUARD_SHA and len(guard_raw)==11404,'KNOWN_SOURCE_GUARD_PIN')
    module=types.ModuleType('nf5_actual_known_guard');module.__file__=str(GUARD);exec(compile(guard_raw,str(GUARD),'exec'),module.__dict__)
    guard=module.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    result=None;primary=None;cleanup=None
    try:
        guard.acquire(list(unique.values()))
        groups={}
        for name in('W09-G01','W09-G02','A06'):
            facts=review_group(packet['groups'][name],choices[name],closure,profile_raw,bp)
            closed=decode(read_ref(packet['groups'][name]['producer_closed_ref']));ready=decode(read_ref(packet['groups'][name]['prepare_ref']))
            facts.update(fact_status='ACTUAL_FACTS_CHECKED_PENDING_TRUE_FULL_MODE',qualified_for_main_formal_consumption=False,
                runtime_closure=reviewed_runtime_closure(closed,ready,choices[name],packet_artifacts(closed,choices[name]),bp),
                Root_outer_exit=0,Root_python_exit=0,producer_actual_exit=0)
            groups[name]=facts
            with(Q/('actual-group-'+name+'.unsealed.json')).open('xb')as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        groups['C19']=review_refused_c19(packet['groups']['C19'],choices['C19'],closure,profile_raw,bp)
        with(Q/'actual-group-C19.unsealed.json').open('xb')as f:f.write((json.dumps(groups['C19'],ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        result=dict(schema='researchos.w09-nf5-four-actual-independent-qualification.v1',reviewer=ACTOR,producer=ROOT_ACTOR,
            source_author='codex:/root/attach_restore_independent_review',qualification='PARTIAL_ACTUAL_FACTS_THREE_CHECKED_C19_REFUSED',
            groups=groups,checked_groups=['W09-G01','W09-G02','A06'],refused_groups=['C19'],overall_qualified=False,
            mode_finalization='MODE_FINALIZATION_REQUIRES_TRUE_FULL_REVIEWER',final_Mode_issued=False,formal_acceptance=False,
            formal_case_accepted_delta=0,new_Native_runs=0,new_Go_runs=0,new_model_requests=0,Main_written=False,Canon_written=False)
    except BaseException as exc:primary=exc
    finally:
        try:cleanup=guard.close()
        finally:
            with(Q/'actual-review-guard.closed.json').open('xb')as f:f.write((json.dumps(cleanup,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    if primary is not None:raise primary
    guard_receipt(cleanup);result['actual_review_guard_ref']=pin(Q/'actual-review-guard.closed.json')
    with(Q/'actual-qualification.unsealed.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=result['qualification'],groups=list(result['groups']),qualification_ref=pin(Q/'actual-qualification.unsealed.json'),formal_case_accepted_delta=0),ensure_ascii=False));return 0
def main(args):return execute_review(args)
if __name__=='__main__':
    rc=1
    try:rc=main(sys.argv[1:])
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
