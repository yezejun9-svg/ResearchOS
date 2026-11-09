from pathlib import Path
import ast,hashlib,json
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';N=Path(__file__).parent
OLD=B/'public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
source=(OLD/'public22_recheck_root.source.py').read_text(encoding='utf-8')
assert hashlib.sha256((OLD/'public22_recheck_root.source.py').read_bytes()).hexdigest()=='c26422a3d9b6153ed4a985568a853d3e7a08f880f0daeb17d74f61a10f264d5f'
# Keep the reviewed registration and audit machinery; replace only its scope.
source=source[:source.index('\nclass ExistingObservationScope:')]
source=source.replace('Import is inert. This caller cannot launch a product child or alter the old case.','Import is inert. Future Root execution permits exactly three new public children.')
source=source.replace("import types","import types\nimport time")
source=source.replace("AUTHOR='codex:/root/native_temp_independent_review'","AUTHOR='codex:/root/attach_restore_independent_review'")
for old,new in [
 ('public22_existing_observation_original1025','public22_to_main23_continuation'),
 ('PUBLIC22_EXISTING_OBSERVATION_ORIGINAL1025','PUBLIC22_TO_MAIN23_CONTINUATION'),
 ('ROOT_REGISTERED_READONLY_EXISTING_PUBLIC22','ROOT_REGISTERED_PUBLIC22_TO_MAIN23_CONTINUATION'),
 ('READONLY_EXISTING_PUBLIC22_ORIGINAL1025','PUBLIC22_TO_MAIN23_CONTINUATION_ONLY'),
 ('public22-existing','public22-continuation'),
 ('public22_existing_observation','public22_continuation'),
 ('public22-recheck-registration-','public22-continuation-registration-'),
 ('public22-recheck-observation-','public22-continuation-'),
 ('recheck_id','continuation_id'),
 ("decision['readonly_only'] is True","decision['continuation_only'] is True and decision['runtime_closure_reviewed'] is True"),
 ('new_native_children=0','maximum_new_native_children=3'),
 ("a.get('source_audit_path')==ROOT_AUDIT","canonical(a.get('source_audit_path'))==canonical(ROOT_AUDIT)")
]:source=source.replace(old,new)
# Our Source review must bind the independent reusable programme and prior component too.
source=source.replace("'calling_contract_ref':source['calling_contract_ref'],'runtime_resources_ref':i['runtime_resources_ref']",
 "'calling_contract_ref':source['calling_contract_ref'],'runtime_resources_ref':i['runtime_resources_ref'],'main23_bound_ref':i['main23_bound_ref'],'existing22_decision_ref':i['existing22_decision_ref']")
source=source.replace("refs+=leaf_audit['refs']+own_audit['refs']+i['source_resource_refs']",
 "refs+=leaf_audit['refs']+own_audit['refs']+i['source_resource_refs']+reuse_chain(q,i)")
source=source.replace("lease_expires_at=q['lease_expires_at'],maximum_new_native_children=3,",
 "lease_expires_at=q['lease_expires_at'],main23_bound_ref=inputs()['main23_bound_ref'],existing22_decision_ref=inputs()['existing22_decision_ref'],phases=['upgrade22to23','backup23','verify23'],maximum_new_native_children=3,")
