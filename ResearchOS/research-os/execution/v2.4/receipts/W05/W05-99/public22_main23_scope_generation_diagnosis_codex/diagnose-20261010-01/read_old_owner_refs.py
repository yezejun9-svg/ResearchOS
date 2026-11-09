import hashlib
import json
import sys
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

def read(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and actual['bytes'] == ref['bytes']
    return json.loads(Path(ref['path']).read_text(encoding='utf-8'))

def main():
    old = json.loads((Q / 'closed-generation-facts.json').read_text(encoding='utf-8'))
    actual_ref = old['actual_state_selected_fields']['actual_request_ref']
    actual = read(actual_ref)
    facts = read(actual['facts_ref'])
    docs = {key: read(facts[key]) for key in ('scope_ref', 'owner_ref', 'worker_ref')}
    journal = Path(old['closure']['transaction_journal'])
    shape = {'path': str(journal), 'is_file': journal.is_file(), 'is_dir': journal.is_dir()}
    if journal.is_dir():
        shape['members'] = [str(path) for path in journal.iterdir() if path.is_file()]
    if journal.is_file():
        shape['journal_ref'] = pin(journal)
        shape['journal'] = json.loads(journal.read_text(encoding='utf-8'))
    result = save('old-generation-owner-links.json', {'schema': 'researchos.public22-main23-old-generation-owner-links.v1',
        'actual_request_ref': actual_ref, 'facts_ref': actual['facts_ref'], 'facts': facts,
        'scope_ref': facts['scope_ref'], 'owner_ref': facts['owner_ref'], 'worker_ref': facts['worker_ref'],
        'documents': docs, 'closure_journal_shape': shape, 'live_Canon_read': False, 'product_calls': 0,
        'note': 'Immutable issued owner/worker docs describe the original lease, not current authorization; closed Canon is separately recorded by Root CP386.'})
    print(json.dumps({'result_ref': result, 'old_owner': docs['owner_ref'], 'old_worker': docs['worker_ref'],
                      'journal_shape': shape}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    code = main(); print('ROOT_PYTHON_EXIT=' + str(code)); sys.exit(code)
