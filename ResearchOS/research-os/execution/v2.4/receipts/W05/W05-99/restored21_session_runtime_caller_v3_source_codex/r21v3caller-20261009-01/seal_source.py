"""Seal the v3 Source-only caller after all in-memory controls pass."""
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def exact(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and actual['bytes'] == ref['bytes']
    return actual


def save(name, value):
    path = N / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)


def main():
    assert len(sys.argv) == 1 and not (N / 'MF.json').exists() and not (N / 'HDF.json').exists()
    contract = json.loads((N / 'contract.json').read_bytes())
    checks = json.loads((N / 'source-controls.json').read_bytes())
    cleanup = json.loads((N / 'source-guard.cleanup.actual.json').read_bytes())
    failed_cleanup = json.loads((N / 'source-guard.cleanup.failed-950.json').read_bytes())
    failure = json.loads((N / 'original-failure.950.json').read_bytes())
    inverse = json.loads((N / 'byte-inverse.json').read_bytes())
    assert checks['status'] == 'PASS_SOURCE_ONLY' and checks['count'] == 21 and checks['input_refs'] == 32
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count'] == 0
    assert failed_cleanup['closed'] and not failed_cleanup['errors'] and failed_cleanup['retained_handles_count'] == 0
    assert failure['ordinal_assigned_by_root'] == 950 and failure['source_python_exit'] == 1
    assert failure['tools_exec_command_result']['exit_code'] is None
    assert contract['expected_composed_sources'] == 63 and contract['expected_unique_test_runs'] == 13
    assert contract['Root_actual_only'] is True and contract['formal_acceptance'] is False
    assert not Path(contract['isolation_output']).exists() and not Path(contract['validation_output']).exists()
    assert len(inverse['files']) == 3 and inverse['reconstruction_verified'] is True
    old = Path(contract['v2_source_handoff']['path']).parent
    for entry in inverse['files']:
        prior = (old / entry['name']).read_bytes()
        current = (N / entry['name']).read_bytes()
        assert base64.b64decode(entry['v2_original_bytes_base64']) == prior
        assert len(prior) == entry['v2_bytes'] and hashlib.sha256(prior).hexdigest() == entry['v2_sha256']
        assert len(current) == entry['v3_bytes'] and hashlib.sha256(current).hexdigest() == entry['v3_sha256']
    prior_handoff = exact(contract['v2_source_handoff'])
    prior_manifest = exact(contract['v2_source_manifest'])
    review_handoff = exact(contract['v2_review_handoff'])
    review_manifest = exact(contract['v2_review_manifest'])
    names = ('contract.json', 'prepare_root_actual.py', 'validate_root_actual.py', 'check_v3_source.py',
             'source-controls.json', 'source-guard.cleanup.actual.json', 'source-guard.cleanup.failed-950.json',
             'original-failure.950.json', 'reversible-v2-to-v3.diff', 'byte-inverse.json',
             'REPORT.md', 'seal_source.py')
    members = [pin(N / name) for name in names]
    assert len(members) == len(set(item['path'] for item in members)) == 12
    manifest = save('MF.json', {'schema': 'researchos.a21-v3-caller-source-manifest.v1',
        'members': members, 'v2_source_handoff_ref': prior_handoff,
        'v2_source_manifest_ref': prior_manifest, 'v2_review_handoff_ref': review_handoff,
        'v2_review_manifest_ref': review_manifest})
    handoff = save('HDF.json', {'schema': 'researchos.a21-v3-caller-source-handoff.v1',
        'status': 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL',
        'manifest_ref': manifest, 'contract_ref': pin(N / 'contract.json'),
        'report_ref': pin(N / 'REPORT.md'), 'controls_ref': pin(N / 'source-controls.json'),
        'guard_cleanup_ref': pin(N / 'source-guard.cleanup.actual.json'),
        'original_failure_950_ref': pin(N / 'original-failure.950.json'),
        'failed_run_guard_cleanup_ref': pin(N / 'source-guard.cleanup.failed-950.json'),
        'reversible_diff_ref': pin(N / 'reversible-v2-to-v3.diff'),
        'byte_inverse_ref': pin(N / 'byte-inverse.json'),
        'v2_source_handoff_ref': prior_handoff, 'v2_source_manifest_ref': prior_manifest,
        'v2_review_handoff_ref': review_handoff, 'v2_review_manifest_ref': review_manifest,
        'source_checks_pass': 21, 'held_inputs': 32, 'actual_test_count': 0,
        'expected_composed_sources': 63, 'expected_parent_count': 9,
        'expected_drift_leaves': 4, 'expected_unique_test_runs': 13,
        'future_development_test_success': 'PARTIAL_NATIVE_QUALIFICATION_OPEN',
        'native_qualification': 'OPEN', 'real_21_22_release_program_provenance': 'OPEN',
        'overall20to24': 'OPEN', 'Main_Canon_v1_v2_modified': False,
        'actual_Root_Git_Go_SQL_native_CLI_model': False,
        'formal_acceptance': False, 'STOP': True, 'FINAL': True})
    assert all(pin(item['path']) == item for item in members)
    print(json.dumps({'handoff_ref': handoff, 'manifest_ref': manifest}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
