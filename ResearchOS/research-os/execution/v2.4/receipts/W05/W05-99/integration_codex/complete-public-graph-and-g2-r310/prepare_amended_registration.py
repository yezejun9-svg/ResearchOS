import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def script(path, source):
    ast.parse(source)
    with path.open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return ref(path)


prepared = json.loads((OUT / 'prepared_refs.json').read_bytes())
for pin in prepared['canonical_before']:
    assert ref(ROOT / pin['path']) == pin
listed = (OUT / 'list_replay.py').read_text('utf-8')
listed = listed.replace('import importlib.util', 'import types')
original = """    helper_spec = importlib.util.spec_from_file_location('researchos_root_owned_windows_process', helper_path)
    helper_module = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper_module)"""
replacement = """    helper_raw = helper_path.read_bytes()
    assert hashlib.sha256(helper_raw).hexdigest() == scope['owned_process_helper_ref']['sha256']
    helper_module = types.ModuleType('researchos_root_owned_windows_process')
    helper_module.__file__ = str(helper_path)
    # Compile verified source bytes directly: no SourceFileLoader or existing pyc read.
    exec(compile(helper_raw, str(helper_path), 'exec'), helper_module.__dict__)"""
assert listed.count(original) == 1
listed = listed.replace(original, replacement).replace("DRAFT / 'list_independent_scope.json'", "DRAFT / 'list_independent_scope.v2.json'")
listed_ref = script(OUT / 'list_replay.v2.py', listed)
listed_scope = json.loads((OUT / 'list_independent_scope.json').read_bytes())
listed_scope['runner_ref'] = listed_ref
listed_scope['prior_unexecuted_draft_scope_ref'] = ref(OUT / 'list_independent_scope.json')
listed_scope['helper_loading_amendment'] = 'Compile verified source bytes directly with ModuleType; no helper SourceFileLoader or helper pyc read. All actual imported module source/cache and DLL resources remain frozen.'
list_scope_ref = save('list_independent_scope.v2.json', listed_scope)
g2 = (OUT / 'g2_replay.v3.py').read_text('utf-8')
original = "        resources=self.resource_paths(); self.guarded=vector(resources); save(self.phaseout/'resources.before.json',self.guarded)"
replacement = "        resources=self.resource_paths(); resource_baseline=vector(resources); self.guarded=resource_baseline; save(self.phaseout/'resources.before.json',resource_baseline)"
assert g2.count(original) == 1
g2 = g2.replace(original, replacement)
original = "        self.guarded=vector(paths); save(self.phaseout/'inputs.before-build.json',self.guarded)"
replacement = """        # Preserve the original resource cohort across export and dependency discovery.
        check_vector(resource_baseline,self.phaseout/'resources.after-export-and-graph.json')
        self.guarded=vector(paths); save(self.phaseout/'inputs.before-build.json',self.guarded)"""
assert g2.count(original) == 1
g2 = g2.replace(original, replacement)
original = "        check_vector(self.guarded,self.phaseout/'inputs.after-build.json')"
replacement = """        check_vector(resource_baseline,self.phaseout/'resources.after-build.json')
        check_vector(self.guarded,self.phaseout/'inputs.after-build.json')"""
assert g2.count(original) == 1
g2 = g2.replace(original, replacement)
g2_ref = script(OUT / 'g2_replay.v4.py', g2)
g2_scope = json.loads((OUT / 'g2_prepare_scope.json').read_bytes())
g2_scope['runner_ref'] = g2_ref
g2_scope['prior_unexecuted_draft_scope_ref'] = ref(OUT / 'g2_prepare_scope.json')
g2_scope['original_resource_baseline_preserved'] = 'Original resources.before pinned vector checked after export/graph before any baseline expansion and again after build; before-build vector also checked unchanged.'
g2_scope_ref = save('g2_prepare_scope.v2.json', g2_scope)
amendment = save('controller-static-fixes.v2.json', {'status': 'STATIC_AMENDED_NOT_EXECUTED',
    'list_original': ref(OUT / 'list_replay.py'), 'list_new': listed_ref,
    'g2_original': ref(OUT / 'g2_replay.v3.py'), 'g2_new': g2_ref,
    'issues': ['Helper existing pyc could be read outside runtime inventory', 'G2 resource baseline could be overwritten before drift comparison'],
    'actual_failed_invocations': 0, 'failure_counter_delta': 0, 'product_test_cases': 0,
    'helper_DLL_SDK_MODEL_Node_HTTP_import_or_execution': 0, 'formal_increment': 0})
register = (OUT / 'register.py').read_text('utf-8').replace('prepared_refs.json', 'prepared_refs.v2.json')
register_ref = script(OUT / 'register.v2.py', register)
wrapper = (OUT / 'run.py').read_text('utf-8').replace('prepared_refs.json', 'prepared_refs.v2.json').replace('register.py', 'register.v2.py').replace('audit.json', 'audit.v2.json')
wrapper_ref = script(OUT / 'run.v2.py', wrapper)
pins = prepared['pins']
pins.update(list_scope=list_scope_ref, list_runner=listed_ref, g2_scope=g2_scope_ref, g2_runner=g2_ref,
            controllers_v2_amendment=amendment)
audit = json.loads((OUT / 'audit.json').read_bytes())
audit['immutable_original_draft_audit'] = ref(OUT / 'audit.json')
audit['static_controller_fixes'] = amendment
audit['scopes'] = {k: pins[k] for k in ['cli17_scope', 'cli_windows4_scope', 'list_scope', 'g2_scope']}
pins['audit'] = save('audit.v2.json', audit)
for pin in [listed_ref, list_scope_ref, g2_ref, g2_scope_ref, amendment, register_ref, wrapper_ref, pins['audit']]:
    if pin not in prepared['verified_refs']:
        prepared['verified_refs'].append(pin)
prepared['immutable_previous_prepared_refs'] = ref(OUT / 'prepared_refs.json')
prepared_ref = save('prepared_refs.v2.json', prepared)
for name, scope, runner, new_scope, new_runner in [
    ('root-list14-launch-r310', 'list_independent_scope.json', 'list_replay.py', list_scope_ref, listed_ref),
    ('root-g2-prepare-launch-r310', 'g2_prepare_scope.json', 'g2_replay.v3.py', g2_scope_ref, g2_ref)]:
    launch_path = OUT.parent / name / 'launch.py'
    source = launch_path.read_text('utf-8').replace('prepared_refs.json', 'prepared_refs.v2.json')
    source = source.replace(scope, Path(new_scope['path']).name).replace(runner, Path(new_runner['path']).name)
    original_scope = ref(OUT / scope)
    original_runner = ref(OUT / runner)
    source = source.replace(original_scope['sha256'], new_scope['sha256']).replace(original_runner['sha256'], new_runner['sha256'])
    script(launch_path.with_name('launch.v2.py'), source)
assert all(ref(ROOT / pin['path']) == pin for pin in prepared['canonical_before'])
print(json.dumps({'state': 'V2_DRAFT_PREPARED_NOT_EXECUTED', 'register': register_ref,
    'wrapper': wrapper_ref, 'prepared': prepared_ref, 'audit': pins['audit'],
    'list_runner': listed_ref, 'list_scope': list_scope_ref, 'g2_runner': g2_ref,
    'g2_scope': g2_scope_ref}, ensure_ascii=True))
