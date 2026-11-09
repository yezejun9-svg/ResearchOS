"""Publish only the already successful independent BR7 Source delta review."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable review member already exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

def main():
    facts = load('review-facts.json')
    controls = load('delta-review-controls.json')
    closure = load('SourceGuard.closed.json')
    if controls['count'] != 7 or controls['passed'] != 7 or any(row['passed'] is not True for row in controls['controls']):
        raise ValueError('independent delta controls have not all passed')
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('independent input guard remains open')
    report = {
        'schema': 'researchos.w09-bridge-independent-source-review-report.v1',
        'reviewer_id': '/root/backup_regression_resources',
        'reviewer_canonical_actor': 'codex:/root/backup_regression_resources',
        'reviewer_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'source_author': '/root/full_w09_source_review', 'executor': '/root',
        'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'generation': facts['generation'],
        'scope': 'BR7 delta only; two bindings and new actual Main pin; no old successful controls or product runs replayed',
        'source_ref': facts['source_ref'], 'consumer_launcher_ref': facts['consumer_launcher_ref'],
        'source_hdf_ref': facts['source_hdf_ref'], 'source_mf_ref': facts['source_mf_ref'],
        'root_calling_contract_ref': facts['root_calling_contract_ref'],
        'Main_required_ref': facts['Main_required_ref'],
        'base_accepted_review_ref': facts['base_accepted_review_ref'],
        'actual_source_author_audit_ref': facts['actual_source_author_audit_ref'],
        'actual_source_author_raw_ref': facts['actual_source_author_raw_ref'],
        'controls_ref': ref(HERE / 'delta-review-controls.json'), 'new_checks': 7,
        'guard_ref': ref(HERE / 'SourceGuard.closed.json'), 'held_input_refs': facts['held_input_refs'],
        'guard_closed': True, 'retained_handles_count': 0,
        'business_functions_changed': [], 'exact_full_byte_inverse': True,
        'inverse_restored_sha256': facts['inverse_restored_sha256'],
        'launcher_byte_identical': True, 'old_Main_SHA_or_bytes_rejected': True,
        'old_generation_and_source_rejected': True,
        'strict_Source_review_field_bindings': ['reviewer_id', 'source_ref', 'consumer_launcher_ref', 'source_hdf_ref', 'source_mf_ref'],
        'Root_preconditions': [
            'Use exact BR7 source/launcher/HDF/MF and this non-author review decision.',
            'Capture this true backend FINAL only after delivery, then provide existing Main actual-role audit proof for raw reviewer /root/backup_regression_resources.',
            'Issue a fresh generation-07 proposal and finite Scope using actual dynamic current4 and unchanged Root current4 CAS/owner/lease gates.',
            'Run all six current CM40 routes after legal activation; prior Native/six Modes are immutable resources, not formal consumer receipts.',
            'Keep controlled common TEMP/TMP physical C parent and existing OwnedJob/resource closure requirements.',
            'Future execute requires Root-owned request/activation capture; this Source verdict creates no Scope or runtime grant.',
        ],
        'old_controls_replayed': False,
        'original1218_preserved': facts['original1218_refs'],
        'new_original_failures': [],
        'limitations': ['No live Root audit file was opened; only exact Root-sealed three-LF Source author capture was checked.', 'Existing Main role-audit replay and future Root Scope authority remain Root runtime obligations.', 'Pure trusted/proposal counterexamples are SYNTHETIC_SOURCE_ONLY; no products or Root stages were invoked.'],
        'findings': [], 'decision': 'ACCEPTED_SOURCE_ONLY',
        'formal_acceptance': False, 'execution_grant': False, 'parent_acceptance': False,
        'Native_Go_SQL_model_TP_Root_stage_calls': 0, 'Main_Canon_Scope_writes': 0,
    }
    report_ref = publish('review-report.json', report)
    decision = {
        'schema': 'researchos.w09-bridge-independent-source-review.v1',
        'reviewer_id': '/root/backup_regression_resources',
        'actor_role': 'INDEPENDENT_NON_AUTHOR_OF_REVIEWED_DELTA',
        'source_ref': facts['source_ref'], 'consumer_launcher_ref': facts['consumer_launcher_ref'],
        'source_hdf_ref': facts['source_hdf_ref'], 'source_mf_ref': facts['source_mf_ref'],
        'decision': 'ACCEPTED_SOURCE_ONLY', 'formal_acceptance': False, 'execution_grant': False,
        'closed_findings': [], 'findings': [], 'report_ref': report_ref,
        'actual_source_author_audit_ref': facts['actual_source_author_audit_ref'],
        'Source_guard_ref': ref(HERE / 'SourceGuard.closed.json'),
        'new_delta_checks': 7, 'old_successful_controls_replayed': False,
        'Root_stages_called': 0, 'Main_Canon_Scope_writes': 0,
    }
    decision_ref = publish('review-decision.json', decision)
    exclusions = ['HDF.json', 'MF.json', 'publication-seal.actual-tool-io.reencoded.json']
    members = [ref(path) for path in sorted(HERE.iterdir(), key=lambda p: p.name) if path.is_file() and path.name not in exclusions]
    manifest = {'schema': 'researchos.w09-bridge-independent-source-review-manifest.v1', 'reviewer_id': decision['reviewer_id'], 'members': members, 'member_count': len(members), 'exclusions': exclusions, 'exclusion_reason': 'No self-referential HDF/MF; actual seal return captured externally after publication.', 'formal_acceptance': False, 'execution_grant': False}
    manifest_ref = publish('MF.json', manifest)
    handoff = {
        'schema': 'researchos.w09-independent-source-review-handoff.v1',
        'reviewer_id': decision['reviewer_id'], 'reviewer_canonical_actor': 'codex:/root/backup_regression_resources',
        'reviewer_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084', 'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'reviewed_author': '/root/full_w09_source_review', 'decision': 'ACCEPTED_SOURCE_ONLY',
        'generation': facts['generation'], 'manifest_ref': manifest_ref,
        'decision_ref': decision_ref, 'report_ref': report_ref,
        'source_ref': facts['source_ref'], 'consumer_launcher_ref': facts['consumer_launcher_ref'],
        'source_hdf_ref': facts['source_hdf_ref'], 'source_mf_ref': facts['source_mf_ref'],
        'Main_required_ref': facts['Main_required_ref'],
        'actual_source_author_audit_ref': facts['actual_source_author_audit_ref'],
        'actual_source_author_raw_ref': facts['actual_source_author_raw_ref'],
        'controls_ref': ref(HERE / 'delta-review-controls.json'),
        'Source_guard_ref': ref(HERE / 'SourceGuard.closed.json'),
        'new_delta_checks': 7, 'held_refs': len(facts['held_input_refs']),
        'all_guards_closed': True, 'retained_handles_count': 0,
        'base_accepted_review_ref': facts['base_accepted_review_ref'],
        'original1218_preserved': facts['original1218_refs'],
        'new_original_failures': [], 'old_successful_controls_replayed': False,
        'future_actual_scope_ref': None, 'future_execution_grant_ref': None,
        'formal_acceptance': False, 'execution_grant': False, 'parent_acceptance': False,
        'Root_stages_called': 0, 'Native_Go_SQL_model_TP_calls': 0,
        'Main_Canon_Scope_writes': 0, 'STOP': True,
    }
    hdf_ref = publish('HDF.json', handoff)
    print(json.dumps({'decision': 'ACCEPTED_SOURCE_ONLY', 'reviewer_id': decision['reviewer_id'], 'HDF': hdf_ref, 'MF': manifest_ref, 'decision_ref': decision_ref, 'source_ref': facts['source_ref'], 'source_hdf_ref': facts['source_hdf_ref'], 'source_mf_ref': facts['source_mf_ref'], 'consumer_launcher_ref': facts['consumer_launcher_ref'], 'all_guards_closed': True, 'checks': 7, 'member_count': len(members)}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
