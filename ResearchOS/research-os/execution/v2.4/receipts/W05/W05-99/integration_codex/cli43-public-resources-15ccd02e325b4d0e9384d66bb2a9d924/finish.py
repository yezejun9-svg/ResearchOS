"""Seal completed resource observations; never run a candidate or write canonical state."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent

def pin(p, relative=False):
    p = Path(p).absolute()
    b = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix() if relative else str(p),
            'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def save(name, obj):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def read_verified(p, sha):
    b = Path(p).read_bytes()
    if hashlib.sha256(b).hexdigest() != sha:
        raise RuntimeError('Actual completed reference changed: ' + str(p))
    return json.loads(b.decode('utf-8'))

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode):
    raise RuntimeError('Use -I -S -X utf8')
sys.dont_write_bytecode = True
audit = read_verified(OUT / 'audit.json', '02e5f29ca636b5ac468badc24aa0e5fce27f1a9c3b0b9bee2ca2a24dbabe3823')
for r in audit['before_refs']:
    if pin(r['path']) != r:
        raise RuntimeError('Canonical/basis drift after completion')
save('completion-observation.json', {
    'schema': 'researchos.known-tool-completion-fields-transcription.v1', 'actor': 'codex:/root',
    'initial_tool_chunk': 'ec0eab', 'session_id': 33011, 'completion_tool_chunk': 'd7b58d',
    'Python_native_exit': 0, 'native_exit_basis': 'Original visible PowerShell explicit LASTEXITCODE marker PythonNativeExit=0; exit bridge present.',
    'outer_exit': None, 'outer_exit_basis': 'Final returned structured fields did not expose an exit_code; never inferred.',
    'raw_native_Python_stdout_or_stderr_artifacts': None,
    'known_fields_transcription_only': True, 'automatic_retry': False, 'counter_reset': False,
    'job_or_DLL_lifecycle_qualification': False, 'actual_cases': 'NOT_RUN', 'formal_increment': 0})
closed = [
    ('execution/v2.4/receipts/W05/W05-99/main38_closed_execution_independent_review_codex/06d85be5c79445b49fc2f27c1b8e886b/review.json', '500acdc5a0aba4b49192362432a76b26a37dc530ae595200376b9e8bae0edc06'),
    ('execution/v2.4/receipts/W05/W05-99/cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e/review.json', 'fe7d4cb67d28517c4c55ca82461c0448f791635b128020faa1278b86d971fbf8'),
    ('execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324/registration-audit.json', '94cc9fdcbae13374e96033015d184f80fbcd460edb338d6167e42fff01a15bfc'),
]
for p, sha in closed:
    read_verified(ROOT / p, sha)
save('current43-authority.json', {
    'schema': 'researchos.cli43.current-source-validation-authority.v1', 'actor': 'codex:/root',
    'source_commit': audit['source_commit'], 'current_canonical_head': audit['source_commit'],
    'source_integration_completed': True, 'unique_combined_source_paths': 43,
    'sealed_integration_refs': [pin(ROOT / p, True) for p, sha in closed],
    'current_canonical_refs': audit['before_refs'][:4], 'resource_preparation_audit_ref': pin(OUT / 'audit.json', True),
    'source_acceptance': False, 'fresh_compilation_or_cases_accepted': False, 'formal_increment': 0,
    'goal_complete': False, 'execution_authorized': False,
    'restriction': 'Actual current source identity only. A separately reviewed scope and actual canonical registration/grant remain required.'})
pending = [
    ('execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_preparation_codex/7bf10c8e8cc54412ba7bb89b53f5a622/failure-origin.e1bbac.json', '31476b8568f1e2e7b8e9b80200f7ec3c81e3e91e7d13d2c8c9060fb23b67ba34'),
    ('execution/v2.4/receipts/W13/W13-03/desktop15_source_import_suitability_independent_review_codex/d2215541c83c463db77326ffb2077dd7/failure-origin.c527ee.json', '3af61608e971242c99ec4829671157d5c0fe02072e8f0ab197c9f93d0fa58f8b'),
    ('execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39/failure-origin.8861e3.json', 'a813aefb3c674c1ed982e37a7874affb40b71828b3b0b1029647583a8d0cd501'),
    ('execution/v2.4/receipts/W05/W05-99/cli43_windows_resource_observation_codex/7a89658e87ad469dab9d17c80ed7270d/failure-origin.3409e4.json', '19982e3de25105c089c907f96caad2f970c2762e064d0dfe3b20a46b1218a256'),
    ('execution/v2.4/receipts/W13/W13-03/desktop15_root_binding_static_independent_review_codex/743aa36608ea40829475e0128ea8992e/failure-origin.a43054.json', 'c11c8407059821062a14a32d5f0fb2c50616a874750fb4856676ebe6cff75104'),
]
for p, sha in pending:
    read_verified(ROOT / p, sha)
save('postcut-pending5.json', {'actor': 'codex:/root', 'registered_origins': 430,
    'pending_refs': [pin(ROOT / p, True) for p, sha in pending], 'observed_lower_bound': 435,
    'prefix_reset': False, 'canonical_writes': 0, 'append_status': 'NOT_REGISTERED_FUTURE_ROOT_CAS_REQUIRED',
    'native_exits': [None, None, None, 1, None], 'no_trace_or_outer_exit_inference': True})
members = [pin(p, True) for p in sorted(OUT.iterdir(), key=lambda p: p.name) if p.is_file()]
save('manifest.json', {'schema': 'researchos.public-resource-preparation-manifest.v1',
    'actor': 'codex:/root', 'entries': members, 'count': len(members), 'self_excluded': True,
    'product_execution': False, 'formal_increment': 0})
print(json.dumps({'manifest_ref': pin(OUT / 'manifest.json'),
                  'authority_ref': pin(OUT / 'current43-authority.json'),
                  'pending_ref': pin(OUT / 'postcut-pending5.json')}, ensure_ascii=False))
