"""Seal only this new Source namespace after source checks pass."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def exact_ref(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and actual['bytes'] == ref['bytes']
    return actual


def save(name, value):
    path = N / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)


def main():
    assert len(sys.argv) == 1
    assert not (N / 'HDF.json').exists() and not (N / 'MF.json').exists()
    names = ('contract.json', 'prepare_root_actual.py', 'validate_root_actual.py', 'build_roster.py',
             'exact-source-roster.json', 'check_source.py', 'source-controls.json',
             'source-guard.cleanup.actual.json', 'original-failure.945.json',
             'original-failure.948.json', 'original-failure.948.patch.txt',
             'reversible-v1-to-v2.diff', 'REPORT.md', 'seal_source.py')
    members = [pin(N / name) for name in names]
    assert len(members) == len(set(x['path'] for x in members)) == 14
    controls = json.loads((N / 'source-controls.json').read_bytes())
    cleanup = json.loads((N / 'source-guard.cleanup.actual.json').read_bytes())
    contract = json.loads((N / 'contract.json').read_bytes())
    assert controls['status'] == 'PASS_SOURCE_STATIC_ONLY' and controls['count'] == 51
    assert controls['input_ref_count'] == 133 and controls['actual_test_count'] == 0
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count'] == 0
    assert contract['Root_actual_only'] is True and contract['formal_acceptance'] is False
    assert contract['expected_composed_sources'] == 63 and contract['expected_unique_test_runs'] == 13
    manifest = save('MF.json', {'schema': 'researchos.restored21-v2-root-caller-source-manifest.v2', 'members': members})
    handoff = save('HDF.json', {'schema': 'researchos.restored21-v2-root-caller-source-handoff.v2',
        'status': 'SOURCE_PREPARED_PENDING_INDEPENDENT_CALLER_REVIEW_AND_ROOT_ACTUAL',
        'manifest_ref': manifest, 'contract_ref': pin(N / 'contract.json'),
        'report_ref': pin(N / 'REPORT.md'), 'controls_ref': pin(N / 'source-controls.json'),
        'guard_cleanup_ref': pin(N / 'source-guard.cleanup.actual.json'),
        'original_failure_945_ref': pin(N / 'original-failure.945.json'),
        'original_failure_948_ref': pin(N / 'original-failure.948.json'),
        'exact_source_roster_ref': pin(N / 'exact-source-roster.json'),
        'reversible_diff_ref': pin(N / 'reversible-v1-to-v2.diff'),
        'superseded_source_handoff_ref': exact_ref(contract['superseded_caller_handoff']),
        'request_changes_review_handoff_ref': exact_ref(contract['request_changes_handoff']),
        'source_controls_pass': 51, 'input_refs': 133, 'actual_test_count': 0,
        'expected_parent_count': 9, 'expected_drift_leaf_count': 4,
        'expected_total_unique_go_runs': 13, 'composed_source_count': 63,
        'Main_or_Canon_or_old_Source_modified': False,
        'actual_Git_Go_compiler_test2json_native_SQL_product_CLI_model': False,
        'component20_plain21_session_ready21_to22': 'PENDING_ROOT_ACTUAL_PARTIAL_NATIVE_QUALIFICATION_OPEN',
        'typed_descendant_evidence': 'NOT_SELECTED_BY_NINE_PARENT_ROSTER',
        'native_qualification': 'OPEN',
        'real21_22_release_program_provenance': 'OPEN',
        'public_late_failure_no_publication': 'OPEN', 'overall20to24': 'OPEN',
        'formal_acceptance': False, 'Root_actual_only': True, 'STOP': True, 'FINAL': True})
    assert all(pin(x['path']) == x for x in members)
    print(json.dumps({'handoff_ref': handoff, 'manifest_ref': manifest}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
