"""Root metadata staging for changed compiler parallelism; no helper, Git, CAS or product launch."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = Path(__file__).absolute().parent
UID = 'efa7776ec48e4a7abaa92ce85eb0dace'
OUT = OLD.parent / ('cli43-fresh-held2-r327-' + UID)
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
V7 = BASE / 'cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea'
RUNNER_PACK = BASE / 'cli43_compiler_parallelism_preparation_codex/8ac0acd36c6047beaab455730692d078'
CLOSED = BASE / 'cli43_failed_execution_independent_review_codex/f41d184815b341e086a26d2a750f0b60/review.json'
REVIEW = BASE / 'cli43_current_bound_scope_independent_review_codex/bbd110051f5647d8b6386372ed2cd08c/review.json'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
CANON = ['execution/v2.4/' + name + '.json' for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')]

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def path(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT / p

def pin(value, relative=False):
    p = path(value).absolute()
    data = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix() if relative else str(p),
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def verified(ref):
    data = path(ref['path']).read_bytes()
    need(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], 'Pinned input changed')
    return data

def doc(value):
    return json.loads(path(value).read_bytes().decode('utf-8'))

def clone(value, data):
    with path(value).open('xb') as stream:
        stream.write(data)
    return pin(value)

def save(value, data):
    return clone(value, (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

def invoke(label, argv, env, timeout):
    save(OUT / (label + '.request.json'), {'argv': argv, 'cwd': str(ROOT), 'environment': env,
        'timeout_seconds': timeout, 'automatic_retry': False, 'Windows_Job_or_OS_lifecycle_qualification': False})
    result = None
    error = None
    try:
        with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save(OUT / (label + '.invocation.json'), {'actual_native_exit': result.returncode if result else None,
            'error': error, 'stdout_ref': pin(OUT / (label + '.stdout.raw')) if (OUT / (label + '.stdout.raw')).is_file() else None,
            'stderr_ref': pin(OUT / (label + '.stderr.raw')) if (OUT / (label + '.stderr.raw')).is_file() else None,
            'automatic_retry': False, 'counter_reset': False, 'product_executed': False})
    need(result.returncode == 0, 'Metadata phase failed: ' + label)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, '-I -S -X utf8')
sys.dont_write_bytecode = True
need(pin(CLOSED)['sha256'] == '8cb8fb307dabe2668a736d7e964177a1fd67605a7f380d5f6e06d9268d59a6bb', 'Actual failed-run independent closure')
need(doc(CLOSED)['reviewer'] == 'codex:/root/w05_merge_review' and
     doc(CLOSED)['decision'] == 'FAILED_EXECUTION_EVIDENCE_CLOSED_WITH_QUALIFICATION_WITHHELD', 'No old-run acceptance')
need(pin(RUNNER_PACK / 'handoff.json')['sha256'] == '906e713f8ba9d6a0787b86d9b43b6d456f8b28d7784352df10e6d89f7543a605', 'Actual changed-input handoff')
runner = pin(doc(RUNNER_PACK / 'handoff.json')['candidate_ref']['path'])
verified(runner)
need(runner['sha256'] == '333d69e00a421efcbb08e9ddf06e1486e911cd82af4a0d46a8bb60c8203f2bea', 'Exact two compiler parallelism arguments')
original_ns = [pin(p) for p in sorted(OLD.rglob('*')) if p.is_file()]
inputs = doc(OLD / 'root-inputs.runtime-bound.json')
canonical = [(name, (ROOT / name).read_bytes()) for name in CANON]
cp, ow = [json.loads(raw.decode('utf-8')) for _, raw in canonical[:2]]
need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [326, 154, 450], 'Actual before tuple')
need(cp['head'] == inputs['main_git']['head'], 'Same Main43 head')
for index, ref in enumerate(doc(OLD / 'prepared_refs.json')['desired_refs']):
    need(canonical[index][1] == verified(ref), 'Actual current canonical equals r326 desired')
need(not OUT.exists(), 'Fresh Root namespace')
OUT.mkdir()
(OUT / 'canonical-before').mkdir()
copies = []
for name, raw in canonical:
    copies.append({'canonical_path': name, 'ref': clone(OUT / 'canonical-before' / (Path(name).stem + '.raw'), raw),
                   'live_original_ref': pin(ROOT / name)})
inputs['canonical_before_ref'] = save(OUT / 'canonical-before.json', {'actor': 'codex:/root', 'entries': copies})
for key, name in [('source_inputs_ref', 'source-inputs.json'), ('failure_prefix430_ref', 'failure-prefix430.json')]:
    inputs[key] = clone(OUT / name, verified(inputs[key]))
late_ref = pin(OLD / 'late-origins.capture.json')
need(late_ref['sha256'] == 'afd2d0f0d09aa6c7c0d9ba78e3e7dbd031e2f05e09963aaed3e641dc32822531', 'Original late8 capture')
late = doc(late_ref['path'])
need(late['registered_origin_count'] == 450 and len(late['origins']) == 8, 'Exact late cut')
origin_paths = [path(row['origin_ref']['path']) for row in late['origins']]
origin_paths.append(BASE / 'cli43_fresh_compiler_executor_codex/477e329b79944cb0b33f9ead24811760/failure.origin.json')
origins = []
for p in origin_paths:
    ref = pin(p, relative=True)
    need(all(old.get('evidence_ref', {}).get('sha256') != ref['sha256'] for old in cp['failure_counters']), 'Origin already registered')
    classification = ('SINGLE_GO_BUILD_NATIVE_EXIT_WITH_UNDETERMINED_CAUSE_NOT_PRODUCT_CASE' if p.name == 'failure.origin.json' else
        'COORDINATION_TOOL_DIAGNOSTIC_NO_INFERRED_NATIVE_FAILURE' if p.name == 'failure-origin.collaboration-source-map-limit.json' else
        'READONLY_INVENTORY_NO_MATCH_EXIT_NO_INFERRED_PRODUCT_FAILURE' if p.name == 'failure-origin.a76746.json' else
        'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE')
    origins.append({'evidence_ref': ref, 'original_payload': doc(p), 'counter_reset': False,
                    'automatic_same_input_retry': False, 'classification': classification})
need(len(origins) == 9 and len({row['evidence_ref']['sha256'] for row in origins}) == 9, 'Exact new origin cut')
inputs['before'] = [326, 154, 450]
inputs['after'] = [327, 155, 459]
inputs['origin_cut_ref'] = save(OUT / 'failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'counter_reset': False, 'origins': origins, 'nested_launch_exits_counted_once': True,
    'native_NULL_fields_and_original_payloads_preserved': True,
    'new_later_origins_not_added_to_this_fixed_cut': True})
template = json.loads(verified(inputs['scope_template_ref']).decode('utf-8'))
template['runner_ref'] = runner
inputs['scope_template_ref'] = save(OUT / 'scope.template.runner-v6.json', template)
v7 = doc(V7 / 'handoff.json')
code = []
for ref in v7['wrapper_refs']:
    dest = OUT / Path(ref['path']).name
    clone(dest, verified(ref))
    code.append(pin(dest, relative=True))
for ref in (v7['metadata_module_ref'], v7['unchanged_refs']['binding_builder']):
    verified(ref)
    code.append(pin(ref['path'], relative=True))
inputs['metadata_code_refs_ref'] = save(OUT / 'metadata-code-refs.json', {'entries': code,
    'source_handoff_ref': pin(V7 / 'handoff.json'), 'independent_preparation_review_ref': inputs['v7_binding_provenance']['preparation_review_ref']})
base_ref = doc(inputs['runtime_resources_ref']['path'])['root_metadata_overlay']['base_ref']
catalog = json.loads(verified(base_ref).decode('utf-8'))
need(base_ref['sha256'] == '98b5efb1e3bfa8ab5c64a7ed3280b62ca6c856cc562e1d5ea59f89caca28d6cf' and len(catalog['files']) == 1242, 'Same partial runtime base')
overlay = [pin(ROOT / ref['path']) for ref in code]
need(len(code) == 8 and not ({r['path'].casefold() for r in overlay} & {r['path'].casefold() for r in catalog['files']}), 'Unique metadata overlay')
catalog['files'] += overlay
catalog['schema'] = 'researchos.cli43-public-runtime-resources.root-metadata-overlay.v4'
catalog['root_metadata_overlay'] = {'base_ref': base_ref, 'base_files': 1242, 'metadata_files': 8,
    'original_metadata_refs': code, 'actual_new_metadata_bytes_verified': True,
    'base_resources_rehashed_by_this_writer': False, 'OS_or_Go_resource_set_expansion': False,
    'unknown_loaded_module_policy_unchanged': True, 'complete_runtime_or_lifecycle_qualification': False}
inputs['runtime_resources_ref'] = save(OUT / 'runtime-with-root-metadata.v4.json', catalog)
inputs['run_uuid'] = UID
inputs['registration_namespace'] = OUT.relative_to(ROOT).as_posix()
inputs['controller_review_path'] = str(REVIEW)
inputs['controller_review_ref'] = None
for key in ('new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root'):
    prior = Path(inputs[key])
    dest = prior.parent / prior.name.replace('477e329b79944cb0b33f9ead24811760', UID)
    need(dest.parent.is_dir() and not dest.exists(), 'Fresh disjoint execution and authority leaves')
    inputs[key] = str(dest)
inputs['r327_changed_input_provenance'] = {'prior_run_independent_failed_closure_ref': pin(CLOSED),
    'runner_preparation_handoff_ref': pin(RUNNER_PACK / 'handoff.json'), 'same_input_retry': False,
    'change': 'build-cli and build-test add -p=1; old quiet native1 cause remains UNKNOWN',
    'parallelism_preparation_review_ref': pin(BASE / 'cli43_compiler_parallelism_static_independent_review_codex/3cd7de459bfb4caf8cbfa7044c75381c/review.json'),
    'prior_actual_root_completion_ref': pin(OLD / 'root-launch.outer-completion.json'),
    'prior_root_closed_manifest_ref': pin(OLD / 'root-launch.closed.manifest.json'),
    'triage_handoff_ref': pin(BASE / 'cli43_quiet_build_readonly_triage_codex/11fc59d13e2547ebbf71c593b46f596a/handoff.json')}
save(OUT / 'root-inputs.runtime-bound.json', inputs)
builder = v7['unchanged_refs']['binding_builder']
argv = [PYTHON, '-I', '-S', '-X', 'utf8', builder['path']]
for key in ('scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
    'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref'):
    argv += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
argv += ['--controller-review-ref', 'null']
for key in ('before', 'after', 'main_git', 'public_environment'):
    argv += ['--' + key.replace('_', '-'), json.dumps(inputs[key], ensure_ascii=False)]
for key in ('run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
            'new_export_root', 'new_authorization_root', 'new_grant_preflight_root'):
    argv += ['--' + key.replace('_', '-'), inputs[key]]
argv += ['--output', str(OUT / 'binding.pre-review.json')]
invoke('binding-build', argv, inputs['public_environment'], 60)
invoke('scope-build', [PYTHON, '-I', '-S', '-X', 'utf8', str(OUT / 'scope_builder.py'),
    '--binding-ref', json.dumps(pin(OUT / 'binding.pre-review.json'), ensure_ascii=False), '--output', str(OUT),
    '--scope-template-ref', json.dumps(inputs['scope_template_ref'], ensure_ascii=False)], inputs['public_environment'], 900)
scope_ref = pin(OUT / 'scope_registration.json')
old_driver = (OLD / 'root-metadata-phase.py').read_bytes()
old_anchor = b"SCOPE_SHA = '68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566'"
need(old_driver.count(old_anchor) == 1, 'Exact single outer scope pin')
clone(OUT / 'root-metadata-phase.py', old_driver.replace(old_anchor, ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii')))
need(all((ROOT / name).read_bytes() == raw for name, raw in canonical), 'Canonical untouched by staging')
need(all(pin(ref['path']) == ref for ref in original_ns), 'Original r326 namespace byte prefix preserved')
save(OUT / 'bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref,
    'scope_invocation_ref': pin(OUT / 'scope_registration.json', relative=True), 'runtime_files': 1250,
    'expected_before': inputs['before'], 'expected_after': inputs['after'], 'actual_metadata_native_exits': [0, 0],
    'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0})
save(OUT / 'bound-scope.manifest.json', {'entries': [pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()], 'self_excluded': True})
print(json.dumps({'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'runtime_ref': inputs['runtime_resources_ref'], 'before': inputs['before'], 'after': inputs['after'],
    'actual_registration_executed': False}, ensure_ascii=False))
