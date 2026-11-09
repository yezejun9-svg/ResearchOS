"""Root-owned exact frozen v2.4 persistence definition projection."""
from pathlib import Path
import copy
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
scope_path = HERE / 'source_repair_scope_codex.json'
scope = json.loads(scope_path.read_bytes())
source_path = Path(scope['projection_source']['path'])
source_raw = source_path.read_bytes()
source_hash = hashlib.sha256(source_raw).hexdigest()
assert source_hash == scope['projection_source']['sha256']
source = json.loads(source_raw)
roots = scope['projection_source']['roots']
definitions = source['$defs']

def refs(value):
    if isinstance(value, dict):
        if '$ref' in value:
            target = value['$ref']
            assert isinstance(target, str) and target.startswith('#/$defs/'), target
            name = target[len('#/$defs/'):]
            assert '/' not in name and name in definitions, target
            yield name
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)

closure = set()
pending = list(roots)
while pending:
    name = pending.pop()
    if name in closure:
        continue
    assert name in definitions
    closure.add(name)
    pending.extend(refs(definitions[name]))

projection = {
    '$schema': source['$schema'],
    '$id': 'https://researchos.invalid/persistence-v24.schema.json',
    'oneOf': [{'$ref': '#/$defs/' + name} for name in roots],
    '$defs': {name: copy.deepcopy(definitions[name]) for name in sorted(closure)},
    'x-source': {
        'package_version': '2.4.0', 'source_path': 'contracts/domain.schema.json',
        'source_sha256': source_hash, 'roots': roots,
        'derivation': 'Exact transitive $defs closure; no thresholds, properties or required fields changed.',
    },
}
target = ROOT / scope['root_owned_projection_path']
assert not target.exists()
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(projection, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
actual = json.loads(target.read_bytes())
assert actual == projection and set(actual['$defs']) == closure
assert all(actual['$defs'][name] == definitions[name] for name in closure)
record = {
    'schema': 'researchos.exact-frozen-projection.v1', 'actor': 'codex:/root',
    'scope': {'path': scope_path.relative_to(ROOT).as_posix(),
        'sha256': hashlib.sha256(scope_path.read_bytes()).hexdigest()},
    'source': {'path': str(source_path), 'sha256': source_hash},
    'projection': {'path': target.relative_to(ROOT).as_posix(),
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest()},
    'roots': roots, 'definition_closure': sorted(closure),
    'definition_count': len(closure), 'definitions_exactly_equal_frozen': True,
    'independent_architecture': {
        'path': 'execution/v2.4/receipts/W03/W03-99/independent_architecture_codex.json',
        'sha256': hashlib.sha256((HERE.parent / 'independent_architecture_codex.json').read_bytes()).hexdigest()},
    'formal_case_count_delta': 0, 'parent_accepted': False,
}
with (HERE / 'persistence_projection_generation_codex.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': 'PASS_EXACT_FROZEN_DEFINITION_PROJECTION',
    'definition_count': len(closure), 'projection_sha256': record['projection']['sha256']}))
