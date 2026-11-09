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
    basis = json.loads((Q / 'basis.json').read_text(encoding='utf-8'))
    w05 = basis['Root_resume']['W05']
    refs = [w05['closure_ref'], w05['old_actual_case_ref']]
    raw = G.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm = types.ModuleType('p22_old_closed_guard'); gm.__file__ = str(G)
    exec(compile(raw, str(G), 'exec'), gm.__dict__)
    guard = gm.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    try:
        guard.acquire(refs)
        closure = json.loads(guard.get_buffer(refs[0]['path']))
        state = json.loads(guard.get_buffer(refs[1]['path']))
        safe_fields = {key: value for key, value in state.items()
                       if key in {'schema', 'status', 'phase', 'calls', 'first_failure', 'secondary_errors',
                                  'source_guard_cleanup', 'closed_receipt_ref', 'actual_request_ref',
                                  'scope_ref', 'facts_ref', 'request_ref', 'registration_result_ref',
                                  'before_canonical_refs', 'original1025_result', 'old_four_children_replayed'}}
        result = save('closed-generation-facts.json', {'schema': 'researchos.public22-main23-closed-generation-facts.v1',
            'refs': refs, 'closure': closure, 'actual_state_top_fields': list(state),
            'actual_state_selected_fields': safe_fields, 'Root_resume_old_scope_state': w05['old_scope_state'],
            'private_owner_file_read_hash_copy': 0, 'live_Canon_read': False, 'product_calls': 0})
        print(json.dumps({'result_ref': result, 'closure': closure, 'actual_state_top_fields': list(state),
                          'state_safe_refs': {key: value for key, value in safe_fields.items() if key.endswith('_ref')},
                          'actual_status': state.get('status'), 'actual_phase': state.get('phase'),
                          'actual_calls_count': len(state.get('calls', [])), 'first_failure': state.get('first_failure')}, ensure_ascii=False))
    finally:
        closed = guard.close()
        close_ref = save('closed-generation-SourceGuard.closed.json', closed)
        print(json.dumps({'close_ref': close_ref, 'closed': closed['closed'], 'retained_handles_count': closed['retained_handles_count']}, ensure_ascii=False))
    assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
    return 0

if __name__ == '__main__':
    code = main(); print('ROOT_PYTHON_EXIT=' + str(code)); sys.exit(code)
