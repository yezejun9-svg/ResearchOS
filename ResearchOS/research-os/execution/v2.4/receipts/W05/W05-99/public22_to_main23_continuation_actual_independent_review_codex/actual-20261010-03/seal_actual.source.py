from pathlib import Path
import datetime, hashlib, json, types

R = Path(r'D:/作品集/ResearchOS/research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
SUPPORT = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
expected_support = '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
support_bytes = SUPPORT.read_bytes()
assert len(support_bytes) == 4940 and hashlib.sha256(support_bytes).hexdigest() == expected_support
s = types.ModuleType('actual_review_support')
s.__file__ = str(SUPPORT)
exec(compile(support_bytes, str(SUPPORT), 'exec'), s.__dict__)
s.D = D

# Capture actual completed review invocations, with original session bytes.
# These are observations of the independent reader, never execution authority.
pairs = [s.capture(chunk, 0, 0) for chunk in ('590125', 'b989b7', '16d113')]
input_refs = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file()]
g = s.guard()
guard_ref = None
try:
    g.acquire(input_refs)
    def own_json(name):
        return json.loads(g.get_buffer(str(D/name)))
    checks = own_json('actual-review-checks.json')
    assert checks['count'] == checks['passed'] == 30
    assert checks['failure'] is None and all(c['passed'] is True for c in checks['checks'])
    assert checks['actual_review_product_calls'] == 0
    summary = checks['summary']
    assert summary['new_child_exits'] == [0, 0, 0]
    assert summary['Root_outer_exit'] == summary['Root_Python_exit'] == 0
    assert summary['all_Jobs_closed'] is True
    assert summary['returned_state_reconstructed'] is False
    assert summary['external_stdout_truncated'] is True
    assert summary['readonly_SQLite_oracle_connections'] == 3
    assert summary['formal_acceptance'] is False and summary['parent_acceptance'] is False
    assert summary['execution_grant'] is False and summary['full20to24'] == 'OPEN'
    prior_guards = []
    for name in ('inventory-guard.closed.json', 'expansion-guard.closed.json', 'actual-review-guard.closed.json'):
        v = own_json(name)
        assert v['verification'] == 'PASSED' and v['closed'] is True
        assert v['retained_handles_count'] == 0 and v['failure'] is None and v['errors'] == []
        assert all(e['verified'] is True and e['closed'] is True for e in v['entries'])
        prior_guards.append(s.pin(D/name))
    inventory = own_json('actual-shape-inventory.json')
    expansion = own_json('actual-expansion.json')
finally:
    closed = g.close()
    guard_ref = s.write('seal-source-guard.closed.json', closed)
assert closed['verification'] == 'PASSED' and closed['closed'] is True
assert closed['retained_handles_count'] == 0 and closed['failure'] is None and closed['errors'] == []
assert all(e['verified'] is True and e['closed'] is True for e in closed['entries'])

