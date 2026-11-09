"""Preserve a failed metadata attempt; stage a changed, disjoint Root input once."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = Path(__file__).absolute().parent
UID = 'b2d4f748ec374f248b2a853426d35292'
OUT = OLD.parent / ('cli43-fresh-held2-r325-' + UID)
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/6270469239494b17b9fd3d239243238b/review.json'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
CANON = ['execution/v2.4/' + name + '.json' for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')]

def need(value, why):
    if not value:
        raise RuntimeError(why)

def pin(path, relative=False):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if relative else str(path),
        'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def raw(ref):
    path = Path(ref['path'])
    if not path.is_absolute():
        path = ROOT / path
    data = path.read_bytes()
    need(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], 'Original bytes changed')
    return data

def doc(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))

def write(path, value):
    with Path(path).open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(path)

def clone(path, data):
    with Path(path).open('xb') as handle:
        handle.write(data)
    return pin(path)

def run_metadata(label, argv, env, timeout):
    write(OUT / (label + '.request.json'), {'argv': argv, 'cwd': str(ROOT), 'environment': env,
        'timeout_seconds': timeout, 'automatic_retry': False, 'product_executed': False,
        'Windows_Job_or_OS_lifecycle_qualification': False})
    with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    write(OUT / (label + '.invocation.json'), {'actual_native_exit': result.returncode,
        'stdout_ref': pin(OUT / (label + '.stdout.raw')), 'stderr_ref': pin(OUT / (label + '.stderr.raw')),
        'counter_reset': False, 'automatic_retry': False, 'product_executed': False})
    need(result.returncode == 0, 'Changed metadata input failed: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
inputs = doc(OLD / 'root-inputs.runtime-bound.json')
before = doc(OLD / 'canonical-before.json')
for entry in before['entries']:
    need((ROOT / entry['canonical_path']).read_bytes() == raw(entry['ref']), 'Canonical drift after failed prepare')
failed = doc(OLD / 'failure.prepare.json')
invocation = doc(OLD / 'metadata-prepare.invocation.json')
need(invocation['actual_native_exit'] == 1 and failed['phase'] == 'prepare', 'Actual metadata failure')
need(failed['error'] == "RuntimeError('unstaged or unpinned metadata wrapper register.py')", 'Exact first cause')
origin_ref = write(OLD / 'failure-origin.23f9cc.json', {'schema': 'researchos.original-root-metadata-failure-origin.v1',
    'actor': 'codex:/root', 'first_cause_ref': pin(OLD / 'failure.prepare.json'),
    'original_first_cause': failed, 'original_native_invocation_ref': pin(OLD / 'metadata-prepare.invocation.json'),
    'original_native_stdout_ref': invocation['stdout_ref'], 'original_native_stderr_ref': invocation['stderr_ref'],
    'actual_stage_native_exit': 1, 'actual_outer_tool_exit': 1, 'actual_root_python_exit': 1,
    'original_tool_start': '98f349', 'original_tool_completion': '23f9cc',
    'original_outer_raw_files': None, 'outer_raw_limit': 'Original visible tool trace and explicit PythonNativeExit=1 marker; no standalone outer raw files',
    'target_native_calls': 0, 'actual_canonical_source_writes': 0, 'automatic_same_input_retry': False,
    'counter_reset': False, 'count_once': True, 'failure_kind': 'ROOT_METADATA_REFERENCE_SERIALIZATION_MISMATCH'})
write(OLD / 'failed-preparation-closure.json', {'actor': 'codex:/root', 'status': 'STOPPED_BEFORE_CAS_AND_RUNTIME_HELPER',
    'before': inputs['before'], 'canonical_after_refs': [pin(ROOT / name) for name in CANON],
    'canonical_drift': 0, 'first_failure_origin_ref': origin_ref, 'actual_stage_native_exit': 1,
    'actual_outer_exit': 1, 'target_calls': 0, 'grant_or_registration': False, 'formal_increment': 0,
    'counter_reset': False, 'same_input_retry': False})
write(OLD / 'failed-preparation.manifest.json', {'entries': [pin(path) for path in sorted(OLD.rglob('*'))
    if path.is_file() and path.name != 'failed-preparation.manifest.json'], 'self_excluded': True,
    'original_bound_scope_manifest_unchanged': True, 'status': 'STOPPED_NO_CAS_NO_GRANT'})

need(not OUT.exists(), 'New Root namespace must be absent')
OUT.mkdir()
(OUT / 'canonical-before').mkdir()
new_entries = []
for entry in before['entries']:
    copied = clone(OUT / 'canonical-before' / (Path(entry['canonical_path']).stem + '.raw'), raw(entry['ref']))
    new_entries.append(dict(entry, ref=copied))
inputs['canonical_before_ref'] = write(OUT / 'canonical-before.json', dict(before, entries=new_entries))
for key, name in [('source_inputs_ref', 'source-inputs.json'), ('failure_prefix430_ref', 'failure-prefix430.json')]:
    inputs[key] = clone(OUT / name, raw(inputs[key]))

codes = doc(OLD / 'metadata-code-refs.json')['entries']
normalized = []
for ref in codes:
    oldpath = Path(ref['path'])
    oldpath = oldpath if oldpath.is_absolute() else ROOT / oldpath
    if oldpath.parent == OLD:
        path = OUT / oldpath.name
        clone(path, raw(ref))
    else:
        path = oldpath
        raw(ref)
    normalized.append(pin(path, relative=True))
need(len(normalized) == 8, 'Six wrappers plus two reviewed definitions')
# The pipeline pin() serializes repository inputs as Root-relative paths.
need(all(not Path(ref['path']).is_absolute() for ref in normalized), 'Exact pipeline serialization')
inputs['metadata_code_refs_ref'] = write(OUT / 'metadata-code-refs.json', {'entries': normalized,
    'normalization': 'Root-relative path spelling only; SHA and bytes preserved',
    'original_refs_ref': pin(OLD / 'metadata-code-refs.json'), 'code_bytes_changed': 0})
prior_cut = doc(OLD / 'failure-origins.cut.json')
pending = doc(OLD / 'postcut-pending2.json')['additional_pending_refs']
origins = copy.deepcopy(prior_cut['origins'])
for ref in pending + [origin_ref]:
    origins.append({'evidence_ref': ref, 'original_payload': json.loads(raw(ref).decode('utf-8')),
        'counter_reset': False, 'automatic_same_input_retry': False,
        'classification': 'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE'})
need(len(origins) == 10 and len({item['evidence_ref']['sha256'] for item in origins}) == 10, 'Ten unique actual origins')
inputs['after'] = [325, 153, 440]
inputs['origin_cut_ref'] = write(OUT / 'failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'origins': origins, 'counter_reset': False, 'actual_registration_executed': False, 'no_inferred_native_exits': True})
inputs['run_uuid'] = UID
inputs['registration_namespace'] = OUT.relative_to(ROOT).as_posix()
inputs['controller_review_path'] = str(REVIEW)
for key in ['new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    prior_path = Path(inputs[key])
    path = prior_path.parent / prior_path.name.replace('8e28fdaa3a7244edbbd2fc72e307b689', UID)
    need(path.parent.is_dir() and not path.exists(), 'Fresh authority/execution leaf')
    inputs[key] = str(path)
inputs['controller_review_ref'] = None
inputs['changed_input_provenance'] = {'failed_namespace_manifest_ref': pin(OLD / 'failed-preparation.manifest.json'),
    'metadata_path_normalization': True, 'new_disjoint_UUID': True, 'old_input_retry': False}
write(OUT / 'root-inputs.runtime-bound.json', inputs)
write(OUT / 'staging-audit.json', {'actor': 'codex:/root', 'before': inputs['before'], 'after': inputs['after'],
    'metadata_codes': normalized, 'code_bytes_changed': 0, 'canonical_writes': 0, 'formal_increment': 0})
write(OUT / 'staging.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})

builder = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5/build_binding.v5.proposed.py'
need(pin(builder)['sha256'] == '179de3dc1763cdf956b08327cb8727e231a3a227b9067ee84c4fc8158c88ad5a', 'Reviewed builder bytes')
args = [PYTHON, '-I', '-S', '-X', 'utf8', str(builder)]
for key in ['scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
        'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref']:
    args += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
args += ['--controller-review-ref', 'null']
for key in ['before', 'after', 'main_git', 'public_environment']:
    args += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
for key in ['run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
        'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    args += ['--' + key.replace('_', '-'), inputs[key]]
args += ['--output', str(OUT / 'binding.pre-review.json')]
run_metadata('binding-build', args, inputs['public_environment'], 60)
run_metadata('scope-build', [PYTHON, '-I', '-S', '-X', 'utf8', str(OUT / 'scope_builder.py'),
    '--binding-ref', json.dumps(pin(OUT / 'binding.pre-review.json'), ensure_ascii=False), '--output', str(OUT),
    '--scope-template-ref', json.dumps(inputs['scope_template_ref'], ensure_ascii=False)], inputs['public_environment'], 900)
scope_ref = pin(OUT / 'scope_registration.json')
write(OUT / 'bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref, 'binding_ref': pin(OUT / 'binding.pre-review.json'),
    'before': inputs['before'], 'after': inputs['after'], 'actual_metadata_native_exits': [0, 0],
    'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0, 'counter_reset': False})
write(OUT / 'bound-scope.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
print(json.dumps({'root_namespace': str(OUT), 'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'failed_old_manifest_ref': pin(OLD / 'failed-preparation.manifest.json'), 'actual_registration_executed': False}, ensure_ascii=False))
