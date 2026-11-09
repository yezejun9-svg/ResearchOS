import ast, datetime, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W09/W09-99'
Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
PR=B/'full_w09_nf6_independent_source_review_codex/review-20261010-01'
OLD=B/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
ACTOR='codex:/root/backup_regression_resources'
BACKEND='/root/backup_regression_resources'
AUTHOR='codex:/root/full_w09_source_review'

def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    ph=json.loads((P/'HDF.json').read_bytes())
    review=json.loads((PR/'decision.json').read_bytes())
    choice=json.loads(Path(ph['source_choice_ref']['path']).read_bytes())
    refs=[pin(P/'HDF.json'),pin(P/'MF.json'),ph['calling_contract_ref'],ph['source_choice_ref'],pin(PR/'HDF.json'),pin(PR/'MF.json'),pin(PR/'decision.json'),
          review['source_runtime_delta_qualification_ref'],pin(R/'execution/v2.4/formal_profile_w09.py'),pin(R/'ops/ci/retrieval.py'),pin(R/'ops/ci/w09_formal_router.py'),pin(R/'ops/ci/w09_evidence_closure.py'),
          pin(R/'internal/domain/retrieval_test.go'),pin(OLD/'input-contract.v8.json'),pin(OLD/'review_actual_nf5.v7.py')]
    guard_bytes=GUARD.read_bytes()
    if hashlib.sha256(guard_bytes).hexdigest()!='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85':raise ValueError('PINNED_SOURCE_GUARD')
    gm=types.ModuleType('nf6_actual_preparation_guard');gm.__file__=str(GUARD)
    exec(compile(guard_bytes,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=2*1024*1024,total_cap=8*1024*1024)
    primary=None;produced={}
    try:
        guard.acquire(refs)
        get=lambda path:guard.get_buffer(str(path))
        raw_profile=get(R/'execution/v2.4/formal_profile_w09.py')
        if hashlib.sha256(raw_profile).hexdigest()!='d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f':raise ValueError('CURRENT_MAIN_PROFILE_EXACT_SOURCE')
        if hashlib.sha256(get(R/'ops/ci/retrieval.py')).hexdigest()!='b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11':raise ValueError('CURRENT_MAIN_CASE_ORDER')
        tree=ast.parse(get(R/'ops/ci/w09_formal_router.py'))
        constants={}
        nodes=[n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'NATIVE','FORMAL','SOURCE_SCOPE','SELECTED'}]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pinned route constants only>','exec'),constants)
        routes=[]
        for route,native_ids in constants['NATIVE'].items():
            key=route[2] or route[3];part=choice['selectors'][key]
            if list(constants['SELECTED'][route])!=part['selected_tests'] or set(native_ids)!=set(part['expected_native_ids']):raise ValueError('CURRENT_SIX_ROUTE_ROSTER')
            routes.append(dict(route=list(route),selector_key=key,mode='LIVE_WINDOWS' if key=='W09-G02' else 'FIXTURE',native_scope=constants['SOURCE_SCOPE'][route],selected_tests=part['selected_tests'],expected_native_ids=list(native_ids),formal_ids=list(constants['FORMAL'][route]),run_id=part['run_id'],state='PENDING_ACTUAL_CLOSURE',mode_ref=None,independent_receipt_ref=None))
        if len(routes)!=6 or len({tuple(x['route']) for x in routes})!=6:raise ValueError('SIX_DISTINCT_ROUTES')
        selectors=list(choice['selectors'])
        if set(selectors)!={'W09-G01','W09-G02','A06','C19'}:raise ValueError('EXACT_FOUR_SELECTOR_KEYS')
        now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
        base=dict(actor_id=ACTOR,backend_actor=BACKEND,source_author_id=AUTHOR,executor='codex:/root',prepared_utc=now,
                  actual_review_executed=False,Mode_issued=False,formal_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,
                  Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None)
        contract=dict(base,schema='researchos.w09-nf6-actual-independent-review-calling-contract.v1',status='PREPARED_PENDING_FOUR_CLOSED_ROOT_GROUPS',
            input_schema='researchos.w09-nf6-four-actual-review-input.v1',input_exact_fields=['schema','source_review_ref','groups'],
            source_review_ref=pin(PR/'decision.json'),exact_group_keys=['W09-G01','W09-G02','A06','C19'],
            group_exact_fields=['prepare_ref','producer_closed_ref','prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'],
            ref_exact_fields=['path','sha256','bytes'],ref_types=dict(path='string verified physical regular file, repo-relative only normalized at guard boundary',sha256='bare lowercase 64hex',bytes='exact nonnegative int; bool forbidden'),
            future_actual_input_ref=None,Root_registration_observation=dict(revision=383,ownership_revision=187,status='ROOT_REPORTED_PENDING_CLOSED_INPUT_BINDING',O6='execution/v2.4/receipts/W09/W09-99/w09_nf6_root_registration_root/e38d72def3e1427cb9ef0b49dc130ba1'),
            Root_capture_schemas=['researchos.w09-native-producer.actual-audit.v1','researchos.root-native-actual-host-pair.v1'],
            Root_capture_binding='Immutable original three LF lines: Root header, actual call, returned output; exact offsets/hash/bytes/call_id/chunk and same yielded session to completion. Nullable initial exits remain null; completed exits match actual markers. No extra prepare observation artifact.',
            source_choice_assembly='dict(common, **selectors[key]); preserve all current Source21 refs and exact run IDs.',
            historical_current4_boundary='Each original request/vector plus runtime guard and original CP383/OW187 archive are reviewed for execution. Later closed Canon is separately reported and cannot invalidate or authorize earlier runs.',
            Scope_lease_binding='Exact request/scope/registered generation, owner and worker; actual invocation within finite lease; no borrowed old NF5/Main23/public scopes.',
            expected_routes=routes,
            all_four_required_for_overall_qualification=True,failed_group_policy='Report preserved failure/nullable actual exits and refuse only corresponding Mode; never turn incomplete or failed groups into QUALIFIED.',
            source_reuse=dict(prior_nf6_source_review_ref=pin(PR/'decision.json'),prior_source_runtime_delta_qualification_ref=review['source_runtime_delta_qualification_ref'],immutable_nf5_unchanged_source_controls_reused=True,old_successful_controls_rerun=False,old_source_control_counts_not_new_actual_results=True),
            required_actual_checks=['four original report, ToolRun, stdout/stderr and native exact rosters; C19 two tests/five IDs',
                'strict JSONL unique run/pass terminals and real report interval; no skip/fail/duplicate/malformed/unexpected scoped tests',
                'all actual list/Python OwnedJobs and inherited inner Go lifetime: observed exit, nonzero uint64 FILETIME, exclusive Job, primary exit, descendants idle0, handles closed, errors empty',
                'all actual prepare/producer guard receipts exact original refs, closed0; actual compiler blueprint3905 and private generated/export inputs held during execution;19 modules and loaded runtime exact',
                'Root complete initial/completed immutable host pairs; precise canonical historical/request/resource/source provenance',
                'Main current b85 exact native argv and Source21; no regex equivalence substitute',
                'FIXTURE in-process httptest recorder and root paths under exact controlled C temp parent; G02 real Windows11 x64 branch, actual cmd mklink/J result and output pin',
                'six separate route Mode documents plus independent receipt, real reviewer backend and future Root role registry; no formal grant'],
            prohibited_here=['Root stage','Native','Go','SQL connection','model','TP','Main/Canon/Scope write','live Root or own audit capture'],
            FILETIME_policy='Python exact int plus decimal string; never JS Number; unobserved individual descendant exits remain null')
        produced['input_contract_ref']=save(Q/'input-contract.json',contract)
        schemas=dict(base,schema='researchos.w09-nf6-mode-schema-specification.v1',status='SCHEMA_ONLY_NO_MODE_DECISION',
            production_verifier_ref=pin(R/'ops/ci/w09_evidence_closure.py'),profile_ref=pin(R/'execution/v2.4/formal_profile_w09.py'),
            mode_schema='researchos.w09-mode-decision.v2',independent_receipt_schema='researchos.w09-independent-mode-review.v1',
            Mode_decision_only_after_actual_review='QUALIFIED',Mode_reviewer_id=BACKEND,independent_receipt_actor_id=BACKEND,metadata_canonical_actor=ACTOR,
            producer_id='codex:/root',reviewer_role='INDEPENDENT_NON_AUTHOR',
            required_Mode_fields=['schema','route','mode','run_id','report_ref','report_sha256','stdout_sha256','source_sha256','go_executable','producer_id','reviewer_id','reviewer_role','decision','independent_review_ref'],
            required_receipt_fields=['schema','actor_id','actor_role','producer_id','run_id','report_sha256','source_sha256','go_executable','run_os','run_os_release','decision'],
            shared_binding='Exact current run/report/native Source21/go/stdout pins; each route document distinct; independent receipt outside producer report directory.',
            FIXTURE_extra_fields=dict(input_origin='OWNED_TEMP_DIR'),FIXTURE_predicates=['all actual HTTP exchanges delivery IN_PROCESS_HTTptest_RECORDER','at least one pinned state root_path under consumer tempfile.gettempdir(); future consumer TEMP/TMP exact C:/Users/yqyyds/.researchos/w09-native-v5'],
            LIVE_WINDOWS_extra_fields=['locked_go_sha256','host_witness','junction_witness','witness_allowlist','junction_root_path','junction_target_path'],
            LIVE_WINDOWS_witness_schemas=['researchos.w09-host-witness.v1','researchos.w09-junction-witness.v1'],
            LIVE_WINDOWS_predicates=['actual Windows11 x64 build>=22000; current locked Go sha','two exact typed distinct witness refs only, frozen witness_allowlist set exactly both','witness same run/report/go/Source21 and actual_platform Windows 11 x64','actual g02-os-branch windows/amd64/junction_branch true','actual g02-junction-command root_path/target_path absolute distinct; exact cmd.exe /c mklink /J argv, exit0 and raw output pin'],
            six_route_specs=routes,
            Root_role_registry_obligation='Root must newly bind actual raw reviewer /root/backup_regression_resources as verifier, distinct from actual Source author Full, executor Root and assembler. VERIFIER provenance pointer /reviewer_id must exactly equal actual Mode origin and backend peer; final acceptance issuer remains true verifier.',
            original_true_peer_capture_obligation='Root captures future real Backup FINAL after actual review; no predicted metadata, witness or delivery now.',
            current_Mode_documents=[],current_independent_receipts=[],future_final_issuance_ref=None)
        produced['mode_schema_ref']=save(Q/'six-mode-schema.json',schemas)
        produced['basis_ref']=save(Q/'immutable-input-basis.json',dict(base,schema='researchos.w09-nf6-actual-review-preparation-basis.v1',held_refs=refs,guard_source_ref=pin(GUARD),prior_nf5_actual_reviewer_is_reference_only=True,prior_nf5_wrong_root_target_field_not_reused=True,actual_G02_event_fields=['root_path','target_path'],future_reports_not_read=True,current_Canon_not_read=True,live_audit_not_captured=True))
    except BaseException as exc:
        primary=dict(type=type(exc).__name__,message=str(exc));traceback.print_exc()
    finally:
        close=guard.close();close_ref=save(Q/'preparation-SourceGuard.closed.json',close)
        result_ref=save(Q/'preparation-result.json',dict(schema='researchos.w09-nf6-actual-review-preparation-result.v1',actor_id=ACTOR,produced_refs=produced,primary_error=primary,guard_cleanup_ref=close_ref,guards_closed=close['closed'],retained_handles_count=close['retained_handles_count'],actual_review_executed=False,Mode_issued=False,execution_grant=False,formal_acceptance=False))
        print(json.dumps(dict(result_ref=result_ref,produced_refs=produced,guard_cleanup_ref=close_ref,primary_error=primary,guards_closed=close['closed'],retained_handles_count=close['retained_handles_count']),ensure_ascii=False))
    return 0 if primary is None and close['closed'] and close['errors']==[] and close['retained_handles_count']==0 else 1

if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
