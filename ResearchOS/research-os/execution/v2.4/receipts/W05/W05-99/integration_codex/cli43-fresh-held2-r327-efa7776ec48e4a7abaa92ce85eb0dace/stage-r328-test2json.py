"""Root metadata staging for explicit fresh test2json and rejected-load diagnostics; no helper, Git, CAS or product launch."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = Path(__file__).absolute().parent
UID = 'bf943a8137c74df09e010347615b0eec'
OUT = OLD.parent / ('cli43-fresh-held2-r328-' + UID)
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
V7 = BASE / 'cli43_root_binding_preparation_revision_codex/9fd9cbeb1343442aa6e34e41f3f2deea'
RUNNER_PACK = BASE / 'cli43_test2json_preparation_codex/72d89fe5130e4e83a7dc44257289c1db'
CLOSED = BASE / 'cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317/review.json'
REVIEW = BASE / 'cli43_current_bound_scope_independent_review_codex/b8b6f2f680cd4cb5986152ac4ef09994/review.json'
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
need(pin(CLOSED)['sha256'] == '3e4fe1b97b9a3a937ed2c557d240c91477e309c0e114d0549fbb4e83cce9dbcb', 'Actual failed-run independent closure')
need(doc(CLOSED)['reviewer'] == 'codex:/root/w05_merge_review' and
     doc(CLOSED)['decision'] == 'ACTUAL_FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD', 'No old-run acceptance')
need(pin(RUNNER_PACK / 'handoff.json')['sha256'] == '3f84b6b3c1230d237f0ac6c327e87b3d4152228810d47818d68c0c1b0b74c289', 'Actual changed-input handoff')
runner = pin(doc(RUNNER_PACK / 'handoff.json')['runner_ref']['path'])
verified(runner)
need(runner['sha256'] == '5297321f966da060d2f9e941d358052ef2dae63ccc6e1f1217e22bef87c52c0e', 'Exact independently reviewed test2json runner')
helper = pin(doc(RUNNER_PACK / 'handoff.json')['diagnostic_helper_ref']['path'])
need(helper['sha256'] == '9c771cd3b9fd41a71b70ced0b27ca45bd6a138b3ebff88ff50153530db407095', 'Exact independently reviewed diagnostic helper')
original_ns = [pin(p) for p in sorted(OLD.rglob('*')) if p.is_file()]
inputs = doc(OLD / 'root-inputs.runtime-bound.json')
canonical = [(name, (ROOT / name).read_bytes()) for name in CANON]
cp, ow = [json.loads(raw.decode('utf-8')) for _, raw in canonical[:2]]
need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [327, 155, 459], 'Actual before tuple')
need(cp['head'] == inputs['main_git']['head'], 'Same Main43 head')
for index, ref in enumerate(doc(OLD / 'prepared_refs.json')['desired_refs']):
    need(canonical[index][1] == verified(ref), 'Actual current canonical equals r327 desired')
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
late_ref = pin(OLD / 'late-origins.capture.for-r328.json')
need(late_ref['sha256'] == '175c220137bc50a94e8af955797addf6b96cedb7535bfe87eb789de54af93af9', 'Fixed ten-origin cut retained verbatim')
late = doc(late_ref['path'])
need(late['before'] == [327,155,459] and late['after'] == [328,156,469] and len(late['origins']) == 10, 'Exact late cut')
origins = copy.deepcopy(late['origins'])
for row in origins:
    verified(row['evidence_ref'])
    need(all(old.get('evidence_ref', {}).get('sha256') != row['evidence_ref']['sha256'] for old in cp['failure_counters']), 'Origin already registered')
need(len({r['evidence_ref']['sha256'] for r in origins}) == 10, 'Distinct original evidence per origin')
inputs['before'] = [327, 155, 459]
inputs['after'] = [328, 156, 469]
inputs['origin_cut_ref'] = save(OUT / 'failure-origins.cut.json', {'before': inputs['before'], 'after': inputs['after'],
    'counter_reset': False, 'origins': origins, 'nested_launch_exits_counted_once': True,
    'native_NULL_fields_and_original_payloads_preserved': True,
    'new_later_origins_not_added_to_this_fixed_cut': True})
template = json.loads(verified(inputs['scope_template_ref']).decode('utf-8'))
template['runner_ref'] = runner
template['debug_tree_helper_ref'] = helper
inputs['scope_template_ref'] = save(OUT / 'scope.template.runner-v7.json', template)
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
    dest = prior.parent / prior.name.replace('efa7776ec48e4a7abaa92ce85eb0dace', UID)
    need(dest.parent.is_dir() and not dest.exists(), 'Fresh disjoint execution and authority leaves')
    inputs[key] = str(dest)
inputs['r328_changed_input_provenance'] = {'prior_run_independent_failed_closure_ref': pin(CLOSED),
    'runner_preparation_handoff_ref': pin(RUNNER_PACK / 'handoff.json'), 'same_input_retry': False,
    'change': 'fresh cmd/test2json graph/build/buildinfo/pin then direct tool; first rejected hFile fact metadata only; old generation16 identity remains NULL',
    'test2json_preparation_review_ref': pin(BASE / 'cli43_test2json_static_independent_review_codex/9fb108715041425d8c6dda77f2bd4d02/review.json'),
    'prior_actual_root_completion_ref': pin(OLD / 'root-launch.outer-completion.json'),
    'prior_root_closed_manifest_ref': pin(OLD / 'root-launch.closed.manifest.json'),
    'triage_handoff_ref': pin(BASE / 'cli43_failed_execution_independent_review_codex/3199a5187cee46729d7b8b2a6a5f7317/handoff.json'), 'diagnostic_helper_ref': helper, 'late_cut_capture_ref': late_ref}
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
old_anchor = b"SCOPE_SHA = '320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'"
need(old_driver.count(old_anchor) == 1, 'Exact single outer scope pin')
clone(OUT / 'root-metadata-phase.py', old_driver.replace(old_anchor, ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii')))
need(all((ROOT / name).read_bytes() == raw for name, raw in canonical), 'Canonical untouched by staging')
need(all(pin(ref['path']) == ref for ref in original_ns), 'Original r327 namespace byte prefix preserved')
save(OUT / 'bound-scope-audit.json', {'actor': 'codex:/root', 'scope_ref': scope_ref,
    'scope_invocation_ref': pin(OUT / 'scope_registration.json', relative=True), 'runtime_files': 1250,
    'expected_before': inputs['before'], 'expected_after': inputs['after'], 'actual_metadata_native_exits': [0, 0],
    'actual_helper_Git_CAS_grant_product_calls': 0, 'formal_increment': 0})
save(OUT / 'bound-scope.manifest.json', {'entries': [pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()], 'self_excluded': True})
print(json.dumps({'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.manifest.json'),
    'runtime_ref': inputs['runtime_resources_ref'], 'before': inputs['before'], 'after': inputs['after'],
    'actual_registration_executed': False}, ensure_ascii=False))