# The complete immutable case and bounded actual host captures remain the
# authority for facts. The large truncated console output is not reconstructed.
seven_path = W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w05.gen02.seven-actual-input.root.json'
seven_ref = s.exact_ref(seven_path, '4838d3b0ecce99c69a0975643cc2116d15d33e4c7b5256ddf91a22c0c14ea829', 2419)
assert s.pin(seven_path) == seven_ref
seven = json.loads(seven_path.read_bytes())
A2 = B/'public22_to_main23_continuation_actual_independent_review_codex/actual-20261010-02'
prepared_contract_ref = s.exact_ref(A2/'actual-input-contract.json', 'f3e67121fce48c2b7135a880ad6d16b277a7a738dad05e0b835ed523af13b141', 29796)
PR4 = B/'public22_to_main23_continuation_independent_review_codex/review-20261010-04-full'
source_review_refs = [
    s.exact_ref(PR4/'HDF.json', 'ea3a33f2dba9546fbdef9376ce14a491713aab587e8ac395593980aad42af277', 14539),
    s.exact_ref(PR4/'MF.json', '7d578f9d96bf8ed19540d8ce58c259543fa740b094d9f07f4c32b54191f96fb8', 6213),
    s.exact_ref(PR4/'review-decision.json', '303a8f11bd8308e7ea0b919116163ccf3a6856771c7bade0ce90da9b3b532851', 23135),
]
reviewed_utc = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
common = {
    'review_author': 'codex:/root/full_w09_source_review',
    'backend_actor_id': '/root/full_w09_source_review',
    'actor_thread_id': '01a1215b-7210-7613-b033-756b9d553b83',
    'root_thread_id': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    'source_author': 'codex:/root/attach_restore_independent_review',
    'actual_executor': 'codex:/root',
    'independent_non_author': True,
    'reviewed_utc': reviewed_utc,
    'component': 'PUBLIC22_TO_MAIN23_CONTINUATION_ONLY',
    'generation': 'GEN02',
    'seven_actual_input_ref': seven_ref,
    'actual_input_contract_ref': prepared_contract_ref,
    'source_refs': summary['source_refs'],
    'source_review_refs': source_review_refs,
    'source_scope_ref': summary['scope_ref'],
    'actual_case_closed_ref': summary['complete_case_ref'],
    'current4_at_independent_review': summary['current_refs'],
    'actual_check_result_ref': s.pin(D/'actual-review-checks.json'),
    'independent_reader_hostpairs': pairs,
    'source_guards': prior_guards + [guard_ref],
    'all_guards_closed_zero': True,
    'retained_handles_count': 0,
    'live_Canon_handles_held': 0,
    'formal_acceptance': False,
    'parent_acceptance': False,
    'execution_grant': False,
    'formal_case_accepted_delta': 0,
    'full20to24': 'OPEN',
    'new_review_failures': [],
    'product_calls': 0,
    'old_four_children_replayed': False,
    'prior_controls_replayed': False,
    'runtime144_149_replayed': False,
    'private_key_owner_contents_read_or_hashed': False,
    'STOP': True,
}
decision = {
    'schema': 'researchos.public22-continuation-actual-independent-component-decision.v1',
    **common,
    'verdict': 'QUALIFIED_COMPONENT_ONLY',
    'status': 'ACCEPTED_COMPONENT_ONLY',
    'actual_component_review_performed': True,
    'actual_component_qualified': True,
    'new_checks': {'count': 30, 'passed': 30, 'failed': 0},
    'actual_evidence': seven,
    'actual_summary': summary,
    'qualification_scope': 'Only the actual Source04 GEN02 public22 -> Main23 upgrade, backup23 and verify23 slice. No full20to24 or formal acceptance.',
    'causal_evidence': 'Original Root preentry and initial/completion tool records, exact active registration, complete immutable case, three persisted invocation/raw/report records and independent readonly DB oracles were reviewed.',
    'Root_console_output': {'truncated': True, 'reconstructed': False, 'complete_case_is_fact_authority': True},
    'cleanup': {'actual_execute_source_guard_entries': 860, 'actual_execute_guard_closed': True, 'actual_OwnedJobs_closed': 3, 'review_guard_closed': True},
    'readonly_database_oracle': {'unique_public_database_connections': 3, 'Leaf_existing_reader': True, 'mode': 'ro/immutable/query_only', 'values_emitted': False, 'product_SQL_process_invoked': False, 'product_SQL_exit': None},
    'failure_history': {'original1025': 'FAILED_RETAINED', 'original1201': 'FAILED_RETAINED_NO_NATIVE', 'original1223_preparation': 'FAILED_RETAINED_NOT_RECOUNTED', 'reset': False, 'automatic_retry': False},
    'remaining_OPEN': ['Full 20 -> 24 programme acceptance, including the later 23 -> 24 slice and any other contract-required uncovered gates.'],
    'current4_rule': 'This review observed CP391/OW195/SS-null-revision/CM40 during the actual scope. It issues no new Scope or lease; Root remains the only Scope consumer and Canon writer.',
}
decision_ref = s.write('review-decision.json', decision)
members = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json', 'MF.json')]
mf_ref = s.write('MF.json', {
    'schema': 'researchos.public22-continuation-actual-independent-review-manifest.v1',
    'actor_id': common['review_author'], 'backend_actor_id': common['backend_actor_id'],
    'member_count': len(members), 'members': members,
    'member_scope': 'Immutable independent review files. HDF and MF are excluded to avoid self-reference.',
    'all_guards_closed_zero': True, 'execution_grant': False, 'formal_acceptance': False,
})
hdf_ref = s.write('HDF.json', {
    'schema': 'researchos.public22-continuation-actual-independent-review-handoff.v1',
    **common,
    'status': 'ACCEPTED_COMPONENT_ONLY',
    'verdict': 'QUALIFIED_COMPONENT_ONLY',
    'decision_ref': decision_ref,
    'manifest_ref': mf_ref,
    'actual_component_review_performed': True,
    'actual_component_qualified': True,
    'actual_review_checks': {'count': 30, 'passed': 30, 'failed': 0},
    'actual_child_exits': [0, 0, 0],
    'actual_Root_outer_exit': 0,
    'actual_Root_Python_exit': 0,
    'actual_SourceGuard_closed': True,
    'actual_SourceGuard_entries': 860,
    'actual_OwnedJobs_closed': 3,
    'readonly_oracles': 3,
    'product_SQL_process_invoked': False,
    'actual_returned_state_reconstructed': False,
    'actual_console_stdout_truncated': True,
    'original1025': 'FAILED_RETAINED',
    'original1201': 'FAILED_RETAINED_NO_NATIVE',
})
print(json.dumps({'HDF_ref': hdf_ref, 'MF_ref': mf_ref, 'decision_ref': decision_ref, 'member_count': len(members), 'checks': 30, 'passed': 30, 'retained_handles_count': 0, 'verdict': 'QUALIFIED_COMPONENT_ONLY', 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
