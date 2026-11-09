from pathlib import Path
import copy,datetime,hashlib,json,re,types,sqlite3,_sqlite3
R=Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
A2=B/'public22_to_main23_continuation_actual_independent_review_codex/actual-20261010-02'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
inv=json.loads((D/'actual-shape-inventory.json').read_bytes());exp=json.loads((D/'actual-expansion.json').read_bytes())
bundle=json.loads((S/'w05.gen02.seven-actual-input.root.json').read_bytes())
facts=inv['facts'];actual=inv['actual_request'];activation=inv['registration_result']
q=exp['registration']['request_ref'];scope=exp['registration']['scope_ref'];owner=exp['registration']['owner_ref'];worker=exp['registration']['worker_ref']
i=json.loads((N/'source-inputs.json').read_bytes());case=json.loads(Path(bundle['case_closed_ref']['path']).read_bytes())
prior_state=json.loads(Path(i['evidence']['returned_state_ref']['path']).read_bytes())
root=Path(scope['receipt_root']);reg=Path(q['registration_root']);journal=Path(activation['transaction']['transaction_journal'])
refs=[s.pin(__file__),s.pin(HELPER),s.GREF,s.pin(D/'actual-shape-inventory.json'),s.pin(D/'actual-expansion.json'),
    s.pin(S/'w05.gen02.seven-actual-input.root.json'),*bundle.values(),s.pin(A2/'actual-input-contract.json'),
    s.pin(N/'public22_to23_root.source.py'),s.pin(N/'HDF.json'),s.pin(N/'MF.json'),s.pin(N/'source-inputs.json'),
    s.pin(N/'root-calling-contract.source.json'),*[facts[k] for k in ('request_ref','scope_ref','owner_ref','worker_ref')],
    *facts['before_archive_refs'],*actual['current_canonical_refs'],s.pin(journal/'committed.json'),
    *[s.pin(reg/name) for name in ('0.after.proposed.json','1.after.proposed.json','build.guard.closed.json','check.guard.closed.json','activate.guard.closed.json')],
    i['leaf_runner_ref'],i['leaf_contract_ref'],i['main23_bound_ref'],i['main23_program_ref'],i['main_recovery_source_ref'],
    i['case_request_ref'],i['existing22_decision_ref'],i['evidence']['returned_state_ref'],i['evidence']['backup_manifest_ref'],
    q['review_decision_ref'],q['review_audit_ref'],q['postreview_live_audit_ref'],i['runtime_resources_ref'],i['generation_predecessor_ref'],
    prior_state['baseline_manifest_ref']]
for host in (inv['preentry'],inv['initial_host'],inv['completed_host']):refs.append(host['original_capture_ref'])
for call in case['calls']:
    refs.extend(call[k] for k in ('before_ref','stdout_ref','stderr_ref','result_ref'))
for name in ('working_copy_before_ref','upgrade_manifest_ref','upgrade_report_ref','backup23_manifest_ref','restore23_report_ref'):refs.append(case[name])
for name,value in case['observations'].items():
    if name!='working22_schema_compatibility':refs.append(value['database_ref'])
runtime_manifest=json.loads(Path(i['runtime_resources_ref']['path']).read_bytes())
sqlite_module_paths={Path(p).resolve(strict=True) for module in (sqlite3,sqlite3.dbapi2,_sqlite3)
    for p in (getattr(module,'__file__',None),getattr(module,'__cached__',None)) if p and Path(p).is_file()}
sqlite_resource_refs=[ref for ref in runtime_manifest['resource_refs'] if Path(ref['path']).resolve(strict=True) in sqlite_module_paths
    or Path(ref['path']).name.lower()=='sqlite3.dll']
refs.extend(sqlite_resource_refs)
unique={}
for ref in refs:
    identity=str(Path(ref['path']).resolve(strict=True))
    normalized=dict(path=str(Path(ref['path'])),sha256=ref['sha256'],bytes=ref['bytes'])
    assert identity not in unique or all(unique[identity][key]==normalized[key] for key in ('sha256','bytes'))
    unique[identity]=normalized
