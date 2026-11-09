"""Functions inserted into the pinned C19 lifecycle; import performs no execution."""

def choice(selector):
    require(selector in ('W09-G01','W09-G02','A06','C19'),'FOUR_SELECTORS_ONLY')
    all_choices=decode((N/'source.choice.json').read_bytes())
    require(set(all_choices['selectors'])=={'W09-G01','W09-G02','A06','C19'},'EXACT_FOUR_CHOICES')
    return dict(all_choices['common'],**all_choices['selectors'][selector])

def exact_host_peer_author(actor):
    """Map a canonical Codex peer identity to its exact host message author."""
    require(type(actor) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',actor) is not None,'CANONICAL_PEER_ACTOR')
    return actor.removeprefix('codex:')

def actual_audit(ref,actor,binding):
    """Verify finite original Root audit records, not self-reported provenance."""
    a=decode(read_ref(ref))
    require(set(a)=={'schema','actor_id','Root_thread_id','source_audit_path','source_line_offsets',
                    'original_line_sha256','source_prefix_size_observed','original_capture_ref','binding_sha256'},'AUDIT_FIELDS')
    require(a['schema']=='researchos.w09-native-producer.actual-audit.v1' and a['actor_id']==actor
        and a['Root_thread_id']==ROOT_THREAD_ID and a['source_audit_path']==ROOT_AUDIT
        and a['binding_sha256']==binding,'AUDIT_FIXED_ROOT_ACTOR_BINDING')
    raw=read_ref(a['original_capture_ref']);lines=raw.splitlines(keepends=True)
    require(len(lines)==3 and all(line.endswith(b'\n') for line in lines),'THREE_ORIGINAL_AUDIT_RECORDS')
    head,call,result=[decode(line) for line in lines]
    require(head.get('type')=='session_meta' and head.get('ordinal')==0
        and head.get('payload',{}).get('id')==ROOT_THREAD_ID,'ROOT_AUDIT_SESSION')
    first,last=call.get('payload',{}),result.get('payload',{})
    require(type(call.get('ordinal')) is int and type(result.get('ordinal')) is int
        and 0<call['ordinal']<result['ordinal'],'AUDIT_ORDER')
    if actor==ROOT_ACTOR:
        require(call.get('type')==result.get('type')=='response_item'
            and first.get('type') in ('function_call','custom_tool_call')
            and last.get('type') in ('function_call_output','custom_tool_call_output')
            and type(first.get('call_id')) is str and bool(first['call_id'])
            and first['call_id']==last.get('call_id') and type(first.get('name')) is str,'ROOT_ACTUAL_TOOL_PAIR')
    else:
        host_author=exact_host_peer_author(actor)
        require(call.get('type')=='inter_agent_communication_metadata' and result.get('type')=='response_item'
            and result['ordinal']==call['ordinal']+1 and call.get('timestamp')==result.get('timestamp')
            and last.get('type')=='agent_message' and last.get('author')==host_author and last.get('recipient')=='/root'
            and result.get('metadata',{}).get('client_authored') is False
            and type(last.get('content')) is list and len(last['content'])==1
            and last['content'][0].get('type')=='input_text','ACTUAL_PEER_DELIVERY')
    require(binding in lines[1].decode('utf-8')+lines[2].decode('utf-8'),'AUDIT_ARTIFACT_BINDING')
    offsets=a['source_line_offsets'];hashes=a['original_line_sha256'];size=a['source_prefix_size_observed']
    require(type(offsets) is list and len(offsets)==3 and offsets==sorted(set(offsets))
        and all(type(v) is int and v>=0 for v in offsets) and offsets[0]==0
        and type(hashes) is list and len(hashes)==3 and type(size) is int and size>0,'AUDIT_RANGES')
    with Path(ROOT_AUDIT).open('rb') as stream:
        for offset,digest,line in zip(offsets,hashes,lines):
            require(offset+len(line)<=size and hashlib.sha256(line).hexdigest()==digest,'AUDIT_RANGE_DIGEST')
            stream.seek(offset);require(stream.read(len(line))==line,'ACTUAL_ROOT_AUDIT_BYTES')
    return [ref,a['original_capture_ref']]

def validate_authority(request_ref,c):
    from datetime import datetime, timezone
    q=decode(read_ref(request_ref))
    require(set(q)=={'schema','issued_by','selector','scope_ref','canonical_vector_ref','calling_contract_ref','scope_audit_ref'},'REQUEST_FIELDS')
    require(q['schema']=='researchos.root-w09-four-selector-native-request.v1' and q['issued_by']==ROOT_ACTOR
        and q['selector']==c['selector_key'] and Path(request_ref['path']).is_relative_to(W),'ROOT_REQUEST')
    sr=q['scope_ref'];scope=decode(read_ref(sr));contract_ref=pin(N/'root-calling-contract.json')
    require(q['calling_contract_ref']==contract_ref,'CURRENT_CALLING_CONTRACT')
    contract=decode(read_ref(contract_ref));require(set(scope)==set(contract['scope_required_fields']),'SCOPE_FIELDS')
    require(scope['schema']=='researchos.root-w09-four-selector-native-scope.v1'
        and scope['status']=='ROOT_AUTHORIZED_SINGLE_SELECTOR_NATIVE' and scope['issued_by']==scope['executor']==ROOT_ACTOR,'ROOT_SCOPE')
    require(all(scope[k] is False for k in BOOL_FALSE) and all(type(scope[k]) is int and scope[k]==0 for k in ZERO),'SCOPE_BOUNDARY')
    require(all(type(scope[k]) is int and scope[k]==v for k,v in {'maximum_go_test_runs':1,'maximum_go_list_runs':1,
        'list_timeout_seconds':240,'producer_timeout_seconds':420,'inner_Go_timeout_seconds':180}.items()),'FINITE_EXECUTION_BUDGET')
    href,mref,refs=package_refs()
    require(scope['source_handoff_ref']==href and scope['source_manifest_ref']==mref,'EXACT_SOURCE_PAIR')
    bound={key:pin(N/name) for key,name in contract['source_file_bindings'].items()}
    require(all(scope[k]==v for k,v in bound.items()),'EXACT_SOURCE_CALLERS')
    for key in ('selector_key','selector','mode','native_scope','packages','source_root','run_id','receipt_root','scratch_root',
                'output_root','selected_tests','expected_native_ids','source21','generation'):
        require(scope[key]==c[key],'EXACT_SCOPE_'+key)
    review,rr=pair(scope['source_review_handoff_ref'],scope['source_review_manifest_ref'])
    dr=scope['source_review_decision_ref'];decision=decode(read_ref(dr));actor=decision.get('actor_id')
    require(dr in rr and review['source_decision_ref']==dr and review['actor_id']==actor,'SOURCE_DECISION_MEMBER')
    require(decision['schema']=='researchos.w09-four-selector-producer-independent-source-decision.v1'
        and decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE'
        and decision['actor_role']=='INDEPENDENT_NON_AUTHOR' and type(actor) is str
        and actor.startswith('codex:/root/') and actor not in (AUTHOR,ROOT_ACTOR),'INDEPENDENT_SOURCE_DECISION')
    for key,want in dict(source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=contract_ref,**bound).items():
        require(decision[key]==want,'REVIEW_BINDING_'+key)
    all_choices=decode(read_ref(bound['choice_ref']))
    require(decision['selectors']==all_choices['selectors'] and decision['source21']==c['source21']
        and decision['actual_executed'] is False and type(decision['formal_case_accepted_delta']) is int
        and decision['formal_case_accepted_delta']==0,'SOURCE_REVIEW_BOUNDARY')
    audits=[]
    for ref,who,digest in ((scope['source_author_audit_ref'],AUTHOR,href['sha256']),
        (scope['source_review_audit_ref'],actor,dr['sha256']),(q['scope_audit_ref'],ROOT_ACTOR,sr['sha256'])):
        audits.extend(actual_audit(ref,who,digest))
    issued=datetime.fromisoformat(scope['lease_issued_at']);expires=datetime.fromisoformat(scope['lease_expires_at'])
    require(issued.tzinfo is not None and expires.tzinfo is not None and 0<(expires-issued).total_seconds()<=3600
        and issued<=datetime.now(timezone.utc)<expires and type(scope['lease_id']) is str
        and re.fullmatch('[0-9a-f]{32}',scope['lease_id']),'CURRENT_FINITE_LEASE')
    vr=q['canonical_vector_ref'];vector=decode(read_ref(vr))
    require(set(vector)=={'schema','checkpoint_revision','ownership_revision','refs'}
        and vector['schema']=='researchos.w09-four-selector-native-canonical-vector.v1'
        and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>371
        and type(vector['ownership_revision']) is int and vector['ownership_revision']>175,'POST_REVIEW_CANONICAL_VECTOR')
    require(len(vector['refs'])==4 and [r['path'] for r in vector['refs']]==[str(p) for p in CANON],'FOUR_ORDERED_CURRENT_CANONICAL')
    cp,ow,ss,commands=[decode(read_ref(r)) for r in vector['refs']]
    require(cp['revision']==vector['checkpoint_revision'] and ow['revision']==vector['ownership_revision']
        and cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['head']==c['expected_git_head'],'CURRENT_PROJECT_VECTOR')
    require(ow['active_integrator']['id']==ROOT_ACTOR and ow['shared_integrator']=='qoder-desktop:/root/platform_owner'
        and ow['card_path_bindings']['W09-99']['owner']==ROOT_ACTOR,'ROOT_CURRENT_ROLE')
    require(cp['work_in_progress']['w09_native_producer_scope_generations'][c['generation']][c['selector_key']]==sr,'CANONICAL_SCOPE_REGISTRATION')
    owner=dict(generation=c['generation'],owner=ROOT_ACTOR,current_source_writer=None,state='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE',scope_ref=sr,
        source_handoff_ref=href,source_manifest_ref=mref,source_review_handoff_ref=scope['source_review_handoff_ref'],
        source_review_manifest_ref=scope['source_review_manifest_ref'],source_root=str(R),selector=c['selector_key'],
        run_id=c['run_id'],receipt_root=c['receipt_root'],scratch_root=c['scratch_root'],output_root=c['output_root'],
        lease_id=scope['lease_id'],lease_issued_at=scope['lease_issued_at'],lease_expires_at=scope['lease_expires_at'],
        formal_case_accepted_delta=0,parent_acceptance=False)
    require(ow['card_path_bindings']['W09-99']['subtasks'][OWNER_KEY+'_'+c['selector_key']]==owner,'EXACT_REGISTERED_OWNER')
    worker=dict(generation=c['generation'],step_id='W09-99',slice_id=SLICE+'_'+c['selector_key'],owner=ROOT_ACTOR,state=owner['state'],scope_ref=sr,
        source_handoff_ref=href,source_review_handoff_ref=scope['source_review_handoff_ref'],run_id=c['run_id'],lease_id=scope['lease_id'])
    require([v for v in cp['workers'] if v.get('slice_id')==worker['slice_id']]==[worker],'UNIQUE_REGISTERED_WORKER')
    require(c['generation']=='fullw09-20261010-04' and c['source_root']==str(R) and re.fullmatch('[0-9a-f]{32}',c['run_id'])
        and c['output_root']==str(R/'execution/receipts/W09/retrieval'/('run-'+c['run_id']))
        and c['receipt_root']==str(N/('actual-'+c['selector_key']+'-'+c['run_id']))
        and c['scratch_root']==str(Path('C:/Users/yqyyds/AppData/Local/ResearchOS/w09-native-v4')/(c['selector_key']+'-'+c['run_id'])),'FIXED_PRIVATE_PATHS')
    for ref in c['source21']:read_ref(ref)
    return unique(refs+rr+audits+[request_ref,sr,contract_ref,dr,vr,*vector['refs'],*bound.values()]),scope,vector

def verify_directories(bp):
    for directory,names in bp['main_directory_inventory'].items():
        p=exact_path(directory)
        actual=sorted(child.name for child in p.iterdir() if child.is_file())
        require(actual==names,'MAIN_COMPILE_DIRECTORY_INVENTORY_DRIFT')

def read_inputs(c):
    bp=decode(read_ref(c['compiler_blueprint_ref']));verify_directories(bp)
    refs=[pin(N/'source.choice.json'),c['compiler_blueprint_ref'],c['guard_ref'],c['owned_job_ref'],c['toolchain_ref'],
        c['identity_ref'],c['spec_manifest_ref'],*c['tool_refs'].values(),*c['source21'],*bp['stable_input_refs']]
    require(bp['source_only'] is True and bp['actual_package_count'] is None
        and bp['required_packages']==['./adapters/retrieval','./internal/domain'] and set(c['packages']).issubset(bp['required_packages']) and len(bp['allowed_package_roster'])==len(set(bp['allowed_package_roster'])),'SOURCE_COMPILER_BLUEPRINT')
    lock=decode(read_ref(c['toolchain_ref']))
    for key,ref in c['tool_refs'].items():
        require(lock['tools'][key]['path']==ref['path'] and lock['tools'][key]['sha256']==ref['sha256'],'LOCKED_TOOL_'+key)
    require(pin(sys.executable)==c['tool_refs']['python'],'LOCKED_PYTHON_EXECUTION')
    require(decode(read_ref(c['identity_ref']))['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','IDENTITY')
    for mod in tuple(sys.modules.values()):
        for field in ('__file__','__cached__'):
            path=getattr(mod,field,None)
            if path and Path(path).is_file():refs.append(pin(Path(path).resolve()))
    return unique(refs),bp

def job_closed(result):
    if type(result) is not dict:return False
    cleanup=result.get('job_cleanup',{})
    return (type(result.get('owned_child_pid')) is int and 0<result['owned_child_pid']<=0xffffffff
        and type(result.get('creation_time_100ns')) is int and 0<result['creation_time_100ns']<=0xffffffffffffffff
        and type(cleanup.get('active_processes_last_observed')) is int and cleanup['active_processes_last_observed']==0
        and not cleanup.get('errors') and all(cleanup.get(k) is True for k in
        ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))

def validate_packet(c,packet):
    report_path=packet/'report.json';tool_path=packet/'native-tool-run.json'
    report=decode(report_path.read_bytes());tool=decode(tool_path.read_bytes())
    require(packet==Path(c['output_root']) and report['run_id']==c['run_id']==tool['run_id'],'FIXED_MAIN_NATIVE_RUN')
    require(report['version_manifest']['git_head']==c['expected_git_head'],'ACTUAL_HEAD')
    require(report['version_manifest']['source_sha256']=={Path(ref['path']).relative_to(R).as_posix():'sha256:'+ref['sha256'] for ref in c['source21']},'EXACT_SOURCE21')
    relative=report_path.relative_to(R).as_posix();source=dict(report);source['report_reference']=relative
    require(tool['report_ref']==relative and tool['report_sha256']==pin(report_path)['sha256'],'TOOL_SAME_REPORT')
    require(tool['schema']=='researchos.w09-native-producer-tool-run.v1' and tool['formal_acceptance']=='NOT_RUN','TOOL_SCHEMA')
    require(report['actual_invocation']==tool['actual_invocation']==[c['tool_refs']['go']['path'],*c['go_test_argv_suffix']],'EXACT_NATIVE_ARGV')
    require(report['task_id']=='W09' and report['check_id']==(c['selector']['check_id'] or None)
        and report['case_id']==(c['selector']['case_id'] or None) and report['scope']==c['native_scope'],'EXACT_ROUTE_MODE')
    require(tool['stdout_ref']==report['raw_evidence_references'][0] and tool['stderr_ref']==report['raw_evidence_references'][1]
        and tool['stdout_sha256']==pin(packet/'go-test.stdout.jsonl')['sha256']
        and tool['stderr_sha256']==pin(packet/'go-test.stderr.txt')['sha256'],'EXACT_ORIGINAL_STREAMS')
    require(type(tool['native_exit_code']) is int and tool['native_exit_code']==0 and type(report['exit_code']) is int
        and report['exit_code']==0 and report['timed_out'] is False and report['status']=='PASS','ACTUAL_NATIVE_PASS')
    require(report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING'
        and type(report['formal_case_accepted_delta']) is int and report['formal_case_accepted_delta']==0,'NATIVE_NOT_FORMAL')
    require(report['selected_tests']==c['selected_tests'] and sorted(report['assertion_ids'])==sorted(c['expected_native_ids']),'EXACT_SELECTED_TESTS_ASSERTIONS')
    closure=module(next(ref for ref in c['source21'] if ref['path']==str(R/'ops/ci/w09_evidence_closure.py')))
    closure.verify_native(R,source,report,c['expected_native_ids'],c['selected_tests'])
    owned=closure.verify_owned(R,source,report,c['selected_tests'],c['assertion_owner'])
    if c['selector_key'] in ('W09-G01','C19'):closure.verify_c19(owned)
    if c['selector_key'] in ('W09-G01','W09-G02','A06'):closure.verify_a06(owned)
    require(all(Path(rec['owned_export_ref']['path']).is_relative_to(packet/'owned') for rec in report['assertion_results']),'ABSOLUTE_ASSERTION_PINS')
    return dict(report_ref=pin(report_path),tool_run_ref=pin(tool_path),run_id=c['run_id'],source_root=str(R),
        selector=c['selector'],mode=c['mode'],native_ids=c['expected_native_ids'],native_test_exit=report['exit_code'],
        owned_members=len(owned['members']),mode_independent_review='NOT_RUN_REQUIRED',formal_acceptance=False)
