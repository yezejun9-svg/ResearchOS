import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent

def ref(path, expected=None):
    path = Path(path).resolve()
    raw = path.read_bytes()
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result

before_ref = ref(OUT / 'postcut.pending-origins.json', '7b114f1efbf863eaaf3e99cc1421e995707f2e3115f285bbc3692aa8ea8cb8b1')
before = json.loads((ROOT / before_ref['path']).read_bytes())
failed_script_ref = ref(OUT / 'prepare-registration.py', '06cfb7218f5ed4b6ca371ef8e21c5c7ae840c2fc649617dfaa1008981b90cadb')
failure = {'schema': 'researchos.root-preparation-tool-origin.v1', 'actor': 'codex:/root',
    'tool_chunk': '48480e', 'actual_outer_exit': 1, 'actual_native_python_exit': 1,
    'native_exit_capture': 'Original PowerShell command explicitly exits with $LASTEXITCODE after pinned Python; tool exit was 1.',
    'actual_native_product_exit': None, 'failed_script_ref': failed_script_ref,
    'cause': 'Registration generator required handoff as a member of a manifest sealed before handoff was appended; KeyError in member_manifest before any generation/Git/CAS.',
    'first_error': 'KeyError handoff.json at prepare-registration.py:55 via main:96',
    'original_tool_response_locator': 'conversation tools.exec_command 48480e',
    'separate_original_native_stdout_stderr_collected': False,
    'source_FF_or_CLI_import': 0, 'canonical_writes': 0, 'product_cases_run': 0,
    'automatic_retry': False, 'counter_reset': False}
raw = (json.dumps(failure, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
failure_path = OUT / 'failure-origin.48480e.json'
with failure_path.open('xb') as stream:
    stream.write(raw)
failure_ref = ref(failure_path)
pending = dict(before)
pending.update(previous_pending_bundle_ref=before_ref, observed_lower_bound=427,
    origin_refs=before['origin_refs'] + [failure_ref], origins=before['origins'] + [{
        'origin_key': 'root-cli-registration-preparation-48480e', 'actor': 'codex:/root',
        'actual_outer_exit': 1, 'actual_native_exit': 1, 'actual_native_product_exit': None,
        'product_cases_run': 0, 'cause': failure['cause'], 'evidence_ref': failure_ref, 'original_payload': failure}])
assert len(pending['origin_refs']) == len(pending['origins']) == 2
assert pending['registered_before'] == [322, 150, 425] and pending['registration_cut_after'] == [323, 151, 425]
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 322 and len(cp['failure_counters']) == 425
encoded = (json.dumps(pending, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'postcut.pending-origins.v2.json').open('xb') as stream:
    stream.write(encoded)
print(json.dumps({'origin_ref': failure_ref, 'pending_bundle_ref': ref(OUT / 'postcut.pending-origins.v2.json')}))
