import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
old_path = OUT / 'prepare.py'
raw = old_path.read_bytes()
origin = {'origin_key': 'r316-root-preparation-schema-4410af', 'actor': 'codex:/root',
    'event_kind': 'ACTUAL_NONZERO_EXECUTION', 'actual_outer_exit': 1, 'actual_native_exit': 1,
    'native_kind': 'ROOT_PYTHON_DRAFT_PREPARATION', 'product_cases_run': 0,
    'cause': 'Draft used cases_executed; immutable v3 stopped report actual field is actual_cases. KeyError before any generated draft or canonical mutation.',
    'original_tool_ref': '4410af', 'failed_line': 85, 'exception': "KeyError: 'cases_executed'",
    'raw_file': None, 'raw_limitation': 'Original traceback retained in exec tool 4410af; command had no redirected raw file.',
    'source_ref': {'path': old_path.relative_to(Path.cwd()).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)},
    'canonical_registration_executed': False, 'count_once': True, 'counter_reset': False}
with (OUT / 'failure_origin.prepare-4410af.json').open('xb') as stream:
    stream.write((json.dumps(origin, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
source = raw.decode('utf-8')
assert source.count("stopped['cases_executed']") == 1
source = source.replace("stopped['cases_executed']", "stopped['actual_cases']")
marker = "assert len(origins) == len({row['origin_key'] for row in origins}) == 11"
assert source.count(marker) == 1
source = source.replace(marker, "raw = json.loads(read(OUT / 'failure_origin.prepare-4410af.json'))\npins['root_prepare_failure'] = pin(OUT / 'failure_origin.prepare-4410af.json')\norigins.append({**raw, 'evidence_ref': pins['root_prepare_failure'], 'original_payload': raw})\nassert len(origins) == len({row['origin_key'] for row in origins}) == 12")
source = source.replace("len(prepared['origins']) == 11", "len(prepared['origins']) == 12")
source = source.replace('404', '405').replace("'new_actual_nonzero_origins': 9", "'new_actual_nonzero_origins': 10")
source = source.replace('Old393+9 nonzero+2 qualification deviations=405', 'Old393+10 nonzero+2 qualification deviations=405')
ast.parse(source)
with (OUT / 'prepare.v2.py').open('xb') as stream:
    stream.write(source.encode('utf-8'))
print(json.dumps({'original_failure_preserved': origin['origin_key'], 'new_preparation_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(), 'actual_cases_field_readonly_confirmed': True}))
