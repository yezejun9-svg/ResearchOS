import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def write(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('new readonly observation already exists')
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(path)

try:
    facts = json.loads((HERE / 'diagnosis-facts.json').read_text(encoding='utf-8'))
    proposal_path = Path(facts['proposal_ref']['path'])
    proposal_raw = proposal_path.read_bytes()
    if hashlib.sha256(proposal_raw).hexdigest() != facts['proposal_ref']['sha256'] or len(proposal_raw) != facts['proposal_ref']['bytes']:
        raise ValueError('actual proposal observation drift')
    proposal = json.loads(proposal_raw)
    ranges = proposal['dependency_snapshot']['audit_ranges']
    shapes = Counter(tuple(sorted(row)) if type(row) is dict else (type(row).__name__,) for row in ranges)
    paths = Counter(row.get('path') if type(row) is dict else None for row in ranges)
    observation = {'schema': 'researchos.actual-audit-range-shape-observation.v1', 'proposal_ref': facts['proposal_ref'], 'actual_total_audit_ranges': len(ranges), 'actual_outside_generic_ref_count': len(facts['all_outside_dependencies']), 'first_range': ranges[0], 'key_shape_counts': [{'keys': list(keys), 'count': count} for keys, count in shapes.items()], 'path_counts': [{'path': path, 'count': count} for path, count in paths.items()], 'Source_guard_acquired_for_this_metadata_observation': False, 'prior_guard_refs_preserved': [facts['Source_guard_ref'], ref(HERE / 'completion-SourceGuard.closed.json')], 'no_failure_replay': True, 'Native_Go_SQL_model_TP_Root_stage_calls': 0}
    observation_ref = write('actual-range-shape.observation.json', observation)
    origin = {'schema': 'researchos.readonly-source-diagnostic-original.v1', 'original_ordinal': 1225, 'actual_host_chunk_id': '8d968a', 'io_ref': ref(HERE / 'original-8d968a.actual-tool-io.reencoded.json'), 'raw_ref': None, 'capture_kind': 'REENCODED_ACTUAL_TOOL_REQUEST_RESULT', 'failed_script_ref': ref(HERE / 'complete_typed_range_diagnosis.py'), 'actual_outer_exit': 1, 'actual_marked_python_exit': 1, 'actual_other_exits': None, 'Source_guard_finally_ref': ref(HERE / 'completion-SourceGuard.closed.json'), 'cause': 'Diagnostic checker assumed all snapshot audit ranges were identical to the first outside Root range; actual item schema has been read separately.', 'Root_original1224_product_failure_unchanged': True, 'prior_first_cause_and_guard_success_preserved': True, 'old_original_replayed': False}
    origin_ref = write('original1225.origin.json', origin)
    print(json.dumps({'observation_ref': observation_ref, 'observation': observation, 'original1225_ref': origin_ref}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
