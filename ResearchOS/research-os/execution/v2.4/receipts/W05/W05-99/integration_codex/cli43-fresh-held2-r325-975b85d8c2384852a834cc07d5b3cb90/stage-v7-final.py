"""Root v7 finite scope staging only; independent code review is mandatory."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = Path(__file__).absolute().parent
UID = '71b091d20d94443bbf4e732d201eeb29'
OUT = OLD.parent / ('cli43-fresh-held2-r325-' + UID)
V7 = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/362294226719402294e4e3f5f2e5275c/review.json'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(path, relative=False):
    path = Path(path).absolute()
    data = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if relative else str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def raw(ref):
    path = Path(ref['path'])
    path = path if path.is_absolute() else ROOT / path
    data = path.read_bytes()
    need(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], 'Original input changed')
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

def invoke(label, command, env, timeout):
    write(OUT / (label + '.request.json'), {'argv': command, 'cwd': str(ROOT), 'environment': env,
        'timeout_seconds': timeout, 'automatic_retry': False, 'Windows_Job_or_OS_lifecycle_qualification': False})
    with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    write(OUT / (label + '.invocation.json'), {'actual_native_exit': result.returncode,
        'stdout_ref': pin(OUT / (label + '.stdout.raw')), 'stderr_ref': pin(OUT / (label + '.stderr.raw')),
        'automatic_retry': False, 'counter_reset': False, 'product_executed': False})
    need(result.returncode == 0, 'Metadata phase stopped: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--preparation-review-path', required=True)
parser.add_argument('--preparation-review-sha256', required=True)
args = parser.parse_args()
prep_ref = pin(args.preparation_review_path)
need(prep_ref['sha256'] == args.preparation_review_sha256, 'Explicit actual v7 review SHA')
prep = doc(args.preparation_review_path)
need(prep['reviewer'] == 'codex:/root/w05_merge_review' and prep['requested_changes'] == [] and
    prep['decision'] == 'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED', 'Independent v7 review required')
need(pin(V7 / 'handoff.json')['sha256'] == '795d8d6ec2a42011cdaa2425d028b2395f3da2f84db60027d625c93895727e2f', 'Known v7 handoff')
need(pin(V7 / 'manifest.complete.json')['sha256'] == '2ef49a19cd9d7f7f711afdb124089e547d56d9eb7775951cf197b5ed31507d15', 'Known v7 complete manifest')
for ref in doc(V7 / 'manifest.complete.json')['entries']:
    raw(ref)
before_refs = [pin(path) for path in sorted(OLD.rglob('*')) if path.is_file()]
inputs = doc(OLD / 'root-inputs.runtime-bound.json')
before = doc(OLD / 'canonical-before.json')
for entry in before['entries']:
    need((ROOT / entry['canonical_path']).read_bytes() == raw(entry['ref']), 'Current canonical four drift')
need(inputs['before'] == [324, 152, 430] and inputs['after'] == [325, 153, 442], 'Actual fixed tuple/cut')
need(not OUT.exists(), 'Fresh disjoint Root namespace')
OUT.mkdir()
(OUT / 'canonical-before').mkdir()
copies = []
for entry in before['entries']:
    copied = clone(OUT / 'canonical-before' / (Path(entry['canonical_path']).stem + '.raw'), raw(entry['ref']))
    copies.append(dict(entry, ref=copied))
inputs['canonical_before_ref'] = write(OUT / 'canonical-before.json', dict(before, entries=copies))
for key, name in [('source_inputs_ref', 'source-inputs.json'), ('failure_prefix430_ref', 'failure-prefix430.json'), ('origin_cut_ref', 'failure-origins.cut.json')]:
    inputs[key] = clone(OUT / name, raw(inputs[key]))
handoff = doc(V7 / 'handoff.json')
code = []
for ref in handoff['wrapper_refs']:
    path = OUT / Path(ref['path']).name
    clone(path, raw(ref))
    code.append(pin(path, relative=True))
for ref in [handoff['metadata_module_ref'], handoff['unchanged_refs']['binding_builder']]:
    raw(ref)
    code.append(pin(ref['path'], relative=True))
need(len(code) == 8, 'Six Root wrappers and two definitions')
inputs['metadata_code_refs_ref'] = write(OUT / 'metadata-code-refs.json', {'entries': code,
    'source_handoff_ref': pin(V7 / 'handoff.json'), 'independent_preparation_review_ref': prep_ref})
base_ref = inputs['runtime_resources_ref']
need(base_ref['sha256'] == '98b5efb1e3bfa8ab5c64a7ed3280b62ca6c856cc562e1d5ea59f89caca28d6cf', 'Original partial runtime base')
catalog = json.loads(raw(base_ref).decode('utf-8'))
need(len(catalog['files']) == 1242, 'Original runtime count')
overlay = [pin(ROOT / ref['path']) for ref in code]
old_paths = {str(Path(ref['path']).absolute()).casefold() for ref in catalog['files']}
need(all(ref['path'].casefold() not in old_paths for ref in overlay), 'Unique metadata overlay')
catalog['files'] += overlay
catalog['schema'] = 'researchos.cli43-public-runtime-resources.root-metadata-overlay.v4'
catalog['root_metadata_overlay'] = {'base_ref': base_ref, 'base_files': 1242, 'metadata_files': 8,
    'original_metadata_refs': code, 'actual_new_metadata_bytes_verified': True,
    'base_resources_rehashed_by_this_writer': False, 'OS_or_Go_resource_set_expansion': False,
    'unknown_loaded_module_policy_unchanged': True, 'complete_runtime_or_lifecycle_qualification': False}
inputs['runtime_resources_ref'] = write(OUT / 'runtime-with-root-metadata.v4.json', catalog)
inputs['run_uuid'] = UID
inputs['registration_namespace'] = OUT.relative_to(ROOT).as_posix()
inputs['controller_review_path'] = str(REVIEW)
inputs['controller_review_ref'] = None
for key in ['new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    path = Path(inputs[key])
    path = path.parent / path.name.replace('975b85d8c2384852a834cc07d5b3cb90', UID)
    need(path.parent.is_dir() and not path.exists(), 'Fresh authority/execution leaves')
    inputs[key] = str(path)
inputs['v7_binding_provenance'] = {'preparation_review_ref': prep_ref, 'v7_handoff_ref': pin(V7 / 'handoff.json'),
    'old_v2_scope_manifest_ref': pin(OLD / 'bound-scope.v2.manifest.json'), 'scope_invocation_ref_spelling': 'Root-relative'}
write(OUT / 'root-inputs.runtime-bound.json', inputs)
write(OUT / 'staging-audit.json', {'actor': 'codex:/root', 'expected_before': inputs['before'], 'expected_after': inputs['after'],
    'v7_preparation_review_ref': prep_ref, 'actual_canonical_source_writes': 0, 'formal_increment': 0})
write(OUT / 'staging.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
builder = handoff['unchanged_refs']['binding_builder']
command = [PYTHON, '-I', '-S', '-X', 'utf8', builder['path']]
for key in ['scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
        'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref']:
    command += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
command += ['--controller-review-ref', 'null']
for key in ['before', 'after', 'main_git', 'public_environment']:
    command += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
for key in ['run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
        'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    command += ['--' + key.replace('_', '-'), inputs[key]]
command += ['--output', str(OUT / 'binding.pre-review.json')]
invoke('binding-build', command, inputs['public_environment'], 60)
invoke('scope-build', [PYTHON, '-I', '-S', '-X', 'utf8', str(OUT / 'scope_builder.py'),
    '--binding-ref', json.dumps(pin(OUT / 'binding.pre-review.json'), ensure_ascii=False), '--output', str(OUT),
    '--scope-template-ref', json.dumps(inputs['scope_template_ref'], ensure_ascii=False)], inputs['public_environment'], 900)
scope_ref = pin(OUT / 'scope_registration.json')
driver = (OLD / 'root-metadata-phase.v2.py').read_bytes()
driver = driver.replace(b"SCOPE_SHA = 'ce591233d917afe8e2e16128385ca4ef0a113ab26541eaf92f6397cfa3928ca0'",
    ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii'))
for old, new in [(b'root-inputs.runtime-bound.v2.json', b'root-inputs.runtime-bound.json'),
        (b'binding.pre-review.v2.json', b'binding.pre-review.json'), (b'scope_registration.v2.json', b'scope_registration.json')]:
    need(old in driver, 'Outer driver version anchor')
    driver = driver.replace(old, new)
clone(OUT / 'root-metadata-phase.py', driver)
write(OUT / 'bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref,
    'scope_invocation_ref': pin(OUT / 'scope_registration.json', relative=True), 'v7_review_ref': prep_ref,
    'runtime_ref': inputs['runtime_resources_ref'], 'runtime_files': 1250,
    'expected_before': inputs['before'], 'expected_after': inputs['after'], 'actual_metadata_native_exits': [0, 0],
    'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0})
need(all(pin(ref['path']) == ref for ref in before_refs), 'Old namespace prefix changed')
write(OUT / 'bound-scope.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
print(json.dumps({'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'runtime_ref': inputs['runtime_resources_ref'], 'actual_registration_executed': False}, ensure_ascii=False))
