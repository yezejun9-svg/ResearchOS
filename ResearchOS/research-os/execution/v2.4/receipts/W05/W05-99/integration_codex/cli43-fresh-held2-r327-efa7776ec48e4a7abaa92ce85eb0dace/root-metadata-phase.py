"""Root once-only orchestration of already reviewed metadata scripts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
BUILDER = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5/build_binding.v5.proposed.py'
SCOPE_SHA = '320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(path):
    path = Path(path).absolute()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def doc(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))

def save(name, value):
    with (OUT / name).open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

def invoke(label, argv, env, timeout):
    save(label + '.request.json', {'argv': argv, 'cwd': str(ROOT), 'environment': env,
        'timeout_seconds': timeout, 'purpose': 'Root metadata only', 'automatic_retry': False,
        'outer_subprocess_Job_or_OS_lifecycle_qualification': False})
    result = None
    error = None
    try:
        with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save(label + '.invocation.json', {'actual_native_exit': result.returncode if result else None,
            'wrapper_error': error, 'stdout_ref': pin(OUT / (label + '.stdout.raw')),
            'stderr_ref': pin(OUT / (label + '.stderr.raw')), 'automatic_retry': False,
            'counter_reset': False, 'product_cases_executed': False})
    need(result.returncode == 0, 'Metadata phase stopped: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['prepare', 'run', 'seal', 'grant'])
parser.add_argument('--review-sha256')
parser.add_argument('--registration-review-path')
args = parser.parse_args()
inputs = doc(OUT / 'root-inputs.runtime-bound.json')
scope_ref = pin(OUT / 'scope_registration.json')
scope_ref['path'] = (OUT / 'scope_registration.json').relative_to(ROOT).as_posix()
need(scope_ref['sha256'] == SCOPE_SHA, 'Full current reviewed scope')
flags = ['-I', '-S', '-X', 'utf8']
if args.phase == 'prepare':
    review_ref = pin(inputs['controller_review_path'])
    need(review_ref['sha256'] == args.review_sha256 and len(args.review_sha256) == 64, 'Explicit actual independent review SHA')
    review = doc(inputs['controller_review_path'])
    scope = doc(OUT / 'scope_registration.json')
    need(review['reviewer'] == 'codex:/root/w05_merge_review' and review['requested_changes'] == [] and
        review['decision'] == 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and review['scope_sha256'] == SCOPE_SHA, 'Actual independent scope review')
    for key, refkey in [('runner_sha256', 'runner_ref'), ('launcher_sha256', 'launcher_ref'), ('gate_sha256', 'authorization_gate_ref')]:
        need(review[key] == scope[refkey]['sha256'], 'Reviewed executable metadata pin')
    need(pin(BUILDER)['sha256'] == '179de3dc1763cdf956b08327cb8727e231a3a227b9067ee84c4fc8158c88ad5a', 'Reviewed builder')
    command = [PYTHON, *flags, str(BUILDER)]
    for key in ['scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
            'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref']:
        command += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
    command += ['--controller-review-ref', json.dumps(review_ref, ensure_ascii=False)]
    for key in ['before', 'after', 'main_git', 'public_environment']:
        command += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
    for key in ['run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
            'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
        command += ['--' + key.replace('_', '-'), inputs[key]]
    command += ['--output', str(OUT / 'binding.json')]
    invoke('binding-final', command, inputs['public_environment'], 60)
    need(doc(OUT / 'binding.json') == dict(doc(OUT / 'binding.pre-review.json'), controller_review_ref=review_ref),
        'Final binding only inserts reviewed reference')
binding_ref = pin(OUT / 'binding.json')
wrapper = OUT / ({'grant': 'grant_preflight'}.get(args.phase, args.phase) + '.py')
command = [PYTHON, *flags, str(wrapper), '--binding-ref', json.dumps(binding_ref, ensure_ascii=False), '--output', str(OUT)]
if args.phase in ('prepare', 'grant'):
    command += ['--scope-ref', json.dumps(scope_ref, ensure_ascii=False)]
if args.phase == 'run':
    need(args.registration_review_path and args.review_sha256, 'Actual independent registration review required')
    registration_ref = pin(args.registration_review_path)
    need(registration_ref['sha256'] == args.review_sha256, 'Registration review SHA')
    command += ['--review-ref', json.dumps(registration_ref, ensure_ascii=False)]
invoke('metadata-' + args.phase, command, inputs['public_environment'], 900)
manifest_name = {'prepare': 'registration-draft.manifest.json', 'run': 'registration-run-driver.manifest.json',
    'seal': 'registration-seal-driver.manifest.json', 'grant': 'grant-driver.manifest.json'}[args.phase]
save(manifest_name, {'actor': 'codex:/root', 'entries': [pin(path) for path in sorted(OUT.rglob('*'))
    if path.is_file() and path.name != manifest_name], 'self_excluded': True, 'phase': args.phase, 'formal_increment': 0})
print(json.dumps({'phase': args.phase, 'actual_metadata_native_exit': 0,
    'manifest_ref': pin(OUT / manifest_name), 'binding_ref': binding_ref, 'formal_increment': 0}, ensure_ascii=False))
