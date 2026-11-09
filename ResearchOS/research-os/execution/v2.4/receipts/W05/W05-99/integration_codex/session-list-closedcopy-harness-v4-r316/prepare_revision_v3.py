import ast
import hashlib
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
old_path = OUT / 'prepare.v2.py'
raw = old_path.read_bytes()
origin = {'origin_key': 'r316-root-preparation-hash-literal-17e95e', 'actor': 'codex:/root',
    'event_kind': 'ACTUAL_NONZERO_EXECUTION', 'actual_outer_exit': 1, 'actual_native_exit': 1,
    'native_kind': 'ROOT_PYTHON_DRAFT_PREPARATION', 'product_cases_run': 0,
    'cause': 'Preparation revision globally replaced count404 and unintentionally altered expected immutable source SHA substring404 to405; source hash guard stopped before any canonical mutation or generated draft.',
    'original_tool_ref': '17e95e', 'failed_line': 79, 'exception': 'AssertionError: pinned source sha256 differs from accidentally rewritten literal',
    'raw_file': None, 'raw_limitation': 'Original traceback retained in exec tool 17e95e; command had no redirected raw file.',
    'source_ref': {'path': old_path.relative_to(Path.cwd()).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)},
    'canonical_registration_executed': False, 'count_once': True, 'counter_reset': False}
with (OUT / 'failure_origin.prepare-17e95e.json').open('xb') as stream:
    stream.write((json.dumps(origin, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
source = (OUT / 'prepare.py').read_text(encoding='utf-8', errors='strict')
assert source.count("stopped['cases_executed']") == 1
source = source.replace("stopped['cases_executed']", "stopped['actual_cases']")
marker = "assert len(origins) == len({row['origin_key'] for row in origins}) == 11"
assert source.count(marker) == 1
insertion = "for name in ['failure_origin.prepare-4410af.json', 'failure_origin.prepare-17e95e.json']:\n    raw = json.loads(read(OUT / name))\n    evidence = pin(OUT / name)\n    pins['root_' + name] = evidence\n    origins.append({**raw, 'evidence_ref': evidence, 'original_payload': raw})\nassert len(origins) == len({row['origin_key'] for row in origins}) == 13"
source = source.replace(marker, insertion)
source = source.replace("len(prepared['origins']) == 11", "len(prepared['origins']) == 13")
source = re.sub(r'(?<![A-Za-z0-9])404(?![A-Za-z0-9])', '406', source)
source = source.replace("'new_actual_nonzero_origins': 9", "'new_actual_nonzero_origins': 11")
source = source.replace('Old393+9 nonzero+2 qualification deviations=406', 'Old393+11 nonzero+2 qualification deviations=406')
assert "9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae" in source
for token in re.findall(r"'[0-9a-f]{64}'", (OUT / 'prepare.py').read_text(encoding='utf-8')):
    assert token in source
ast.parse(source)
with (OUT / 'prepare.v3.py').open('xb') as stream:
    stream.write(source.encode('utf-8'))
print(json.dumps({'original_failure_preserved': origin['origin_key'], 'new_preparation_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(), 'all_original_SHA_literals_unchanged': True}))
