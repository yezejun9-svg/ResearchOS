"""Seal this completed readonly diagnosis; do not replay any checked input."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = 'codex:/root/backup_regression_resources'
BACKEND = '/root/backup_regression_resources'
SOURCE = {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-07/w09_root_bridge.source.py', 'sha256': '16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668', 'bytes': 54832}

def reference(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def checked(ref):
    data = Path(ref['path']).read_bytes()
    if len(data) != ref['bytes'] or hashlib.sha256(data).hexdigest() != ref['sha256']:
        raise ValueError('sealed diagnosis member pin mismatch')
    return data

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('new immutable seal member already exists: ' + name)
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8'))
    return reference(path)

try:
    expected = {'path': str(HERE / 'diagnosis-facts.v2.json'), 'sha256': '1fa070348ac8ffc774e54eb7f10f406743a71d630de60d21d6a851fcdc46cbf1', 'bytes': 33800}
    facts = json.loads(checked(expected))
    if facts['actual_total_audit_ranges'] != 12 or facts['actual_outside_generic_ref_count'] != 12 or len(facts['actual_typed_ranges']) != 12:
        raise ValueError('actual diagnosis quantity differs')
    if facts['Root_stages_Native_Go_SQL_model_TP_calls'] != 0 or facts['Main_Canon_Scope_Registry_writes'] != 0 or facts['physical_failure_replayed'] is not False:
        raise ValueError('readonly diagnostic boundary differs')
    guards = []
    for ref in facts['guard_refs']:
        observed = json.loads(checked(ref))
        if observed['closed'] is not True or observed['retained_handles_count'] != 0 or observed['errors']:
            raise ValueError('existing actual diagnostic guard closure differs')
        guards.append(ref)
    io_ref = reference(HERE / 'complete.actual-tools.reencoded.json')
    io = json.loads(checked(io_ref))
    if io['capture_kind'] != 'COMPLETE_ACTUAL_TOOL_REQUEST_RESULTS_REENCODED' or len(io['tool_pairs']) != 14:
        raise ValueError('actual stored tool IO boundary differs')
    failed_pair = [p for p in io['tool_pairs'] if p['store_key'] == 'br7_activation_completion_run']
    if len(failed_pair) != 1 or failed_pair[0]['actual_result']['chunk_id'] != '8d968a' or failed_pair[0]['actual_result']['exit_code'] != 1:
        raise ValueError('original1225 actual stored tool result differs')
    api = facts['Main_api_excerpt_refs']
    md = '\n'.join([
        'BR7 activation readonly diagnosis',
        '',
        'Result: SOURCE_REVISION_REQUIRED_TYPED_AUDIT_RANGES_PROMOTED_TO_WHOLE_FILE_REFS.',
        'Root actual original1224 is preserved. No Root stage or rejection replay occurred in this diagnosis.',
        '',
        'First rejected input is /dependency_snapshot/audit_ranges/0, generic traversal index4909.',
        'Its C Root audit path is a typed range with offset0, bytes22732 and range SHA85ee364805d248e6bcf377f21ef902c143b8f9e189ff5c9f7309531339fcc273.',
        'historical_dependency_refs381..394 clones the proposal; references(cleaned)391 drops the offset.',
        'main885 passes this projected whole-file ref to physical84..96, which rejects at90 REPO_PATH_REQUIRED.',
        'Guard.acquire909 and registration912 have not been reached in the actual Root failed activation.',
        '',
        'There are exactly12 audit_ranges and12 outside generic references, all exact path/offset/bytes/sha256 typed range objects.',
        'Six original paths use backslashes and six use forward slashes for the same Windows path identity. Preserve all original strings/objects.',
        'RESOURCE_OWNER is neither the first rejected ref nor any of the12 current outside generic refs; main872..879 already validates/registers it separately.',
        '',
        'Minimal Source revision: validate then omit only cloned dependency_snapshot.audit_ranges from generic whole-file enumeration.',
        'Before omission retain canonical_identity(range.path) not in CANON, including aliases, and the original UNDECLARED_HISTORICAL_CANONICAL_REFERENCE rejection.',
        'Keep original snapshot/ranges and general references(), physical(), checked() byte semantics unchanged; no generic C exception.',
        'Retain all Root Source/role/lease/current4/archive/SS/CM/CAS/finite Scope/OwnedJob/six-route/Mode gates.',
        '',
        'Dedicated original byte-range validation remains in API _audit_range lines' + str(api['_audit_range']['start_line']) + '..' + str(api['_audit_range']['end_line']) + ' and recheck_inputs lines' + str(api['recheck_inputs']['start_line']) + '..' + str(api['recheck_inputs']['end_line']) + '.',
        'Existing BR7 snapshot314, registration539, publication715 and authority_snapshot910 recheck calls remain; registration/publication checks precede TP.',
        'Range SHA/length describes the declared bytes at offset, never the current whole growing audit file.',
        '',
        'Necessary controls are specified in diagnosis-facts.v2.json: clone-only exclusion; exact original preservation; both slash spellings; bad shape/int/SHA rejection; Canon aliases; unchanged range mutation checks; unrelated C refs; precise inverse.',
        'These are Source-author follow-up controls, NOT_RUN here; no future candidate or independent Source acceptance is fabricated.',
        '',
        'Original1225 8d968a actualouter/Python1/1 is preserved with complete arguments/result/script and actual finallyclosed0.',
        'Correction: its failed condition was raw-string path equality, not audit-range quantity. The exploratory owner-marker minimum-revision advice is superseded, with old file bytes preserved.',
        'Original6-input and5-input Guards are actualclosed with retained_handles_count0/errors[]; neither was replayed.',
        'Tool objects are complete actual stored request/results honestly REENCODED; original audit JSONL was not captured here and no live audit/Canon handle is held.',
        '',
        'formal_acceptance=false; execution_grant=false; Native/Go/SQLite/model/TP/Root stage calls0; Main/Canon/Scope/Registry writes0.',
        ''
    ])
    summary_ref = publish('report.md', md)
    decision = {
        'schema': 'researchos.w09-br7-activation-boundary-readonly-diagnosis.v1',
        'decision': facts['decision'],
        'reviewer_id': BACKEND,
        'diagnostic_actor': AUTHOR,
        'author_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'source_ref': SOURCE,
        'proposal_ref': facts['proposal_ref'],
        'facts_ref': expected,
        'report_ref': summary_ref,
        'Main_api_ref': facts['Main_api_ref'],
        'first_rejected_reference': facts['first_rejected_reference'],
        'actual_total_audit_ranges': 12,
        'actual_outside_generic_ref_count': 12,
        'all_original_typed_ranges_preserved': True,
        'minimum_revision': facts['minimum_revision'],
        'existing_dedicated_range_recheck_calls_preserved': [314, 539, 715, 910],
        'future_delta_controls_status': 'SPECIFIED_NOT_RUN_SOURCE_AUTHOR_FOLLOWUP',
        'original_root_failure': {'ordinal': 1224, 'status': 'ACTUAL_ROOT_FAILURE_PRESERVED_NOT_REPLAYED'},
        'original_diagnostic_failure_ref': facts['original1225_origin_ref'],
        'original_diagnostic_failure_correction': facts['original1225_cause_correction'],
        'actual_guard_refs': guards,
        'all_guards_closed': True,
        'retained_handles_count': 0,
        'guard_errors': [],
        'guard_prefix_replayed': False,
        'actual_tool_io_ref': io_ref,
        'original_audit_capture_ref': None,
        'original_audit_capture_status': 'NOT_CAPTURED_HERE_REENCODED_ACTUAL_OBJECTS_ONLY',
        'future_candidate_ref': None,
        'future_candidate_review_ref': None,
        'Root_stages_Native_Go_SQL_model_TP_calls': 0,
        'Main_Canon_Scope_Registry_writes': 0,
        'formal_acceptance': False,
        'execution_grant': False,
    }
    decision_ref = publish('decision.json', decision)
    members = [reference(p) for p in sorted(HERE.iterdir(), key=lambda p: p.name) if p.is_file() and p.name not in {'HDF.json', 'MF.json'}]
    mf_ref = publish('MF.json', {'schema': 'researchos.readonly-diagnosis-member-manifest.v1', 'members': members, 'member_count': len(members), 'excluded_self_descriptors': ['HDF.json', 'MF.json'], 'excluded_external_return': 'Final sealer returned tool pair cannot be embedded before it exists; Root may capture the actual ordinary FINAL afterward.'})
    hdf_ref = publish('HDF.json', {
        'schema': 'researchos.readonly-diagnosis-handoff.v1',
        'diagnostic_actor': AUTHOR,
        'backend_actor': BACKEND,
        'author_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'decision': decision['decision'],
        'MF_ref': mf_ref,
        'decision_ref': decision_ref,
        'facts_ref': expected,
        'report_ref': summary_ref,
        'source_ref': SOURCE,
        'proposal_ref': facts['proposal_ref'],
        'Main_api_ref': facts['Main_api_ref'],
        'actual_guard_refs': guards,
        'all_guards_closed': True,
        'retained_handles_count': 0,
        'guard_errors': [],
        'actual_tool_io_ref': io_ref,
        'original_diagnostic_failure_ref': facts['original1225_origin_ref'],
        'original_failures_preserved': [1224, 1225],
        'failure_count_reset': False,
        'future_source_revision_and_independent_review': 'OPEN_ROOT_ASSIGNS_SOURCE_AUTHOR_THEN_NONAUTHOR_REVIEW',
        'Root_stages_Native_Go_SQL_model_TP_calls': 0,
        'Main_Canon_Scope_Registry_writes': 0,
        'formal_acceptance': False,
        'execution_grant': False,
        'external_sealer_return_pair_status': 'NOT_YET_RETURNED_AT_SEAL_TIME_NOT_CLAIMED_EMBEDDED',
    })
    print(json.dumps({'HDF_ref': hdf_ref, 'MF_ref': mf_ref, 'decision_ref': decision_ref, 'facts_ref': expected, 'report_ref': summary_ref, 'member_count': len(members), 'actual_range_count': 12, 'actual_outside_ref_count': 12, 'all_guards_closed': True, 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
