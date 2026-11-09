import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import re
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
OUT = Path(__file__).resolve().parent
original = (OUT / 'prepare.py').read_bytes()
assert hashlib.sha256(original).hexdigest() == '3bd6696705c0c6727c631cdd5c0fb9363ebd1bc31d48aea44de06074489a2e9a'
text = original.decode('utf-8')

def once(old, new):
    global text
    assert text.count(old) == 1, old
    text = text.replace(old, new, 1)

once("assert completed['scope_ref'] == scope_ref and completed['grant_ref'] == launcher_completed['grant_ref']",
    "assert completed['scope_ref'] == scope_ref\nfor authority in [completed['grant_ref'], launcher_completed['grant_ref']]:\n    assert ref(authority['path'], authority['sha256'])['bytes'] == authority['bytes']\nassert ref(completed['grant_ref']['path']) == ref(launcher_completed['grant_ref']['path'])")
once("assert len({row['origin_key'] for row in origins}) == 2", """root_origin_ref = ref(OUT / 'failure-origin.d6c6f9.json', 'f3b914c3ca9ba9483c93d46a820f5c53fc93fca2fad12b3d89bb099477746f24')
root_origin = doc(root_origin_ref)
assert root_origin['actual_outer_exit'] == root_origin['actual_native_python_exit'] == 1
origins.append({'origin_key': 'root-after-main38-preparation-d6c6f9', 'actor': 'codex:/root',
    'actual_outer_exit': 1, 'actual_native_exit': 1, 'actual_native_product_exit': None,
    'event_kind': 'PREPARATION_ONLY_ACTUAL_NONZERO', 'cause': root_origin['cause'],
    'evidence_ref': root_origin_ref, 'original_payload': root_origin, 'product_cases_run': 0})
pins['root_post_integration_preparation_origin'] = root_origin_ref
assert len({row['origin_key'] for row in origins}) == 3""")
once("len(prepared['origins']) == 2", "len(prepared['origins']) == 3")
once("'new_actual_nonzero_origins': 2", "'new_actual_nonzero_origins': 3")
once('TWO_PENDING_DIAGNOSTICS_APPENDED', 'TWO_PENDING_AND_ONE_ROOT_PREPARATION_DIAGNOSTICS_APPENDED')
once('Preserve all424 failures', 'Preserve all425 failures')
text, count = re.subn(r'(?<![A-Za-z0-9])424(?![A-Za-z0-9])', '425', text)
assert count == 13, count
old_hashes = set(re.findall(r'\b[0-9a-f]{64}\b', original.decode('utf-8')))
new_hashes = set(re.findall(r'\b[0-9a-f]{64}\b', text))
assert old_hashes.issubset(new_hashes)
raw = text.encode('utf-8')
ast.parse(raw, filename='prepare.v2.py')
with (OUT / 'prepare.v2.py').open('xb') as stream:
    stream.write(raw)
audit = {'old_sha256': hashlib.sha256(original).hexdigest(), 'old_bytes': len(original),
    'new_sha256': hashlib.sha256(raw).hexdigest(), 'new_bytes': len(raw),
    'original_failed_draft_preserved': (OUT / 'prepare.py').read_bytes() == original,
    'grant_comparison': 'actual canonical path plus matching original SHA and bytes; original refs retained',
    'new_failure_origin_added': 'd6c6f9', 'expected_before': [321, 149, 422], 'expected_after': [322, 150, 425],
    'new_origin_count': 3, 'all_original64hex_literals_preserved': True,
    'source_FF_retry': False, 'counter_reset': False, 'formal_increment': 0}
with (OUT / 'prepare-derivation-audit.json').open('xb') as stream:
    stream.write((json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps(audit))
