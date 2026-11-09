"""Independent read-only closure of two already executed C19 fixture consumers.
No Source entrypoint, dispatcher, Native producer, model, or canonical writer runs.
"""
import ast
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import types

N = Path(__file__).resolve().parent
W = N.parent.parent
R = W.parents[4]
D = W / 'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
PREV = W / 'cp370_actual_registration_independent_review_codex/actualr4-01a120ab'
REG = W / 'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
checks = []

def pin(p):
    p = Path(p).resolve(strict=True)
    b = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))

def read(p):
    return json.loads(Path(p).read_bytes())

def save(name, obj):
    with (N / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode())
    return pin(N / name)

def mod(p):
    m = types.ModuleType('review_' + Path(p).stem)
    m.__file__ = str(p)
    exec(compile(Path(p).read_bytes(), str(p), 'exec'), m.__dict__)
    return m

def check(name, ok, detail=None):
    checks.append(dict(name=name, passed=bool(ok), detail=detail))

def refs(x):
    if type(x) is dict:
        if set(x) == {'path', 'sha256', 'bytes'}:
            yield x
        else:
            for v in x.values():
                yield from refs(v)
    elif type(x) is list:
        for v in x:
            yield from refs(v)

def utc(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))

def filetime(s):
    # Preserve integer FILETIME; no IEEE-754 conversion.
    return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=s // 10)

