import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
path = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_static_independent_review_codex/71ce8cd4985f4ed1bb1fb73ea21d5c78/failure-origin.036820.json'
raw = path.read_bytes()
ref = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
assert ref['sha256'] == 'b4da1dc23cf70fd9935ac59ed13315e3b3d94b2b2ef7cf3f035ed8fccb2eecdb' and ref['bytes'] == 1296
origin = json.loads(raw)
assert origin['actor'] == 'codex:/root/command_queue_impl' and origin['origin_id'] == '036820'
assert origin['actual_outer_exit'] == 1 and origin['actual_native_exit'] is None
assert origin['product_controller_helper_Go_Node_SQL_HTTP_MODEL_calls'] == origin['canonical_source_index_writes'] == 0
assert origin['original_command_retried'] is False and origin['counter_reset'] is False
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 322 and len(cp['failure_counters']) == 425
assert not any(row.get('origin_key') == 'desktop15-static-display-036820' for row in cp['failure_counters'])
pending = {'schema': 'researchos.aftercut-pending-origin-bundle.v1',
    'registered_before': [322, 150, 425], 'registration_cut_after': [323, 151, 425],
    'observed_lower_bound': 426, 'origin_refs': [ref], 'origins': [{
        'origin_key': 'desktop15-static-display-036820', 'actor': origin['actor'],
        'actual_outer_exit': 1, 'actual_native_exit': None, 'actual_native_product_exit': None,
        'product_cases_run': 0, 'cause': origin['cause'], 'evidence_ref': ref, 'original_payload': origin}],
    'next_registration': 'Root324 appends once after actual CLI source-only closure and forward head registration.',
    'counter_reset': False, 'formal_increment': 0}
encoded = (json.dumps(pending, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'postcut.pending-origins.json').open('xb') as stream:
    stream.write(encoded)
print(json.dumps({'pending_bundle_ref': {'path': (OUT / 'postcut.pending-origins.json').relative_to(ROOT).as_posix(),
    'sha256': hashlib.sha256(encoded).hexdigest(), 'bytes': len(encoded)}}))