# Canonical keys and status only; exact inverse and all original failure counters remain enforced.
append = r'''
def reuse_chain(q,i):
    bound=doc(i['main23_bound_ref']);contract=doc(i['leaf_contract_ref'])
    need(bound['schema']=='researchos.root-current-main23-programme-qualification.v1'
        and bound['issued_by']==ROOT and bound['root_thread_id']==ROOT_THREAD
        and bound['status']=='QUALIFIED_CURRENT_MAIN23_BUILD'
        and bound['independent_non_author'] is True and bound['execution_grant'] is False
        and bound['source_refs']==contract['current_main_source_refs'],'EXACT_EXISTING_MAIN23_QUALIFICATION')
    need(bound['program_ref']!=contract['main23_candidate_only'] and bound['review_author'] not in (ROOT,bound['source_author']),'NO_UNREBOUND_CANDIDATE')
    need(bound['program_ref']==i['main23_program_ref'],'FIXED_MAIN23_BINARY')
    existing=doc(i['existing22_decision_ref'])
    need(existing['decision']=='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED'
        and existing['original1025_result']=='FAILED_RETAINED'
        and existing['readonly83_oracle_source_ref']==i['leaf_runner_ref']
        and existing['new_Native_children_by_reviewer']==0 and existing['formal_acceptance'] is False,'EXISTING22_COMPONENT_ONLY')
    expected=[i['existing22_hdf_ref'],i['existing22_mf_ref'],i['existing22_decision_ref']]
    prior_audit=audit(q['existing22_review_audit_ref'],existing['actor_id'],expected)
    programme_audit=audit(q['main23_review_audit_ref'],bound['review_author'],bound['review_refs'][:3])
    root_programme=audit(q['main23_root_binding_audit_ref'],ROOT,[i['main23_bound_ref']])
    refs=[i['main23_bound_ref'],bound['program_ref'],bound['qualification_ref'],bound['provenance_ref'],
        *bound['source_refs'],*bound['review_refs'],*expected,*prior_audit['refs'],*programme_audit['refs'],*root_programme['refs']]
    for ref in refs:checked(ref)
    return refs

def continuation_projection(contract,original_case,receipt_root,program,leaf):
    old=leaf.compile_case(contract,original_case)
    need(original_case['end_version']==22,'EXISTING22_ONLY')
    root=Path(receipt_root)
    paths=dict(old['paths'])
    for k,rel in {'root':'.','work22':'working22','workdb22':'working22/researchos.sqlite',
        'snapshot23':'upgrade22to23.snapshot','candidate23':'candidate23','db23':'candidate23/researchos.sqlite',
        'backup23':'backup23','verify23':'verified23','raw':'raw','tmp':'tmp'}.items():
        paths[k]=str(root if rel=='.' else root/rel)
    # Old original data/backup/key paths are never rewritten. No owner credential is read.
    phases=leaf.upgrade23_phases(contract,dict(paths=paths),program)
    need([p['id'] for p in phases]==['upgrade22to23','backup23','verify23'],'THREE_UNCOVERED_PHASES_ONLY')
    need(canonical(paths['workdb22'])!=canonical(paths['db22']),'ORIGINAL_NOT_UPGRADE_INPUT')
    return dict(paths=paths,phases=phases)

def record_observation(invocation,observed,ended,stdout_path,stderr_path,pinner):
    # Persist the returned native facts in memory before any fallible output hashing.
    invocation['observation']=observed
    invocation['actual_exit']=observed.get('actual_exit')
    invocation['ended_at_unix_ns']=ended
    invocation['creation_time_100ns_decimal']=str(observed['creation_time_100ns']) if type(observed.get('creation_time_100ns')) is int else None
    invocation['stdout_ref']=pinner(stdout_path)
    invocation['stderr_ref']=pinner(stderr_path)

def validate_upgrade23(leaf,sealed,target,report,snapshot,contract,program):
    leaf.validate_ledger(sealed,22);leaf.validate_ledger(target,23)
    new={'client_command_identities','host_model_configurations','host_model_config_heads'}
    need(set(target['tables'])==set(sealed['tables'])|new,'EXACT_THREE_ADDED_TABLES')
    need(all(target['tables'][k]==v for k,v in sealed['tables'].items() if k not in ('schema_migrations','auth_credentials')),'ALL_OLD_TABLE_STATE_PRESERVED')
    need(all(target['tables'][k]['count']==0 for k in new),'NEW_TABLES_EMPTY')
    need(target['credentials']['all_revoked_one'] is True
        and target['tables']['auth_credentials']['count']==sealed['tables']['auth_credentials']['count']
        and target['tables']['auth_credentials']['rows_sha256']==sealed['credentials']['expected_revoked_rows_sha256'],'EXACT_OWNER_CREDENTIAL_REVOCATION')
    plan=snapshot['purpose']['plan']
    need(plan['id']==contract['plan22to23'] and plan['source_versions']==list(range(1,23))
        and plan['target_versions']==list(range(1,24)),'EXACT_UPGRADE_PLAN')
    need(plan['program_hashes']==dict(source='sha256:'+contract['old22_control']['sha256'],target='sha256:'+program['sha256']),'NATIVE_PROGRAMME_HASH_BINDING')
    need(plan['source_schema_hash']=='sha256:'+sealed['schema_sha256']
        and plan['target_schema_with_restore_fence_hash']=='sha256:'+target['schema_sha256'],'NATIVE_SOURCE_TARGET_SCHEMA_BINDING')
    need(report['status']==leaf.RESTORED and report['backup_id']==snapshot['id']
        and report['before']==snapshot['inventory'],'UPGRADE_PUBLIC_RECEIPT_BINDING')
    return True

def validate_backup23(leaf,before,after,manifest):
    leaf.validate_ledger(after,23)
    need(after['tables']==before['tables'] and after['schema_rows']==before['schema_rows'],'BACKUP23_SOURCE_UNCHANGED')
    need(manifest['migrations']==list(range(1,24)) and manifest['schema_hash']=='sha256:'+after['schema_sha256'],'BACKUP23_SCHEMA_LEDGER')
    return True

def validate_restore23(leaf,before,after,manifest,report):
    leaf.validate_ledger(after,23)
    need(before['schema_rows']==after['schema_rows'] and before['schema_sha256']==after['schema_sha256'],'RESTORE23_EXACT_EXISTING_FENCE_SCHEMA')
    need(before['tables']==after['tables'] and after['credentials']['all_revoked_one'] is True,'RESTORE23_ALL_TABLE_HASHES')
    need(report['status']==leaf.RESTORED and report['backup_id']==manifest['id']
        and report['before']==report['after']==manifest['inventory']
        and report['recovery']['credentials']=='REVOKED_REPROVISION_LOCALLY','RESTORE23_PUBLIC_REPORT')
    return True

def execute(actual_ref):
    actual=doc(actual_ref)
    need(actual['schema']=='researchos.root-public22-continuation-actual-request.v1' and actual['issued_by']==ROOT
        and actual['formal_acceptance'] is False and actual['parent_acceptance'] is False,'ROOT_CONTINUATION_REQUEST')
    scope,facts,q,current=live(actual);source=source_chain(q);i=inputs();original=original_evidence(i)
    need(scope==scope_projection(q,facts['request_ref'],source,original),'EXACT_CONTINUATION_SCOPE')
    activation=doc(actual['registration_result_ref'])
    need(activation['mode']=='activate' and activation['facts_ref']==actual['facts_ref']
        and activation['scope_ref']==actual['scope_ref'] and activation['complete_inverse'] is True
        and activation['SS_CM_unchanged'] is True and activation['transaction'] is not None,'ACTUAL_ACTIVATION')
    journal=Path(activation['transaction']['transaction_journal'])
    need(journal.parent==Path(q['registration_root']),'EXACT_TP_JOURNAL')
    committed_ref=pin(journal/'committed.json');committed=doc(committed_ref)
    need(committed['both_verified_while_exclusively_held'] is True and committed['written_indices']==[0,1]
        and len(committed['after_refs'])==2 and all(same(a,b) for a,b in zip(committed['after_refs'],current['refs'][:2])),'ACTUAL_TP_CURRENT')
    witness=audit(actual['preentry_actual_root_binding_ref'],ROOT,
        [actual_ref,actual['registration_result_ref'],actual['scope_ref'],*actual['current_canonical_refs']])
    need(witness['result_time']>=when(q['created_utc']),'PREENTRY_AFTER_REGISTRATION')
    # preentry capture refers to this immutable actual_ref; it is supplied separately
    # via execute CLI rather than embedded in actual_ref (see execute_bound).
    root=Path(scope['receipt_root']);physical(root,True);need(not root.exists(),'FRESH_UNUSED_CONTINUATION_OUTPUT')
    leaf=load(i['leaf_runner_ref'],'accepted_public22_v3_pure_helpers')
    contract=doc(i['leaf_contract_ref']);bound=doc(i['main23_bound_ref'])
    projection=continuation_projection(contract,original['case'],str(root),bound['program_ref'],leaf);paths=projection['paths']
    runtime=runtime_refs(i);job=load(i['owned_job_ref'],'continuation_owned_job')
    refs=refs_unique(source['refs']+original['refs']+witness['refs']+runtime+[actual_ref,actual['facts_ref'],
        actual['scope_ref'],facts['request_ref'],facts['owner_ref'],facts['worker_ref'],actual['registration_result_ref'],
        committed_ref,*current['refs']])
    guard=load(GUARD_REF,'continuation_held_guard').SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024)
    state=dict(schema='researchos.public22-to-main23-continuation-return.v1',actual_request_ref=actual_ref,
        status='STARTED',phase='prepare',calls=[],observations={},first_failure=None,secondary_errors=[],
        new_native_children_attempted=0,original1025_result='FAILED_RETAINED',original_four_children_replayed=False,
        original_baseline_refs=original['baseline']['references'],full20to24='OPEN',formal_acceptance=False,
        parent_acceptance=False,formal_case_accepted_delta=0,automatic_retry=False,
        source_guard_cleanup=None,closed_receipt_ref=None,external_original_hostpair_required=True)
    created=False
    try:
        guard.acquire(refs);live(actual);root.mkdir();created=True
        for key in ('work22','raw','tmp'):Path(paths[key]).mkdir()
        # Read retained public observations. No second baseline SQL read; existing accepted oracle is reused.
        sealed=original['state']['observations']['sealed22']
        need(leaf.observed_ref(paths['db22'])==i['evidence']['source_db_ref'],'EXACT_RETAINED22_SOURCE')
        data=guard.get_buffer(paths['db22'])
        with Path(paths['workdb22']).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        need(pin(paths['workdb22'])['sha256']==i['evidence']['source_db_ref']['sha256'],'EXACT_WORKING_COPY')
        state['working_copy_before_ref']=pin(paths['workdb22'])
        # Only the public child opens this existing opaque key. Caller never reads, hashes, copies or logs key bytes.
        physical(paths['key']);need(Path(paths['key']).is_file(),'OPAQUE_RECOVERY_KEY_EXISTS')
        env=leaf._environment(paths);env['RESEARCHOS_DATA_DIR']=paths['work22']
        manifest23=None
        for phase in projection['phases']:
            state['phase']=phase['id'];live(actual)
            need([x['phase'] for x in state['calls']]==['upgrade22to23','backup23','verify23'][:len(state['calls'])],'MONOTONIC_PHASE_ORDER')
            for ref in refs:checked(ref)
            outpath=Path(paths['raw'])/(phase['id']+'.stdout');errpath=Path(paths['raw'])/(phase['id']+'.stderr')
            invocation=dict(phase=phase['id'],argv=phase['argv'],cwd=phase['cwd'],env=env,timeout_seconds=90,
                started_at_unix_ns=time.time_ns(),observation=None,actual_exit=None,native_child_kind='public_go_program')
            state['calls'].append(invocation)
            invocation['before_ref']=save(Path(paths['raw']),phase['id']+'.before.json',invocation)
            with outpath.open('xb') as out,errpath.open('xb') as err:
                state['new_native_children_attempted']+=1
                observed=job.run_owned(phase['argv'],phase['cwd'],env,out,err,90,creation_flags=0x08000000)
            record_observation(invocation,observed,time.time_ns(),outpath,errpath,pin)
            invocation['result_ref']=save(Path(paths['raw']),phase['id']+'.result.json',invocation)
            leaf.closed_job(observed)
            need(outpath.stat().st_size<=4*1024*1024 and errpath.stat().st_size<=4*1024*1024,'RAW_OUTPUT_CAP')
            emitted=strict(outpath.read_bytes())
            if phase['id']=='upgrade22to23':
                persisted=strict((Path(paths['candidate23'])/'restore-report.json').read_bytes());leaf.same_json(emitted,persisted)
                target=leaf.readonly_database_observation(paths['db23'])
                snapshot=strict((Path(paths['snapshot23'])/'manifest.json').read_bytes())
                validate_upgrade23(leaf,sealed,target,emitted,snapshot,contract,bound['program_ref'])
                state['observations']['upgrade23']=target
                state['upgrade_manifest_ref']=pin(Path(paths['snapshot23'])/'manifest.json')
                state['upgrade_report_ref']=pin(Path(paths['candidate23'])/'restore-report.json')
            elif phase['id']=='backup23':
                manifest23=strict((Path(paths['backup23'])/'manifest.json').read_bytes());leaf.same_json(emitted,manifest23)
                target=leaf.readonly_database_observation(paths['db23'])
                validate_backup23(leaf,state['observations']['upgrade23'],target,manifest23)
                state['observations']['backup23_source']=target;state['backup23_manifest_ref']=pin(Path(paths['backup23'])/'manifest.json')
            else:
                report=strict((Path(paths['verify23'])/'restore-report.json').read_bytes());leaf.same_json(emitted,report)
                target=leaf.readonly_database_observation(Path(paths['verify23'])/'state.sqlite')
                validate_restore23(leaf,state['observations']['backup23_source'],target,manifest23,report)
                state['observations']['restored23']=target;state['restore23_report_ref']=pin(Path(paths['verify23'])/'restore-report.json')
            live(actual)
        need(len(state['calls'])==3,'EXACT_THREE_COMPLETED_PHASES')
        for ref in refs:checked(ref)
        state['status']='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW'
    except BaseException as exc:
        state['status']='STOPPED_AT_FIRST_FAILURE'
        state['first_failure']=dict(phase=state['phase'],type=type(exc).__name__,message=str(exc),
            last_child_exit=state['calls'][-1]['actual_exit'] if state['calls'] else None,
            Root_assignment_required=True,original_ordinal=None)
    finally:
        try:
            state['source_guard_cleanup']=guard.close()
            c=state['source_guard_cleanup']
            need(c['closed'] is True and c['retained_handles_count']==0 and c['errors']==[],'ALL_HELD_HANDLES_CLOSED')
        except BaseException as exc:
            state['secondary_errors'].append(dict(phase='guard-close',error=repr(exc)))
            state['status']='STOPPED_GUARD_CLEANUP_UNCONFIRMED'
        state['publication']={k:Path(paths[k]).exists() for k in ('root','work22','snapshot23','candidate23','backup23','verify23')}
        state['recoverability']=dict(original22_retained=True,old_backup22_path=paths['backup22'],opaque_key_path=paths['key'],
            key_bytes_read_by_caller=False,new_registration_required=True,automatic_recovery=False)
        if created:
            try:state['closed_receipt_ref']=save(root,'case.closed.json',state)
            except BaseException as exc:
                state['secondary_errors'].append(dict(phase='closed-receipt-save',error=repr(exc)))
                state['status']='STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED'
    print(json.dumps(state,ensure_ascii=False),flush=True)
    return state

def execute_bound(actual_ref,preentry_ref):
    # Avoid a self-referential request/capture digest. Both immutable refs are CLI inputs.
    global live
    original_doc=doc
    actual=original_doc(actual_ref)
    need('preentry_actual_root_binding_ref' not in actual,'NO_SELF_REFERENTIAL_PREENTRY_REF')
    injected=dict(actual,preentry_actual_root_binding_ref=preentry_ref)
    # Local immutable request wrapper; never changes a source file or global document loader.
    return execute_core(actual_ref,injected)

'''
# Make execute accept a separately supplied preentry reference without monkeypatching or circular file refs.
append=append[:append.index('\ndef execute_bound(')]
append=append.replace('def execute(actual_ref):\n    actual=doc(actual_ref)',
 'def execute(actual_ref,preentry_ref):\n    actual=doc(actual_ref)')