def main():
    request_ref = pin(D / 'Main-C19-two-dispatcher-request.actual.root.json')
    check('handed exact Root request', (request_ref['sha256'], request_ref['bytes']) == ('3b4503947bf2a476c00a04a3c6f727277366193dec01cf9a788a4937130abf34', 5071))
    request = read(request_ref['path'])
    out = Path(request['output_dir'])
    closed_ref = pin(out / 'caller.closed.json')
    closed = read(closed_ref['path'])
    actual_guard = closed['source_guard_cleanup']
    sh = read(request['source_hdf_ref']['path'])
    sm = read(sh['manifest_ref']['path'])
    caller = mod(sh['caller_source_ref']['path'])
    check('workspace from paths and accepted source', R == caller.ROOT)
    scope = read(request['scope_ref']['path'])
    vector = read(request['current_canonical_vector_ref']['path'])
    proof = read(request['actual_registration_proof_ref']['path'])
    review = read(request['source_review_ref']['path'])
    owner = read(request['current_owner_ref']['path'])
    worker = read(request['current_worker_ref']['path'])
    current = vector['refs']
    cp, ow, ss, cm = [read(r['path']) for r in current]
    prior_h = read(PREV / 'HDF.json')
    prior_d = read(prior_h['actual_decision_ref']['path'])
    registrar_h = read(REG / 'HDF.json')
    registrar = mod(registrar_h['registrar_ref']['path'])
    bio_ref = pin(D / 'Main-C19-two-dispatchers.actual.original-tool-io.root.json')
    bio = read(bio_ref['path'])
    previous = mod(PREV / 'review.py')
    previous.N = N
    root_binding = read(PREV / 'activation.actual-host.binding.json')
    rootcap = previous.capture(root_binding['source_audit_path'], root_binding['source_line_offsets'][1], '9c95c2', 'two-consumers')
    own_audit = read(PREV / 'facts-review-seal.actual-host.binding.json')['source_audit_path']
    sealcap = previous.capture(own_audit, 0, '22a505', 'registration-review-seal')
    actual_refs = [{k: e[k] for k in ('path', 'sha256', 'bytes')} for e in actual_guard['entries']]
    documents = [request, sh, sm, scope, vector, proof, review, owner, worker, prior_h, prior_d]
    allrefs = [request_ref, closed_ref, bio_ref, pin(__file__), pin(PREV/'HDF.json'), pin(PREV/'review.py'), pin(REG/'HDF.json'), registrar_h['registrar_ref'], *actual_refs]
    for document in documents:
        allrefs.extend(refs(document))
    observations = []
    for route in caller.ROUTES:
        stem = route.replace('.', '-')
        outer_ref = pin(out / (stem + '.outer-observation.json'))
        verified_ref = pin(out / (stem + '.verified.json'))
        outer, verified = read(outer_ref['path']), read(verified_ref['path'])
        receipt = read(verified['dispatcher_receipt_ref']['path'])
        stdout_ref = pin(R / receipt['stdout']['path'])
        stderr_ref = pin(R / receipt['stderr']['path'])
        report = read(stdout_ref['path'])
        allrefs.extend([outer_ref, verified_ref, stdout_ref, stderr_ref, *refs(verified)])
        for p in report['source_pins']:
            allrefs.append(dict(p, path=str((R / p['path']).resolve())))
        allrefs.append(pin(R / report['native_tool_run_ref']))
        observations.append(dict(route=route, outer=outer, verified=verified, receipt=receipt, report=report, outer_ref=outer_ref, verified_ref=verified_ref, stdout_ref=stdout_ref, stderr_ref=stderr_ref))
    for cap in (rootcap, sealcap):
        allrefs.extend((cap['cap_ref'], cap['binding_ref']))
    failure_refs = [pin(N/'failure-a7cd3a.actual-host.raw.jsonl'), pin(N/'failure-a7cd3a.actual-host.binding.json')]
    allrefs.extend(failure_refs)
    old = scope['before_canonical_refs']
    archives = request['historical_cp369_archives']
    oldmap = {r['path'].casefold(): (r, a) for r, a in zip(old, archives)}
    resolved = []
    for ref in allrefs:
        known = oldmap.get(ref['path'].casefold())
        resolved.append(known[1] if known and ref == known[0] else ref)
    # Finite real SourceReadGuard over all 1,164 actual inputs plus review inputs.
    held, held_count = registrar.held_guard(resolved, False)
    summaries = []
    try:
        check('current four canonical exact execution vector', [pin(x['path']) for x in current] == current and current == prior_d['current_canonical_refs'])
        check('canonical CP370 OW174 commands39', cp['revision'] == 370 and ow['revision'] == 174 and cm['revision'] == 39)
        check('registration proof exact independent closure', proof['actual_registration_independent_review_refs'] == [pin(PREV/'HDF.json'), prior_h['manifest_ref'], prior_h['actual_decision_ref']] and proof['actual_registration_verified'] is True and prior_d['decision'] == 'ACTUAL_REGISTRATION_VERIFIED_NONFORMAL')
        check('actual outer host IO exact full result', registrar.extract_original_result_block(rootcap['output']['payload']['output']) == bio['result'] == rootcap['result'])
        check('actual Root input exact saved command', json.dumps(bio['args']['cmd'],ensure_ascii=False)[1:-1] in rootcap['call']['payload']['input'] and request_ref['sha256']+' '+str(request_ref['bytes']) in bio['args']['cmd'] and sh['caller_source_ref']['path'] in bio['args']['cmd'])
        check('actual Root outer and Python0 no poll', type(bio['actual_outer_exit']) is int and bio['actual_outer_exit'] == 0 and type(bio['actual_python_exit']) is int and bio['actual_python_exit'] == 0 and bio['result']['output'] == 'ROOT_SOURCE_PYTHON_EXIT=0\r\n' and 'session_id' not in bio['result'])
        check('wrapper unknown consumer exit fields remain NULL', all(bio[k] is None for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))
        published = json.loads(sealcap['result']['output'].splitlines()[0])
        check('actual independent registration seal precedes consumers', published['HDF'] == pin(PREV/'HDF.json') and published['decision'] == prior_h['actual_decision_ref'] and utc(rootcap['call']['timestamp']) > utc(sealcap['output']['timestamp']) and utc(rootcap['call']['timestamp']) > utc(proof['created_utc']))
        caller.validate_scope(scope)
        caller.validate_source_review(review,scope,request['source_hdf_ref'],sh['manifest_ref'],sh['caller_source_ref'],sh['root_contract_ref'])
        caller.validate_canon_lease(cp,ow,scope,request['scope_ref'],request['source_hdf_ref'],request['source_review_ref'],request['current_owner_ref'],request['current_worker_ref'],owner,worker,out)
        check('unmodified current Source scope review and unique owner lease validators', True)
        plan_ref = caller.frozen_plan()
        pointer_ref, registry_ref = caller.selected_registry(plan_ref)
        sealed_ref, static = caller.sealed_static_refs(plan_ref)
        expected = caller.dispatch_revisions(static)
        interface, interface_ref, modes = caller.qualified_modes()
        actual_table = {r['path'].casefold():r for r in actual_refs}
        check('actual finite1164 guard closed all entries',len(actual_refs)==1164 and actual_guard['attempted'] is True and actual_guard['verification']=='PASSED' and actual_guard['share_mode']=='FILE_SHARE_READ_ONLY' and actual_guard['closed'] is True and actual_guard['retained_handles_count']==0 and actual_guard['failure'] is None and actual_guard['errors']==[] and all(e['verified'] is True and e['final_path_match'] is True and e['closed'] is True for e in actual_guard['entries']))
        check('actual A8 sealed static refs held unchanged through both consumers',len(static)==8 and all(actual_table.get(r['path'].casefold())==r for r in static))
        check('actual current4 Source native modes request proof owner worker held',all(actual_table.get(r['path'].casefold())==r for r in [request_ref,*current,sh['caller_source_ref'],request['scope_ref'],request['actual_registration_proof_ref'],request['current_owner_ref'],request['current_worker_ref'],request['native_qualified_hdf_ref'],request['native_handoff_ref'],interface_ref,*[r for pair in modes for r in pair]]))
        handoff=read(request['native_handoff_ref']['path'])
        ready=read(handoff['prepare_ready_ref']['path']); native_closed=read(handoff['producer_closed_ref']['path']); packet=read(handoff['native_packet_ref']['path'])
        old_paths, actual_archives=caller.historical_archive_bindings(request,scope,(ready,native_closed))
        check('historical old369 four mapped only genuine Root archives', actual_archives==archives and all(pin(r['path'])==r for r in archives) and len(old_paths)==4)
        inventory=caller.packet_inventory(packet)
        check('all486 native original and486 archive members held',len(inventory)==972 and all(actual_table.get(r['path'].casefold())==r for r in inventory))
        source=Path(sh['caller_source_ref']['path']).read_text(encoding='utf-8')
        tree=ast.parse(source)
        execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
        env_expr=next(n.value for n in ast.walk(execute) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='env' for t in n.targets))
        env=eval(compile(ast.Expression(env_expr),'<sealed-env-dict>','eval'),{'str':str,'PYTHON':caller.PYTHON,'TEMP':caller.TEMP,'interface':interface})
        check('sealed Source TEMP TMP exact original Native directory',env['TEMP']==env['TMP']==str(caller.TEMP) and caller.TEMP.is_dir() and all(row['consumer_environment_required']=={'TEMP':str(caller.TEMP),'TMP':str(caller.TEMP)} for row in interface['modes']))
        check('sealed Source explicit environment excludes inherited credentials', not any(s in k.upper() for k in env for s in ('TOKEN','SECRET','PASSWORD','API_KEY')) and all(env[k]==str(caller.TEMP.parent/'profile') for k in ('USERPROFILE','LOCALAPPDATA','APPDATA')))
        calls=[(ast.unparse(n.func),n.lineno) for n in ast.walk(execute) if isinstance(n,ast.Call)]
        acquire=[line for name,line in calls if name=='held.acquire']; close=[line for name,line in calls if name=='held.close']; run=[line for name,line in calls if name=='helper.run_owned']
        loops=[n for n in ast.walk(execute) if isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(ROUTES)']
        check('sealed Source holds A8 before both actual consumers until finally',len(acquire)==len(close)==len(run)==len(loops)==1 and acquire[0]<loops[0].lineno<run[0]<close[0] and any(isinstance(n,ast.Try) and any(isinstance(a,ast.Call) and ast.unparse(a.func)=='held.close' for x in n.finalbody for a in ast.walk(x)) for n in ast.walk(execute)))
        router_tree=ast.parse(caller.ROUTER.read_bytes())
        tables={}
        for node in router_tree.body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('NATIVE','PRESERVED','FORMAL','SELECTED'):
                tables[node.targets[0].id]=ast.literal_eval(node.value)
        main=next(n for n in router_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        preserved=next(n for n in main.body if isinstance(n,ast.If) and ast.unparse(n.test)=='route in PRESERVED')
        spawn=[n for n in ast.walk(main) if isinstance(n,ast.Call) and ast.unparse(n.func).startswith('subprocess.')]
        closure_tree=ast.parse((R/'ops/ci/w09_evidence_closure.py').read_bytes())
        check('actual C19 routes select readonly Native branch never preserved Go branch',all((r,'W09','','C19') in tables['NATIVE'] and (r,'W09','','C19') not in tables['PRESERVED'] for r in caller.ROUTES) and all(n in list(ast.walk(preserved)) for n in spawn))
        forbidden=('subprocess.','socket.','requests.','httpx.','urllib.request.','os.system','os.popen')
        check('evidence closure contains no producer or outbound calls',not any(isinstance(n,ast.Call) and ast.unparse(n.func).startswith(forbidden) for n in ast.walk(closure_tree)))
        actual_identity=[(4524,134360260688116248),(13080,134360260721617605)]
        for index,item in enumerate(observations):
            route=item['route']; outer=item['outer']; verified=item['verified']; receipt=item['receipt']; report=item['report']; result=outer['result']; job=result['job_cleanup']
            caller.strict_pass(result,receipt,route,expected)
            check(route+' actual Source strictpass',True)
            check(route+' outer to verified exact extension',{k:v for k,v in verified.items() if k!='dispatcher_receipt_ref'}==outer)
            expected_argv=[str(caller.PYTHON),'-I','-S','-B','-X','utf8',str(caller.DISPATCHER),route,'--task-id','W09','--case-id','C19']
            check(route+' actual original frozen selector argv without spec',outer['argv']==expected_argv and outer['cwd']==str(R) and '--spec' not in outer['argv'])
            summary=read(outer['stdout_ref']['path'])
            check(route+' full raw summary ties invocation receipt',summary==dict(status='PASS',assertions=3,invocation_id=receipt['invocation_id'],receipt=verified['dispatcher_receipt_ref']['path']) and Path(outer['stderr_ref']['path']).read_bytes()==b'')
            check(route+' primary identity exact int FILETIME',type(result['owned_child_pid']) is int and type(result['creation_time_100ns']) is int and (result['owned_child_pid'],result['creation_time_100ns'])==actual_identity[index])
            check(route+' primary creation and receipt within Root call window',utc(rootcap['call']['timestamp'])<filetime(result['creation_time_100ns'])<=utc(receipt['started_at'])<utc(receipt['ended_at'])<utc(rootcap['output']['timestamp']))
            check(route+' normal job cleanup fully observed',result['resumed'] is True and result['stage']=='WAIT_PRIMARY_AND_JOB_IDLE' and job['termination_requested'] is False and job['termination_succeeded'] is None and job['termination_code_requested'] is None and job['unassigned_suspended_child_termination_requested'] is False and job['unassigned_suspended_child_termination_succeeded'] is None)
            check(route+' unobserved descendant identity remains NULL',outer['descendant_unobserved_pid'] is None and outer['descendant_unobserved_filetime'] is None and type(receipt['pid']) is int)
            check(route+' child report raw bytes match recorded sanitized hashes',item['stdout_ref']['sha256']==receipt['stdout']['sha256'] and item['stderr_ref']['sha256']==receipt['stderr']['sha256'] and item['stderr_ref']['bytes']==0 and receipt['stdout_sanitized'] is True and receipt['stderr_sanitized'] is True)
            check(route+' receipt child invocation exact registry argv',receipt['argv']==[str(caller.PYTHON),*cm['commands'][route]['argv']] and receipt['cwd']==str(R) and receipt['scope']=='CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE')
            row=cm['commands'][route]
            check(route+' TEMP TMP and mode refs allowed unchanged into router',all(k in row['allowed_env'] and k not in row.get('fixed_env',{}) and k not in row.get('tool_env',{}) and k in receipt['environment_names'] for k in ('TEMP','TMP','RESEARCHOS_W09_MODE_DECISION_REF','RESEARCHOS_W09_MODE_DECISION_SHA256','RESEARCHOS_W09_NATIVE_REPORT_REF','RESEARCHOS_W09_NATIVE_REPORT_SHA256','RESEARCHOS_W09_TOOL_RUN_REF','RESEARCHOS_W09_TOOL_RUN_SHA256')))
            check(route+' actual child C19 report exact IDs native5 and486members',report['status']=='PASS' and report['assertion_ids']==['C19-01','C19-02','C19-03'] and type(report['assertions']) is int and report['assertions']==3 and report['task_id']=='W09' and report['check_id'] is None and report['case_id']=='C19' and report['native_assertion_ids']==list(tables['NATIVE'][(route,'W09','','C19')]) and report['owned_export_member_count']==486)
            mode=report['mode_evidence']
            check(route+' distinct actual qualified FIXTURE mode exact report provenance',outer['mode_decision_ref']==modes[index][1] and pin(R/mode['decision_ref'])==modes[index][1] and mode['decision_sha256']==modes[index][1]['sha256'] and mode['mode']=='FIXTURE' and mode['formal_authority'] is False and report['formal_acceptance']=='PENDING_INDEPENDENT_VERIFIER' and report['native_tool_run_ref']==interface['native_tool_run_ref'])
            check(route+' original Native report and tool all held at execution',all(actual_table.get(str((R/p['path']).resolve()).casefold())==dict(p,path=str((R/p['path']).resolve())) for p in report['source_pins']) and actual_table.get(str((R/report['native_tool_run_ref']).resolve()).casefold())==pin(R/report['native_tool_run_ref']))
            summaries.append(dict(route=route,dispatcher_receipt_ref=verified['dispatcher_receipt_ref'],outer_observation_ref=item['outer_ref'],verified_ref=item['verified_ref'],stdout_ref=outer['stdout_ref'],stderr_ref=outer['stderr_ref'],dispatcher_child_stdout_ref=item['stdout_ref'],dispatcher_child_stderr_ref=item['stderr_ref'],mode_decision_ref=outer['mode_decision_ref'],actual_dispatcher_exit=0,actual_router_child_exit=0,owned_primary_pid=result['owned_child_pid'],owned_primary_filetime_decimal=str(result['creation_time_100ns']),descendant_unobserved_pid=None,descendant_unobserved_filetime=None,job_closed=True,mode='FIXTURE',formal_acceptance=False))
        check('two consumers distinct invocations and modes in serial order',observations[0]['receipt']['invocation_id']!=observations[1]['receipt']['invocation_id'] and modes[0][1]!=modes[1][1] and utc(observations[0]['receipt']['ended_at'])<filetime(observations[1]['outer']['result']['creation_time_100ns']))
        check('actual closed source and jobs component only',closed['status']=='TWO_C19_CONSTRUCTION_CONSUMERS_OBSERVED_PENDING_INDEPENDENT_REVIEW' and closed['routes_attempted']==list(caller.ROUTES) and closed['all_job_descendants_closed'] is True and closed['formal_case_accepted_delta']==0 and closed['formal_acceptance'] is False and closed['parent_acceptance'] is False)
        check('current formal count0 ParentW09 false preserved',cp['work_in_progress']['formal_cases_current']==0 and cp['current_effective_formal_status']['formal_cases_accepted']==0 and cp['current_effective_formal_status']['accepted_case_ids']==[] and not any(str(x).startswith('W09') for x in cp['parent_tasks_accepted']))
        for ref in resolved:
            check('all-input final held pin '+ref['path'],pin(ref['path'])==ref)
        for cap in (rootcap,sealcap):
            with cap['audit'].open('rb') as file:
                for offset,raw in cap['rows']:
                    file.seek(offset)
                    check('actual audit preserved exact byte range',file.read(len(raw))==raw)
        check('current Canon unchanged by independent review',[pin(x['path']) for x in current]==current)
    finally:
        cleanup=held.close()
        cleanup_ref=save('sourceguard.closed.json',cleanup)
    check('independent finite real reader guard released0',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
    findings=[x for x in checks if not x['passed']]
    controls=save('actual-checks.json',dict(checks=checks,count=len(checks),blocking_findings=findings,guard_ref_count=held_count,Source_entrypoints_executed=False,dispatcher_or_Native_or_model_executed=False))
    attribution=save('historical-canonical-attribution.json',dict(bindings=[dict(historical_logical_ref=r,physical_archive_ref=a,current_claim=False) for r,a in zip(old,archives)],Source_loaders_monkeypatched=False,current_refs=current))
    observations_ref=save('consumer-summary.json',dict(consumers=summaries,provenance='Full original Root host command and result, immutable Source bytes, actual owned process observations, dispatcher receipt and child stdout.',environment_evidence='Pinned caller explicit environment plus registry filtering and actual route mode/report consumption; no OS environment dump is claimed.',no_producer_or_outbound_evidence='Pinned C19 read-only branch excludes PRESERVED subprocess path and evidence closure has no outbound calls; no OS network trace is claimed.'))
    status='ACTUAL_MAIN_C19_TWO_CONSUMERS_COMPONENT_FIXTURE_VERIFIED' if not findings else 'REQUEST_CHANGES'
    decision=save('actual-decision.json',dict(schema='researchos.w09-c19-two-consumer-independent-actual-decision.v1',decision=status,actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',reviewed_at=datetime.now(timezone.utc).isoformat(),root_request_ref=request_ref,source_hdf_ref=request['source_hdf_ref'],source_mf_ref=sh['manifest_ref'],caller_source_ref=sh['caller_source_ref'],source_review_ref=request['source_review_ref'],root_actual_io_ref=bio_ref,actual_host_capture_ref=rootcap['cap_ref'],actual_host_binding_ref=rootcap['binding_ref'],registration_independent_review_refs=proof['actual_registration_independent_review_refs'],caller_closed_ref=closed_ref,consumer_summary_ref=observations_ref,current_canonical_refs=current,checks_ref=controls,source_guard_ref=cleanup_ref,historical_attribution_ref=attribution,actual_two_consumers_verified=not findings,qualification='COMPONENT_AND_FIXTURE_ONLY',CURRENT_formal_cases_accepted=0,formal_case_accepted_delta=0,FormalCaseAccepted=False,ParentW09=False,WholeGoalDONE=False,full_G01='OPEN',full_G02='OPEN',full_A06='OPEN',Root_formal_capture_index='OPEN',Native_rerun_by_reviewer=False,dispatcher_rerun_by_reviewer=False,Main_Canon_written_by_reviewer=False,new_original_diagnostics=[dict(ordinal=1005,chunk_id='a7cd3a',classification='INDEPENDENT_REVIEW_READ_SCHEMA_KEYERROR',actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_capture_ref=failure_refs[0],actual_binding_ref=failure_refs[1],counted_once=True,consumer_failure=False)],Root_next_original=1006,blocking_findings=findings))
    mf=save('MF.json',dict(schema='researchos.w09-c19-two-consumer-independent-actual-manifest.v1',members=[pin(__file__),decision,controls,cleanup_ref,attribution,observations_ref,*failure_refs,*[cap[k] for cap in (rootcap,sealcap) for k in ('cap_ref','binding_ref')]],root_request_ref=request_ref,current_canonical_refs=current))
    hdf=save('HDF.json',dict(schema='researchos.w09-c19-two-consumer-independent-actual-handoff.v1',decision=status,actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=mf,actual_decision_ref=decision,root_request_ref=request_ref,consumer_summary_ref=observations_ref,source_guard_ref=cleanup_ref,source_guard_ref_count=held_count,source_guard_closed=True,retained_handles_count=0,checks=len(checks),blocking_findings_count=len(findings),CURRENT_formal_cases_accepted=0,FormalCaseAccepted=False,ParentW09=False,WholeGoalDONE=False,qualification='COMPONENT_AND_FIXTURE_ONLY',full_G01_G02_A06_and_Root_formal_capture_index='OPEN',STOP=True,FINAL=True))
    for ref in (hdf,mf,decision):
        assert pin(ref['path'])==ref
    print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,status=status,checks=len(checks),guard_refs=held_count,blocking_findings=findings),ensure_ascii=False))

if __name__=='__main__':
    main()
