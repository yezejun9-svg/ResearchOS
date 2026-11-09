"""Prepare one export-only byte ownership fix; preserve every business assertion."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode = True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
ROOT = Path('D:/作品集/ResearchOS/research-os')
PARENT = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OLD = PARENT / 'cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39'
OUT = PARENT / 'cli43_http_bytes_ownership_preparation_codex' / uuid.uuid4().hex

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, obj):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

old_helper = OLD / 'cli43_receipt_instrumentation_test.go.txt'
old_plan = OLD / 'instrumentation-plan.json'
old_test = OLD / 'cli_sessions_test.instrumented.go.txt'
assert pin(old_helper)['sha256'] == '199d3ed6f87e33eae74046fd12cef2687d737dff74fae51b2cfa4b327774dc3d'
assert pin(old_plan)['sha256'] == 'b4e3ce1368b3ade50510505fed9aec90a61aab641aaddb767521512cca4144ff'
assert pin(old_test)['sha256'] == '37220e2a574343f7e291b41745e556d23775711d79f01cc8deb47ee1c0b19966'
before = [pin(p) for p in (old_helper, old_plan, old_test)]
old = old_helper.read_bytes()
needle = b'func cli43Bytes(b []byte) map[string]any{return map[string]any'
replacement = b'func cli43Bytes(b []byte) map[string]any{b=bytes.Clone(b);return map[string]any'
assert old.count(needle) == 1 and b' "bytes"' in old
new = old.replace(needle, replacement)
assert new.replace(replacement, needle) == old
OUT.mkdir(parents=True, exist_ok=False)
new_path = OUT / 'cli43_receipt_instrumentation_test.go.proposed.txt'
with new_path.open('xb') as f:
    f.write(new)
plan = json.loads(old_plan.read_bytes())
assert plan['additional_file_ref']['sha256'] == before[0]['sha256']
plan['additional_file_ref'] = pin(new_path)
save('instrumentation-plan.proposed.json', plan)
assert dict(plan, additional_file_ref=json.loads(old_plan.read_bytes())['additional_file_ref']) == json.loads(old_plan.read_bytes())
with (OUT / 'instrumentation.diff').open('xb') as f:
    f.write(''.join(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),
        new.decode('utf-8').splitlines(keepends=True), fromfile='original-export-only-helper',
        tofile='owned-bytes-export-only-helper')).encode('utf-8'))
after = [pin(p) for p in (old_helper, old_plan, old_test)]
assert before == after
save('static-checks.json', {
    'exact_single_function_insertion': 'b=bytes.Clone(b);', 'whole_byte_inverse_equal': True,
    'existing_bytes_import_used': True, 'plan_only_additional_file_ref_changed': True,
    'all_original_test_instrumentation_and_assertions_unchanged': True,
    'nil_and_non_nil_empty_slice_semantics': 'bytes.Clone existing standard-library implementation; future non-author source verification required',
    'non_empty_length_SHA_strict_validator_unchanged': True,
    'old_corrupt_HTTP_evidence_not_repaired': True,
    'Go_AST_compile_gofmt_SQL_HTTP_product_execution': 'NOT_RUN',
    'current43_qualification': False, 'input_drift': 0
})
save('inputs.before.json', {'files': before})
save('inputs.after.json', {'files': after})
save('handoff.json', {
    'schema': 'researchos.cli43.http-byte-ownership-preparation.v1', 'actor': 'codex:/root',
    'status': 'PREPARATION_ONLY_STOPPED', 'helper_ref': pin(new_path),
    'instrumentation_plan_ref': pin(OUT / 'instrumentation-plan.proposed.json'),
    'old_helper_ref': before[0], 'old_plan_ref': before[1], 'unchanged_instrumented_test_ref': before[2],
    'reason': 'Delayed JSON marshal retained caller write buffer after reuse. Own an immediate clone before raw/length/SHA values are constructed.',
    'changed_functions': ['cli43Bytes'], 'whole_byte_inverse_equal': True,
    'business_assertions_changed': False, 'original_bytes_and_plan_preserved': True,
    'HTTP_budget_or_timeout_changed': False, 'strict_validator_changed': False,
    'Go_SQL_SDK_MODEL_HTTP_executed': 0, 'source_acceptance': False, 'formal_increment': 0,
    'requires': ['Non-author source review including standard-library Clone nil semantics.',
        'Actual new Root scope/registration/seal/unique grant and fresh build/execution.',
        'Independent qualification of both finite case results after execution.'],
    'counter_reset': False, 'manifest': 'manifest.json self excluded'
})
save('manifest.json', {'files': [pin(p) for p in sorted(OUT.iterdir()) if p.is_file()], 'self_excluded': True})
print(json.dumps({'handoff_ref': pin(OUT / 'handoff.json'), 'manifest_ref': pin(OUT / 'manifest.json'),
    'helper_ref': pin(new_path), 'plan_ref': pin(OUT / 'instrumentation-plan.proposed.json'),
    'product_execution': 0, 'formal_increment': 0}, ensure_ascii=False))
