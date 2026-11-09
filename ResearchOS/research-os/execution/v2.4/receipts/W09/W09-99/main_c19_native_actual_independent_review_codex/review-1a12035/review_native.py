from pathlib import Path
import ast,copy,hashlib,json,os,re,sys,tempfile,types,uuid
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r369_native_source_root/cp369-c19-20261009';O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review';PRODUCER='codex:/root';RUN='9e912dfc1058454da08ae7f93f4de24d'
checks=[];refs={};raws={};controls=[]
def ck(n,v,d=None):checks.append(dict(name=n,passed=bool(v),detail=d))
def pinraw(p,b):return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def pin(p):p=Path(p);return pinraw(p,p.read_bytes())
def read(r):
    if not(type(r)==dict and set(r)=={'path','sha256','bytes'} and type(r['path'])==str and type(r['sha256'])==str and re.fullmatch('[0-9a-f]{64}',r['sha256']) and type(r['bytes'])==int and r['bytes']>=0):raise ValueError('EXACT_TYPED_REF')
    p=Path(r['path']);k=str(p).casefold()
    if k in refs:
        if refs[k]!=r:raise ValueError('CONFLICTING_REF_'+str(p))
        return raws[k]
    b=p.read_bytes();ck('exact_pin:'+str(p),pinraw(p,b)==r)
    if pinraw(p,b)!=r:raise ValueError('PIN_DRIFT_'+str(p))
    refs[k]=r;raws[k]=b;return b
def obj(r):return json.loads(read(r))
def discover(p):r=pin(p);return r,obj(r)
def save(name,data):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def relref(r):return dict(r,path=Path(r['path']).relative_to(R).as_posix())
def module(r,name):
    m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m;exec(compile(read(r),r['path'],'exec'),m.__dict__);return m
def caught(f):
    try:f()
    except Exception as e:return {'type':type(e).__name__,'error':str(e)}
    return None
def guard_ok(g):
    return g['closed'] is True and type(g['retained_handles_count'])==int and g['retained_handles_count']==0 and g['errors']==[] and g['verification']=='PASSED' and g['failure'] is None
