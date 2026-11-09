"""Root actual reviewed binding and metadata preparation, once; no CAS or grant."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
V5 = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/1bcae38e2c3a483d8a1a37602b4e6dcb/review.json'

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(path, sha):
    path = Path(path)
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == sha, 'Pinned metadata document changed')
    return json.loads(raw.decode('utf-8'))

def save(name, value):
    with (OUT / name).open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

def run_metadata(label, argv, environment, timeout):
    save(label + '.request.json', {'argv': argv, 'cwd': str(ROOT), 'environment': environment,
        'timeout_seconds': timeout, 'automatic_retry': False, 'purpose': 'Metadata preparation only',
        'Windows_Job_or_OS_lifecycle_qualification': False})
    result = None
    error = None
    try:
        with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
            result = subprocess.run(argv, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save(label + '.invocation.json', {'actual_native_exit': result.returncode if result else None,
            'wrapper_error': error, 'stdout_ref': pin(OUT / (label + '.stdout.raw')),
            'stderr_ref': pin(OUT / (label + '.stderr.raw')), 'automatic_retry': False,
            'counter_reset': False, 'actual_product_execution': False})
    need(result.returncode == 0, 'Metadata phase failed: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
inputs = checked(OUT / 'root-inputs.runtime-bound.json', pin(OUT / 'root-inputs.runtime-bound.json')['sha256'])
review = checked(REVIEW, '3ec51876fcc1fe29da2c729350093474cd6f1cc20be22d1aa358acba76e8eebe')
need(review['decision'] == 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and review['requested_changes'] == [], 'Actual scope review required')
scope_ref = pin(OUT / 'scope_registration.json')
need(scope_ref['sha256'] == '4e93937bed5ad9ab68c0b89f9db378b8b70e2da32437ebd01f6e93c7408c94a4', 'Actual reviewed full scope')

# This failed locator is outside the immutable seven-origin registration cut.
save('failure-origin.879f01.json', {'actor': 'codex:/root', 'tool_call_id': '879f01',
    'classification': 'READONLY_METADATA_LOCATOR_WRONG_RECEIPT_PARENT',
    'original_tool_fields': {'chunk_id': '879f01', 'wall_time_seconds': 0.6703002,
        'exit_code': 1, 'original_token_count': 103,
        'output': "Get-Content: \r\nLine |\r\n   2 |  Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2. …\r\n     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n     | Cannot find path 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/integration_codex/cli43-fresh-held2-r325-8e28fdaa3a7244edbbd2fc72e307b689/root-inputs.runtime-bound.json' because it does not exist.\r\n"},
    'actual_native_exit': None, 'native_exit_reason': 'No separately observed native process exit field',
    'raw_native_stdout_ref': None, 'raw_native_stderr_ref': None,
    'provenance_limit': 'Exact known structured tool fields; no reconstructed raw native stream',
    'automatic_same_input_retry': False, 'counter_reset': False, 'target_executed': False})
new_origins = [*review['new_failure_origin_refs'], pin(OUT / 'failure-origin.879f01.json')]
save('postcut-pending2.json', {'registered_before': 430, 'fixed_registration_cut_count': 7,
    'proposed_registered_after': 437, 'additional_pending_refs': new_origins,
    'additional_pending_count': 2, 'observed_total': 439, 'counter_reset': False,
    'fixed_cut_unchanged': True, 'formal_increment': 0})

builder = V5 / 'build_binding.v5.proposed.py'
need(pin(builder)['sha256'] == '179de3dc1763cdf956b08327cb8727e231a3a227b9067ee84c4fc8158c88ad5a', 'Reviewed builder SHA')
argv = [PYTHON, '-I', '-S', '-X', 'utf8', str(builder)]
for key in ['scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
        'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref']:
    argv += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
argv += ['--controller-review-ref', json.dumps(pin(REVIEW), ensure_ascii=False)]
for key in ['before', 'after', 'main_git', 'public_environment']:
    argv += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
for key in ['run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
        'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    argv += ['--' + key.replace('_', '-'), inputs[key]]
argv += ['--output', str(OUT / 'binding.json')]
run_metadata('binding-final', argv, inputs['public_environment'], 60)
final_binding = json.loads((OUT / 'binding.json').read_bytes().decode('utf-8'))
prior_binding = json.loads((OUT / 'binding.pre-review.json').read_bytes().decode('utf-8'))
expected = dict(prior_binding, controller_review_ref=pin(REVIEW))
need(final_binding == expected, 'Only the actual controller review reference may change')
run_metadata('metadata-prepare', [PYTHON, '-I', '-S', '-X', 'utf8', str(OUT / 'prepare.py'),
    '--binding-ref', json.dumps(pin(OUT / 'binding.json'), ensure_ascii=False), '--output', str(OUT),
    '--scope-ref', json.dumps(scope_ref, ensure_ascii=False)], inputs['public_environment'], 900)
save('registration-draft.manifest.json', {'actor': 'codex:/root',
    'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'registration-draft.manifest.json'],
    'self_excluded': True, 'actual_CAS_grant_product_execution': False, 'formal_increment': 0})
print(json.dumps({'binding_ref': pin(OUT / 'binding.json'), 'prepared_refs': pin(OUT / 'prepared_refs.json'),
    'audit_ref': pin(OUT / 'audit.json'), 'manifest_ref': pin(OUT / 'registration-draft.manifest.json'),
    'pending_after_cut': new_origins, 'actual_registration_executed': False}, ensure_ascii=False))
