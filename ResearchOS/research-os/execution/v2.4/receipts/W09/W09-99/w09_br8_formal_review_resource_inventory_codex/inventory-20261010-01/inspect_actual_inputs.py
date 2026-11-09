"""Inspect only frozen actual input shapes; no Main or review function calls."""
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
RUN = R / 'execution/v2.4/receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
INPUTS = {
    'assemble': {'path': str(RUN / 'assemble-259182b5a7584e23bc58a273088e06cd/result.json'), 'sha256': 'f4521b817ea5f1a0e3890ef5e7b8379a447c9112cba02bd9ae13c1926708de30', 'bytes': 2803360},
    'consume': {'path': str(RUN / 'consume-fb16497eef2f43c2858a3e00df3ba31f/result.json'), 'sha256': '02ebf5113249e0e0d74ad425be3f78e5898826da95ebe41f21ef86f77d8008f0', 'bytes': 20196},
    'proposal': {'path': str(RUN / 'propose-e1111124d5e54bfc810d9ebe1d167664/result.json'), 'sha256': '8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f', 'bytes': 2047990},
    'v4_contract': {'path': str(R / 'execution/v2.4/receipts/W09/W09-99/w09_br8_formal_actual_review_codex/prepare-20261010-01/input-contract.json'), 'sha256': 'f332836db8cfd6cf19e7b6b427cc059843e652820b74d95519085ff9f9811ecb', 'bytes': 22062},
}
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(item):
    raw = Path(item['path']).read_bytes()
    if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('actual input pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('readonly actual shape member exists: ' + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(path)

guard = None
error = None
shape = {}
try:
    module = types.ModuleType('actual_resource_inventory_inspection_guard')
    module.__file__ = GUARD_REF['path']
    sys.modules[module.__name__] = module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), module.__dict__)
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire([*INPUTS.values(), GUARD_REF])
    docs = {key: json.loads(bytes(guard.get_buffer(item['path']))) for key, item in INPUTS.items()}
    assemble, consume, proposal = (docs[key] for key in ('assemble', 'consume', 'proposal'))
    shape = {'input_refs': INPUTS, 'assemble_keys': list(assemble), 'assemble_schema': assemble.get('schema'), 'assemble_context_ref': assemble.get('context_ref'), 'assemble_snapshot_keys': list(assemble.get('dependency_snapshot', {})), 'assemble_snapshot_files_count': len(assemble.get('dependency_snapshot', {}).get('files', {})), 'assemble_inventory_count': len(assemble.get('dependency_snapshot', {}).get('inventories', [])), 'assemble_audit_ranges_count': len(assemble.get('dependency_snapshot', {}).get('audit_ranges', [])), 'consume_keys': list(consume), 'consume_schema': consume.get('schema'), 'consume_registered_count': len(consume.get('registered_commands', [])), 'consume_processes_count': len(consume.get('processes', [])), 'first_consumer_process_keys': list(consume['processes'][0]) if consume.get('processes') else [], 'proposal_keys': list(proposal), 'proposal_reference_fields': {key: value for key, value in proposal.items() if type(value) is dict and set(value) in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'})}, 'Source_only': True, 'actual_review_called': False, 'product_calls': 0}
except BaseException as failure:
    error = {'exception': repr(failure), 'traceback': traceback.format_exc()}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('shape-SourceGuard.closed.json', closure)
    if error is not None:
        publish('shape.failure.json', {'error': error, 'Source_guard_ref': closure_ref})

if error is not None:
    print(json.dumps({'error': error, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('actual input inspection Source guard not closed')
shape['Source_guard_ref'] = closure_ref
shape_ref = publish('actual-input-shapes.json', shape)
print(json.dumps({'shape_ref': shape_ref, **shape}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