refs=list(unique.values())
g=s.guard();checks=[];failure=None;summary={};closed_time=None
def read(ref):return g.get_buffer(str(Path(ref['path'])))
def doc(ref):return caller.strict(read(ref))
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
    if not value:raise ValueError(name)
def call_check(name,func,detail=None):
    value=func();check(name,value is not False,detail);return value
def guard_closed(value):
    return value.get('closed') is True and value.get('retained_handles_count')==0 and value.get('errors')==[]
try:
    g.acquire(refs)
    caller=s.inert(N/'public22_to23_root.source.py',g.get_buffer(str(N/'public22_to23_root.source.py')))
    leaf=s.inert(i['leaf_runner_ref']['path'],read(i['leaf_runner_ref']))
    contract=doc(i['leaf_contract_ref']);bound=doc(i['main23_bound_ref']);case=doc(bundle['case_closed_ref'])
    accepted_review=doc(q['review_decision_ref']);prior=doc(i['evidence']['returned_state_ref'])
    case_request=doc(i['case_request_ref']);old_manifest=doc(i['evidence']['backup_manifest_ref'])
    check('new_GEN02_Source04_exact_accepted_bindings_and_component_scope',
        q['source_hdf_ref']==s.pin(N/'HDF.json') and q['source_mf_ref']==s.pin(N/'MF.json')
        and accepted_review['decision']=='ACCEPTED_SOURCE_ONLY'
        and accepted_review['caller_ref']==s.pin(N/'public22_to23_root.source.py')
        and q['case_request_ref']==actual['case_request_ref']==i['case_request_ref']
        and q['evidence']==scope['evidence']==i['evidence'] and scope['phases']==['upgrade22to23','backup23','verify23']
        and scope['maximum_new_native_children']==3 and owner['slice_id']==worker['slice_id']==caller.SLICE)
    live_scope,live_facts,live_request,current=caller.live(actual)
    check('actual_Root_registered_current4_owner_worker_lease_live_exact',
        live_scope==scope and live_facts==facts and live_request==q
        and current['documents'][0]['revision']==391 and current['documents'][1]['revision']==195,
        dict(current_refs=current['refs'],observed_revisions=[391,195,None,40],
            lease_expires_at=scope['lease_expires_at'],reviewed_live_utc=caller.utc() if hasattr(caller,'utc') else datetime.datetime.now(datetime.timezone.utc).isoformat()))
    before_raw=[read(ref) for ref in facts['before_archive_refs']]
    check('complete_original_four_archives_identity_SHA_bytes_and_SS_CM',
        len(before_raw)==4 and all(hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes']
            for raw,ref in zip(before_raw,q['before_canonical_refs']))
        and current['refs'][2:]==q['before_canonical_refs'][2:])
    cp0,ow0=[caller.strict(raw) for raw in before_raw[:2]]
    after=caller.projection(cp0,ow0,facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],bundle['registration_facts_ref'],owner,worker,q['created_utc'])
    check('exact_Source04_projection_full_inverse_failure_counters_and_next_preserved',
        all(caller.encoded(value)==raw for value,raw in zip(after,current['raw'][:2]))
        and all(caller.encoded(value)==g.get_buffer(str(reg/f'{index}.after.proposed.json')) for index,value in enumerate(after))
        and after[0]['failure_counters']==cp0['failure_counters']
        and after[0]['work_in_progress'].get('root_next_failure_ordinal_live')==cp0['work_in_progress'].get('root_next_failure_ordinal_live'))
    committed=caller.strict(g.get_buffer(str(journal/'committed.json')))
    check('actual_activation_TP_committed_exclusive_pair_exact_after_refs',
        activation['mode']=='activate' and activation['scope_ref']==facts['scope_ref']
        and activation['facts_ref']==bundle['registration_facts_ref']
        and activation['complete_inverse'] is True and activation['SS_CM_unchanged'] is True
        and journal.parent==reg and committed['both_verified_while_exclusively_held'] is True
        and committed['written_indices']==[0,1] and all(caller.same(a,b) for a,b in zip(committed['after_refs'],current['refs'][:2])))
    registration_guards=[caller.strict(g.get_buffer(str(reg/name))) for name in ('build.guard.closed.json','check.guard.closed.json','activate.guard.closed.json')]
    cleanup=case['source_guard_cleanup']
    check('all_actual_registration_and_execute_Source_guards_closed_verified_zero',
        all(guard_closed(v) and v['verification']=='PASSED' and all(e['verified'] is True and e['closed'] is True for e in v['entries'])
            for v in [*registration_guards,cleanup]),
        dict(registration_held_counts=[len(v['entries']) for v in registration_guards],execute_held_count=len(cleanup['entries']),
            accepted_old_runtime_149_and_public144_replayed=False))
    observed_entry_refs=[{k:e[k] for k in ('path','sha256','bytes')} for e in cleanup['entries']]
    needed=[s.pin(N/'public22_to23_root.source.py'),q['source_hdf_ref'],q['source_mf_ref'],q['review_decision_ref'],
        i['main23_program_ref'],i['leaf_runner_ref'],i['runtime_resources_ref'],bundle['actual_request_ref'],facts['scope_ref']]
    check('actual_execute_guard_binds_current_Caller_qualified_Main23_and_reused_runtime',
        all(any(caller.same(a,b) for b in observed_entry_refs) for a in needed)
        and bound['program_ref']==i['main23_program_ref'] and bound['status']=='QUALIFIED_CURRENT_MAIN23_BUILD'
        and bound['independent_non_author'] is True and bound['execution_grant'] is False
        and bound['program_ref']!=contract['main23_candidate_only'],dict(program_ref=bound['program_ref'],runtime_qualification_reissued=False))
    pre=caller.audit(bundle['execute_preentry_audit_ref'],caller.ROOT,
        [bundle['actual_request_ref'],actual['registration_result_ref'],actual['scope_ref'],*actual['current_canonical_refs']])
    init=caller.audit(bundle['execute_initial_host_capture_ref'],caller.ROOT,[])
    complete=caller.audit(bundle['execute_completed_host_capture_ref'],caller.ROOT,[])
    first_values=[v for v in s.docs(init['result']['payload']['output']) if v.get('chunk_id')=='7fd876']
    last_values=[v for v in s.docs(complete['result']['payload']['output']) if v.get('chunk_id')=='afddbe']
    check('real_Root_header_offsets_call_result_pairs_preentry_and_session_completion',
        len(first_values)==len(last_values)==1 and first_values[0].get('session_id')==24494
        and first_values[0].get('exit_code') is None and last_values[0]['exit_code']==0
        and 'ROOT_ACTUAL_PYTHON_EXIT=0' in last_values[0]['output']
        and pre['result_time']>=caller.when(q['created_utc'])
        and caller.when(init['call']['timestamp'])>pre['result_time']
        and complete['result_time']>=init['result_time'])
    input_code=init['call']['payload']['input'];completion_code=complete['call']['payload']['input']
    check('actual_Root_Source04_execute_command_template_seven_exact_bound_arguments',
        'load("W05_source04_registration_request").caller_ref' in input_code
        and "-I -S -B -X utf8 '${source.path}' execute '${q.path}' ${q.sha256} ${q.bytes} '${fr.path}' ${fr.sha256} ${fr.bytes}" in input_code
        and 'W05_gen02_actual_request_ref' in input_code and 'W05_gen02_preentry_ref' in input_code
        and '24494' in completion_code,
        dict(command_is_actual_original_template=True,resolved_dynamic_refs_bound_by_request_Scope_and_actual_guard=True,
            concrete_cli_ref_arguments=[bundle['actual_request_ref'],bundle['execute_preentry_audit_ref']]))
    last=last_values[0]
    check('immutable_complete_case_primary_external_stdout_truncation_preserved',
        case['schema']=='researchos.public22-to-main23-continuation-return.v1'
        and case['actual_request_ref']==bundle['actual_request_ref']
        and case['status']=='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW'
        and case['closed_receipt_ref'] is None and case['first_failure'] is None and case['secondary_errors']==[]
        and case['new_native_children_attempted']==3 and [c['phase'] for c in case['calls']]==scope['phases'],
        dict(external_original_token_count=last.get('original_token_count'),complete_returned_state_available=False,
            returned_state_reconstructed=False,primary_case_ref=bundle['case_closed_ref']))
    projection=caller.continuation_projection(contract,case_request,scope['receipt_root'],bound['program_ref'],leaf)
    paths=projection['paths'];wanted_env=leaf._environment(paths);wanted_env['RESEARCHOS_DATA_DIR']=paths['work22']
    ft=[]
    for phase,call in zip(projection['phases'],case['calls']):
        name=phase['id'];before=doc(call['before_ref']);result=doc(call['result_ref'])
        check(name+'_actual_argv_environment_before_and_result_exact',
            call['argv']==phase['argv'] and call['cwd']==phase['cwd'] and call['env']==wanted_env
            and call['timeout_seconds']==90 and call['native_child_kind']=='public_go_program'
            and before['observation'] is None and before['actual_exit'] is None
            and all(before[k]==call[k] for k in ('phase','argv','cwd','env','timeout_seconds','started_at_unix_ns','native_child_kind'))
            and result=={k:v for k,v in call.items() if k!='result_ref'},dict(argv=call['argv'],cwd=call['cwd'],program_ref=bound['program_ref']))
        leaf.closed_job(call['observation'])
        creation=call['observation']['creation_time_100ns']
        check(name+'_actual_exit_uint64_FILETIME_and_exclusive_OwnedJob_closed',
            type(call['actual_exit']) is int and call['actual_exit']==0
            and type(creation) is int and 0<creation<2**64 and call['creation_time_100ns_decimal']==str(creation)
            and type(call['started_at_unix_ns']) is int and type(call['ended_at_unix_ns']) is int
            and call['started_at_unix_ns']<=((creation-116444736000000000)*100)<=call['ended_at_unix_ns']
            and call.get('output_close_errors',[])==[],dict(creation_time_100ns_decimal=str(creation),owned_child_pid=call['observation']['owned_child_pid']))
        ft.append(str(creation))
        stdout=read(call['stdout_ref']);stderr=read(call['stderr_ref'])
        check(name+'_complete_raw_output_caps_empty_stderr_and_persisted_native_report',
            len(stdout)<=4*1024*1024 and len(stderr)<=4*1024*1024 and len(stderr)==0
            and leaf.same_json(caller.strict(stdout),doc(case[{'upgrade22to23':'upgrade_report_ref','backup23':'backup23_manifest_ref','verify23':'restore23_report_ref'}[name]])),
            dict(stdout_ref=call['stdout_ref'],stderr_ref=call['stderr_ref'],result_ref=call['result_ref']))
    observations=case['observations'];working=observations['working22_input'];up=observations['upgrade23'];backup=observations['backup23_source'];restored=observations['restored23']
    leaf.validate_ledger(working,22)
    compat=caller.validate_working22(leaf,working,prior['observations']['sealed22'],old_manifest)
    check('byte_identical_working22_all_83_table_hashes_dual_schema_and_ledger22',
        compat==observations['working22_schema_compatibility']
        and all(case['working_copy_before_ref'][k]==i['evidence']['source_db_ref'][k] for k in ('sha256','bytes')),
        dict(tables=len(working['tables']),database_ref=working['database_ref'],logical_observation_source='actual sealed immutable Root observation; no new SQL query'))
    call_check('upgrade22to23_ledger23_three_empty_additions_revocation_and_program_schema_plan',
        lambda:caller.validate_upgrade23(leaf,working,up,doc(case['upgrade_report_ref']),doc(case['upgrade_manifest_ref']),contract,bound['program_ref']))
    expected_fence=leaf.expected_restore_trigger_sql(read(i['main_recovery_source_ref']).decode())
    check('exact_Main23_restore_fence_only_expected_trigger_on_domain_objects',
        [row for row in up['schema_rows'] if row[:2]==['trigger','backup_require_fresh_observation']]
        ==[['trigger','backup_require_fresh_observation','domain_objects',expected_fence]])
    call_check('backup23_preserves_all_tables_schema_and_ledger23_manifest',lambda:caller.validate_backup23(leaf,up,backup,doc(case['backup23_manifest_ref'])))
    call_check('verify23_all_table_hashes_existing_fence_schema_revoked_credentials_report_inventory',
        lambda:caller.validate_restore23(leaf,backup,restored,doc(case['backup23_manifest_ref']),doc(case['restore23_report_ref'])))
    db_refs=[v['database_ref'] for v in (working,up,backup,restored)]
    for ref in db_refs:leaf.quiescent_database(ref['path'])
    observed_again={}
    for name,value in [('working22_input',working),('upgrade23',up),('backup23_source',backup),('restored23',restored)]:
        identity=str(Path(value['database_ref']['path']).resolve(strict=True))
        if identity not in observed_again:observed_again[identity]=leaf.readonly_database_observation(value['database_ref']['path'])
        check(name+'_independent_existing_Leaf_readonly_database_oracle_all_fields_exact',observed_again[identity]==value,
            dict(tables=len(value['tables']),schema_rows=len(value['schema_rows']),ledger=value['versions'],
                public_rows_emitted=False,mode='ro/immutable/query_only',product_SQL_process_exit=None))
    check('new_public_database_byte_pins_quiescent_and_no_private_material_read',
        all(s.pin(ref['path'])==ref for ref in db_refs)
        and case['recoverability']['key_bytes_read_by_caller'] is False
        and case['recoverability']['opaque_key_path']==paths['key'] and Path(paths['key']).is_file(),
        dict(public_database_refs=db_refs,readonly_SQLite_oracle_connections=len(observed_again),
            product_SQL_processes=0,product_SQL_exit=None,private_key_and_owner_read_hash_copy=False))
    check('original1025_and1201_preserved_old_four_children_not_replayed_full20to24_OPEN',
        case['original1025_result']=='FAILED_RETAINED' and case['original_four_children_replayed'] is False
        and case['automatic_retry'] is False and case['full20to24']=='OPEN'
        and case['formal_acceptance'] is False and case['parent_acceptance'] is False and case['formal_case_accepted_delta']==0
        and case['original_baseline_refs']==doc(prior['baseline_manifest_ref'])['references']
        and caller.PREDECESSOR['actual_failed_case_ref']!=bundle['case_closed_ref'],
        dict(original1201_closed_no_native_predecessor_verified_by_Source_projection=True,new_child_count=3,old_child_count=0))
    caller.live(actual)
    summary=dict(scope_ref=facts['scope_ref'],source_refs=[q['source_hdf_ref'],q['source_mf_ref'],s.pin(N/'public22_to23_root.source.py'),s.pin(N/'root-calling-contract.source.json')],
        current_refs=current['refs'],Root_actor=caller.ROOT,Source_author=caller.AUTHOR,review_actor=s.ACTOR,
        raw_FILETIME_decimal=ft,new_child_exits=[c['actual_exit'] for c in case['calls']],Root_outer_exit=last['exit_code'],Root_Python_exit=0,
        actual_Source_guard_entries=len(cleanup['entries']),old_four_replayed=False,all_Jobs_closed=True,
        database_oracles='Actual immutable observations checked with the accepted Source pure validators and independently reread by the existing Leaf ro/immutable/query-only oracle; public database bytes pinned, no product SQL process.',
        readonly_SQLite_oracle_connections=len(observed_again),
        external_stdout_truncated=True,returned_state_reconstructed=False,complete_case_ref=bundle['case_closed_ref'],
        original1025='FAILED_RETAINED',original1201='FAILED_RETAINED_NO_NATIVE',full20to24='OPEN',
        formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,
        new_review_Native_Go_SQL_TP_RootStage_model_calls=0)
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    cleanup_ref=s.write('actual-review-guard.closed.json',g.close())
    result_ref=s.write('actual-review-checks.json',dict(schema='researchos.public22-gen02-actual-independent-checks.v1',
        checks=checks,count=len(checks),passed=sum(v['passed'] for v in checks),failure=failure,held_ref_count=len(refs),
        held_refs=refs,Source_guard_ref=cleanup_ref,summary=summary,old_successful_controls_replayed=False,
        Source_only_review_of_actual_component=True,actual_review_product_calls=0,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(result_ref=result_ref,checks=len(checks),passed=sum(v['passed'] for v in checks),
    cleanup_ref=cleanup_ref,summary=summary,HDF_MF_decision_sealed=False),ensure_ascii=False))
