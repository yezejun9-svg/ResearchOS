"""Extract existing Main contracts only; never invoke a verifier or product."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json

R=Path(r'D:/作品集/ResearchOS/research-os')
K=Path(r'D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def doc(p):return json.loads(Path(p).read_bytes())

def save(name,value):
    with (D/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
    return pin(D/name)

def extract(relative,names):
    p=R/relative;raw=p.read_bytes();text=raw.decode('utf-8-sig');tree=ast.parse(text);lines=text.splitlines()
    definitions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    return dict(source_ref=pin(p),functions=[dict(name=name,line=definitions[name].lineno,
        end_line=definitions[name].end_lineno,source_text='\n'.join(lines[definitions[name].lineno-1:definitions[name].end_lineno])) for name in names])

def main():
    main_refs={name:pin(R/name) for name in ('execution/v2.4/formal_profile_w09.py','execution/v2.4/formal_case_index.py',
        'execution/v2.4/commands.json','execution/command_dispatcher/dispatch.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py')}
    expected={'execution/v2.4/formal_profile_w09.py':('d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f',71397),
        'execution/v2.4/commands.json':('12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97',67323)}
    pin_checks={k:dict(expected_sha256=sha,expected_bytes=size,actual_ref=main_refs[k],matches=(main_refs[k]['sha256']==sha and main_refs[k]['bytes']==size)) for k,(sha,size) in expected.items()}
    excerpts=save('existing-Main-interface-excerpts.json',dict(schema='researchos.w09-existing-main-interface-excerpts.v1',actor_id=ACTOR,
        source_functions_executed=False,source_text_is_reference_only=True,excerpts=[
            extract('execution/v2.4/formal_profile_w09.py',['_historical_registry','_role_audit','_role_registry','_route_execution_actor',
                '_independent_roles','_vector','_native','_dispatches','_global','_review_execution_cutoff','_capture_registry','_root_original','_independent','verify_owner']),
            extract('execution/v2.4/formal_case_index.py',['Reader','_canonical_state','_w09_profile','_registered_roots','_verify_owner','recheck_inputs','derive_formal_cases','main']),
            extract('ops/ci/w09_formal_router.py',['_pinned_native_report','main']),
            extract('ops/ci/w09_evidence_closure.py',['verify_mode']),
            extract('execution/command_dispatcher/dispatch.py',['execute'])],product_calls=0,execution_grant=False,formal_acceptance=False))
    spec_refs={name:pin(K/'contracts'/name) for name in ('tasks.json','acceptance.json','execution.plan.json')}
    acceptance=doc(K/'contracts/acceptance.json');plan=doc(K/'contracts/execution.plan.json');tasks=doc(K/'contracts/tasks.json')
    step=next(x for x in plan['steps'] if x['id']=='W09-99');task=next(x for x in tasks['tasks'] if x.get('id',x.get('task_id'))=='W09')
    cases={x['id']:x for x in acceptance['cases'] if x['id'] in ('C19','A06')}
    observation=doc(D/'current-contract-observation.json')
    original_prefix=doc(D/'original-1118.successful-prefix.json')['actual_values']
    prior_request=original_prefix[0]['old_C19_request_fields']
    old_summary_ref=pin(W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd/consumer-summary.json')
    old_summary=doc(old_summary_ref['path'])
    route_rows=[]
    for binding in step['verification_commands']:
        key=binding['key'];check=binding.get('check_id','');case=binding.get('case_id','')
        route_rows.append(dict(command_key=key,check_id=check,case_id=case,expected_assertion_ids=binding['expected_assertion_ids'],
            reuse_existing=(case=='C19'),producer_selector=(check or case),native_mode=('LIVE_WINDOWS' if check=='W09-G02' else 'FIXTURE'),
            dispatcher_cli_executable_tool='python',dispatcher_cli_args=['-I','-S','-B','-X','utf8',str(R/'execution/command_dispatcher/dispatch.py'),key,
                '--task-id','W09',*(['--check-id',check] if check else ['--case-id',case]),'--spec','v2.4']))
    native_case=W/'w09_profile_nf3_root_adoption_root/646e71a406c74abda1990f72fb0a34e6'
    native_vector_ref=pin(native_case/'native.canonical-vector.json');native_vector=doc(native_vector_ref['path'])
    native_scope_facts=[]
    for key in ('W09-G01','W09-G02','A06'):
        p=native_case/('scope.'+key+'.json');v=doc(p)
        native_scope_facts.append(dict(scope_ref=pin(p),selector=v['selector'],schema=v['schema'],lease_expires_at=v['lease_expires_at'],
            formal_dispatcher=v['formal_dispatcher'],routes_field_present='routes' in v,source_actor_field_present='source_actor' in v,
            can_stand_in_for_formal_route_scope=False))
    cp_archive=S/'historical.cp376.before-native.checkpoint.json';cp=doc(cp_archive)
    authorities={k:dict(present=k in cp.get('work_in_progress',{}),value=cp.get('work_in_progress',{}).get(k))
        for k in ('w09_execution_role_registry_ref','w09_root_delivery_capture_index_ref')}
    api_contract=dict(schema='researchos.w09-existing-formal-consumer-api-contract.v1',actor_id=ACTOR,
        existing_main_refs=main_refs,existing_main_excerpts_ref=excerpts,
        assembler_and_capture_cli=dict(status='OPEN_NOT_PUBLISHED',Root_inventory_confirmation=True,
            meaning='The current Main engine validates evidence. No published Root assembler/consumer/Capture registrar CLI was found. A new bounded Source adapter must call the existing engine and be independently reviewed; this document creates none.'),
        dispatcher=dict(api='execute(key, selectors=None, *, root=ROOT, spec="auto")',return_value='(receipt_dict, receipt_Path)',
            explicit_spec='v2.4',cwd=str(R),locked_toolchain_ref=pin(R/'execution/toolchains/locked.json'),routes=route_rows,
            six_env=['RESEARCHOS_W09_NATIVE_REPORT_REF','RESEARCHOS_W09_NATIVE_REPORT_SHA256','RESEARCHOS_W09_TOOL_RUN_REF',
                'RESEARCHOS_W09_TOOL_RUN_SHA256','RESEARCHOS_W09_MODE_DECISION_REF','RESEARCHOS_W09_MODE_DECISION_SHA256'],
            env_pin_paths='repo-relative report/tool/mode artifact paths; a fresh explicit environment with unused selector empty/absent',
            registered_child_argv='Use exact CM40 entry argv. Do not replace the pinned registered child arguments.',
            postrun_mode_api='verify_mode(root, source, report, route, ctx, native, decision_ref, decision_sha)',
            mode_schema='researchos.w09-mode-decision.v2',mode_decision='QUALIFIED',mode_authority=False,
            mode_review_schema='researchos.w09-independent-mode-review.v1',independent_reviewer_role='INDEPENDENT_NON_AUTHOR',
            mode_binding=['route','mode','run_id','report_ref','report_sha256','stdout_sha256','source_sha256','go_executable',
                'producer_id','reviewer_id','independent_review_ref'],
            G02='Actual Windows11x64, locked Go, exact same-run host/junction witnesses and frozen allowlist, actual mklink /J raw and root/target/command/output equality are mandatory.',
            final_scope='CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE',output_formal_acceptance='PENDING_INDEPENDENT_VERIFIER',
            new_invocations=4,old_invocations_reused=2,producer_rerun=False),
        stable_context=dict(schema='researchos.w09.current-context.v1',required_consumed_fields=['schema','task_id','step_id','executor_id','run_id',
            'created_at','acceptance_baseline_ref','version_vector','source_coverage','role_policy','registered_commands','global_evidence_refs'],
            task_id='W09',step_id='W09-99',registered_commands_required_fields=['command_key','check_id','case_id','receipt_ref','native_report_ref',
                'native_tool_run_ref','mode_decision_ref'],
            version_vector_exact_fields=['schema','package_version','spec_files','source_files','input_files','lock_files','tool_files','environment','components'],
            version_schema='researchos.w09.version-vector.v1',package_version='2.4.0',
            mandatory_stable_input_paths=['execution/v2.4/commands.json','execution/toolchains/locked.json',
                'execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json'],
            mutable_live_CP_OW_not_required_in_context_vector=True,
            sources='All fixed trusted Source files plus complete current *.go inventory under internal/domain and adapters/retrieval, Source21 hashes and source_coverage.',
            components='model/rubric: not_applicable with reason; adapter/policy: applicable with version and pinned refs',
            global_evidence_keys=['C19','A06'],global_four_ref_keys=['run_receipt','version_manifest','command_receipt','assertion_results'],
            global_schemas=['researchos.w09.run-receipt.v1','researchos.w09.version-manifest.v1','researchos.w09.command-receipt.v1','researchos.w09.assertion-results.v1'],
            global_assertion_fields=['id','expected','actual','status','raw_evidence_refs','refusal_evidence_refs'],
            global_raw='Each actual links to matching Native owned /actual; both case routes must contain each assertion. A06-02 requires nonempty refusal_evidence_refs.',
            global_clock='Each GLOBAL start <= original Native start <= Go events <= Native end <= consumer start <= consumer end <= GLOBAL end; do not claim a newly run C19 interval.',
            exact_global_expected={k:v['assertions'] for k,v in cases.items()}),
        role_registration=dict(fixed_path='execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json',
            checkpoint_slot='work_in_progress.w09_execution_role_registry_ref',authority_exact_keys=['path','sha256','bytes'],
            schema='researchos.w09.execution-role-registry.v1',registry_exact_fields=['schema','writer_actor','run_id','roles','provenance','route_execution_refs'],
            writer_actor='codex:/root',role_exact_fields=['source_authors','executor','assembler','verifier','root_observer'],
            independence='verifier casefold differs from every source_author, executor, assembler and root_observer; executor/assembler/root_observer may be Root.',
            provenance_exact_fields=['role','actor_id','origin_kind','raw_ref','actual_audit_ref'],
            provenance_conditions=[['SOURCE_AUTHOR','ROOT_SCOPE_REGISTRATION','/source_actor'],['EXECUTOR','ACTUAL_MODE_DECISION','/producer_id'],
                ['EVIDENCE_ASSEMBLER','ROOT_OWNER_REGISTRATION','/selected_worker_id'],['VERIFIER','ACTUAL_MODE_DECISION','/reviewer_id'],
                ['ROOT_OBSERVER','ROOT_SCOPE_REGISTRATION','/issued_by']],
            assembly_scope=dict(issued_by='codex:/root',slice_id='W09_FULL_FORMAL_ASSEMBLY',owner_id='Root or actual executor',
                selected_worker_id='actual assembler',lease_status='ACTIVE',lease_expires_at='>= context.created_at',
                location='W09 Source receipt boundary',scope_ref_keys=['path','sha256','bytes']),
            route_execution_ref_exact_fields=['command_key','check_id','case_id','scope_ref','owner_ref'],route_count=6,
            route_lease='Root-issued Scope.routes and owner.routes contain the command; owner.scope_ref physical path/hash/bytes == Scope; selected_worker == actual Native producer == roles.executor; ACTIVE; original consumer ended_at <= original lease_expires_at.',
            old_C19_scope_ref=prior_request['scope_ref'],old_C19_owner_ref=prior_request['current_owner_ref'],old_C19_worker_ref=prior_request['current_worker_ref'],
            actual_role_audit_schema='researchos.w09.actual-role-audit.v1',actual_role_audit_exact_fields=['schema','actor_id','role','Root_thread_id',
                'source_audit_path','source_line_offsets','original_line_sha256','source_prefix_size_observed','original_capture_ref','binding_sha256'],
            actual_audit='Three original Root session records at actual offsets/hash/bytes; Root actor uses real call/result; peers use adjacent metadata/message. Artifact digest must occur in original public call/delivery.',
            original_prefix_path='execution/v2.4/root_original_events/W09/W09-99/',Root_thread_id=ROOT_THREAD),
        formal_review=dict(schema='researchos.w09.independent-review.v1',decision='ACCEPTED',missing=[],failed=[],supersedes_review_refs=[],
            reviewer_id='registered independent Verifier',issuer_id='same Verifier',executor_id='actual Root executor',
            context_ref='exact current context path/hash',same_context_fields=['acceptance_baseline_ref','version_vector','registered_commands','global_evidence_refs'],
            exact_verdict_ids=['C19-01','C19-02','C19-03','A06-01','A06-02','A06-03','W09-G01','W09-G02'],
            verdict_conditions='PASS/nonempty actual; GLOBAL actual/expected equal case rows; gate mode/run_id and report /assertion_results raw pin match actual output.',
            delivery='Normal plaintext backend Final after review. Full review and context SHA in the original text. Actual sender equals registered reviewer; no fabricated Root witness or future timestamps.'),
        capture_registration=dict(fixed_index='execution/v2.4/root_delivery_captures/W09/W09-99/index.json',
            checkpoint_slot='work_in_progress.w09_root_delivery_capture_index_ref',authority_exact_keys=['path','sha256','bytes'],
            index_schema='researchos.root-delivery-capture-index.v2',writer_actor='codex:/root',Root_thread_id=ROOT_THREAD,
            entry_required_fields=['event_id','capture_ref','origin_ref'],event_ids_unique=True,entry_refs_exact_keys=['path','sha256','bytes'],
            capture_schema='researchos.root-actual-audit-formal-delivery.v1',required_capture_fields=['schema','issued_by','protocol_observation_only',
                'W09_parent_or_formal_delivery','Root_thread_id','message_id','sender','recipient','received_at','original_capture_ref','review_ref','context_ref',
                'content_sha256','root_observed_at','source_line_offsets','original_line_sha256','source_audit_path','source_prefix_size_observed'],
            protocol_observation_only=False,W09_parent_or_formal_delivery=True,
            actual_original='Unchanged session header + metadata + adjacent backend agent_message; exact original offsets/hash/bytes and prefix bounds. client_authored=false, recipient=/root, same timestamps, same event_id, one plaintext input_text.',
            issuance_schema='researchos.w09.root-observed-issuance.v1',issuance_required_fields=['schema','task_id','step_id','run_id','context_ref','review_ref',
                'actor','observer_id','issuer_id','executor_id','reviewer_id','event_id','delivery_ref','origin_event_ref','observed_at'],
            actor='codex:/root',observer_id='codex:/root',issuer_id='actual independent Verifier',
            time_order='all six Native/Go/consumer ends <= context.created_at <= review.issued_at <= actual received_at <= root_observed_at <= issuance.observed_at <= owner.accepted_at; both GLOBAL ends <= review.issued_at'),
        verifier=dict(existing_api='verify_owner(api, reader, owner, roots, plan_path)',
            exact_main_path=str(R/'execution/v2.4/formal_profile_w09.py'),api_provider='formal_case_index._profile_api()',reader_provider='formal_case_index.Reader(repo_root)',
            roots_exact_keys=['context','review','issuance'],roots_values='actual verified absolute Paths under W09-99',
            owner_required_fields=['status','executor_id','verifier_id','accepted_at','evidence'],owner_status='ACCEPTED',
            owner_evidence_ref_keys=['path','sha256'],owner_evidence_path='relative to execution/v2.4; exactly one root of each schema',
            preregistration_check='Existing verify_owner may validate an explicitly Root-approved prospective owner only after true review/capture refs exist; result is pure validation, not canonical acceptance.',
            verify_owner_return='context plus _verified_owned_inventories and _verified_audit_ranges; Reader.read_hashes is the CAS dependency set',
            public_api='derive_formal_cases(repo_root, state_path, plan_path)',public_return_schema='researchos.formal-case-index.v1',
            fixed_canonical_state=str(R/'execution/v2.4/step_state.json'),temporary_state_rejected='CANONICAL_STATE',
            cli=[str(R/'execution/v2.4/formal_case_index.py'),'--repo',str(R),'--state',str(R/'execution/v2.4/step_state.json'),
                '--plan',str(K/'contracts/execution.plan.json')],
            accepted_predicate='W09 owner.integrity == VALID_ACCEPTED and accepted_case_ids == [A06,C19]; eight assertions are not eight cases. Whole index integrity PASS is distinct from this owner predicate.',
            CAS_api='recheck_inputs(result.dependency_snapshot)',CAS_checks=['files','complete Source/owned inventories','original Root audit byte ranges'],
            CLI_exit='0 only overall integrity PASS; otherwise1. Inspect per-owner results and preserve other owners.'),
        known_strict_conditions=['Main author equality uses actual backend string literally; no NF3 canonical/backend alias decoder is called.',
            'Main peer metadata/message timestamp must be identical; future formal delivery is unobserved and must not be predicted.',
            'No live CP/OW pin is mandatory in context vector; stage requests still need actual fresh Current4 and Root Scope/owner/worker authority. Avoid a context pin of live files a later registration necessarily changes.',
            'No historical Native Current4 == formal Current4 requirement exists in _native. All actual Source21/tool/report/raw/mode/registry pins and original leases remain mandatory.',
            'CM39 exception is only the two fixed C19 receipts and exact CM40 semantic delta; CM41 is rejected.'],
        execution_grant=False,formal_acceptance=False,product_calls=0)
    api_ref=save('existing-Main-consumer-contract.json',api_contract)
    result=save('readiness.json',dict(schema='researchos.w09-consumer-readiness-readonly.v1',actor_id=ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),
        status='READONLY_CONTRACT_PREPARED_CALLER_IMPLEMENTATION_OPEN',existing_Main_contract_ref=api_ref,existing_Main_excerpts_ref=excerpts,
        main_pin_observations=pin_checks,spec_refs=spec_refs,frozen_required_cases=len(acceptance['cases']),frozen_required_tasks=len(tasks['tasks']),
        W09_owned_case_ids=['C19','A06'],gate_checks=task['task_gate_checks'],dependencies=observation['dependency_status'],
        W09_parent_row_present=False,CP376_archive_ref=pin(cp_archive),CP376_authority_slots=authorities,
        actual_native_registration_vector_ref=native_vector_ref,actual_native_registration_vector=native_vector,native_scope_facts=native_scope_facts,
        old_C19_independent_review_decision_ref=pin(W/'c19_two_actual_consumers_independent_review_codex/consumers-01a120dd/actual-decision.final.json'),
        old_C19_actual_Root_tool_io_ref=pin(S/'Main-C19-two-dispatchers.actual.original-tool-io.root.json'),
        old_C19_consumer_summary_ref=old_summary_ref,old_C19_consumers=old_summary['consumers'],old_C19_original_scope_owner_worker_observation_ref=pin(D/'original-1118.successful-prefix.json'),
        current_commands_observation_ref=pin(D/'current-contract-observation.json'),
        existing_Source_reviews_reused=[pin(W/'w09_profile_nf3_root_adoption_independent_review_codex/review-adopt-20261010-01/Source-decision.json'),
            pin(W/'w09_profile_nf3_root_adoption_independent_review_codex/review-adopt-20261010-02/Source-decision.json')],
        required_next_sequence=['Finish all three Native prepare/run under unchanged CP376/OW180 and retain real outputs/closed jobs.',
            'Independent actual mode review for each new producer and route-specific mode decisions; reuse original C19 decisions.',
            'Publish and independently review the missing bounded Root formal bridge Source; it must reuse the fixed Main verifier.',
            'Only after all three Native runs finish, Root registers new assembly/consumer Scope, owners/workers/leases and actual role registry using a fresh Current4 and pending suffix.',
            'Execute only four new CM40 consumer routes under the registered authority; reuse exactly two old C19 receipts with their original Scope/owner/lease.',
            'Assemble current Source/version/context plus C19/A06 GLOBAL actual records from the real packets and six receipts; no second test engine.',
            'Independent full Verifier replays the existing Main closures and emits true formal review; Root receives the normal backend Final.',
            'Root captures the actual original delivery, seals issuance, and registers the fixed capture index pin in current CP.',
            'Use existing verify_owner for a truthful preregistration check; Root alone registers actual W09-99 owner acceptance and full evidence.',
            'Run existing derive_formal_cases on fixed actual canonical state, then CAS recheck; accept C19/A06 only if VALID_ACCEPTED and all current conditions pass.'],
        missing_published_bridge=True,Root_scope_created=False,Root_capture_created=False,role_registry_written=False,
        native_run_artifacts_examined=False,registered_native_Scopes_only_examined=True,old_Go_Native_SQL_model_dispatcher_controls_reexecuted=False,
        original_diagnostics=[dict(ordinal=n,raw_ref=pin(D/('original-'+str(n)+'.raw.jsonl')),binding_ref=pin(D/('original-'+str(n)+'.binding.json'))) for n in (1117,1118)],
        normal_no_match_queries_ref=pin(D/'readonly-query-originals.json'),original_failures_counted_once=True,counter_reset=False,
        source_functions_executed=False,product_calls=0,Main_Canon_writes=0,live_Canon_handles=0,SourceReadGuard_created=False,
        execution_grant=False,programme_qualification=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(readiness_ref=result,existing_Main_contract_ref=api_ref,existing_Main_excerpts_ref=excerpts,
        main_pin_observations=pin_checks,product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
