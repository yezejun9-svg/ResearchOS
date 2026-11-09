"""Seal successful independent BR8 Source review without replaying controls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_REF = {'path': str(HERE / 'review-report.json'), 'sha256': '1f4ddc03e8268a55a77931759b604787a93824606d6ec69777b98825d22991e4', 'bytes': 9645}
GUARD_REF = {'path': str(HERE / 'SourceGuard.closed.json'), 'sha256': '5369ae2cf6c2098b9b9b899f848f43daad426b3876344cbc4c55c3ee0dad3727', 'bytes': 17529}

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(reference):
    raw = Path(reference['path']).read_bytes()
    if len(raw) != reference['bytes'] or hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('sealed successful independent review pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable independent review member exists: ' + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8'))
    return ref(path)

try:
    report = json.loads(checked(REPORT_REF))
    closure = json.loads(checked(GUARD_REF))
    if len(report['checks']) != 10 or not all(item['passed'] is True for item in report['checks']) or report['findings']:
        raise ValueError('successful Source control result differs')
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('actual independent Source Guard closure differs')
    io_ref = ref(HERE / 'actual-tools.reencoded.json')
    tools = json.loads(checked(io_ref))
    actual = [item for item in tools['tool_pairs'] if item['store_key'] == 'br8_review_run']
    if len(actual) != 1 or actual[0]['actual_result']['chunk_id'] != 'b9af23' or actual[0]['actual_result']['exit_code'] != 0 or 'ROOT_PYTHON_EXIT=0' not in actual[0]['actual_result']['output']:
        raise ValueError('actual Source control invocation differs')
    decision = {
        'schema': 'researchos.w09-bridge-independent-source-review.v1',
        'reviewer_id': '/root/backup_regression_resources',
        'actor_role': 'INDEPENDENT_NON_AUTHOR_OF_REVIEWED_DELTA',
        'source_author': report['source_author'],
        'source_ref': report['source_ref'],
        'consumer_launcher_ref': report['consumer_launcher_ref'],
        'source_hdf_ref': report['source_hdf_ref'],
        'source_mf_ref': report['source_mf_ref'],
        'decision': 'ACCEPTED_SOURCE_ONLY',
        'formal_acceptance': False,
        'execution_grant': False,
        'closed_findings': [],
        'findings': [],
        'BR7_actual_original1224_preserved': True,
        'BR8_actual_activation_status': 'NOT_EXECUTED_BY_THIS_REVIEW',
        'report_ref': REPORT_REF,
        'actual_source_author_audit_ref': report['actual_source_author_audit_ref'],
        'Source_guard_ref': GUARD_REF,
        'all_guards_closed': True,
        'retained_handles_count': 0,
        'guard_errors': [],
        'new_delta_checks': 10,
        'BR8_Source_delta_checks': 8,
        'Root_role_metadata_preparation_checks': 2,
        'Root_role_metadata_preparation_ref': report['Root_role_metadata_preparation_ref'],
        'role_metadata_preparation_verdict': 'INDEPENDENT_METADATA_PREPARATION_ONLY_NO_RUNTIME_GRANT',
        'Root_role_builder_executed': False,
        'old_successful_controls_replayed': False,
        'existing_Native_and_six_Mode_replayed': False,
        'Root_stages_called': 0,
        'Main_Canon_Scope_Registry_writes': 0,
        'Native_Go_SQL_model_TP_dispatcher_calls': 0,
        'actual_control_chunk_id': 'b9af23',
        'actual_outer_exit': 0,
        'actual_python_exit': 0,
        'actual_tool_io_ref': io_ref,
        'own_original_audit_capture_ref': None,
        'own_tool_io_kind': 'COMPLETE_ACTUAL_TOOL_REQUEST_RESULTS_REENCODED',
        'future_Root_Source_review_peer_audit_ref': None,
        'future_Root_execution_grant_ref': None,
    }
    decision_ref = publish('review-decision.json', decision)
    members = [ref(path) for path in sorted(HERE.iterdir(), key=lambda path: path.name) if path.is_file() and path.name not in {'HDF.json', 'MF.json'}]
    mf_ref = publish('MF.json', {'schema': 'researchos.w09-bridge-independent-source-review-manifest.v1', 'members': members, 'member_count': len(members), 'exclusions': ['HDF.json', 'MF.json'], 'external_final_sealer_return': 'The sealer actual return does not exist before sealing. Not claimed embedded; Root may capture the true ordinary FINAL afterward.'})
    hdf_ref = publish('HDF.json', {
        'schema': 'researchos.w09-bridge-independent-source-review-handoff.v1',
        'reviewer_id': '/root/backup_regression_resources',
        'reviewer_canonical_actor': 'codex:/root/backup_regression_resources',
        'reviewer_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'source_author': report['source_author'],
        'decision': 'ACCEPTED_SOURCE_ONLY',
        'decision_ref': decision_ref,
        'manifest_ref': mf_ref,
        'report_ref': REPORT_REF,
        'source_ref': report['source_ref'],
        'consumer_launcher_ref': report['consumer_launcher_ref'],
        'source_hdf_ref': report['source_hdf_ref'],
        'source_mf_ref': report['source_mf_ref'],
        'root_calling_contract_ref': report['root_calling_contract_ref'],
        'actual_source_author_audit_ref': report['actual_source_author_audit_ref'],
        'prior_Source_review_ref': report['prior_Source_review_ref'],
        'Source_guard_ref': GUARD_REF,
        'all_guards_closed': True,
        'retained_handles_count': 0,
        'guard_errors': [],
        'actual_control_chunk_id': 'b9af23',
        'actual_outer_exit': 0,
        'actual_python_exit': 0,
        'actual_tool_io_ref': io_ref,
        'own_original_audit_capture_ref': None,
        'own_tool_io_kind': 'COMPLETE_ACTUAL_TOOL_REQUEST_RESULTS_REENCODED',
        'new_delta_checks': 10,
        'BR8_Source_delta_checks': 8,
        'Root_role_metadata_preparation_checks': 2,
        'Root_role_metadata_preparation_ref': report['Root_role_metadata_preparation_ref'],
        'role_metadata_preparation_verdict': 'INDEPENDENT_METADATA_PREPARATION_ONLY_NO_RUNTIME_GRANT',
        'Root_role_builder_executed': False,
        'old_successful_controls_replayed': False,
        'existing_Native_and_six_Mode_replayed': False,
        'live_Canon_or_audit_handles_held': 0,
        'original_failures_preserved': [1224, 1225, 1229],
        'failure_count_reset': False,
        'Root_stages_called': 0,
        'Native_Go_SQL_model_TP_dispatcher_calls': 0,
        'Main_Canon_Scope_Registry_writes': 0,
        'formal_acceptance': False,
        'execution_grant': False,
        'future_Root_Source_review_peer_audit_ref': None,
        'STOP': True,
    })
    print(json.dumps({'HDF_ref': hdf_ref, 'MF_ref': mf_ref, 'review_decision_ref': decision_ref, 'report_ref': REPORT_REF, 'Source_guard_ref': GUARD_REF, 'decision': 'ACCEPTED_SOURCE_ONLY', 'reviewer_id': '/root/backup_regression_resources', 'new_delta_checks': 10, 'role_metadata_preparation_verdict': decision['role_metadata_preparation_verdict'], 'all_guards_closed': True, 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
