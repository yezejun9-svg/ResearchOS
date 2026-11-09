import ast,hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(name,raw):
    p=Q/name
    with p.open('xb')as f:f.write(raw)
    return pin(p)
def main():
    base=Q/'review_actual_nf5.v2.py';old=base.read_bytes()
    assert hashlib.sha256(old).hexdigest()=='960c47fb7179c48c8b93a2478b7629789613132020d60d803dde63d79c89d585'
    text=old.decode('utf-8');newline='\r\n'if '\r\n'in text else '\n'
    edits=[]
    def replace_once(before,after):
        nonlocal text
        before=before.replace('\n',newline);after=after.replace('\n',newline)
        assert text.count(before)==1,(before[:90],text.count(before))
        start=text.index(before);edits.append(dict(start=start,before=before,after=after));text=text[:start]+after+text[start+len(before):]
    replace_once('def root_run_pair(initial_ref,completed_ref,invocation_ref,c,request_ref):','def root_run_pair(initial_ref,completed_ref,invocation_ref,c,request_ref,expected_Root_exit=0):')
    replace_once("    require(type(last.get('exit_code'))is int and last['exit_code']==0\n        and'ROOT_ACTUAL_PYTHON_EXIT=0'in last['output'].splitlines(),'ACTUAL_ROOT_PYTHON_EXIT_ZERO')",
                 "    require(type(expected_Root_exit)is int and expected_Root_exit in(0,1)and type(last.get('exit_code'))is int\n        and last['exit_code']==expected_Root_exit and('ROOT_ACTUAL_PYTHON_EXIT='+str(expected_Root_exit))in last['output'].splitlines(),\n        'ACTUAL_ROOT_PYTHON_EXIT_EXACT')")
    replace_once("        summary=closed['summary'];report=add(summary['report_ref']);add(summary['tool_run_ref']);add(summary['compiler_inventory_ref'])",
                 "        summary=packet_artifacts(closed,c);report=add(summary['report_ref']);add(summary['tool_run_ref']);add(summary['compiler_inventory_ref'])")
    original_group=text[text.index('def review_group('):text.index('\ndef execute_review('.replace('\n',newline))]
    common=original_group[original_group.index('    jobs=[];require'):original_group.index('    captures=[')]
    helpers='''def packet_artifacts(closed,c):
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
__COMMON__
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

'''.replace('__COMMON__',common.rstrip('\r\n').replace('\r\n','\n'))
    insert='def collect_actual_refs(packet,choices):'
    replace_once(insert,helpers+insert)
    start=text.index('        result=dict(schema=');end=text.index("    except BaseException as exc:primary=exc",start)
    before=text[start:end]
    after='''        groups={}
        for name in('W09-G01','W09-G02','A06'):
            facts=review_group(packet['groups'][name],choices[name],closure,profile_raw,bp)
            closed=decode(read_ref(packet['groups'][name]['producer_closed_ref']));ready=decode(read_ref(packet['groups'][name]['prepare_ref']))
            facts.update(fact_status='ACTUAL_FACTS_CHECKED_PENDING_TRUE_FULL_MODE',qualified_for_main_formal_consumption=False,
                runtime_closure=reviewed_runtime_closure(closed,ready,choices[name],packet_artifacts(closed,choices[name]),bp),
                Root_outer_exit=0,Root_python_exit=0,producer_actual_exit=0)
            groups[name]=facts
            with(Q/('actual-group-'+name+'.unsealed.json')).open('xb')as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\\n').encode('utf-8'))
        groups['C19']=review_refused_c19(packet['groups']['C19'],choices['C19'],closure,profile_raw,bp)
        with(Q/'actual-group-C19.unsealed.json').open('xb')as f:f.write((json.dumps(groups['C19'],ensure_ascii=False,indent=2)+'\\n').encode('utf-8'))
        result=dict(schema='researchos.w09-nf5-four-actual-independent-qualification.v1',reviewer=ACTOR,producer=ROOT_ACTOR,
            source_author='codex:/root/attach_restore_independent_review',qualification='PARTIAL_ACTUAL_FACTS_THREE_CHECKED_C19_REFUSED',
            groups=groups,checked_groups=['W09-G01','W09-G02','A06'],refused_groups=['C19'],overall_qualified=False,
            mode_finalization='MODE_FINALIZATION_REQUIRES_TRUE_FULL_REVIEWER',final_Mode_issued=False,formal_acceptance=False,
            formal_case_accepted_delta=0,new_Native_runs=0,new_Go_runs=0,new_model_requests=0,Main_written=False,Canon_written=False)
'''
    replace_once(before.replace(newline,'\n'),after)
    ast.parse(text)
    restored=text
    for item in reversed(edits):
        assert restored[item['start']:item['start']+len(item['after'])]==item['after']
        restored=restored[:item['start']]+item['before']+restored[item['start']+len(item['after']):]
    assert restored.encode('utf-8')==old
    candidate=put('review_actual_nf5.v3.py',text.encode('utf-8'))
    inverse=put('partial-review-revision.inverse.json',(json.dumps(dict(schema='researchos.readonly-review-source-exact-inverse.v1',
        base_ref=pin(base),candidate_ref=candidate,edits=edits,exact_inverse_byte_equal=True,changes_only_readonly_review=True,
        prior_controls_rerun=False,product_executions=0,formal_acceptance=False),ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    contract=json.loads((Q/'input-contract.v3.json').read_text(encoding='utf-8'))
    contract['reviewer_program_ref']=candidate
    contract['future_argv'][6]=candidate['path']
    contract['status']='PREPARED_THREE_SUCCESS_AND_C19_ORIGINAL_REFUSAL_FACT_REVIEW'
    contract['actual_result_policy']={'three_success_groups':['W09-G01','W09-G02','A06'],'C19_original_Root_failure_ordinal':1156,
        'C19_Root_outer_exit':1,'C19_Root_python_exit':1,'C19_known_producer_exit':0,'C19_refusal':'EXACT_NATIVE_ARGV',
        'failed_summary':None,'failed_stage_artifacts':'PINNED_ORIGINAL_PACKET_AND_ORIGINAL_COMPILER_EXPORTS_LAUNCHER_PERMIT_GUARDS',
        'no_regex_equivalence_acceptance':True,'overall_qualified':False,'Mode_issued':False,'formal_case_accepted_delta':0}
    contract['previous_contract_ref']=pin(Q/'input-contract.v3.json');contract['inverse_ref']=inverse
    contract_ref=put('input-contract.v4.json',(json.dumps(contract,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status='READONLY_PARTIAL_REVIEW_PREPARED',program_ref=candidate,contract_ref=contract_ref,inverse_ref=inverse,
        original_source_retained=True,Native_runs=0,Go_runs=0,formal_acceptance=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
