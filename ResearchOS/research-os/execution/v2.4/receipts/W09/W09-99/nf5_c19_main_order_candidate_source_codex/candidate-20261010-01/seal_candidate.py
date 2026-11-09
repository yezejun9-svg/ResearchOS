"""Seal the candidate publication; never execute or adopt the Main candidate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, types

R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
support_path = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('review_support')
s.__file__ = str(support_path)
exec(compile(support_path.read_bytes(), str(support_path), 'exec'), s.__dict__)
s.D = D

def load_pinned(ref):
    raw = Path(ref['path']).read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('PERSISTED_PUBLICATION_PIN_DRIFT: ' + ref['path'])
    return json.loads(raw)

checks_ref = {'path': str(D / 'candidate-new-file-checks.json'), 'sha256': '86750a17ec97387d86af28d771b20462212eeabae01bd32be1ebd4b38672dc39', 'bytes': 3540}
checks = load_pinned(checks_ref)
pins_ref = checks['published_refs']['input_pins_ref']
pins = load_pinned(pins_ref)
guard_ref = checks['guard_ref']
guard = load_pinned(guard_ref)
if checks['failure'] is not None or checks['new_checks_passed'] != 6 or not all(row['passed'] for row in checks['checks']):
    raise ValueError('PERSISTED_NEW_FILE_CHECKS_NOT_PASSED')
if guard['verification'] != 'PASSED' or not guard['closed'] or guard['retained_handles_count'] != 0 or guard['errors'] or len(guard['entries']) != 8:
    raise ValueError('PERSISTED_EIGHT_INPUT_GUARD_NOT_CLOSED')
for key in ('before_source_ref', 'candidate_ref', 'diff_ref'):
    ref = checks['published_refs'][key]
    if s.pin(ref['path']) != ref:
        raise ValueError('PERSISTED_NEW_SOURCE_FILE_PIN_DRIFT: ' + key)

author = 'codex:/root/full_w09_source_review'
backend_author = '/root/full_w09_source_review'
thread = '01a1215b-7210-7613-b033-756b9d553b83'
root_thread = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
created = datetime.now(timezone.utc).isoformat()
published = checks['published_refs']
publication_host = s.capture('d55133', 0, 0)
before = published['before_main_ref']
candidate = published['candidate_ref']
advisory = load_pinned(pins['advisory_decision_ref'])

contract = {
    'schema': 'researchos.w09-c19-main-order-root-calling-adoption-contract.v1',
    'operation': 'ROOT_SINGLE_TARGET_MAIN_SOURCE_ADOPTION',
    'source_author': author,
    'source_author_backend': backend_author,
    'source_author_thread_id': thread,
    'root_actor': 'codex:/root',
    'root_actor_backend': '/root',
    'root_thread_id': root_thread,
    'source_namespace': str(D),
    'created_utc': created,
    'status': 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',
    'implementation_kind': 'SOURCE_CONTRACT_ONLY_NO_ADOPTION_EXECUTABLE',
    'before_main_ref': before,
    'before_source_ref': published['before_source_ref'],
    'sourcecandidate_ref': candidate,
    'single_line_diff_ref': published['diff_ref'],
    'candidate_new_file_checks_ref': checks_ref,
    'input_pins_ref': pins_ref,
    'input_guard_ref': guard_ref,
    'source_publication_host': publication_host,
    'change': {
        'target_line_before': 178,
        'old_expression': 'selected = GROUPS[check] if check else list(TESTS)',
        'new_expression': 'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]',
        'line_replacements': 1,
        'whole_byte_inverse_required': True,
        'check_branch_unchanged': True,
        'subsequent_case_intersection_unchanged': True,
        'A06_selection_unchanged': True,
        'changed_current_routes': ['test.research.fixture/W09/C19', 'test.retrieval/W09/C19'],
        'router_closure_NF5_exact_argv_gates_unchanged': True,
    },
    'mandatory_independent_review': {
        'required_before_Main_adoption': True,
        'reviewer_cannot_equal_source_author': True,
        'reviewer_cannot_be_Root_executor': True,
        'review_must_bind_exact_candidate_HDF_MF_contract_and_candidate_refs': True,
        'Root_must_observe_actual_backend_peer_delivery_and_original_byte_offsets': True,
        'prior_advisory_18_checks_are_reused_property_evidence_only': True,
        'prior_advisory_is_not_independent_acceptance_of_this_authored_candidate': True,
        'independent_review_refs': None,
        'actual_Root_peer_witness_ref': None,
    },
    'Root_actual_adoption_request_required_fields': {
        'schema': 'researchos.w09-c19-main-order-actual-adoption-request.v1',
        'request_id': 'Root-issued fresh UUID; no value pre-issued here',
        'Root_actor_and_thread': 'exact Root backend /root and root_thread_id above',
        'source_handoff_ref': 'exact published candidate HDF 3-key ref',
        'source_manifest_ref': 'exact published candidate MF 3-key ref',
        'calling_contract_ref': 'exact this published contract 3-key ref',
        'before_main_ref': before,
        'sourcecandidate_ref': candidate,
        'independent_review_refs': 'actual non-author HDF/MF/decision 3-key refs; no placeholder accepted',
        'Root_actual_peer_witness_ref': 'actual completed Root observation of author and non-author deliveries; never a future toolpair',
        'target_path': before['path'],
        'Root_ownScope_owner_worker_lease_binding': 'Root-issued actual current authority under project frozen contract; candidate package issues no Scope or lease',
        'original_byte_archive_path': 'new Root-owned immutable archive; exact before bytes retained',
        'closed_input_guards': 'actual closed0 before exclusive Main write',
    },
    'Root_single_target_adoption_sequence': [
        'Validate completed actual author and independent non-author peer proofs plus exact published refs; do not infer a grant from HDF status.',
        'Ensure all review/Source read guards are closed with zero retained handles before acquiring the Main target.',
        'Use the exact local physical target path above; reject aliases, traversal, device/UNC/reparse targets and ref drift under existing project path rules.',
        'Acquire Root-authorized exclusive target handle with share_mode=0 and validate current target SHA256/bytes equals before_main_ref while held.',
        'Retain the complete original target bytes in a new Root-owned immutable archive before modifying the sole target; never delete historical qualification/failure evidence.',
        'Install only the exact sourcecandidate bytes through the exclusive target; no other Main, Canon, Source, NF5, Scope or role file may be changed by this adoption operation.',
        'Read back installed target bytes and require candidate SHA256/bytes, retaining exact Root actual call/result, original archive ref and write/readback outcome.',
        'Close the exclusive target in finally; retain failure/partial state if any operation fails, with no automatic rollback, retry, product execution or fabricated successful return.',
    ],
    'after_adoption_qualification': {
        'retrieval_py_is_one_of_complete_current_Source21': True,
        'all_four_prior_Native_reports_become_historical_for_current_Source21': True,
        'historical_passes_and_all_original_failures_must_remain_byte_unchanged': True,
        'fresh_current_Source21_generation_and_independent_Source_review_required': True,
        'fresh_Root_issued_Native_Scopes_and_runtime_resource_qualification_required': True,
        'fresh_Native_selectors_required': ['W09-G01', 'W09-G02', 'A06', 'C19'],
        'fresh_CM40_routes_required': [
            {'command': 'test.retrieval', 'week': 'W09', 'check': 'W09-G01', 'case': ''},
            {'command': 'test.retrieval', 'week': 'W09', 'check': 'W09-G02', 'case': ''},
            {'command': 'test.research.fixture', 'week': 'W09', 'check': '', 'case': 'C19'},
            {'command': 'test.retrieval', 'week': 'W09', 'check': '', 'case': 'C19'},
            {'command': 'test.retrieval', 'week': 'W09', 'check': '', 'case': 'A06'},
            {'command': 'test.security', 'week': 'W09', 'check': '', 'case': 'A06'},
        ],
        'CM40_route_definitions_are_unchanged': True,
        'current_Mode_and_formal_acceptance_require_existing_Main_engines': True,
        'unchanged_Go_compiler_cache_bytes_may_be_reused_only_under_new_actual_resource_closure': True,
        'source21_qualification': False,
        'runtime_qualification': False,
        'Mode_qualification': False,
        'formal_acceptance': False,
    },
    'rejection_conditions': [
        'Any author/peer/ref/path/hash/bytes/Root authority or lease binding mismatch.',
        'Missing actual independent non-author review or missing completed Root peer observation.',
        'Any retained Source guard or inability to acquire exclusive share0 Main target.',
        'Current Main target differs from before_main_ref, including same physical path with different ref spelling when the downstream contract requires exact objects.',
        'Candidate contains any change beyond the one expression or its full inverse differs from original target bytes.',
        'Original bytes not archived completely before writing; partial/write/readback failure must stay failed.',
        'Attempt to use a prior Native or Mode as current after the Source21 change, or to create execution/Scope/formal authority from this Source package.',
    ],
    'original_failure_ordinals_retained': [1158, 1159],
    'original_failure_evidence': pins['original_failure_evidence'],
    'prior_Root_C19_authority_failure': {'original_ordinal': 1156, 'retained_by': 'Root original ledger and immutable actual C19 artifacts; no reclassification by this package'},
    'execution_grant': False,
    'formal_acceptance': False,
    'candidate_independently_accepted': False,
    'Main_adopted': False,
    'RootScope_lease_or_qualification_issued': False,
}
contract_ref = s.write('root-calling-adoption-contract.source.json', contract)
decision_ref = s.write('source-publication-decision.json', {
    'schema': 'researchos.w09-c19-main-order-candidate-publication-decision.v1',
    'verdict': 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',
    'source_author': author,
    'source_author_backend': backend_author,
    'source_author_thread_id': thread,
    'root_thread_id': root_thread,
    'created_utc': created,
    'before_main_ref': before,
    'before_source_ref': published['before_source_ref'],
    'sourcecandidate_ref': candidate,
    'single_line_diff_ref': published['diff_ref'],
    'calling_contract_ref': contract_ref,
    'new_file_checks_ref': checks_ref,
    'input_pins_ref': pins_ref,
    'guard_ref': guard_ref,
    'actual_publication_host': publication_host,
    'new_checks_passed': 6,
    'reused_advisory_property_checks': 18,
    'reused_advisory_decision_ref': pins['advisory_decision_ref'],
    'reused_advisory_properties_ref': pins['advisory_properties_ref'],
    'old_18_controls_rerun': False,
    'non_author_independent_acceptance': False,
    'independent_review_refs': None,
    'Main_Canon_NF5_Scope_written': False,
    'actual_Go_Native_SQL_model_TP_calls': 0,
    'new_failures': [],
    'original_failure_ordinals_retained': [1158, 1159],
    'original_failure_evidence': pins['original_failure_evidence'],
    'guard_refs_acquired': 8,
    'guard_final_retained_handles_count': 0,
    'execution_grant': False,
    'formal_acceptance': False,
    'Source21_qualification': False,
    'Mode_qualification': False,
})
members = [s.pin(path) for path in sorted(D.iterdir(), key=lambda p: p.name) if path.is_file() and path.name not in ('HDF.json', 'MF.json')]
mf_ref = s.write('MF.json', {
    'schema': 'researchos.w09-c19-main-order-candidate-source-manifest.v1',
    'source_author': author,
    'source_author_thread_id': thread,
    'created_utc': created,
    'members': members,
    'member_count': len(members),
    'handoff_excluded_to_avoid_circular_hash': True,
    'external_inputs_ref': pins_ref,
    'Source21_and_current_Native_qualification': False,
    'execution_grant': False,
    'formal_acceptance': False,
})
hdf_ref = s.write('HDF.json', {
    'schema': 'researchos.w09-c19-main-order-candidate-source-hdf.v1',
    'status': 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',
    'source_author': author,
    'source_author_backend': backend_author,
    'source_author_thread_id': thread,
    'root_thread_id': root_thread,
    'created_utc': created,
    'source_namespace': str(D),
    'manifest_ref': mf_ref,
    'decision_ref': decision_ref,
    'calling_contract_ref': contract_ref,
    'before_main_ref': before,
    'before_source_ref': published['before_source_ref'],
    'sourcecandidate_ref': candidate,
    'single_line_diff_ref': published['diff_ref'],
    'new_file_checks_ref': checks_ref,
    'input_pins_ref': pins_ref,
    'guard_ref': guard_ref,
    'actual_publication_host': publication_host,
    'new_checks_passed': 6,
    'reused_advisory_property_checks': 18,
    'reused_advisory_decision_ref': pins['advisory_decision_ref'],
    'reused_advisory_properties_ref': pins['advisory_properties_ref'],
    'old_18_controls_rerun': False,
    'guard_refs_acquired': 8,
    'guard_final_retained_handles_count': 0,
    'independent_review_required': True,
    'independent_review_refs': None,
    'candidate_independently_accepted': False,
    'original_failure_ordinals_retained': [1158, 1159],
    'original_failure_evidence': pins['original_failure_evidence'],
    'new_failures': [],
    'Main_Canon_NF5_Scope_written': False,
    'actual_Go_Native_SQL_model_TP_calls': 0,
    'execution_grant': False,
    'formal_acceptance': False,
    'Source21_qualification': False,
    'Mode_qualification': False,
    'RootScope_lease_or_qualification_issued': False,
})
print(json.dumps({
    'schema': 'researchos.w09-c19-main-order-candidate-source-delivery.v1',
    'operation': 'SOURCE_CANDIDATE_PUBLICATION',
    'status': 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',
    'source_author': author,
    'source_author_backend': backend_author,
    'source_author_thread_id': thread,
    'root_thread_id': root_thread,
    'source_refs': {'hdf': hdf_ref, 'mf': mf_ref, 'calling_contract': contract_ref},
    'publication_decision_ref': decision_ref,
    'before_main_ref': before,
    'before_source_ref': published['before_source_ref'],
    'sourcecandidate_ref': candidate,
    'single_line_diff_ref': published['diff_ref'],
    'new_file_checks_ref': checks_ref,
    'guard_ref': guard_ref,
    'actual_publication_host': publication_host,
    'new_checks_passed': 6,
    'reused_advisory_property_checks': 18,
    'old_18_controls_rerun': False,
    'guard_closed': True,
    'guard_retained_handles_count': 0,
    'new_failures': [],
    'original_failure_ordinals_retained': [1158, 1159],
    'Main_Canon_NF5_Scope_written': False,
    'actual_Go_Native_SQL_model_TP_calls': 0,
    'candidate_independently_accepted': False,
    'execution_grant': False,
    'formal_acceptance': False,
    'Source21_qualification': False,
    'Mode_qualification': False,
    'STOP': True,
}, ensure_ascii=False))
