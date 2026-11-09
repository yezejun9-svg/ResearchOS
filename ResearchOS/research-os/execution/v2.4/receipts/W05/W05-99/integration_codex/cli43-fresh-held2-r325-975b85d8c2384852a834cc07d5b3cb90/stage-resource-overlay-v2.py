"""Root input-only repair for exact gate ref spelling and observed metadata modules."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/46bfd2f723c84ad68e321774d6e08b30/review.json'

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

def save(name, value):
    with (OUT / name).open('xb') as handle:
        handle.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)

def doc(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
before_refs = [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()]
need(pin(OUT / 'scope_registration.json')['sha256'] == '3c70764ec5eec52475ede71e196557a354b4aecef4d50c84b7df6433d7d150dc', 'Old full scope unchanged')
need(not (OUT / 'binding.json').exists() and not (OUT / 'prepare.started.json').exists(), 'No previous metadata preparation')
inputs = doc(OUT / 'root-inputs.runtime-bound.json')
for entry in doc(OUT / 'canonical-before.json')['entries']:
    need((ROOT / entry['canonical_path']).read_bytes() == raw(entry['ref']), 'Live four canonical unchanged')
base_ref = inputs['runtime_resources_ref']
need(base_ref['sha256'] == '98b5efb1e3bfa8ab5c64a7ed3280b62ca6c856cc562e1d5ea59f89caca28d6cf', 'Original bounded runtime')
base = json.loads(raw(base_ref).decode('utf-8'))
need(len(base['files']) == 1242, 'Original declared runtime count')
overlay = []
original_code = doc(OUT / 'metadata-code-refs.json')['entries']
for ref in original_code:
    data = raw(ref)
    absolute = pin(ROOT / ref['path'])
    need(absolute['sha256'] == ref['sha256'] and absolute['bytes'] == ref['bytes'], 'Metadata absolute identity')
    overlay.append(absolute)
need(len(overlay) == 8, 'Six wrappers and two fixed metadata modules')
old_paths = {str(Path(ref['path']).absolute()).casefold() for ref in base['files']}
need(all(ref['path'].casefold() not in old_paths for ref in overlay), 'Overlay paths must be new to runtime catalog')
catalog = copy.deepcopy(base)
catalog['schema'] = 'researchos.cli43-public-runtime-resources.root-metadata-overlay.v4'
catalog['files'] += overlay
catalog['root_metadata_overlay'] = {'base_ref': base_ref, 'base_files': 1242, 'metadata_files': 8,
    'actual_new_metadata_bytes_verified': True, 'metadata_original_refs': original_code,
    'base_resources_rehashed_by_this_metadata_writer': False,
    'OS_or_Go_resource_set_expansion': False, 'unknown_loaded_module_policy_unchanged': True,
    'complete_runtime_or_lifecycle_qualification': False}
runtime_ref = save('runtime-with-root-metadata.v4.json', catalog)
inputs['runtime_resources_ref'] = runtime_ref
inputs['controller_review_path'] = str(REVIEW)
inputs['controller_review_ref'] = None
inputs['input_only_cross_path_repair'] = {'scope_reference_spelling': 'Root-relative, exactly Gate.Reader.ref()',
    'metadata_runtime_overlay': 'Eight already pinned public source modules; original1242 retained verbatim',
    'previous_scope_manifest_ref': pin(OUT / 'bound-scope.manifest.json'), 'old_scope_product_execution': False}
save('root-inputs.runtime-bound.v2.json', inputs)
binding = doc(OUT / 'binding.pre-review.json')
binding.update(runtime_resources_ref=runtime_ref, controller_review_path=str(REVIEW), controller_review_ref=None)
save('binding.pre-review.v2.json', binding)
scope = doc(OUT / 'scope_registration.json')
scope.update(runtime_resources_ref=runtime_ref, controller_review_path=str(REVIEW))
scope_ref = save('scope_registration.v2.json', scope)

# All other outer orchestration code remains byte-for-byte identical.
driver = (OUT / 'root-metadata-phase.py').read_bytes()
old_driver = driver
replacements = [
    (b"SCOPE_SHA = '3c70764ec5eec52475ede71e196557a354b4aecef4d50c84b7df6433d7d150dc'",
        ("SCOPE_SHA = '" + scope_ref['sha256'] + "'").encode('ascii')),
    (b"root-inputs.runtime-bound.json", b"root-inputs.runtime-bound.v2.json"),
    (b"binding.pre-review.json", b"binding.pre-review.v2.json"),
    (b"scope_registration.json", b"scope_registration.v2.json"),
    (b"scope_ref = pin(OUT / 'scope_registration.v2.json')",
        b"scope_ref = pin(OUT / 'scope_registration.v2.json')\nscope_ref['path'] = (OUT / 'scope_registration.v2.json').relative_to(ROOT).as_posix()"),
]
for old, new in replacements:
    need(old in driver, 'Exact outer driver replacement anchor')
    driver = driver.replace(old, new)
with (OUT / 'root-metadata-phase.v2.py').open('xb') as handle:
    handle.write(driver)
restored = driver
for old, new in reversed(replacements):
    restored = restored.replace(new, old)
need(restored == old_driver, 'Whole outer driver inverse bytes')
save('resource-overlay.audit.json', {'actor': 'codex:/root', 'old_scope_ref': pin(OUT / 'scope_registration.json'),
    'new_scope_ref': scope_ref, 'scope_invocation_ref': pin(OUT / 'scope_registration.v2.json', relative=True),
    'new_runtime_ref': runtime_ref, 'runtime_total': 1250, 'metadata_overlay': overlay,
    'outer_driver_inverse': True, 'future_expected_before': inputs['before'], 'future_expected_after': inputs['after'],
    'actual_binding_builder_helper_Git_CAS_product_calls': 0, 'formal_increment': 0})
need(all(pin(ref['path']) == ref for ref in before_refs), 'Original namespace prefix changed')
save('bound-scope.v2.manifest.json', {'entries': [pin(path) for path in sorted(OUT.rglob('*')) if path.is_file()],
    'self_excluded': True, 'original_namespace_prefix_unchanged': True})
print(json.dumps({'scope_ref': scope_ref, 'manifest_ref': pin(OUT / 'bound-scope.v2.manifest.json'),
    'runtime_ref': runtime_ref, 'actual_registration_executed': False}, ensure_ascii=False))