append=append.replace("audit(actual['preentry_actual_root_binding_ref'],ROOT,","audit(preentry_ref,ROOT,")
append=append.replace("    # preentry capture refers to this immutable actual_ref; it is supplied separately\n    # via execute CLI rather than embedded in actual_ref (see execute_bound).\n","")
append += r'''
def main(args):
    need(len(args) in (4,7),'MODE_AND_EXACT_REF_ARGUMENTS')
    mode=args[0];ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]))
    if mode=='build':need(len(args)==4,'BUILD_ARGS');result=build(ref)
    elif mode=='check':need(len(args)==4,'CHECK_ARGS');result=registration('check',ref)
    elif mode=='activate':
        need(len(args)==7,'ACTIVATION_ARGS')
        result=registration('activate',ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
    elif mode=='execute':
        need(len(args)==7,'PREENTRY_CAPTURE_ARGUMENTS')
        result=execute(ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
        print(json.dumps(dict(mode=mode,result=result,formal_acceptance=False),ensure_ascii=False),flush=True)
        return 0 if result['status']=='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW' else 1
    else:raise ValueError('EXACT_FOUR_MODES_ONLY')
    print(json.dumps(dict(mode=mode,result_ref=result,formal_acceptance=False),ensure_ascii=False),flush=True)
    return 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
'''
source+=append
ast.parse(source)
with (N/'public22_to23_root.source.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
i=json.loads((OLD/'source-inputs.json').read_bytes());i['schema']='researchos.public22-continuation-source-inputs.v1'
i['reuse_registration_source_ref']=pin(OLD/'public22_recheck_root.source.py')
main=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/main23.programme.qualification.bound.actual.root.json'
bound=json.loads(main.read_bytes())
i['main23_bound_ref']=pin(main);i['main23_program_ref']=bound['program_ref']
p=B/'public22_existing_observation_actual_independent_review_codex/actual-20261010-01'
for key,filename in [('existing22_decision_ref','decision.json'),('existing22_hdf_ref','HDF.json'),('existing22_mf_ref','MF.json')]:i[key]=pin(p/filename)
i['runtime_resources_ref']=pin(OLD/'runtime-resources.complete.json')
# Add source material consumed by Main's release manifest and target restore-fence oracle.
i['source_resource_refs'] += [pin(R/'internal/domain/backup_recovery.go'),pin(R/'migrations/sqlite/0023_host_model_configuration.sql')]
save('source-inputs.json',i)
save('source-changes.json',dict(source_author='codex:/root/attach_restore_independent_review',
 reused_registration_source_ref=pin(OLD/'public22_recheck_root.source.py'),
 new_modes=['build','check','activate','execute'],new_native_phases=['upgrade22to23','backup23','verify23'],
 old4_native_replay=False,actual_Source_author_executions=0,private_owner_or_key_read_hash_copy=False,
 current4_dynamic_CAS=True,own_runtime_independent_review_required=True,
 original1025='FAILED_RETAINED',formal_acceptance=False,full20to24='OPEN'))
print(json.dumps(dict(caller_ref=pin(N/'public22_to23_root.source.py'),inputs_ref=pin(N/'source-inputs.json')),ensure_ascii=False))

