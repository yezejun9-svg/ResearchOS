import hashlib
import json
import sys
import types
from pathlib import Path

Q = Path(__file__).resolve().parent
G = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def main():
    links = json.loads((Q / 'old-generation-owner-links.json').read_text(encoding='utf-8'))
    closed_facts = json.loads((Q / 'closed-generation-facts.json').read_text(encoding='utf-8'))
    members = links['closure_journal_shape']['members']
    cp_path = next(path for path in members if Path(path).name == '0.after.proposed.json')
    ow_path = next(path for path in members if Path(path).name == '1.after.proposed.json')
    refs = [pin(cp_path), pin(ow_path), links['facts_ref'], links['scope_ref'], links['owner_ref'], links['worker_ref']]
    for actual, expected in zip(refs[:2], (closed_facts['closure']['checkpoint_ref'], closed_facts['closure']['ownership_ref'])):
        assert actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']
    raw = G.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm = types.ModuleType('p22_archived_guard'); gm.__file__ = str(G)
    exec(compile(raw, str(G), 'exec'), gm.__dict__)
    guard = gm.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    try:
        guard.acquire(refs)
        cp = json.loads(guard.get_buffer(cp_path)); ow = json.loads(guard.get_buffer(ow_path))
        key = 'public22_to_main23_continuation'; slice_id = 'PUBLIC22_TO_MAIN23_CONTINUATION'
        old_owner = ow['card_path_bindings']['W05-99']['subtasks'][key]
        workers = [worker for worker in cp['workers'] if worker.get('slice_id') == slice_id]
        result = save('archived-canonical-closed-generation.json', {
            'schema': 'researchos.public22-main23-archived-canonical-generation-diagnosis.v1',
            'archive_refs': refs[:2], 'old_generation_resource_refs': refs[2:],
            'checkpoint_revision': cp['revision'], 'ownership_revision': ow['revision'],
            'old_KEY': key, 'old_SLICE': slice_id, 'old_subtask': old_owner, 'old_workers': workers,
            'old_worker_count': len(workers), 'failure_counters': cp.get('failure_counters'),
            'failure_counters_digest': hashlib.sha256(json.dumps(cp.get('failure_counters'), sort_keys=True,
                                              separators=(',', ':')).encode('utf-8')).hexdigest(),
            'root_next_failure_ordinal_live': cp['work_in_progress'].get('root_next_failure_ordinal_live'),
            'old_source_projection_precondition_holds': key not in ow['card_path_bindings']['W05-99']['subtasks']
                and not any(worker.get('slice_id') == slice_id for worker in cp['workers']),
            'live_Canon_read': False, 'root_stage_called': False, 'source_projection_called': False})
        print(json.dumps({'result_ref': result, 'checkpoint_revision': cp['revision'], 'ownership_revision': ow['revision'],
            'owner_state': old_owner.get('state'), 'owner_lease_status': old_owner.get('lease_status'),
            'old_worker_states': [{'state': item.get('state'), 'lease_status': item.get('lease_status'),
                                  'slice_id': item.get('slice_id')} for item in workers],
            'registration_precondition_holds': False}, ensure_ascii=False))
    finally:
        cleanup = guard.close(); cleanup_ref = save('archived-canonical-SourceGuard.closed.json', cleanup)
        print(json.dumps({'cleanup_ref': cleanup_ref, 'closed': cleanup['closed'], 'retained_handles_count': cleanup['retained_handles_count']}, ensure_ascii=False))
    assert cleanup['closed'] and cleanup['retained_handles_count'] == 0 and cleanup['errors'] == []
    return 0

if __name__ == '__main__':
    code = main(); print('ROOT_PYTHON_EXIT=' + str(code)); sys.exit(code)
