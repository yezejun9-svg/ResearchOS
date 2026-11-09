"""Finish untouched staged inputs with a changed schema-aware continuation; no retry."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
OLD = OUT.parent / 'cli43-fresh-held2-r325-b2d4f748ec374f248b2a853426d35292'
UID = '975b85d8c2384852a834cc07d5b3cb90'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/7ef71c4ad3b14fd6a2d83ed1887894fa/review.json'
REQUEST = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/6270469239494b17b9fd3d239243238b/review.json'
PREP_REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_static_independent_review_codex/b1ec9670bbd3454dbf0b25cb336e1bbe/review.json'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(path):
    path = Path(path).absolute()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def raw(ref):
    path = Path(ref['path'])
    path = path if path.is_absolute() else ROOT / path
    data = path.read_bytes()
    need(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], 'Pinned input changed')
    return data

def doc(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))

def save(name, value):
    with (OUT / name).open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)

def invoke(label, argv, env, timeout):
    save(label + '.request.json', {'argv': argv, 'cwd': str(ROOT), 'environment': env, 'timeout_seconds': timeout,
        'product_executed': False, 'automatic_retry': False, 'Windows_Job_or_OS_lifecycle_qualification': False})
    with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    save(label + '.invocation.json', {'actual_native_exit': result.returncode,
        'stdout_ref': pin(OUT / (label + '.stdout.raw')), 'stderr_ref': pin(OUT / (label + '.stderr.raw')),
        'counter_reset': False, 'automatic_retry': False, 'product_executed': False})
    need(result.returncode == 0, 'Metadata phase stopped: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
need(not (OUT / 'scope.started.json').exists() and not (OUT / 'binding.pre-review.json').exists(), 'No previous binding/template attempt')
initial_refs = [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()]
for entry in doc(OUT / 'canonical-before.json')['entries']:
    need((ROOT / entry['canonical_path']).read_bytes() == raw(entry['ref']), 'Actual four canonical unchanged')
need(pin(REQUEST)['sha256'] == '213d5c888e689fa910cbbaaa42220083322466d790875407962a7ac3be42623b', 'Actual old REQUEST')
need(pin(PREP_REVIEW)['sha256'] == '83d8c1be4a4b6c41f671d4f875e1c7ad0836973c6848644a608fdadb3b406512', 'Actual v6 independent review')
need(doc(PREP_REVIEW)['decision'] == 'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED' and
    doc(PREP_REVIEW)['requested_changes'] == [], 'Reviewed v6')
origin = save('failure-origin.a7c53a.json', {'schema': 'researchos.original-root-metadata-failure-origin.v1',
    'actor': 'codex:/root', 'tool_chunk_id': 'a7c53a', 'actual_outer_exit': 1, 'actual_root_python_exit': 1,
    'original_program_ref': pin(OLD / 'rebind-v6-r325.py'), 'first_cause': "KeyError: 'new_failure_origin_refs'",
    'actual_review_key': 'new_failure_origins', 'original_tool_known_fields': {'chunk_id': 'a7c53a',
        'wall_time_seconds': 0.9630473, 'exit_code': 1, 'original_token_count': 101,
        'output': "Traceback (most recent call last):\r\n  File \"D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\cli43-fresh-held2-r325-b2d4f748ec374f248b2a853426d35292\\rebind-v6-r325.py\", line 112, in <module>\r\n    new_origins = old_review['new_failure_origin_refs']\r\n                  ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^\r\nKeyError: 'new_failure_origin_refs'\r\nPythonNativeExit=1\r\n"},
    'original_native_raw_files': None, 'raw_limit': 'Exact known structured combined tool output and explicit root Python exit marker',
    'actual_binding_template_helper_Git_CAS_product_calls': 0, 'counter_reset': False,
    'automatic_same_input_retry': False, 'changed_input': 'New continuation program uses actual review schema and adds first cause to twelve-origin cut'})
save('partial-staging-closure.json', {'actor': 'codex:/root', 'original_failure_ref': origin,
    'initial_staged_refs': initial_refs, 'actual_original_binding_or_template_calls': 0,
    'original_program_not_rerun': True, 'canonical_drift': 0, 'formal_increment': 0})

inputs = doc(OLD / 'root-inputs.runtime-bound.json')
inputs['canonical_before_ref'] = pin(OUT / 'canonical-before.json')
inputs['source_inputs_ref'] = pin(OUT / 'source-inputs.json')
inputs['failure_prefix430_ref'] = pin(OUT / 'failure-prefix430.json')
inputs['metadata_code_refs_ref'] = pin(OUT / 'metadata-code-refs.json')
for ref in doc(OUT / 'metadata-code-refs.json')['entries']:
    raw(ref)
origins = copy.deepcopy(doc(OLD / 'failure-origins.cut.json')['origins'])
extra = doc(REQUEST)['new_failure_origins']
need(len(extra) == 1 and extra[0]['sha256'] == 'b7bbd04af065ae6dbd45935d9eba180e3686b7a250da7b27bcbefc86082d2c25', 'Actual pending origin')
for ref in [*extra, origin]:
    origins.append({'evidence_ref': ref, 'original_payload': json.loads(raw(ref).decode('utf-8')),
        'counter_reset': False, 'automatic_same_input_retry': False,
        'classification': 'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE'})
need(len(origins) == 12 and len({row['evidence_ref']['sha256'] for row in origins}) == 12, 'Twelve unique origins')
inputs['after'] = [325, 153, 442]
inputs['origin_cut_ref'] = save('failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'origins': origins, 'counter_reset': False, 'actual_registration_executed': False, 'no_inferred_native_exits': True})
inputs['run_uuid'] = UID
inputs['registration_namespace'] = OUT.relative_to(ROOT).as_posix()
inputs['controller_review_path'] = str(REVIEW)
inputs['controller_review_ref'] = None
for key in ['new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    path = Path(inputs[key])
    path = path.parent / path.name.replace('b2d4f748ec374f248b2a853426d35292', UID)
    need(path.parent.is_dir() and not path.exists(), 'Fresh grant/execution leaf')
    inputs[key] = str(path)
inputs['changed_input_provenance'] = {'old_static_proposal_manifest_ref': pin(OLD / 'static-proposal.manifest.json'),
    'v6_independent_review_ref': pin(PREP_REVIEW), 'partial_staging_closure_ref': pin(OUT / 'partial-staging-closure.json'),
    'old_program_not_rerun': True, 'same_staged_prefix_preserved': True}
save('root-inputs.runtime-bound.json', inputs)
save('staging-audit.json', {'actor': 'codex:/root', 'expected_before': inputs['before'], 'expected_after': inputs['after'],
    'preserved_initial_refs': initial_refs, 'canonical_writes': 0, 'actual_binding_template_calls': 0, 'formal_increment': 0})
save('staging.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
builder_ref = doc(OUT / 'metadata-code-refs.json')['entries'][-1]
raw(builder_ref)
builder_path = ROOT / builder_ref['path']
command = [PYTHON, '-I', '-S', '-X', 'utf8', str(builder_path)]
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
old_driver = (OLD / 'root-metadata-phase.py').read_bytes()
anchor = b"SCOPE_SHA = 'c04fa8a47db6b2430530f326ed50c6e27f89109462a9ecb9ee34aeb9b76c19ed'"
need(old_driver.count(anchor) == 1, 'Exact outer driver anchor')
with (OUT / 'root-metadata-phase.py').open('xb') as handle:
    handle.write(old_driver.replace(anchor, ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii')))
save('bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref, 'binding_ref': pin(OUT / 'binding.pre-review.json'),
    'expected_before': inputs['before'], 'expected_after': inputs['after'], 'v6_independent_review_ref': pin(PREP_REVIEW),
    'actual_metadata_native_exits': [0, 0], 'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0})
save('bound-scope.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()], 'self_excluded': True})
need(all(pin(ref['path']) == ref for ref in initial_refs), 'Original staged prefix changed')
print(json.dumps({'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'after': inputs['after'], 'original_failure_ref': origin, 'actual_registration_executed': False}, ensure_ascii=False))
