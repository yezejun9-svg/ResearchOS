"""Root changed v6 metadata binding, after its independent static review."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = Path(__file__).absolute().parent
UID = '975b85d8c2384852a834cc07d5b3cb90'
OUT = OLD.parent / ('cli43-fresh-held2-r325-' + UID)
V6 = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/65d40dc010de45a3a06485b0b9a2c37b'
OLD_REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/6270469239494b17b9fd3d239243238b/review.json'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/7ef71c4ad3b14fd6a2d83ed1887894fa/review.json'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
CANON = ['execution/v2.4/' + name + '.json' for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')]

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(path, relative=False):
    path = Path(path).absolute()
    data = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if relative else str(path),
        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

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

def invoke(label, argv, env, timeout):
    write(OUT / (label + '.request.json'), {'argv': argv, 'cwd': str(ROOT), 'environment': env,
        'timeout_seconds': timeout, 'automatic_retry': False, 'product_executed': False,
        'Windows_Job_or_OS_lifecycle_qualification': False})
    with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    write(OUT / (label + '.invocation.json'), {'actual_native_exit': result.returncode,
        'stdout_ref': pin(OUT / (label + '.stdout.raw')), 'stderr_ref': pin(OUT / (label + '.stderr.raw')),
        'automatic_retry': False, 'counter_reset': False, 'product_executed': False})
    need(result.returncode == 0, 'Metadata binding stopped: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--preparation-review-path', required=True)
parser.add_argument('--preparation-review-sha256', required=True)
args = parser.parse_args()
v6_review_ref = pin(args.preparation_review_path)
need(v6_review_ref['sha256'] == args.preparation_review_sha256, 'Explicit v6 independent review SHA')
v6_review = doc(args.preparation_review_path)
need(v6_review['reviewer'] == 'codex:/root/w05_merge_review' and v6_review['requested_changes'] == [] and
    v6_review['decision'] == 'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED', 'Actual v6 independent review')
need(pin(V6 / 'handoff.json')['sha256'] == '31a99abd1fdce62aa33f46e4658727ea5e0398b597aeb7a436749f63b6f71085', 'V6 actual handoff')
need(pin(V6 / 'manifest.json')['sha256'] == 'cb98e08960285b0fafaecff858e8e0b44c96d4150313ef2a67a3b1cbb0828357', 'V6 actual manifest')
for entry in doc(V6 / 'manifest.json')['entries']:
    raw(entry)
need(pin(OLD_REVIEW)['sha256'] == '213d5c888e689fa910cbbaaa42220083322466d790875407962a7ac3be42623b', 'Old actual scope REQUEST')
old_review = doc(OLD_REVIEW)
need(old_review['decision'] == 'REQUEST_CHANGES', 'Old proposal not executable')
inputs = doc(OLD / 'root-inputs.runtime-bound.json')
before = doc(OLD / 'canonical-before.json')
for entry in before['entries']:
    need((ROOT / entry['canonical_path']).read_bytes() == raw(entry['ref']), 'Live canonical changed')
write(OLD / 'static-proposal-closure.json', {'status': 'STOPPED_STATIC_REQUEST_BEFORE_PREPARE_CAS_GRANT',
    'review_ref': pin(OLD_REVIEW), 'canonical_refs': [pin(ROOT / name) for name in CANON],
    'canonical_drift': 0, 'product_or_registration_calls': 0, 'same_input_retry': False, 'formal_increment': 0})
write(OLD / 'static-proposal.manifest.json', {'entries': [pin(path) for path in sorted(OLD.rglob('*')) if path.is_file()], 'self_excluded': True})

need(not OUT.exists(), 'New disjoint Root namespace')
OUT.mkdir()
(OUT / 'canonical-before').mkdir()
new_entries = []
for entry in before['entries']:
    ref = clone(OUT / 'canonical-before' / (Path(entry['canonical_path']).stem + '.raw'), raw(entry['ref']))
    new_entries.append(dict(entry, ref=ref))
inputs['canonical_before_ref'] = write(OUT / 'canonical-before.json', dict(before, entries=new_entries))
for key, name in [('source_inputs_ref', 'source-inputs.json'), ('failure_prefix430_ref', 'failure-prefix430.json')]:
    inputs[key] = clone(OUT / name, raw(inputs[key]))
handoff = doc(V6 / 'handoff.json')
code = []
for ref in handoff['wrapper_refs']:
    path = OUT / Path(ref['path']).name
    clone(path, raw(ref))
    code.append(pin(path, relative=True))
for ref in [handoff['metadata_module_ref'], handoff['unchanged_refs']['binding_builder']]:
    raw(ref)
    code.append(pin(ref['path'], relative=True))
need(len(code) == 8 and all(not Path(ref['path']).is_absolute() for ref in code), 'Eight canonical serialized refs')
inputs['metadata_code_refs_ref'] = write(OUT / 'metadata-code-refs.json', {'entries': code,
    'source_handoff_ref': pin(V6 / 'handoff.json'), 'independent_preparation_review_ref': v6_review_ref,
    'serialized_paths': 'Root-relative', 'runtime_paths': 'Same verified refs canonicalized to absolute by reviewed v6 runtime'})
origins = copy.deepcopy(doc(OLD / 'failure-origins.cut.json')['origins'])
new_origins = old_review['new_failure_origin_refs']
need(len(new_origins) == 1 and new_origins[0]['sha256'] == 'b7bbd04af065ae6dbd45935d9eba180e3686b7a250da7b27bcbefc86082d2c25', 'Actual extra pending origin')
for ref in new_origins:
    origins.append({'evidence_ref': ref, 'original_payload': json.loads(raw(ref).decode('utf-8')),
        'counter_reset': False, 'automatic_same_input_retry': False,
        'classification': 'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE'})
need(len(origins) == 11 and len({item['evidence_ref']['sha256'] for item in origins}) == 11, 'Eleven unique actual failure origins')
inputs['after'] = [325, 153, 441]
inputs['origin_cut_ref'] = write(OUT / 'failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'origins': origins, 'counter_reset': False, 'actual_registration_executed': False, 'no_inferred_native_exits': True})
inputs['run_uuid'] = UID
inputs['registration_namespace'] = OUT.relative_to(ROOT).as_posix()
inputs['controller_review_path'] = str(REVIEW)
inputs['controller_review_ref'] = None
for key in ['new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    path = Path(inputs[key])
    path = path.parent / path.name.replace('b2d4f748ec374f248b2a853426d35292', UID)
    need(path.parent.is_dir() and not path.exists(), 'Fresh disjoint runtime leaf')
    inputs[key] = str(path)
inputs['changed_input_provenance'] = {'previous_static_proposal_manifest_ref': pin(OLD / 'static-proposal.manifest.json'),
    'v6_handoff_ref': pin(V6 / 'handoff.json'), 'v6_independent_review_ref': v6_review_ref,
    'old_input_retry': False, 'new_disjoint_UUID': True}
write(OUT / 'root-inputs.runtime-bound.json', inputs)
write(OUT / 'staging-audit.json', {'actor': 'codex:/root', 'before': inputs['before'], 'after': inputs['after'],
    'code_refs': code, 'actual_canonical_source_writes': 0, 'formal_increment': 0})
write(OUT / 'staging.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
builder = Path(handoff['unchanged_refs']['binding_builder']['path'])
command = [PYTHON, '-I', '-S', '-X', 'utf8', str(builder)]
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
driver = (OLD / 'root-metadata-phase.py').read_bytes()
anchor = b"SCOPE_SHA = 'c04fa8a47db6b2430530f326ed50c6e27f89109462a9ecb9ee34aeb9b76c19ed'"
need(driver.count(anchor) == 1, 'Exact Root outer metadata driver anchor')
clone(OUT / 'root-metadata-phase.py', driver.replace(anchor, ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii')))
write(OUT / 'bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref, 'binding_ref': pin(OUT / 'binding.pre-review.json'),
    'expected_before': inputs['before'], 'expected_after': inputs['after'], 'v6_independent_review_ref': v6_review_ref,
    'actual_metadata_native_exits': [0, 0], 'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0})
write(OUT / 'bound-scope.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
print(json.dumps({'root_namespace': str(OUT), 'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'actual_registration_executed': False, 'proposed_after': inputs['after']}, ensure_ascii=False))
