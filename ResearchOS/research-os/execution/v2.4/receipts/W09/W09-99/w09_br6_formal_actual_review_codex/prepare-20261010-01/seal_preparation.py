import hashlib
import json
import sys
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def main():
    result = json.loads((Q / 'preparation.v2.result.json').read_text(encoding='utf-8'))
    basis = json.loads((Q / 'basis.json').read_text(encoding='utf-8'))
    contract = json.loads((Q / 'input-contract.v2.json').read_text(encoding='utf-8'))
    for filename in ('preparation-SourceGuard.closed.json', 'new-source-SourceGuard.closed.json', 'revision-SourceGuard.closed.json'):
        closed = json.loads((Q / filename).read_text(encoding='utf-8'))
        assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
    assert all(row['result'] in ('PASS', 'EXPECTED_REJECTION') for row in
               json.loads((Q / 'new-pure-controls.json').read_text(encoding='utf-8'))['checks'])
    decision = {
        'schema': 'researchos.w09-br6-formal-actual-review-preparation-decision.v1',
        'decision': 'PREPARED_SOURCE_ONLY_WAITING_ACTUAL_SIX_CONSUMERS_AND_CONTEXT',
        'author_id': 'codex:/root/backup_regression_resources', 'backend_actor': '/root/backup_regression_resources',
        'author_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'product_Source_author': '/root/full_w09_source_review', 'executor': 'codex:/root', 'assembler': 'codex:/root',
        'caller_ref': result['caller_ref'], 'contract_ref': result['contract_ref'],
        'preparation_result_ref': pin(Q / 'preparation.v2.result.json'),
        'existing_six_Mode_refs': [row['mode_ref'] for row in basis['six_Mode_refs']],
        'route_Mode_bindings': basis['six_Mode_refs'],
        'required_review_schema': 'researchos.w09.independent-review.v1',
        'verdict_ids': contract['verdict_ids'],
        'GLOBAL_documents': {'C19': sorted(contract['GLOBAL']['each_case_types']),
                             'A06': sorted(contract['GLOBAL']['each_case_types'])},
        'future_input_template_ref': pin(Q / 'future-input.OPEN.json'),
        'future_actual_review_ref': None, 'future_Root_scope_grant': None,
        'future_Root_issuance_ref': None, 'future_true_Final_capture_ref': None,
        'OPEN_inputs': contract['OPEN'],
        'reported_Root_propose_block': {'original_ordinal': 1208, 'host_chunk': 'aeeae7',
            'actual_outer_exit': 1, 'actual_Python_exit': 1, 'code': 'TYPE_ARRAY',
            'location': 'Main _native:642 router formal IDs',
            'source': 'Root message only; no invented raw/capture ref',
            'consumer_started': False, 'new_Scope_started': False,
            'effect': 'keep this formal branch OPEN until Root resolves current Main gate; no six formal results exist yet'},
        'Source_controls': result['Source_controls'],
        'all_Source_guards_closed': True, 'retained_handles_count': 0,
        'source_process_original_io_ref': pin(Q / 'Source-tools.original-io.REENCODED.json'),
        'raw_Source_audit_capture_ref': None,
        'Source_io_label': 'REENCODED actual stored tool requests/results; true future Root capture occurs after this Final',
        'previous_Native_and_Mode_success_replayed': 0, 'future_entry_called': False,
        'Root_stages_called': 0, 'Native_calls': 0, 'Go_calls': 0, 'SQL_calls': 0, 'model_calls': 0,
        'TP_calls': 0, 'live_Canon_handles_held': 0, 'Main_Canon_Scope_writes': 0,
        'formal_acceptance': False, 'execution_grant': False, 'Source_self_acceptance': False,
        'stop_after_delivery': True,
    }
    decision_ref = save('preparation-decision.json', decision)
    members = [pin(path) for path in sorted(Q.iterdir(), key=lambda path: path.name)
               if path.is_file() and path.name not in ('HDF.json', 'MF.json')]
    manifest_ref = save('MF.json', {'schema': 'researchos.immutable-source-preparation-manifest.v1',
        'namespace': str(Q), 'members': members, 'member_count': len(members),
        'exclusions': ['HDF.json', 'MF.json', 'external seal call/result captured by Root after final delivery'],
        'formal_acceptance': False, 'execution_grant': False})
    handoff_ref = save('HDF.json', {'schema': 'researchos.w09-br6-formal-review-preparation-handoff.v1',
        'decision': decision['decision'], 'author_id': decision['author_id'], 'backend_actor': decision['backend_actor'],
        'manifest_ref': manifest_ref, 'decision_ref': decision_ref, 'caller_ref': result['caller_ref'],
        'contract_ref': result['contract_ref'], 'future_input_template_ref': decision['future_input_template_ref'],
        'basis_ref': pin(Q / 'basis.json'), 'source_inputs': basis['source_refs'],
        'guard_refs': [pin(Q / filename) for filename in
                       ('preparation-SourceGuard.closed.json', 'new-source-SourceGuard.closed.json', 'revision-SourceGuard.closed.json')],
        'existing_six_Mode_refs': decision['existing_six_Mode_refs'],
        'formal_acceptance': False, 'execution_grant': False, 'stop_after_delivery': True})
    # Recheck complete frozen local manifest without replaying Source controls.
    for ref in members:
        assert pin(ref['path']) == ref
    print(json.dumps({'HDF_ref': handoff_ref, 'MF_ref': manifest_ref, 'decision_ref': decision_ref,
                      'caller_ref': result['caller_ref'], 'contract_ref': result['contract_ref'],
                      'members': len(members), 'all_Source_guards_closed': True,
                      'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        code = main()
    except BaseException:
        traceback.print_exc(); code = 1
    print('ROOT_PYTHON_EXIT=' + str(code))
    sys.exit(code)