handoffref=dict(path=str(S/'Main-C19-actual-handoff.root.json'),sha256='cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835',bytes=4474)
h=obj(handoffref);ready=obj(h['prepare_ready_ref']);closed=obj(h['producer_closed_ref']);packet=obj(h['native_packet_ref']);sh=obj(h['source_handoff_ref']);sm=obj(h['source_manifest_ref'])
request=obj(h['request_ref']);scope=obj(request['scope_ref']);vector=obj(h['vector_ref'])
choice=obj(sh['choice_ref']);blueprint=obj(sh['compiler_blueprint_ref']);contract=obj(sh['root_calling_contract_ref'])
for r in sm['members']:read(r)
sourceh=obj(scope['source_review_handoff_ref']);sourcem=obj(scope['source_review_manifest_ref']);sourced=obj(scope['source_review_decision_ref'])
adoptionh=obj(scope['adoption_review_handoff_ref']);adoptionm=obj(scope['adoption_review_manifest_ref']);adoptiond=obj(scope['adoption_review_decision_ref']);adoption=obj(scope['adoption_outcome_ref'])
ck('sealed_Source_v2_exact',sh['source_revision']=='v2' and sh['manifest_ref']==h['source_manifest_ref']==scope['source_manifest_ref'] and scope['source_handoff_ref']==h['source_handoff_ref'] and sourceh['manifest_ref']==scope['source_review_manifest_ref'] and sourceh['source_decision_ref']==scope['source_review_decision_ref'] and sourced['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SINGLE_MAIN_C19_PRODUCER' and sourced['actor_id']==ACTOR and sourced['actor_role']=='INDEPENDENT_NON_AUTHOR' and sourced['execution_grant'] is False)
ck('registered_actual_request_vector',request['issued_by']==h['issued_by']==PRODUCER and request['canonical_vector_ref']==h['vector_ref'] and request['scope_ref']['path']==str(S/'scope-registration.root.json') and ready['request_ref']==closed['request_ref']==h['request_ref'] and vector==ready['canonical_vector'] and vector['checkpoint_revision']==369 and vector['ownership_revision']==173)
canon=[obj(r) for r in vector['refs']]
cp,ow=canon[:2]
factsref=cp['work_in_progress']['mu_sdk_r369']['facts_ref'];facts=obj(factsref)
ck('Root_scope_owner_worker_current',len(scope)==45 and len(facts['owner'])==17 and len(facts['worker'])==9 and scope==obj(facts['scope_ref']) and facts['scope_ref']==request['scope_ref'] and [w for w in cp['workers'] if w.get('slice_id')==facts['worker']['slice_id']]==[facts['worker']] and facts['owner'] in ow['card_path_bindings']['W09-99']['subtasks'].values() and ow['active_integrator']['id']==PRODUCER)
ck('component_only_scope',scope['formal_acceptance'] is False and h['formal_case_accepted_delta']==0 and h['formal_acceptance'] is False and h['parent_acceptance'] is False)
for r in sh['source21']+sh['main_seven_after_refs']:read(r)
ck('Source21_sevenMain_current',len(sh['source21'])==21 and len(sh['main_seven_after_refs'])==7 and ready['source21']==choice['source21']==sh['source21'])
ck('run_main_paths',h['run_id']==ready['run_id']==choice['run_id']==packet['run_id']==closed['summary']['run_id']==RUN and h['source_root']==ready['source_root']==choice['source_root']==packet['consumer_source_root']==str(R))
invocations=[obj(r) for r in h['actual_invocation_refs']]
inventory=obj(closed['summary']['compiler_inventory_ref']);permit=obj(closed['summary']['launcher_permit_ref'])
producer=Path(h['producer_closed_ref']['path']).parent
startref,started=discover(producer/'launcher.started.json');closeref,launcherclosed=discover(producer/'launcher.closed.json')
intentref,intent=discover(producer/'attempt.intent.json')
reportref=packet['original_report_ref'];toolref=packet['original_tool_run_ref'];report=obj(reportref);tool=obj(toolref)
for r in h['original_tool_io_refs']:obj(r)
guardobservations=[]
for stage_name,stage in [('prepare',ready),('run',closed)]:
    ck(stage_name+'_no_errors',stage['error'] is None and stage['original_exception_type'] is None and stage['original_invocation_diagnostics'] is None and stage['original_invocation_errors']==[] and stage['cleanup_errors']==[])
    ck(stage_name+'_closed_no_formal',stage['all_guards_closed'] is True and stage['all_cleanup_receipts_saved'] is True and stage['all_owned_jobs_closed'] is True and stage['actual_formal_consumers'] is False and stage['formal_case_accepted_delta']==0 and stage['Main_source_written'] is False and stage['Canon_written'] is False and stage['automatic_retry'] is False and stage['individual_unobserved_native_exits'] is None)
    for g in stage['guard_cleanups']:
        z=obj(g['ref']);ck(stage_name+'_guard_'+g['label'],g['closed'] is True and g['receipt_saved'] is True and z==g['observation'] and guard_ok(z))
        for e in z['entries']:
            ck('guard_entry_closed:'+stage_name+':'+e['path'],e['verified'] is True and e['final_path_match'] is True and e['closed'] is True)
            read({k:e[k] for k in ['path','sha256','bytes']})
        guardobservations.append(dict(stage=stage_name,label=g['label'],ref=g['ref'],entries=len(z['entries']),closed=z['closed'],retained_handles_count=z['retained_handles_count']))
ck('prepare_no_native',ready['status']=='PREPARED_ALL_GUARDS_CLOSED' and ready['native_started'] is False and ready['invocation_refs']==[] and ready['invocation_observations']==[])
ck('two_run_owned_jobs',closed['status']=='MAIN_C19_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW' and closed['invocation_refs']==h['actual_invocation_refs'] and len(closed['invocation_observations'])==2 and closed['native_packet_ref']==h['native_packet_ref'])
processfacts=[]
for i,(ref,inv,obs) in enumerate(zip(h['actual_invocation_refs'],invocations,closed['invocation_observations'])):
    result=inv['result'];job=result['job_cleanup'];expectedft=[134360155122022473,134360159867473886][i]
    ck('typed_PID_FILETIME_exit:'+str(i),type(result['owned_child_pid'])==int and result['owned_child_pid']>0 and type(result['creation_time_100ns'])==int and result['creation_time_100ns']==expectedft and inv['creation_time_100ns_decimal']==str(expectedft) and type(result['actual_exit'])==int and result['actual_exit']==0 and type(inv['actual_outer_exit'])==int and inv['actual_outer_exit']==0)
    ck('job_cleanup:'+str(i),all(job[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and type(job['active_processes_last_observed'])==int and job['active_processes_last_observed']==0 and job['errors']==[] and job['termination_requested'] is False and job['termination_succeeded'] is None and job['termination_code_requested'] is None)
    ck('original_owned_observation:'+str(i),obs['ref']==ref and obs['record']==inv and obs['verified'] is True and obs['job_closed'] is True and inv['exception'] is None and inv['evidence_errors']==[] and result['error'] is None and result['timed_out'] is False and result['resumed'] is True and inv['individual_child_numeric_exit'] is None)
    ck('owned_same_cwd_env:'+str(i),inv['cwd']==str(R) and inv['public_environment']==ready['environment']==permit['environment']==intent['actual_environment'])
    read(inv['stdout_ref']);read(inv['stderr_ref'])
    processfacts.append(dict(label=obs['label'],invocation_ref=ref,pid=result['owned_child_pid'],creation_time_100ns=result['creation_time_100ns'],creation_time_100ns_decimal=inv['creation_time_100ns_decimal'],actual_exit=result['actual_exit'],individual_descendant_exit=None,job_cleanup=job))
ck('intent_exact_once',intent['request_ref']==h['request_ref'] and intent['canonical_vector']==vector and intent['run_id']==RUN and intent['one_go_list'] is True and intent['one_go_test'] is True and intent['no_automatic_retry'] is True)
expected_list=[choice['tool_refs']['go']['path'],'list','-test','-deps','-compiled','-export','-json','./internal/domain']
expected_launcher=[choice['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',sh['launcher_ref']['path'],closed['summary']['launcher_permit_ref']['path'],closed['summary']['launcher_permit_ref']['sha256'],str(closed['summary']['launcher_permit_ref']['bytes'])]
ck('argv_exact_owned_jobs',invocations[0]['argv']==expected_list and invocations[1]['argv']==expected_launcher and invocations[0]['timeout_seconds']==240 and invocations[1]['timeout_seconds']==420)
expected_env=ready['environment'];scratch=Path(choice['scratch_root'])
ck('private_run_environment',expected_env['TEMP']==expected_env['TMP']==str(scratch/'temp') and expected_env['GOCACHE']==str(scratch/'gocache') and expected_env['RESEARCHOS_TASK_ID']=='W09' and expected_env['RESEARCHOS_CASE_ID']=='C19' and expected_env['RESEARCHOS_CHECK_ID']=='' and expected_env['RESEARCHOS_RETRIEVAL_MODE']=='fixture' and expected_env['GOENV']=='off' and expected_env['GOWORK']=='off' and expected_env['GOPROXY']=='off' and expected_env['GOSUMDB']=='off' and expected_env['GOTOOLCHAIN']=='local' and expected_env['GOFLAGS']=='-mod=readonly -p=1')
for r in choice['tool_refs'].values():read(r)
for name in ['guard_ref','owned_job_ref','toolchain_ref','identity_ref','spec_manifest_ref']:read(choice[name])
# Reconstruct compiler closure from the original concatenated go-list JSON, without invoking Go.
text=read(invocations[0]['stdout_ref']).decode('utf-8');decoder=json.JSONDecoder();pos=0;packages=[];stable={};generated={};exports={};gomods={};embeds=[]
bpstable={x['path']:x for x in blueprint['stable_input_refs']}
fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
while pos<len(text):
    while pos<len(text) and text[pos].isspace():pos+=1
    if pos==len(text):break
    pkg,pos=decoder.raw_decode(text,pos);packages.append(pkg['ImportPath']);ck('package_no_error:'+pkg['ImportPath'],not pkg.get('Error') and not pkg.get('DepsErrors'))
    directory=Path(pkg['Dir']) if pkg.get('Dir') else None
    for field in fields:
        for name in pkg.get(field,[]):
            path=Path(name);path=path if path.is_absolute() else directory/path
            rr=pin(path);read(rr)
            if path.is_relative_to(scratch/'gocache'):generated[rr['path']]=rr
            else:
                ck('stable_matches_blueprint:'+rr['path'],bpstable.get(rr['path'])==rr);stable[rr['path']]=rr
            if field.endswith('EmbedFiles'):embeds.append(dict(package=pkg['ImportPath'],field=field,ref=rr))
    mod=pkg.get('Module')
    while mod:
        if mod.get('GoMod'):
            rr=pin(Path(mod['GoMod']));read(rr);ck('Module_GoMod_held:'+rr['path'],bpstable.get(rr['path'])==rr);gomods[rr['path']]=rr
        mod=mod.get('Replace')
    if pkg.get('Export'):
        path=Path(pkg['Export']);ck('private_export:'+str(path),path.is_relative_to(scratch/'gocache'));rr=pin(path);read(rr);exports[rr['path']]=rr
    elif not pkg.get('DepOnly') and pkg.get('Name') not in (None,'main'):ck('only_builtin_no_export:'+pkg['ImportPath'],pkg['ImportPath'] in ('unsafe','builtin'))
ck('exact351_roster',len(packages)==351 and packages==inventory['packages'] and sorted(packages)==sorted(blueprint['package_roster']) and inventory['package_count']==351)
for key,values in [('stable_build_input_refs',stable),('private_generated_input_refs',generated),('private_export_refs',exports),('module_go_mod_refs',gomods)]:
    ck('inventory_reproduced:'+key,inventory[key]==list(values.values()))
ck('inventory_34embeds_19gomods',inventory['actual_embed_files']==embeds and len(embeds)==34 and gomods=={r['path']:r for r in blueprint['module_go_mod_refs']} and len(gomods)==19)
ck('inventory_current_Main_Source',inventory['source21']==sh['source21'] and inventory['source_root']==str(R) and inventory['private_GOCACHE']==str(scratch/'gocache') and inventory['blueprint_ref']==sh['compiler_blueprint_ref'])
# Original and archived byte sets must be one-to-one, with all original paths confined to this run.
original_map={};archive_map={}
for row in packet['raw_copy_mapping']:
    a,b=row['original_ref'],row['archive_ref'];ab,bb=read(a),read(b);pa,pb=Path(a['path']),Path(b['path'])
    ck('archive_exact:'+a['path'],ab==bb and pa.is_relative_to(Path(choice['output_root'])) and pb.is_relative_to(producer/'native-packet') and pa.relative_to(Path(choice['output_root']))==pb.relative_to(producer/'native-packet'))
    ck('archive_unique:'+a['path'],a['path'] not in original_map and b['path'] not in archive_map)
    original_map[a['path']]=a;archive_map[b['path']]=b
ck('packet_exact490',len(original_map)==len(archive_map)==490 and {str(p) for p in Path(choice['output_root']).rglob('*') if p.is_file()}==set(original_map) and {str(p) for p in (producer/'native-packet').rglob('*') if p.is_file()}==set(archive_map))
ck('packet_report_tool_same',closed['summary']['report_ref']==reportref and closed['summary']['tool_run_ref']==toolref and packet['immutable_original_bytes'] is True and packet['formal_acceptance'] is False)
source=dict(report,report_reference=Path(reportref['path']).relative_to(R).as_posix())
ck('MainSource_version_exact',report['version_manifest']['source_sha256']=={Path(r['path']).relative_to(R).as_posix():'sha256:'+r['sha256'] for r in sh['source21']} and report['version_manifest']['git_head']==choice['expected_git_head'] and report['version_manifest']['go_lock_sha256']=='sha256:'+choice['toolchain_ref']['sha256'] and report['version_manifest']['spec_manifest_sha256']=='sha256:'+choice['spec_manifest_ref']['sha256'])
ck('actual_os_fixture',report['version_manifest']['os']=='Windows' and report['version_manifest']['os_release']=='11' and report['scope']=='FIXTURE_IMPLEMENTED_SERVICE' and report['task_id']=='W09' and report['check_id'] is None and report['case_id']=='C19')
ck('original_native_pass_not_formal',report['run_id']==RUN and report['status']=='PASS' and type(report['exit_code'])==int and report['exit_code']==0 and report['timed_out'] is False and report['assertions']==5 and sorted(report['assertion_ids'])==sh['expected_native_ids'] and report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING' and report['formal_case_accepted_delta']==0 and tool['formal_acceptance']=='NOT_RUN')
ck('tool_report_raw_exact',tool['schema']=='researchos.w09-native-producer-tool-run.v1' and tool['report_ref']==source['report_reference'] and tool['report_sha256']==reportref['sha256'] and tool['run_id']==RUN and tool['actual_invocation']==report['actual_invocation'] and tool['native_exit_code']==report['exit_code'] and tool['stdout_ref']==report['raw_evidence_references'][0] and tool['stderr_ref']==report['raw_evidence_references'][1] and tool['stdout_sha256']==original_map[str(R/tool['stdout_ref'])]['sha256'] and tool['stderr_sha256']==original_map[str(R/tool['stderr_ref'])]['sha256'])
emitted=json.loads(read(invocations[1]['stdout_ref']))
ck('producer_original_stdout_bound',emitted['report_reference']==source['report_reference'] and emitted['tool_run_reference']==Path(toolref['path']).relative_to(R).as_posix() and emitted['tool_run_sha256']==toolref['sha256'] and all(emitted[k]==v for k,v in report.items() if k not in ('assertion_results','owned_export')))
# Launcher causality: bind permit, original started/closed, exact runner/runtime, and private one-shot UUID.
runnerref=next(r for r in sh['source21'] if Path(r['path']).name=='retrieval.py')
ck('launcher_permit_current',permit['request_ref']==h['request_ref'] and permit['run_id']==RUN and permit['output_root']==choice['output_root'] and permit['launcher_ref']==sh['launcher_ref'] and permit['runner_ref']==runnerref and set(permit)=={'schema','request_ref','run_id','output_root','launcher_ref','runner_ref','environment'})
ck('launcher_started_current',started['permit_ref']==closed['summary']['launcher_permit_ref'] and started['launcher_ref']==sh['launcher_ref'] and started['runner_ref']==runnerref and started['fixed_run_id']==RUN and started['fixed_output_root']==choice['output_root'] and started['source_root']==str(R) and started['Source21']==sh['source21'] and started['adapter']=='RUNNER_PRIVATE_UUID_OBJECT_ONLY' and started['stdlib_uuid_modified'] is False and started['Main_source_modified'] is False)
ck('launcher_closed_current',launcherclosed['permit_ref']==closed['summary']['launcher_permit_ref'] and launcherclosed['runner_ref']==runnerref and launcherclosed['launcher_ref']==sh['launcher_ref'] and type(launcherclosed['runner_returned_exit'])==int and launcherclosed['runner_returned_exit']==0 and launcherclosed['one_uuid_consumed'] is True and launcherclosed['cleanup_errors']==[] and launcherclosed['error'] is None and launcherclosed['stdlib_uuid_modified'] is False and launcherclosed['Main_source_modified'] is False and launcherclosed['unknown_individual_descendant_exit'] is None)
runnerraw=read(runnerref);ltree=ast.parse(read(sh['launcher_ref']));rtree=ast.parse(runnerraw);attrs=[n for n in ast.walk(rtree) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='uuid']
ck('runner_uuid_only_evidence_directory',len(attrs)==1 and attrs[0].attr=='uuid4' and any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='evidence' for t in n.targets) and attrs[0] in list(ast.walk(n.value)) for n in ast.walk(rtree)))
ltext=read(sh['launcher_ref']).decode();ck('launcher_exact_runner_runtime_no_global_uuid_patch',"runner.uuid=provider" in ltext and 'runner.uuid=original_uuid' in ltext and 'stdlib_uuid4=uuid.uuid4' in ltext and 'uuid.uuid4 is stdlib_uuid4' in ltext and sh['runtime_ref']['sha256'] in ltext and "runner.ROOT==m.R" in ltext)
cls=next(n for n in ltree.body if isinstance(n,ast.ClassDef) and n.name=='OneShotEvidenceUUID')
ns={'uuid':uuid};exec(compile(ast.Module(body=[cls],type_ignores=[]),'<private-UUID-class-only>','exec'),ns)
u=ns['OneShotEvidenceUUID'](RUN);stdlibbefore=uuid.uuid4
ck('UUID_class_first_call_exact',u.uuid4().hex==RUN and uuid.uuid4 is stdlibbefore)
for label,f in [('UUID_second_call',lambda:u.uuid4()),('UUID_other_attribute',lambda:getattr(u,'uuid1')),('UUID_internal_access',lambda:getattr(u,'_value'))]:
    e=caught(f);ck('reject_'+label,e is not None);controls.append(dict(case=label,expected_rejection=e))
# Root tool fidelity including all original progress chunks. Values remain Python integers/decimal strings.
toolios=[obj(r) for r in h['original_tool_io_refs']]
runio=next(d for d in toolios if d['original_exec_command_result']['chunk_id']=='0ba7eb')
prepareio=next(d for d in toolios if d['original_exec_command_result']['chunk_id']=='2812db')
progress=[]
for d in [runio]:
    for result in [d['original_exec_command_result'],*d.get('polls',[])]:
        for line in result['output'].splitlines():
            if line.startswith('{'):
                value=json.loads(line)
                if 'progress' in value:progress.append(value)
ck('Root_original_run_end0',runio['original_exec_command_result']['session_id']==7632 and runio['polls'][-1]['chunk_id']=='0704e1' and runio['polls'][-1]['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in runio['polls'][-1]['output'])
ck('Root_progress_lossless',len(progress)==2 and [p['receipt_ref'] for p in progress]==h['actual_invocation_refs'] and [p['creation_time_100ns_decimal'] for p in progress]==[v['creation_time_100ns_decimal'] for v in invocations] and all(type(p['actual_outer_exit'])==int and p['actual_outer_exit']==0 and p['original_error'] is None and p['evidence_errors']==[] and p['unsaved_invocation'] is None for p in progress))
preparelast=prepareio.get('polls',[prepareio['original_exec_command_result']])[-1]
ck('Root_prepare_end0',preparelast['chunk_id']=='a7e7f3' and preparelast['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in preparelast['output'])
for io,name in [(runio,'producer_caller_ref'),(prepareio,'prepare_caller_ref')]:
    cmd=io['original_exec_command_args']['cmd'];ck('Root_exact_request_caller:'+name,all(x in cmd for x in [sh[name]['path'],h['request_ref']['path'],h['request_ref']['sha256'],str(h['request_ref']['bytes'])]))
# Finite guard covers actual evidence, compiler closure, canonical vector, Source21 and all author-held inputs.
gm=module(choice['guard_ref'],'native_actual_review_guard')
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);held=list(refs.values())
print(json.dumps(dict(progress='REVIEW_INPUTS_COLLECTED',files=len(held),bytes=sum(r['bytes'] for r in held),checks=len(checks))),flush=True)
closure_ref=next(r for r in sh['source21'] if Path(r['path']).name=='w09_evidence_closure.py');router_ref=next(r for r in sh['source21'] if Path(r['path']).name=='w09_formal_router.py')
try:
    guard.acquire(held)
    ck('finite_inputs_held_identical',all(guard.get_buffer(r['path'])==raws[str(Path(r['path'])).casefold()] for r in held))
    closure=module(closure_ref,'w09_evidence_closure')
    native=closure.verify_native(R,source,report,sh['expected_native_ids'],sh['selected_tests'])
    owner={aid:'TestW09C19ChainInvalidation' if aid=='C19-05' else 'TestW09C19ExplicitOriginAndUnknown' for aid in sh['expected_native_ids']}
    owned=closure.verify_owned(R,source,report,sh['selected_tests'],owner);closure.verify_c19(owned)
    ck('real_Source_readonly_native_owned_C19_verifiers',native['run_id']==RUN and len(native['records'])==5 and len(owned['members'])==486)
    rt=ast.parse(read(router_ref));assigns=[n for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['NATIVE','FORMAL','SELECTED'] for t in n.targets)]
    routing={};exec(compile(ast.Module(body=assigns,type_ignores=[]),'<exact-route-tables-only>','exec'),routing)
    routes=[('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19')]
    for route in routes:ck('route_exact_native_formal:'+route[0],routing['NATIVE'][route]==tuple(sh['expected_native_ids']) and routing['FORMAL'][route]==('C19-01','C19-02','C19-03') and set(routing['SELECTED'][route])==set(sh['selected_tests']))
    states=[x for label,group in owned['events'].items() if label.startswith('state-') for x in group]
    exchanges=owned['events'].get('http-exchange',[])
    ck('fixture_original_temp_roots',bool(states) and all(x['value'].get('root_path') and Path(x['value']['root_path']).is_relative_to(scratch/'temp') for x in states))
    ck('fixture_inprocess_http_actual',bool(exchanges) and all(x['value'].get('delivery')=='IN_PROCESS_HTTptest_RECORDER' for x in exchanges))
    stdout_lines=read(original_map[str(R/tool['stdout_ref'])]).decode().splitlines();parsed=[json.loads(x) for x in stdout_lines];assertionlocators=[]
    for rec in report['assertion_results']:
        rawref=rec['owned_export_ref'];value=json.loads(read(rawref));group=owned['events']['assertion-'+rec['assertion_id']]
        loc=dict(native_id=rec['assertion_id'],test_name=rec['test_name'],run_id=RUN,expected_raw_ref=rawref,expected_pointer='/expected',actual_raw_ref=rawref,actual_pointer='/actual',expected=value['expected'],actual=value['actual'],stdout_ref=native['stdout'],stdout_jsonl_lines_1based=[i+1 for i,e in enumerate(parsed) if rec['assertion_id'] in e.get('Output','') and 'W09_ASSERTION ' in e.get('Output','')],assertion_report_index=report['assertion_results'].index(rec),status=value['status'])
        ck('true_Expected_Actual_locator:'+rec['assertion_id'],group[0]['path']==Path(rawref['path']) and value['actual']==rec['evidence'] and all(value['actual'].get(k)==v for k,v in value['expected'].items()) and len(loc['stdout_jsonl_lines_1based'])==1)
        assertionlocators.append(loc)
finally:
    cleanup=guard.close();cleanupref=save('review-source-guard.cleanup.actual.json',cleanup)
ck('review_guard_all_closed',guard_ok(cleanup))
failed=[x for x in checks if not x['passed']]
# Write qualification envelopes only after complete evidence verification and guard closure.
locatorref=save('C19-Expected-Actual-locators.json',dict(run_id=RUN,report_ref=reportref,assertions=assertionlocators,native_ids=sh['expected_native_ids'],formal_case_accepted_delta=0))
causalref=save('launcher-mode-causality.json',dict(decision='MODE_NEUTRAL_EVIDENCE_ID_RESERVATION' if not failed else 'REQUEST_CHANGES',run_id=RUN,launcher_ref=sh['launcher_ref'],runtime_ref=sh['runtime_ref'],runner_ref=runnerref,permit_ref=closed['summary']['launcher_permit_ref'],started_ref=startref,closed_ref=closeref,invocation_ref=h['actual_invocation_refs'][1],private_runner_uuid_only=True,exactly_one_evidence_uuid=True,actual_report_run_id=report['run_id'],effect=['Reserves evidence output directory and run identifier only','Go test process receives run ID solely for owned evidence correlation','Business IDs and assertions execute in unchanged Go process'],stdlib_uuid_modified=False,Main_Source_modified=False,Original_raw_modified=False,mode='FIXTURE',input_origin='OWNED_TEMP_DIR',consumer_environment_required={'TEMP':expected_env['TEMP'],'TMP':expected_env['TMP']},native_test_exit_observed=report['exit_code'],unobserved_Go_test_PID=None,unobserved_Go_test_FILETIME=None,unobserved_individual_descendant_exits=None))
processref=save('original-process-and-cleanup.json',dict(processes=processfacts,native_test_exit=report['exit_code'],native_test_exit_origin=toolref,inner_Go_PID=None,inner_Go_FILETIME=None,unknown_descendant_exits=None,Root_tool_io_refs=h['original_tool_io_refs'],author_guards=guardobservations,review_guard_cleanup_ref=cleanupref))
compilerref=save('independent-compiler-closure.json',dict(original_go_list_stdout_ref=invocations[0]['stdout_ref'],original_inventory_ref=closed['summary']['compiler_inventory_ref'],independent_package_count=len(packages),stable_input_count=len(stable),private_generated_input_count=len(generated),private_export_count=len(exports),Module_GoMod_count=len(gomods),embed_count=len(embeds),matches_original_inventory=True,blueprint_ref=sh['compiler_blueprint_ref'],no_Go_rerun=True))
nativeproof=save('native-evidence-review.json',dict(schema='researchos.w09-main-c19-independent-native-evidence.v1',decision='NATIVE_C19_COMPONENT_VERIFIED' if not failed else 'REQUEST_CHANGES',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',producer_id=PRODUCER,run_id=RUN,root_handoff_ref=handoffref,prepare_ready_ref=h['prepare_ready_ref'],producer_closed_ref=h['producer_closed_ref'],native_packet_ref=h['native_packet_ref'],report_ref=reportref,tool_run_ref=toolref,actual_canonical_refs=vector['refs'],source_review_handoff_ref=scope['source_review_handoff_ref'],Source21=sh['source21'],main_seven_after_refs=sh['main_seven_after_refs'],C19_locator_ref=locatorref,launcher_causality_ref=causalref,process_evidence_ref=processref,compiler_closure_ref=compilerref,all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanupref,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,actual_consumers_run_by_reviewer=False))
moderefs=[]
if not failed:
    oldtemp=tempfile.tempdir;tempfile.tempdir=expected_env['TEMP']
    try:
        for route in routes:
            suffix=route[0].replace('.','-')
            review=dict(schema='researchos.w09-independent-mode-review.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',producer_id=PRODUCER,run_id=RUN,report_sha256=reportref['sha256'],source_sha256=native['source_hashes'],go_executable=native['go'],run_os=report['version_manifest']['os'],run_os_release=report['version_manifest']['os_release'],decision='QUALIFIED',route=list(route),mode='FIXTURE',input_origin='OWNED_TEMP_DIR',native_evidence_review_ref=nativeproof,launcher_causality_ref=causalref,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,requires_later_actual_consumer=True,consumer_environment_required={'TEMP':expected_env['TEMP'],'TMP':expected_env['TMP']},reviewed_at=datetime.now(timezone.utc).isoformat())
            rr=save(suffix+'.independent-mode-review.json',review)
            decision=dict(schema='researchos.w09-mode-decision.v2',route=list(route),mode='FIXTURE',run_id=RUN,report_ref=source['report_reference'],report_sha256=reportref['sha256'],stdout_sha256=native['stdout']['sha256'],source_sha256=native['source_hashes'],go_executable=native['go'],producer_id=PRODUCER,reviewer_id=ACTOR,reviewer_role='INDEPENDENT_NON_AUTHOR',decision='QUALIFIED',independent_review_ref=relref(rr),input_origin='OWNED_TEMP_DIR',native_evidence_review_ref=nativeproof,launcher_causality_ref=causalref,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,actual_consumer_executed=False,consumer_environment_required={'TEMP':expected_env['TEMP'],'TMP':expected_env['TMP']},qualification_scope='C19_COMPONENT_ONLY')
            dr=save(suffix+'.mode-decision.json',decision)
            verified=closure.verify_mode(R,source,report,route,owned,native,relref(dr)['path'],dr['sha256'])
            ck('read_only_mode_interface:'+route[0],verified['mode']=='FIXTURE' and verified['formal_authority'] is False)
            moderefs.append(dict(route=list(route),independent_review_ref=rr,mode_decision_ref=dr,consumer_mode_decision_ref=relref(dr)['path'],consumer_mode_decision_sha256=dr['sha256'],pure_interface_verification=verified,consumer_environment_required={'TEMP':expected_env['TEMP'],'TMP':expected_env['TMP']}))
    finally:tempfile.tempdir=oldtemp
failed=[x for x in checks if not x['passed']]
status='ACTUAL_MAIN_C19_NATIVE_COMPONENT_AND_FIXTURE_MODES_QUALIFIED' if not failed else 'REQUEST_CHANGES'
cr=save('checks.json',dict(count=len(checks),passed=sum(x['passed'] for x in checks),checks=checks));fr=save('findings.json',dict(blocking_findings=len(failed),findings=failed));save('verified-input-pins.json',list(refs.values()));save('Source-only-negative-controls.json',dict(controls=controls,not_native_runs=True))
interfaceref=save('two-consumer-mode-interface.json',dict(schema='researchos.w09-main-c19-qualified-consumer-mode-inputs.v1',run_id=RUN,native_report_ref=source['report_reference'],native_report_sha256=reportref['sha256'],native_tool_run_ref=Path(toolref['path']).relative_to(R).as_posix(),native_tool_run_sha256=toolref['sha256'],modes=moderefs,must_run_after_this_HDF_sealed_and_Root_received=True,actual_consumers_run=False,source_root=str(R),formal_acceptance=False,formal_case_accepted_delta=0,parent_acceptance=False))
dr=save('actual-decision.json',dict(schema='researchos.w09-main-c19-independent-actual-native-decision.v1',decision=status,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',producer_id=PRODUCER,run_id=RUN,Root_handoff_ref=handoffref,native_evidence_review_ref=nativeproof,mode_qualification_refs=moderefs,consumer_interface_ref=interfaceref,actual_canonical_refs=vector['refs'],C19_native_ids=sh['expected_native_ids'],native_assertions=5,owned_raw_members=486,packet_original_and_copy_count=490,compiler_package_count=351,all_owned_jobs_closed=True,all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanupref,Native_rerun=False,Go_list_rerun=False,producer_rerun=False,dispatcher_executed=False,Canon_written=False,Main_Source_written=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,W09_full='OPEN',W09_G01='OPEN',W09_G02='OPEN',A06='OPEN',execution_grant=False,checks_ref=cr,findings_ref=fr,new_original_failures=[],reviewed_at=datetime.now(timezone.utc).isoformat()))
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(status+'。独立核验同次Main run9e912dfc1058454da08ae7f93f4de24d：351编译包、3701稳定输入、350私有exports、1生成输入、19GoMod与34embeds；Source21及Main7当前字节、CP369/OW173/SS/CM39精确不变。两个owned job PID/FILETIME/exit源自原始IO，均idle/全关；未观测后代数值保持NULL。五C19原始Expected/Actual定位、486 owned raw与490原件/归档逐字节复核。UUID仅私有runner证据ID一次保留，permit/started/closed与原Main runner和runtime绑定，未改变产品fixture语义。两条C19 route按当前Source接口给出FIXTURE模式资格；consumer需相同TEMP/TMP，必须在本包封存并由Root收到后另行执行。只调用只读证据验证函数，未调用consumer main/dispatcher/producer/Go。W09full/G01/G02/A06/Formal/Parent均OPEN，Formal增量0。所有guard实关0。\n')
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mr=save('MF.json',dict(schema='researchos.w09-main-c19-independent-actual-native-manifest.v1',members=members,Root_handoff_ref=handoffref))
hh=save('HDF.json',dict(schema='researchos.w09-main-c19-independent-actual-native-handoff.v1',status=status,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=mr,actual_decision_ref=dr,native_evidence_review_ref=nativeproof,mode_qualification_refs=moderefs,consumer_interface_ref=interfaceref,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held),all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanupref,actual_consumers_run=False,Native_rerun=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,new_original_failures=[],STOP=True,FINAL=True))
for r in members+[mr,hh]:
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
print(json.dumps(dict(status=status,checks=len(checks),blocking_findings=len(failed),findings=failed,HDF=hh,MF=mr,decision=dr,mode_refs=moderefs,interface=interfaceref,held_inputs=len(held)),ensure_ascii=False),flush=True)

