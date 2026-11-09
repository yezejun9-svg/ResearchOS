"""Prepare a read-only component-review input map. No actual component is accepted."""
from pathlib import Path
from datetime import datetime, timezone
import ast, json, types

R = Path(r'D:\作品集\ResearchOS\research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = B / 'public22_to_main23_continuation_caller_source_codex/continue-20261010-02'
REVIEW = B / 'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
def read(path): return json.loads(Path(path).read_bytes())
h = read(N / 'HDF.json'); review = read(REVIEW / 'HDF.json')
i = read(h['source_inputs_ref']['path'])
held = [s.pin(__file__), s.pin(HELPER), s.pin(N / 'HDF.json'), h['manifest_ref'],
        h['caller_ref'], h['source_inputs_ref'], h['calling_contract_ref'],
        s.pin(REVIEW / 'HDF.json'), review['manifest_ref'], review['source_decision_ref'],
        review['runtime_closure_evidence_ref'], i['leaf_runner_ref'], i['leaf_contract_ref'],
        i['owned_job_ref'], i['runtime_resources_ref'], i['existing22_decision_ref'], i['main23_bound_ref']]
# These are public immutable Source, contracts and already-sealed decisions only.
# Neither the live Canon vector, binaries, databases, owner/key files, current
# Native output directories, nor the 144/149 runtime resource files are acquired.
g = s.guard(); prepared = {}; failure = None
try:
    g.acquire(held)
    contract = json.loads(g.get_buffer(h['calling_contract_ref']['path']))
    caller_raw = g.get_buffer(h['caller_ref']['path'])
    leaf_raw = g.get_buffer(i['leaf_runner_ref']['path'])
    caller_tree = ast.parse(caller_raw); leaf_tree = ast.parse(leaf_raw)
    def declarations(tree):
        return {node.name:node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    caller_nodes, leaf_nodes = declarations(caller_tree), declarations(leaf_tree)
    def location(name, leaf=False):
        node = (leaf_nodes if leaf else caller_nodes)[name]
        return dict(ref=i['leaf_runner_ref'] if leaf else h['caller_ref'],
                    function=name, line=node.lineno, end_line=node.end_lineno)
    # Extract the original functions without importing the Caller, Leaf or Owned Job.
    prepared['source_evidence_ref'] = s.write('source-interface-evidence.json', dict(
        caller=s.code_evidence(caller_raw, h['caller_ref']['path'], [
            'audit','source_chain','root_request','native_observation','scope_projection','build',
            'projection','registration','live','reuse_chain','continuation_projection','retain_observation',
            'record_observation','ObservedOutput','validate_upgrade23','validate_backup23',
            'validate_restore23','execute','main']),
        leaf=s.code_evidence(leaf_raw, i['leaf_runner_ref']['path'], [
            'upgrade23_phases','closed_job','validate_ledger','readonly_database_observation']),
        code_extracted_without_import_or_execution=True))

    artifact_contract = dict(
        schema='researchos.public22-continuation-actual-component-review-input-contract.v1',
        status='PREPARED_PENDING_ACTUAL', component='PUBLIC22_TO_MAIN23_CONTINUATION_ONLY',
        prepared_by='codex:/root/full_w09_source_review', backend_actor='/root/full_w09_source_review',
        original_Source_author='codex:/root/attach_restore_independent_review', actual_executor='codex:/root',
        purpose='Packaging and location map for the existing Source02 requirements; no added runtime gate, second acceptance engine or future fact.',
        ref_shape=dict(required_keys=['path','sha256','bytes'],
            spelling='Keep exact supplied foreign ref objects. New Root refs use Windows str(Path); do not normalize dictionary spellings.',
            bytes_type='Python int, never bool; actual source shape/same/checked rules remain authoritative.'),
        accepted_Source_refs=[s.pin(N / 'HDF.json'), h['manifest_ref'], h['caller_ref'], h['calling_contract_ref']],
        accepted_Source_review_refs=[s.pin(REVIEW / 'HDF.json'), review['manifest_ref'], review['source_decision_ref']],
        reused_existing22_decision_ref=i['existing22_decision_ref'],
        reused_Main23_bound_ref=i['main23_bound_ref'], reused_Main23_program_ref=i['main23_program_ref'],
        reused_runtime_resources_ref=i['runtime_resources_ref'],
        reuse=dict(old_four_children_replayed=False, original1025_result='FAILED_RETAINED',
            accepted_resource_144_149_controls_rerun=False, prior_Source_controls_rerun=False,
            qualification_dependency='reuse_chain checks the exact already-issued Main23 programme/source/review/Root bindings; it issues no new programme qualification.',
            runtime_dependency='Existing accepted own Source review binds runtime_resources_ref with runtime_closure_reviewed=true. Source02 runtime_refs checks loaded public Python/_sqlite3/DLL resources at actual Root entry; this preparation does not requalify them.',
            source=location('reuse_chain')),
        future_delivery=dict(
            actual_request_ref=None, registration_facts_ref=None, registration_result_ref=None,
            execute_preentry_audit_ref=None, execute_initial_host_capture_ref=None,
            execute_completed_host_capture_ref=None, case_closed_ref=None,
            actual_returned_state_ref=None,
            actual_returned_state_ref_optional_when_complete_host_result_contains_returned_state=True,
            delivery_rule='Supply full path/sha256/bytes of existing actual artifacts after Root execute closes. Derived Scope/owner/worker/request/current4/archives/journal/raw/report refs are read from facts, request and returned state; no future file names or exits are inferred.'),
        Root_registration=dict(
            registration_request_schema=contract['registration_request_schema'],
            registration_request_required_fields=contract['registration_request_required_fields'],
            scope_schema='researchos.root-public22-continuation-scope.v1',
            facts_schema='researchos.root-public22-continuation-registration-facts.v1',
            result_schema='researchos.root-public22-continuation-registration-result.v1',
            registration_artifacts=['scope.root.json','owner.root.json','worker.root.json','facts.root.json',
                '0.before.raw.json','1.before.raw.json','2.before.raw.json','3.before.raw.json',
                '0.after.proposed.json','1.after.proposed.json','build.guard.closed.json',
                'check.result.json','check.guard.closed.json','activate.result.json','activate.guard.closed.json'],
            scope_ref_location='facts.scope_ref', owner_ref_location='facts.owner_ref', worker_ref_location='facts.worker_ref',
            registration_request_ref_location='facts.request_ref',
            transaction_journal_location='activate.result.transaction.transaction_journal/committed.json',
            committed_predicates=['both_verified_while_exclusively_held is true','written_indices == [0,1]',
                'exact two after_refs equal actual current4 first two refs'],
            authority=['Root issued and registered exact Source02 Scope with the original case/evidence and three phases only.',
                'Owner and one worker are codex:/root, ACTIVE, same finite lease_id/times/Scope/receipt_root; owner/worker cross-links exact.',
                'Current CP contains exact public22_continuation_scope_ref/facts_ref; OW subtask and CP worker documents equal saved owner/worker documents.',
                'Before four byte archives match before refs; complete inverse; CP/OW revisions increment one; SS/CM unchanged.',
                'Old failure ledger/other owners are preserved. New failures retain actual exits and get a single Root-assigned original ordinal.'],
            lease_seconds_max=contract['finite_lease_seconds_max'],
            current4_rule=contract['current4'],
            registration_source=location('registration'), live_source=location('live'),
            inverse_source=location('projection')),
        Root_execute=dict(
            actual_request_schema=contract['actual_request_schema'],
            actual_request_required_fields=contract['actual_request_required_fields'],
            preentry_second_ref=contract['execute_second_ref'],
            preentry_expected_refs=['actual_request_ref','actual.registration_result_ref','actual.scope_ref',
                                    'actual.current_canonical_refs[0:4]'],
            preentry_must_complete_before_execute=True,
            capture_rule='Preserve each actual Root tool call/output as its own real pair with original session header, raw bytes, offsets/lengths/SHA and call_id. If execution yields a session, retain initial and completion pairs and the actual session linkage; never synthesize a combined pair.',
            Root_thread_id=contract['actual_root_thread'], Root_audit_path=contract['actual_root_log'],
            expected_return_schema='researchos.public22-to-main23-continuation-return.v1',
            expected_success_status='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW',
            closed_receipt='Scope.receipt_root/case.closed.json',
            returned_vs_saved_rule='case.closed.json is saved before closed_receipt_ref is assigned to returned state. Compare the actual returned state with only that source-defined self-reference timing difference; preserve the original bytes of both.',
            external_original_hostpair_required=True,
            cli=contract['cli'],
            exact_execute_arguments=['execute','actual_ref.path','actual_ref.sha256','actual_ref.bytes',
                                     'preentry_ref.path','preentry_ref.sha256','preentry_ref.bytes'],
            execute_source=location('execute'), cli_source=location('main'), audit_source=location('audit')),
        new_child_evidence=dict(
            phases=['upgrade22to23','backup23','verify23'], exact_order=True, maximum_attempts=3,
            timeout_seconds=contract['child_timeout_seconds'],
            argv_rule='Use Source02 continuation_projection and Leaf upgrade23_phases with actual Scope.receipt_root and the fixed qualified Main23 program. Contract aaaa paths are examples only.',
            argv_source=location('upgrade23_phases',True), projection_source=location('continuation_projection'),
            per_invocation=['phase','argv','cwd','env','timeout_seconds','started_at_unix_ns','before_ref',
                'observation','actual_exit','ended_at_unix_ns','creation_time_100ns_decimal',
                'stdout_ref','stderr_ref','result_ref'],
            before_files='receipt_root/raw/<phase>.before.json',
            result_files='receipt_root/raw/<phase>.result.json',
            stdout_files='receipt_root/raw/<phase>.stdout', stderr_files='receipt_root/raw/<phase>.stderr',
            before_rule='Original before projection has observation/actual_exit null and is saved before launch; match actual argv/cwd/env/90s/start time to the returned invocation.',
            output_rule='Keep original stdout/stderr bytes and pins; each output cap is 4 MiB. Compare emitted strict JSON with the native persisted manifest/report using Leaf same_json.',
            success_observation=['actual_exit is int 0, timed_out false, error null',
                'owned_child_pid is positive int; resumed true',
                'creation_time_100ns is a Python integer; retain its exact uint64 decimal spelling without JS/float conversion',
                'unnamed_exclusive_job, kill_on_job_close_configured, assigned_before_resume, job_idle_confirmed, primary_exit_confirmed, handles_closed are true',
                'active_processes_last_observed is int 0 and cleanup errors []'],
            observation_source=location('closed_job',True),
            close_fault_rule=contract['first_failure'],
            close_sources=[location('retain_observation'),location('ObservedOutput')]),
        three_phase_oracles=[
            dict(phase='upgrade22to23', observations=['working22_input','upgrade23'],
                reports=['state.upgrade_manifest_ref','state.upgrade_report_ref'],
                files=['working22/researchos.sqlite','upgrade22to23.snapshot/manifest.json',
                       'candidate23/researchos.sqlite','candidate23/restore-report.json'],
                predicates=['working22 starts as a byte-identical copy of the retained original22 source and has equal logical tables/schema.',
                    'Exact source ledger1..22 and target ledger1..23; integrity ok and FK0; sessions/command queue remain empty.',
                    'Target tables equal source tables plus exactly client_command_identities, host_model_configurations, host_model_config_heads; all three empty.',
                    'Every old table hash/count stays equal except ledger addition and exact owner credential revocation; auth credential count retained and rows hash equals expected revoked rows.',
                    'Snapshot plan id/source_versions/target_versions bind source old22 and qualified Main23 programme hashes and source/target-with-fence schema hashes.',
                    'Emitted/persisted restore report equal; restored status, backup id and before inventory bind snapshot.',
                    'Exactly the Main backup_require_fresh_observation trigger on domain_objects matches expected_restore_trigger_sql of the pinned Main recovery Source.'],
                source=location('validate_upgrade23'), fence_source=location('execute')),
            dict(phase='backup23', observations=['upgrade23','backup23_source'],
                reports=['state.backup23_manifest_ref'], files=['backup23/manifest.json','candidate23/researchos.sqlite'],
                predicates=['Ledger1..23 with integrity ok/FK0 and typed empty additive tables.',
                    'Every table hash/count and every schema row equal the pre-backup upgrade23 observation.',
                    'Manifest migrations1..23 and schema hash match the unchanged source; emitted/persisted manifests equal.'],
                source=location('validate_backup23')),
            dict(phase='verify23', observations=['backup23_source','restored23'],
                reports=['state.restore23_report_ref'], files=['verified23/state.sqlite','verified23/restore-report.json'],
                predicates=['Ledger1..23 with integrity ok/FK0.',
                    'Exact already-fenced schema rows and SHA; every table count/hash matches backup23 source, credentials remain revoked.',
                    'Restored status/backup id bind manifest; report before == after == manifest inventory; recovery credentials REVOKED_REPROVISION_LOCALLY.',
                    'Emitted/persisted restore reports equal.'], source=location('validate_restore23'))],
        database_oracle=dict(source=location('readonly_database_observation',True),
            mode='ro,immutable,query_only', public_rows_not_emitted=True,
            current_preparation_SQL_queries=0,
            future_actual_review='Use the existing Leaf oracle against delivered quiescent public artifacts; do not create another engine or replay a child.'),
        cleanup_and_acceptance=dict(
            guard_cleanup='Returned source_guard_cleanup.closed true, retained_handles_count 0, errors []; registration guards likewise closed.',
            successful_component_requires='Three actual successful children in exact order, all source-defined oracles, complete real Root bindings, closed receipt and confirmed Job/Guard cleanup; otherwise retain the precise failed/open component state.',
            first_failure=None, future_actual_result=None, future_actual_verdict=None,
            original1025_result='FAILED_RETAINED', original_four_children_replayed=False,
            automatic_retry=False, full20to24='OPEN',
            remaining_uncovered=contract['remaining_uncovered'],
            formal_acceptance=False, parent_acceptance=False, execution_grant=False,
            formal_case_accepted_delta=0),
        private_material=dict(owner_credentials_read_or_hashed=False, recovery_key_read_or_hashed=False,
            rule=contract['private_owner']),
        current_preparation=dict(actual_native_children=0, actual_Root_stages=0,
            actual_SQL_TP_Go_Native_model_calls=0, actual_scope_issued=False, actual_component_accepted=False,
            live_Canon_refs_held=[], current_Native_outputs_read=False, guards_must_close_zero=True))
    prepared['input_contract_ref'] = s.write('actual-input-contract.json', artifact_contract)
    prepared['input_refs_ref'] = s.write('preparation-input-refs.json', dict(held_refs=held,
        source_pins_preserved_as_supplied=True, reused_evidence_only=True,
        live_Canon_refs_held=[], binaries_databases_private_material_read=False,
        no_runtime_144_149_replay=True, no_Source_control_replay=True))
except BaseException as exc:
    failure = dict(type=type(exc).__name__, message=str(exc))
    raise
finally:
    prepared['guard_ref'] = s.write('preparation-source-guard.closed.json', g.close())
    s.write('preparation-result.json', dict(status='PREPARED_PENDING_ACTUAL' if failure is None else 'PREPARATION_FAILED',
        failure=failure, refs=prepared, actual_component_review_performed=False,
        actual_Native_Go_SQL_TP_Rootstage_model_calls=0, actual_component_accepted=False,
        execution_grant=False, formal_acceptance=False))
print(json.dumps(dict(status='PREPARED_PENDING_ACTUAL', prepared_refs=prepared,
    failure=failure, actual_component_accepted=False, execution_grant=False,
    formal_acceptance=False, actual_Native_Go_SQL_TP_Rootstage_model_calls=0), ensure_ascii=False))
